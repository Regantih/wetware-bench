from ..substrate import Substrate
from .snn_sim import SimSNN
from .snn_stdp import SimSNNSTDP
from .tap_delay import TapDelay
from .linear_pg import LinearPG
from .wetware import WetwareDriver


def make(name: str, **kw) -> Substrate:
    """Substrate factory. A '+enc' suffix wraps any substrate in the
    learned-codec middleware (bench/codec.py) — same interface, the
    encoder is invisible to probes."""
    encoded = name.endswith("+enc")
    if encoded:
        name = name[:-4]
    table = {
        "snn": SimSNN,
        "snn_stdp": SimSNNSTDP,
        "tapdelay": TapDelay,
        "linear_pg": LinearPG,
        "wetware": WetwareDriver,
    }
    if name not in table:
        raise KeyError(f"unknown substrate {name!r}; have {sorted(table)}")
    sub = table[name](**kw)
    if encoded:
        from ..codec import EncodedSubstrate
        sub = EncodedSubstrate(sub, seed=kw.get("seed", 0))
    return sub
