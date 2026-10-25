import numpy as np

from ..substrate import ProbeResult, Substrate

NAME = "criticality"
ROLE = "any"
HEADLINE = "branching_sigma"


def run(sub: Substrate, seed: int = 0, steps: int = 3000,
        thresh_scale: float = 1.0, **_) -> ProbeResult:
    """Where does the substrate sit on the sub/supercritical axis?

    Drives the substrate with zero input (spontaneous activity), treats
    each response as a bin, and measures avalanche statistics on the
    population activity. Avalanches = runs of above-baseline bins —
    on MEA data these are the network events.

      branching_sigma ~ 1   -> critical (max dynamic range/memory, in theory)
      < 1                   -> subcritical (activity dies out)
      > 1                   -> supercritical (runaway bursts)

    Works identically on sim and wetware: stimulate(zeros) reads
    spontaneous activity on any substrate.
    """
    from ..realdata import avalanches
    x = np.zeros(sub.n_inputs)
    counts = np.array([sub.stimulate(x) for _ in range(steps)])
    pop = counts.sum(axis=1)
    if pop.std() < 1e-9:
        return ProbeResult(NAME, sub.name,
                           metrics={"branching_sigma": 0.0,
                                    "alpha_size": 0.0, "n_avalanches": 0},
                           notes="no spontaneous activity")
    thresh = max(1.0, pop.mean() * thresh_scale)
    stats = avalanches(counts, thresh=thresh)
    return ProbeResult(
        NAME, sub.name,
        metrics={"branching_sigma": stats.get("branching_sigma", 0.0),
                 "alpha_size": stats.get("alpha_size", 0.0),
                 "n_avalanches": float(stats.get("n_avalanches", 0)),
                 "av_size_max": stats.get("av_size_max", 0.0)},
        series={"pop_rate": pop.tolist()},
        notes="sigma ~1 = critical; real organoids measured 1.11-1.22 "
              "(docs/real_data_report.md)")
