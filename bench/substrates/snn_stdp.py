import numpy as np

from .snn_sim import SimSNN


class SimSNNSTDP(SimSNN):
    """Same LIF reservoir, but recurrent plasticity is reward-modulated
    pair-based STDP (Izhikevich-style) instead of a co-activity
    eligibility trace.

    Per step we keep exponential pre/post spike traces; the causal
    update  A+ * post x pre_trace  minus the anti-causal
    A- * post_trace x pre  accumulates into _dw, and is only committed
    to W_rec when a reward arrives (dopamine-gated STDP). The learned
    policy layer is unchanged — this substrate isolates whether the
    *recurrent* rule matters.
    """

    name = "snn_stdp"

    def __init__(self, *a, stdp_plus: float = 0.8, stdp_minus: float = 0.5,
                 trace_decay: float = 0.95, stdp_lr: float = 0.05, **kw):
        # params must exist before super().__init__() — the parent's readout
        # calibration already calls _step, which needs them
        self.stdp_plus, self.stdp_minus = stdp_plus, stdp_minus
        self.trace_decay, self.stdp_lr = trace_decay, stdp_lr
        super().__init__(*a, **kw)

    def _init_traces(self) -> None:
        self._pre = np.zeros(self.n_hidden)
        self._post = np.zeros(self.n_hidden)
        self._dw = np.zeros_like(self.W_rec)

    def _init_state(self) -> None:
        super()._init_state()
        if hasattr(self, "_pre"):
            self._init_traces()

    def _step(self, x: np.ndarray) -> np.ndarray:
        if not hasattr(self, "_pre"):       # first call comes from the
            self._init_traces()             # parent's own calibration
        s = super()._step(x)
        self._pre *= self.trace_decay
        self._post *= self.trace_decay
        # LTP: pre fired recently -> post fires now (causal)
        # LTD: post fired recently -> pre fires now (anti-causal)
        self._dw += (self.stdp_plus * np.outer(s, self._pre)
                     - self.stdp_minus * np.outer(self._post, s))
        self._pre[s == 1] = 1.0
        self._post[s == 1] = 1.0
        return s

    def _recurrent_update(self, adv: float) -> None:
        # dopamine-gated STDP: commit the accumulated causal/anti-causal
        # weight change scaled by reward surprise, then clear eligibility
        self.W_rec += self.stdp_lr * adv * self._dw
        np.clip(self.W_rec, -0.5, 0.5, out=self.W_rec)
        self._dw[:] = 0.0
