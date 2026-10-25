import numpy as np

from . import memory_capacity
from ..substrate import ProbeResult, Substrate

NAME = "stability"
ROLE = "open_loop"
HEADLINE = "retention"


def run(sub: Substrate, seed: int = 0, rounds: int = 4,
        drift: float = 0.05, **_) -> ProbeResult:
    """Does the substrate keep working after drift?

    Between rounds we call perturb(drift) — for wetware that means 'come back
    tomorrow', for sims it's relative weight noise. retention = final/initial
    memory capacity. On real neurons this is the 'is the computer still there
    in the morning' test.
    """
    mcs = []
    for _ in range(rounds):
        mcs.append(memory_capacity.run(sub, seed=seed, T=700, wash=100, K=15)
                 .metrics["memory_capacity"])
        sub.perturb(drift)
    mcs = np.array(mcs)
    return ProbeResult(
        probe=NAME, substrate=sub.name,
        metrics={"retention": float(mcs[-1] / max(mcs[0], 1e-9)),
                 "mc_initial": float(mcs[0])},
        series={"mc_per_round": mcs.tolist()},
        notes="retention ~1 = drift-tolerant; <1 = capability decayed.")
