import numpy as np

from ..envs import MiniPong
from ..substrate import ProbeResult, Substrate

NAME = "learning_speed"
ROLE = "closed_loop"
HEADLINE = "final_hit_rate"


def run(sub: Substrate, seed: int = 0, episodes: int = 40,
        steps: int = 300, shape: float = 0.02, **_) -> ProbeResult:
    """The DishBrain probe: play Pong, measure hit rate (hits / arrivals).

    Tests the headline claim of the whole field — that biological networks
    learn with fewer samples than silicon RL. episodes_to_threshold = first
    episode where the 5-episode rolling hit rate reaches 0.8.
    """
    if sub.n_outputs < 2:
        return ProbeResult(NAME, sub.name, notes="needs n_outputs >= 2")
    rng = np.random.default_rng(seed)
    enc = rng.normal(0, 1, (sub.n_inputs, 5))
    env = MiniPong(seed, shape=shape)
    half = sub.n_outputs // 2
    rate_per_ep = []
    for _ in range(episodes):
        env.py, env.hits, env.arrivals = 0.5, 0, 0
        env._spawn()
        sub.reset()
        for _ in range(steps):
            x = np.clip(enc @ env.obs(), -1, 1)
            r = sub.stimulate(x)
            act = 0 if r[:half].sum() >= r[half:].sum() else 1
            sub.reward(env.step(act))
        rate_per_ep.append(env.hits / max(env.arrivals, 1))

    arr = np.array(rate_per_ep, float)
    roll = np.convolve(arr, np.ones(5) / 5, "valid") if len(arr) >= 5 else arr
    reached = np.nonzero(roll >= 0.8)[0]
    e2t = int(reached[0] + 5) if len(reached) else -1
    return ProbeResult(
        probe=NAME, substrate=sub.name,
        metrics={"final_hit_rate": float(arr[-10:].mean()),
                 "best_hit_rate": float(arr.max()),
                 "episodes_to_threshold": e2t},
        series={"hit_rate_per_episode": arr.tolist()},
        notes="episodes_to_threshold=-1 means never reached 0.8 rolling hit rate.")
