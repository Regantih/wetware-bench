import numpy as np

from ..substrate import Substrate


class SimSNN(Substrate):
    """Leaky integrate-and-fire reservoir in numpy.

    Recurrent network with short-term synaptic plasticity (facilitation +
    depression, a light Tsodyks-Markram) and reward-modulated Hebbian
    learning on the recurrent weights. This is the wetware stand-in: same
    I/O contract as a living culture on an electrode array, with known
    ground truth underneath.
    """

    name = "snn_sim"

    def __init__(self, n_inputs: int = 8, n_outputs: int = 32,
                 n_hidden: int = 240, seed: int = 0, window: int = 8,
                 v_th: float = 1.0, rec_density: float = 0.12,
                 lr: float = 0.004, elig_decay: float = 0.9,
                 noise: float = 0.05, policy_lr: float = 2.0):
        self.n_inputs, self.n_outputs, self.n_hidden = n_inputs, n_outputs, n_hidden
        self.window, self.v_th, self.lr = window, v_th, lr
        self.elig_decay, self.noise_amp = elig_decay, noise
        self.policy_lr = policy_lr
        rng = np.random.default_rng(seed)
        self._rng = rng
        self.W_in = rng.normal(0, 0.4, (n_hidden, n_inputs))
        mask = rng.random((n_hidden, n_hidden)) < rec_density
        self.W_rec = (rng.normal(0, 0.35 / np.sqrt(n_hidden * rec_density),
                                 (n_hidden, n_hidden)) * mask)
        np.fill_diagonal(self.W_rec, 0)
        # readout population = last n_outputs neurons; the two halves act as
        # action populations ("vote up" vs "vote down")
        self.ro = np.arange(n_hidden - n_outputs, n_hidden)
        self.bias = np.zeros(n_hidden)
        # action-contingent policy layer: injects current into readout halves
        # proportional to the stimulus pattern. THIS is what learns — the
        # recurrent Hebbian rule alone can't credit the chosen action.
        self.W_act = np.zeros((n_outputs, n_inputs))
        self._init_state()
        self._calibrate_readout()

    def _calibrate_readout(self, target: float = 2.5, iters: int = 40) -> None:
        """Balance the readout channels like a real MEA: tune per-neuron bias
        so each readout neuron holds a moderate baseline firing rate on
        resting input. Without this, channels saturate or go silent and the
        response vector carries almost no information."""
        for _ in range(iters):
            counts = np.zeros(self.n_outputs)
            for _ in range(self.window):
                counts += self._step(np.zeros(self.n_inputs))[self.ro]
            self.bias[self.ro] += 0.15 * (target - counts)
            self._init_state()

    def _init_state(self) -> None:
        self.v = np.zeros(self.n_hidden)
        self.s_prev = np.zeros(self.n_hidden)
        self.fac = np.ones(self.n_hidden)   # facilitation >= 1
        self.dep = np.ones(self.n_hidden)   # depression <= 1
        self.elig = np.zeros_like(self.W_rec)
        self.r_bar = 0.0                    # running reward baseline
        self._last_act = None
        self._last_x = np.zeros(self.n_inputs)

    def reset(self) -> None:
        self._init_state()

    def _step(self, x: np.ndarray) -> np.ndarray:
        eff = self.s_prev * self.fac * self.dep   # STP-scaled presynaptic drive
        I = (self.W_in @ x + self.W_rec @ eff + self.bias
             + self.noise_amp * self._rng.standard_normal(self.n_hidden))
        # policy layer: readout halves get extra drive from learned W_act
        I[self.ro] += self.W_act @ x
        self.v = self.v * 0.9 + I                  # leak
        s = (self.v >= self.v_th).astype(float)
        self.v[s == 1] = 0.0
        # short-term plasticity
        self.fac += (1.0 - self.fac) / 50.0
        self.dep += (1.0 - self.dep) / 200.0
        self.fac[s == 1] += 0.5
        self.dep[s == 1] *= 0.6
        # eligibility: post x pre co-activity on recurrent synapses
        self.elig *= self.elig_decay
        self.elig += np.outer(s, eff)
        self.s_prev = s
        return s

    def stimulate(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        counts = np.zeros(self.n_outputs)
        for _ in range(self.window):
            counts += self._step(x)[self.ro]
        # remember which action population won and the stimulus that drove it
        # — the eligibility record reward() will use
        half = self.n_outputs // 2
        self._last_act = 0 if counts[:half].sum() >= counts[half:].sum() else 1
        self._last_x = x
        return counts

    def reward(self, r: float) -> None:
        adv = r - self.r_bar
        self.r_bar += 0.05 * (r - self.r_bar)
        if adv == 0.0:
            return
        self._recurrent_update(adv)
        # policy update (REINFORCE-style): credit the half that won the vote
        if self._last_act is not None:
            self._policy_update(adv)

    def _recurrent_update(self, adv: float) -> None:
        # recurrent plasticity (weak, non-contingent)
        self.W_rec += self.lr * adv * self.elig
        np.clip(self.W_rec, -0.5, 0.5, out=self.W_rec)

    def _policy_update(self, adv: float) -> None:
        half = self.n_outputs // 2
        a = self._last_act
        sl_win = slice(0, half) if a == 0 else slice(half, None)
        sl_lose = slice(half, None) if a == 0 else slice(0, half)
        self.W_act[sl_win] += self.policy_lr * adv * self._last_x
        self.W_act[sl_lose] -= self.policy_lr * adv * self._last_x
        np.clip(self.W_act, -8, 8, out=self.W_act)

    def fit_policy(self, feats: np.ndarray, acts: np.ndarray,
                   scale: float = 0.5) -> None:
        """Supervised warm start on the policy layer — standard reservoir
        practice (train only the readout). feats: (T, n_inputs) stimulus
        patterns, acts: (T,) 0/1 demonstrating the desired vote."""
        from ..readout import ridge_fit
        feats = np.asarray(feats, dtype=float)
        y = np.where(np.asarray(acts) == 0, 1.0, -1.0)[:, None]
        w = ridge_fit(feats, y)[:-1, 0]
        k = scale / (np.abs(feats @ w).mean() + 1e-9)
        half = self.n_outputs // 2
        self.W_act[:half] = k * w
        self.W_act[half:] = -k * w

    def perturb(self, sigma: float) -> None:
        """Mimic overnight drift of a living culture: relative weight noise."""
        self.W_rec += sigma * np.abs(self.W_rec) * self._rng.standard_normal(self.W_rec.shape)
