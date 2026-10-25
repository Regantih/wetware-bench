"""Real recorded organoid data — first contact with actual biology.

Recorded spike trains can't be *driven* (no closed loop on a recording),
so instead of forcing them through the probe interface we measure the
things that tell us whether our sim is honest:

  * firing statistics: per-channel rates, Fano factor (burstiness)
  * drift: how much channel-rate vectors decorrelate across the recording
  * connectivity: pairwise cross-correlation structure
  * sim comparison: identical metrics on SimSNN spontaneous activity

CLI:  python -m bench.realdata spikes.csv [--report docs/real_data_report.md]
CSV format: one spike per row, columns auto-detected among
{time,timestamp,ts},{channel,electrode,ch}.
"""

import argparse
import csv
from pathlib import Path

import numpy as np


def load_spikes(path):
    """CSV or .mat (v7.3 HDF5) -> (times_seconds, channels_int)."""
    path = str(path)
    if path.endswith(".mat"):
        return _load_mat(path)
    return _load_csv(path)


def _load_mat(path):
    """FinalSpark/Zenodo per-organoid .mat: spike_times is an (n_ch,1) cell
    of per-channel time vectors; channel index = electrode."""
    import h5py
    times, chans = [], []
    with h5py.File(path) as h:
        st = h["spike_times"]
        for i in range(st.shape[0]):
            vec = h[st[i, 0]][()].ravel()
            times.append(vec)
            chans.append(np.full(len(vec), i))
    return np.concatenate(times), np.concatenate(chans).astype(int)


def _load_csv(path):
    """CSV -> (times_seconds, channels_int). Column names auto-detected."""
    with open(path, newline="") as f:
        r = csv.reader(f)
        header = [h.strip().lower() for h in next(r)]
        ti = next((i for i, h in enumerate(header)
                   if h in ("time", "timestamp", "ts", "time_s")), 0)
        ci = next((i for i, h in enumerate(header)
                   if h in ("channel", "electrode", "ch", "chan")), 1)
        rows = [(float(row[ti]), int(float(row[ci])))
                for row in r if len(row) > max(ti, ci) and row[ti].strip()]
    times = np.array([t for t, _ in rows])
    chans = np.array([c for _, c in rows], dtype=int)
    return times, chans


def bin_counts(times, chans, n_ch=None, bin_s=1.0):
    n_ch = n_ch or int(chans.max() + 1)
    t0 = times.min()
    n_bins = int(np.ceil((times.max() - t0) / bin_s))
    counts = np.zeros((n_bins, n_ch))
    idx = ((times - t0) / bin_s).astype(int)
    idx = np.clip(idx, 0, n_bins - 1)
    np.add.at(counts, (idx, chans), 1)
    return counts


def analyze(counts, bin_s=1.0, label="recording", fine=None):
    """Core metrics on a (n_bins, n_ch) count matrix. If `fine` is given
    (same recording at finer binning), also computes transfer entropy
    and neuronal-avalanche statistics on it."""
    rates = counts.mean(axis=0) / bin_s                     # Hz per channel
    active = rates > 0.01
    # burstiness: Fano factor across bins, per channel
    ff = np.array([counts[:, c].var() / max(counts[:, c].mean(), 1e-9)
                   for c in np.where(active)[0]])
    # drift: cosine similarity of channel-rate vectors, first vs last 20%
    k = max(1, counts.shape[0] // 5)
    a, b = counts[:k].mean(0), counts[-k:].mean(0)
    drift = float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
    # connectivity: max/mean pairwise corr between active channels
    if active.sum() > 2:
        cc = np.corrcoef(counts[:, active].T)
        cc = cc[~np.eye(cc.shape[0], dtype=bool)]
        conn = {"mean": float(np.mean(np.abs(cc))),
                "max": float(np.max(cc))}
    else:
        conn = {"mean": 0.0, "max": 0.0}
    out = {
        "label": label,
        "duration_s": float(counts.shape[0] * bin_s),
        "n_channels": int(counts.shape[1]),
        "n_active": int(active.sum()),
        "total_spikes": int(counts.sum()),
        "mean_rate_hz": float(rates[active].mean()) if active.any() else 0.0,
        "max_rate_hz": float(rates.max()),
        "fano_factor": float(np.median(ff)) if len(ff) else 0.0,
        "drift_similarity": drift,          # 1.0 = stationary; <1 = drifting
        "corr_mean": conn["mean"],
        "corr_max": conn["max"],
    }
    if fine is not None:
        out.update(transfer_entropy(fine))
        out.update(avalanches(fine))
    return out


def sim_spontaneous(n_steps=9600, channels=8, bin=64, seed=0):
    """SimSNN resting-state activity, sampled like an MEA: `channels`
    randomly chosen hidden neurons (electrodes sit next to arbitrary
    neurons, not the calibrated readout). Spikes are binned `bin`
    steps at a time — returns (n_steps/bin, channels) counts."""
    from .substrates.snn_sim import SimSNN
    s = SimSNN(seed=seed)
    x = np.zeros(s.n_inputs)
    elec = s._rng.choice(s.n_hidden, channels, replace=False)
    sp = np.array([s._step(x)[elec] for _ in range(n_steps)])
    return sp[:len(sp) - len(sp) % bin].reshape(-1, bin, channels).sum(1)


def transfer_entropy(counts, n_pairs=10, seed=0):
    """Order-1 binary transfer entropy between channel pairs (bits/bin).

    TE_{i->j} = H(j_t | j_{t-1}) - H(j_t | j_{t-1}, i_{t-1}) — how much
    knowing channel i's last bin reduces uncertainty about channel j's
    next bin, beyond what j's own past already explains. Directed
    connectivity, unlike symmetric correlation.
    """
    b = (counts > 0).astype(np.int8)
    n_ch = b.shape[1]
    rng = np.random.default_rng(seed)
    pairs = [(i, j) for i in range(n_ch) for j in range(n_ch) if i != j]
    if len(pairs) > n_pairs:
        idx = rng.choice(len(pairs), n_pairs, replace=False)
        pairs = [pairs[k] for k in idx]
    te = []
    for i, j in pairs:
        x, y = b[:-1, i], b[1:, j]         # past of i, current j
        yp = b[:-1, j]                     # past of j
        # joint histogram over (y_past, x_past, y_now)
        key = (yp << 2) | (x << 1) | y
        cnt = np.bincount(key, minlength=8)
        p = cnt / cnt.sum()
        def P(*bits):  # marginal prob helper
            return p.reshape(2, 2, 2)[bits]
        val = 0.0
        for yp_, x_, y_ in np.ndindex(2, 2, 2):
            pj = P(yp_, x_, y_)
            if pj <= 0:
                continue
            p_y_gx = (P(yp_, x_, y_)
                      / (P(yp_, x_, 0) + P(yp_, x_, 1) + 1e-12))
            p_y = (P(yp_, 0, y_) + P(yp_, 1, y_)) / \
                  (P(yp_, 0, 0) + P(yp_, 0, 1) + P(yp_, 1, 0) + P(yp_, 1, 1) + 1e-12)
            if p_y_gx > 0 and p_y > 0:
                val += pj * np.log2(p_y_gx / p_y)
        te.append(val)
    te = np.array(te)
    return {"te_mean_bits": float(te.mean()), "te_max_bits": float(te.max())}


def avalanches(counts, thresh=1):
    """Neuronal avalanches: runs of bins with >=thresh total spikes,
    bounded by silent bins. Critical systems show size ~ power-law
    (exponent ~-1.5) and branching parameter ~1."""
    pop = counts.sum(axis=1)
    in_av, sizes, durs = False, [], []
    for v in pop:
        if v >= thresh:
            if not in_av:
                sizes.append(0.0)
                durs.append(0)
                in_av = True
            sizes[-1] += v
            durs[-1] += 1
        else:
            in_av = False
    if not sizes:
        return {"n_avalanches": 0}
    sizes, durs = np.array(sizes), np.array(durs)
    # branching parameter: mean ratio of consecutive bin totals inside avalanches
    ratios = [pop[t + 1] / pop[t] for t in range(len(pop) - 1)
              if pop[t] >= thresh and pop[t + 1] >= thresh]
    sigma = float(np.mean(ratios)) if ratios else 0.0
    # crude power-law exponent: MLE for discrete sizes >= xmin
    xmin = max(2, np.percentile(sizes, 50))
    s = sizes[sizes >= xmin]
    alpha = 1 + len(s) / max(np.log(s / (xmin - 0.5)).sum(), 1e-9)
    return {"n_avalanches": int(len(sizes)),
            "av_size_median": float(np.median(sizes)),
            "av_size_max": float(sizes.max()),
            "av_dur_median": float(np.median(durs)),
            "branching_sigma": sigma,       # ~1 = critical, <1 sub, >1 super
            "alpha_size": float(alpha)}     # ~1.5 = critical exponent


def report(datasets, out=None):
    lines = ["# Real-data report — recorded organoid vs. simulated SNN", "",
             "| metric | " + " | ".join(d["label"] for d in datasets) + " |",
             "|---|" + "---|" * len(datasets)]
    keys = [("te_mean_bits", "transfer entropy mean (bits)"),
            ("te_max_bits", "transfer entropy max (bits)"),
            ("n_avalanches", "avalanches"),
            ("av_size_median", "avalanche size (median)"),
            ("av_size_max", "avalanche size (max)"),
            ("branching_sigma", "branching param σ (~1=critical)"),
            ("alpha_size", "avalanche size α (~1.5=critical)"),
            ("duration_s", "duration (s)"), ("n_channels", "channels"),
            ("n_active", "active channels"), ("total_spikes", "spikes"),
            ("mean_rate_hz", "mean rate (Hz)"), ("max_rate_hz", "max rate (Hz)"),
            ("fano_factor", "Fano factor (burstiness)"),
            ("drift_similarity", "drift similarity (1=stationary)"),
            ("corr_mean", "mean |channel corr|"), ("corr_max", "max channel corr")]
    for k, label in keys:
        lines.append(f"| {label} | "
                     + " | ".join(f"{d[k]:.3g}" if k in d else "—"
                                 for d in datasets) + " |")
    lines += ["",
              "- **Fano factor** >>1 means bursty/poisson-clustered activity; "
              "~1 means regular. Living MEA data is typically far burstier "
              "than a Poisson process.",
              "- **Drift similarity** <0.9 over a session means the 'computer' "
              "measurably changed while you watched it.",
              "- **Channel corr** on real MEAs shows structured co-activation; "
              "an uncorrelated sim understates coupling.",
              ""]
    text = "\n".join(lines)
    if out:
        Path(out).write_text(text, encoding="utf-8")
    try:
        print(text)
    except UnicodeEncodeError:  # windows cp1252 console
        print(text.encode("ascii", "replace").decode())
    return text


def main():
    p = argparse.ArgumentParser(prog="bench.realdata")
    p.add_argument("csv", nargs="?")
    p.add_argument("--bin-s", type=float, default=1.0)
    p.add_argument("--sim", action="store_true",
                   help="also analyze SimSNN spontaneous activity")
    p.add_argument("--report", default=None)
    a = p.parse_args()
    ds = []
    if a.csv:
        t, c = load_spikes(a.csv)
        ds.append(analyze(bin_counts(t, c, bin_s=a.bin_s), a.bin_s,
                          label=Path(a.csv).stem))
    if a.sim or not a.csv:
        ds.append(analyze(sim_spontaneous(), a.bin_s * 8,
                          label="sim_snn (resting)"))
    report(ds, a.report)


if __name__ == "__main__":
    main()
