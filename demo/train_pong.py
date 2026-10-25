"""Warm-start the SNN's policy layer for the demo video.

Collects tracker demonstrations (paddle follows ball), ridge-fits the
action populations (W_act) to vote for the demonstrated action — standard
reservoir-computing practice: dynamics are fixed, only the readout/policy
is trained. Reward-modulated plasticity stays live on top.

    python -m demo.train_pong            # writes demo/pong_brain.npz
"""

import numpy as np

from bench.envs import MiniPong
from bench.substrates import make
from bench.substrates.snn_sim import SimSNN

SEED = 3
OUT = "demo/pong_brain.npz"


def demo_traj(snn: SimSNN, enc: np.ndarray, steps: int = 3000):
    env = MiniPong(SEED)
    feats, acts = [], []
    for _ in range(steps):
        x = np.clip(enc @ env.obs(), -1, 1)
        a = 0 if env.by < env.py else 1
        env.step(a)
        feats.append(x)
        acts.append(a)
    return np.array(feats), np.array(acts)


def evaluate(snn: SimSNN, enc: np.ndarray, episodes: int = 10,
             steps: int = 300) -> float:
    env = MiniPong(SEED + 100)
    half = snn.n_outputs // 2
    rates = []
    for _ in range(episodes):
        env.py, env.hits, env.arrivals = 0.5, 0, 0
        env._spawn()
        snn.reset()
        for _ in range(steps):
            x = np.clip(enc @ env.obs(), -1, 1)
            r = snn.stimulate(x)
            env.step(0 if r[:half].sum() >= r[half:].sum() else 1)
        rates.append(env.hits / max(env.arrivals, 1))
    return float(np.mean(rates))


def main():
    snn = make("snn", seed=SEED)
    enc = np.random.default_rng(SEED).normal(0, 1, (snn.n_inputs, 5))

    feats, acts = demo_traj(snn, enc)
    print(f"before fit: hit rate {evaluate(snn, enc):.2f}")
    snn.fit_policy(feats, acts)
    print(f"after fit:  hit rate {evaluate(snn, enc):.2f}")

    np.savez(OUT, enc=enc, W_in=snn.W_in, W_rec=snn.W_rec,
             W_act=snn.W_act, bias=snn.bias)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
