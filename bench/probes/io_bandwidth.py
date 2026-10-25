import numpy as np

from ..readout import ridge_fit, ridge_predict
from ..substrate import ProbeResult, Substrate

NAME = "io_bandwidth"
ROLE = "open_loop"
HEADLINE = "bits_per_write"


def run(sub: Substrate, seed: int = 0, n_classes: int = 8,
        trials_per: int = 30, settle: int = 2, noise: float = 0.05,
        **_) -> ProbeResult:
    """How many bits can you reliably write in and read back?

    Present n_classes distinct stimulation patterns with small jitter, then
    see how well a linear readout on the responses recovers the class.
    bits_per_write = accuracy x log2(n_classes) — a rough channel estimate.
    """
    rng = np.random.default_rng(seed)
    P = rng.choice([-1.0, 1.0], (n_classes, sub.n_inputs))
    z = np.zeros(sub.n_inputs)
    X, y = [], []
    sub.reset()
    for c in range(n_classes):
        for _ in range(trials_per):
            for _ in range(settle):
                sub.stimulate(z)
            X.append(sub.stimulate(P[c] + noise * rng.standard_normal(sub.n_inputs)))
            y.append(c)
    X, y = np.array(X), np.array(y)
    idx = rng.permutation(len(y))
    n_tr = int(0.7 * len(idx))
    tr, te = idx[:n_tr], idx[n_tr:]
    Y = np.eye(n_classes)[y]
    W = ridge_fit(X[tr], Y[tr])
    acc = float((ridge_predict(X[te], W).argmax(1) == y[te]).mean())
    chance = 1.0 / n_classes
    bits = max(0.0, acc - chance) / (1 - chance) * np.log2(n_classes)
    return ProbeResult(
        probe=NAME, substrate=sub.name,
        metrics={"io_accuracy": acc, "bits_per_write": bits},
        notes=f"{n_classes} classes, chance={chance:.3f}")
