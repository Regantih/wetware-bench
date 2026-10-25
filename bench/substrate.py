from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


class Substrate:
    """Uniform interface for any computing substrate under test.

    Contract:
      - you write vectors in via stimulate(), read response vectors out
      - optional scalar reward() for closed-loop plasticity
      - reset() clears fast dynamics between trials; learned state persists
      - perturb(sigma) mimics overnight drift of a living culture (no-op for
        non-living substrates)

    A simulated SNN, a linear policy, and a real organoid behind an API all
    implement the same methods, so probes don't care what's underneath.
    """

    name = "substrate"
    roles: set[str] = {"open_loop", "closed_loop"}
    n_inputs: int = 1
    n_outputs: int = 1

    def reset(self) -> None:
        """Reset fast dynamics between trials/episodes. Learned state persists."""

    def stimulate(self, x: np.ndarray) -> np.ndarray:
        """Drive with input vector x (len n_inputs) -> response (len n_outputs)."""
        raise NotImplementedError

    def reward(self, r: float) -> None:
        """Scalar reward/punishment. Default: ignored (open-loop substrates)."""

    def perturb(self, sigma: float) -> None:
        """Apply parameter drift of relative magnitude sigma. Default: no drift."""


@dataclass
class ProbeResult:
    probe: str
    substrate: str
    metrics: dict[str, float] = field(default_factory=dict)
    series: dict[str, list] = field(default_factory=dict)
    notes: str = ""
