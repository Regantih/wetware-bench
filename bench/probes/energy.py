import time

import numpy as np

from ..substrate import ProbeResult, Substrate

NAME = "energy"
ROLE = "any"
HEADLINE = "joules_per_sample"


def run(sub: Substrate, seed: int = 0, steps: int = 400,
        watts: float = 15.0, **_) -> ProbeResult:
    """Throughput x assumed power = joules per sample.

    watts defaults to a laptop-CPU-ish 15W for the sim. For wetware, measure
    wall power of the rig (CL1 is specced at ~30W; FinalSpark similar order)
    and pass it in — the comparison is the whole point of the sustainability
    claim.
    """
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, sub.n_inputs)
    sub.reset()
    sub.stimulate(x)  # warm-up
    t0 = time.perf_counter()
    for _ in range(steps):
        sub.stimulate(x)
    dt = time.perf_counter() - t0
    sps = steps / dt
    return ProbeResult(
        probe=NAME, substrate=sub.name,
        metrics={"samples_per_sec": sps,
                 "joules_per_sample": watts / sps},
        notes=f"assumed {watts} W wall power — measure the real rig to compare.")
