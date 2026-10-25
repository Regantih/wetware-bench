"""Multi-seed statistics — a single run is an anecdote.

Runs each (probe, substrate) pair on a fresh instance per seed and
reports mean ± 95% CI per metric. All scoreboard claims downstream of
this file should be read as "mean over seeds", never as the value of
one lucky draw.
"""

import numpy as np

from .substrate import ProbeResult
from .substrates import make


def run_probe_seeds(substrate_name: str, probe, seeds, **kw) -> list[ProbeResult]:
    """Fresh substrate per seed -> list of ProbeResults."""
    out = []
    for seed in seeds:
        sub = make(substrate_name, seed=seed)
        res = probe.run(sub, **kw)
        res.substrate = substrate_name
        out.append(res)
    return out


def aggregate(results: list[ProbeResult]) -> ProbeResult:
    """Collapse per-seed ProbeResults into one whose metrics are means.

    Full per-seed detail goes into series["stats"][metric] =
    {mean, std, ci95, n, per_seed}; series["seeds"] merges the first
    seed's series for reference.
    """
    base = results[0]
    stats = {}
    metrics = {}
    keys = sorted({k for r in results for k in r.metrics})
    for k in keys:
        vals = np.array([r.metrics[k] for r in results if k in r.metrics])
        n = len(vals)
        m = float(vals.mean())
        s = float(vals.std(ddof=1)) if n > 1 else 0.0
        ci = float(1.96 * s / np.sqrt(n)) if n > 1 else 0.0
        stats[k] = {"mean": m, "std": s, "ci95": ci, "n": n,
                    "per_seed": vals.tolist()}
        metrics[k] = m
    agg = ProbeResult(base.probe, base.substrate, metrics=metrics,
                      series={"stats": stats, **base.series},
                      notes=base.notes)
    return agg
