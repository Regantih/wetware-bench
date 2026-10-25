import numpy as np

from ..substrate import Substrate


class LinearPG(Substrate):
    """REINFORCE-trained linear softmax policy — the silicon baseline for
    closed-loop probes (learning speed / sample efficiency).

    stimulate(x) samples an action and returns it as a count-like one-hot
    vector, so the probe decodes it exactly like a wetware response. reward()
    accumulates returns; reset() applies the episode-end policy update.
    """

    name = "linear_pg"
    roles = {"closed_loop"}

    def __init__(self, n_inputs: int = 8, n_outputs: int = 2,
                 seed: int = 0, lr: float = 0.02, gamma: float = 0.99, **_):
        self.n_inputs, self.n_outputs = n_inputs, n_outputs
        self.lr, self.gamma = lr, gamma
        self._rng = np.random.default_rng(seed)
        self.W = self._rng.normal(0, 0.01, (n_outputs, n_inputs))
        self._ep: list[tuple[np.ndarray, int, np.ndarray]] = []
        self._rew: list[float] = []

    def stimulate(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        logits = self.W @ x
        p = np.exp(logits - logits.max())
        p /= p.sum()
        a = int(self._rng.choice(self.n_outputs, p=p))
        self._ep.append((x, a, p))
        out = np.zeros(self.n_outputs)
        out[a] = 8.0
        return out

    def reward(self, r: float) -> None:
        self._rew.append(r)

    def reset(self) -> None:
        if not self._ep:
            return
        g, ret = 0.0, np.zeros(len(self._rew))
        for t in range(len(self._rew) - 1, -1, -1):
            g = self._rew[t] + self.gamma * g
            ret[t] = g
        ret = (ret - ret.mean()) / (ret.std() + 1e-8)
        for (x, a, p), g in zip(self._ep, ret):
            grad = -p.copy()
            grad[a] += 1.0
            self.W += self.lr * g * np.outer(grad, x)
        self._ep.clear()
        self._rew.clear()
