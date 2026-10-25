"""Learned codec middleware — attacks the electrode-interface bottleneck.

Wraps any Substrate. On first stimulate() it runs a calibration burst
(random inputs -> responses) and fits a linear channel model. Afterwards:

  * continuous inputs are pushed through a regularized channel inverse,
    so what the substrate *responds with* tracks what you *meant* to send
  * discrete repeated patterns (class vectors) are remapped to stimulation
    patterns that maximize minimum pairwise distance in RESPONSE space —
    greedy max-min selection over a random candidate pool

This is the same calibration step wet labs perform on an MEA, which means
the identical code runs on a simulated reservoir and on living neurons.
"""

import numpy as np

from .readout import ridge_fit
from .substrate import Substrate


class EncodedSubstrate(Substrate):
    def __init__(self, base: Substrate, calib: int = 96, lam: float = 1e-3,
                 seed: int = 0, pool: int = 512, **_):
        self.base = base
        self.name = f"{base.name}+enc"
        self.roles = set(base.roles)
        self.n_inputs, self.n_outputs = base.n_inputs, base.n_outputs
        self.calib, self.lam, self.pool = calib, lam, pool
        self._rng = np.random.default_rng(seed)
        self._A = None            # fitted channel map (n_in, n_out)
        self._S = None            # response gains per stim direction
        self._V = None            # stim-space directions ordered by gain
        self._cache: list[tuple[np.ndarray, np.ndarray]] = []
        self._anchors: list[np.ndarray] = []   # chosen response vectors

    # -- calibration ---------------------------------------------------

    def _calibrate(self) -> None:
        X = self._rng.uniform(-1, 1, (self.calib, self.n_inputs))
        R = np.array([self.base.stimulate(x) for x in X])
        self._A = ridge_fit(X, R)[:-1]           # channel map (n_in, n_out)
        # SVD of A^T: right singular vectors = stim-space directions ordered
        # by response gain. Encoding into them + gain equalization gives the
        # best linear write channel available.
        _, self._S, self._V = np.linalg.svd(self._A.T, full_matrices=False)
        self._cand = self._rng.normal(0, 1, (self.pool, self.n_inputs))
        self._cand /= np.linalg.norm(self._cand, axis=1, keepdims=True) + 1e-9
        self._cand_r = self._cand @ self._A      # response-space image

    # -- encoding ------------------------------------------------------

    def _encode(self, x: np.ndarray) -> np.ndarray:
        """Discrete-pattern remap if x looks like a class vector (uniform
        |x_i|), else channel-inverse."""
        mag = np.abs(x)
        is_pattern = mag.mean() > 0.5 and mag.std() < 0.1 * max(mag.mean(), 1e-9)
        if is_pattern:
            return self._remap_pattern(x)
        # continuous: project x onto the channel's strongest directions,
        # equalize gains, lift back to stim space (truncated inverse —
        # works whether the channel is wide or narrow)
        gains = np.maximum(self._S, self.lam * self._S[0])
        c = (x @ self._V.T) / gains     # coords in response-gain basis
        return c @ self._V

    def _remap_pattern(self, x: np.ndarray) -> np.ndarray:
        """Pick the stim whose response is maximally far from already-chosen
        responses, with a bonus for keeping the direction the input asked
        for. Cache by nearest match (patterns arrive with jitter)."""
        for k, s in self._cache:
            if np.linalg.norm(x - k) < 0.25:
                return s
        d = np.linalg.norm(
            self._cand_r[:, None, :] - np.array(self._anchors)[None]
            if self._anchors else self._cand_r[:, None, :],
            axis=2).min(axis=1) if self._anchors else \
            np.linalg.norm(self._cand_r, axis=1)
        top = np.argsort(d)[-max(4, self.pool // 32):]
        target = x @ self._A
        i = top[np.argmax(self._cand_r[top] @ (target / (np.linalg.norm(target) + 1e-9)))]
        s = self._cand[i] * float(np.abs(x).mean())
        self._cache.append((x.copy(), s))
        self._anchors.append(self._cand_r[i].copy())
        return s

    # -- Substrate interface --------------------------------------------

    def reset(self) -> None:
        self.base.reset()

    def reward(self, r: float) -> None:
        self.base.reward(r)

    def perturb(self, sigma: float) -> None:
        self.base.perturb(sigma)

    def stimulate(self, x: np.ndarray) -> np.ndarray:
        if self._A is None:
            self._calibrate()
        x = np.asarray(x, dtype=float)
        return self.base.stimulate(np.clip(self._encode(x), -1, 1))
