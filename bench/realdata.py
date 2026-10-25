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


def analyze(counts, bin_s=1.0, label="recording"):
    """Core metrics on a (n_bins, n_ch) count matrix."""
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
    return {
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


def sim_spontaneous(n_steps=1200, bin_steps=8, seed=0):
    """SimSNN resting-state counts, same shape as real data (bins x ch)."""
    from .substrates.snn_sim import SimSNN
    s = SimSNN(seed=seed)
    x = np.zeros(s.n_inputs)
    return np.array([s.stimulate(x) for _ in range(n_steps)])


def report(datasets, out=None):
    lines = ["# Real-data report — recorded organoid vs. simulated SNN", "",
             "| metric | " + " | ".join(d["label"] for d in datasets) + " |",
             "|---|" + "---|" * len(datasets)]
    keys = [("duration_s", "duration (s)"), ("n_channels", "channels"),
            ("n_active", "active channels"), ("total_spikes", "spikes"),
            ("mean_rate_hz", "mean rate (Hz)"), ("max_rate_hz", "max rate (Hz)"),
            ("fano_factor", "Fano factor (burstiness)"),
            ("drift_similarity", "drift similarity (1=stationary)"),
            ("corr_mean", "mean |channel corr|"), ("corr_max", "max channel corr")]
    for k, label in keys:
        lines.append(f"| {label} | "
                     + " | ".join(f"{d[k]:.3g}" for d in datasets) + " |")
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
    print(text)
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
        ds.append(analyze(sim_spontaneous(), bin_steps=8,
                          label="sim_snn (resting)"))
    report(ds, a.report)


if __name__ == "__main__":
    main()
