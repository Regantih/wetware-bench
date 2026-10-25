import numpy as np

from ..substrate import ProbeResult, Substrate

NAME = "plasticity"
ROLE = "open_loop"
HEADLINE = "ppf_isi2"


def run(sub: Substrate, seed: int = 0, n_pulses: int = 15, **_) -> ProbeResult:
    """Short-term plasticity assays.

    Paired-pulse: fire twice, vary the gap, measure how the second response
    changes (facilitation > 1, depression < 1). Habituation: same pulse
    repeatedly, measure response decay. These are the minimal signs that a
    substrate is *dynamic* rather than a passive filter.
    """
    rng = np.random.default_rng(seed)
    pulse = rng.uniform(-1, 1, sub.n_inputs)
    z = np.zeros(sub.n_inputs)

    ppf = {}
    for isi in (0, 1, 2, 4, 8):
        sub.reset()
        a1 = sub.stimulate(pulse).sum()
        for _ in range(isi):
            sub.stimulate(z)
        a2 = sub.stimulate(pulse).sum()
        ppf[isi] = a2 / max(a1, 1e-9)

    sub.reset()
    amps = []
    for _ in range(n_pulses):
        amps.append(float(sub.stimulate(pulse).sum()))
        sub.stimulate(z)
    amps = np.array(amps)
    hab = float(amps[-1] / max(amps[0], 1e-9))

    return ProbeResult(
        probe=NAME, substrate=sub.name,
        metrics={"ppf_isi0": ppf[0], "ppf_isi2": ppf[2],
                 "habituation_ratio": hab},
        series={"ppf": [ppf[k] for k in (0, 1, 2, 4, 8)],
                "habituation_amps": amps.tolist()},
        notes="ppf>1 = facilitation, <1 = depression; hab<1 = habituating.")
