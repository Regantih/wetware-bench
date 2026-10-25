"""Session checkpointing — the plumbing for multi-day wetware runs.

Living cultures can't be snapshotted, but every *simulated* substrate's
learned state (weights, traces, calibration) is just ndarray attributes —
save them to .npz, restore into a fresh instance later. Probe results go
to JSON alongside, timestamped, so a multi-session protocol is just:

    save_session("day1", sub, results)
    sub2 = load_session("day1", "snn")   # tomorrow: same weights, fresh run
"""

import json
import time
from pathlib import Path

import numpy as np

from .substrates import make


def save_session(tag: str, sub, results: list, outdir: str = "results/sessions"):
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    arrs = {}
    target = getattr(sub, "base", sub)          # unwrap codec if present
    for k, v in vars(target).items():
        if isinstance(v, np.ndarray) and v.dtype.kind in "fi":
            arrs[k] = v
    # codec state worth persisting: the fitted channel model
    if target is not sub:
        for k in ("_A", "_cand", "_cand_r"):
            v = getattr(sub, k, None)
            if isinstance(v, np.ndarray):
                arrs[f"enc{k}"] = v
    np.savez_compressed(out / f"{tag}_{sub.name}.npz", **arrs)
    blob = {
        "tag": tag, "substrate": sub.name,
        "saved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": [{"probe": r.probe, "substrate": r.substrate,
                     "metrics": r.metrics, "notes": r.notes}
                    for r in results],
    }
    (out / f"{tag}_{sub.name}.json").write_text(json.dumps(blob, indent=2))
    return out / f"{tag}_{sub.name}.npz"


def load_session(tag: str, name: str, outdir: str = "results/sessions",
                 **make_kw):
    sub = make(name, **make_kw)
    target = getattr(sub, "base", sub)
    npz = np.load(Path(outdir) / f"{tag}_{sub.name}.npz")
    for k in npz.files:
        if k.startswith("enc"):
            setattr(sub, k, npz[k])
        else:
            setattr(target, k, npz[k])
    return sub
