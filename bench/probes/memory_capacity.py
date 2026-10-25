import numpy as np

from ..readout import ridge_fit, ridge_predict, squared_corr
from ..substrate import ProbeResult, Substrate

NAME = "memory_capacity"
ROLE = "open_loop"
HEADLINE = "memory_capacity"


def run(sub: Substrate, seed: int = 0, T: int = 1400, wash: int = 200,
        K: int = 20, **_) -> ProbeResult:
    """Jaeger memory capacity: drive with random u(t), then ask a linear
    readout on the responses to reconstruct u(t-k) for k = 1..K.
    MC = sum_k corr^2. Higher = the substrate retains more input history."""
    rng = np.random.default_rng(seed)
    w_in = rng.uniform(-1, 1, sub.n_inputs)
    if sub.n_inputs == 1:
        w_in[:] = 1.0
    u = rng.uniform(-0.5, 0.5, T)
    sub.reset()
    R = np.array([sub.stimulate(u[t] * w_in) for t in range(T)])
    X = R[wash:]
    mc = {}
    for k in range(1, K + 1):
        y = u[wash - k:T - k]
        mc[k] = squared_corr(y, ridge_predict(X, ridge_fit(X, y[:, None])).ravel())
    return ProbeResult(
        probe=NAME, substrate=sub.name,
        metrics={"memory_capacity": sum(mc.values()),
                 "mc_1": mc[1], "mc_10": mc[min(10, K)]},
        series={"mc_curve": [mc[k] for k in range(1, K + 1)]},
    )
