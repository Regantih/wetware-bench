import numpy as np

from ..readout import nrmse, ridge_fit, ridge_predict
from ..substrate import ProbeResult, Substrate

NAME = "narma"
ROLE = "open_loop"
HEADLINE = "narma10_nrmse"


def _narma10(u: np.ndarray) -> np.ndarray:
    """Standard NARMA-10 series: nonlinear, 10-step memory."""
    y = np.zeros(len(u))
    for t in range(9, len(u) - 1):
        y[t + 1] = (0.3 * y[t] + 0.05 * y[t] * y[t - 9:t + 1].sum()
                    + 1.5 * u[t - 9] * u[t] + 0.1)
    return y


def run(sub: Substrate, seed: int = 0, T: int = 1200, wash: int = 200,
        **_) -> ProbeResult:
    """NARMA-10 benchmark: the standard 'can it compute?' test for reservoirs.
    Drive with u(t), linear readout must predict y(t). Lower NRMSE = better."""
    rng = np.random.default_rng(seed)
    w_in = rng.uniform(-1, 1, sub.n_inputs)
    if sub.n_inputs == 1:
        w_in[:] = 1.0
    u = rng.uniform(0.0, 0.5, T)
    y = _narma10(u)
    sub.reset()
    R = np.array([sub.stimulate(u[t] * w_in) for t in range(T)])
    X, Y = R[wash:], y[wash:, None]
    n_tr = int(0.7 * len(X))
    W = ridge_fit(X[:n_tr], Y[:n_tr])
    test = nrmse(Y[n_tr:].ravel(), ridge_predict(X[n_tr:], W).ravel())
    train = nrmse(Y[:n_tr].ravel(), ridge_predict(X[:n_tr], W).ravel())
    return ProbeResult(
        probe=NAME, substrate=sub.name,
        metrics={"narma10_nrmse": test, "narma10_nrmse_train": train},
        notes="NRMSE <~0.4 is decent; ~1.0 means the readout learned nothing.")
