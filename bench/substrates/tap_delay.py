import numpy as np

from ..substrate import Substrate


class TapDelay(Substrate):
    """Linear baseline for open-loop probes: a tapped delay line.

    n_outputs = number of taps. Response is just the recent input history,
    so any probe result is exactly what a plain linear model could do —
    everything a reservoir claims beyond this has to beat it.
    """

    name = "tapdelay"
    roles = {"open_loop"}

    def __init__(self, n_inputs: int = 1, n_outputs: int = 25, **_):
        self.n_inputs, self.n_outputs = n_inputs, n_outputs
        self.buf = np.zeros(n_outputs)

    def reset(self) -> None:
        self.buf[:] = 0.0

    def stimulate(self, x: np.ndarray) -> np.ndarray:
        self.buf[1:] = self.buf[:-1]
        self.buf[0] = float(np.asarray(x).flat[0])
        return self.buf.copy()
