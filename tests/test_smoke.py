import numpy as np

from bench.probes import PROBES
from bench.substrates import make


def test_snn_fires():
    s = make("snn")
    assert s.stimulate(np.ones(s.n_inputs)).sum() > 0


def test_open_loop_probes_finite():
    s = make("snn")
    for name in ("memory_capacity", "narma", "io_bandwidth",
                 "plasticity", "energy"):
        res = PROBES[name].run(s, T=300, wash=50, K=8,
                               trials_per=6, steps=50)
        assert res.metrics, name
        assert all(np.isfinite(v) for v in res.metrics.values()), name


def test_closed_loop_probes_run():
    for sub_name in ("snn", "linear_pg"):
        res = PROBES["learning_speed"].run(make(sub_name), episodes=3, steps=150)
        assert "final_hit_rate" in res.metrics


def test_stability_on_sim():
    res = PROBES["stability"].run(make("snn"), rounds=2)
    assert np.isfinite(res.metrics["retention"])


def test_wetware_lazy_connect():
    # constructing the driver must not touch hardware or require the SDK
    w = make("wetware")
    assert w.n_inputs > 0 and w.n_outputs > 0
    assert w._sdk is None


def test_codec_helps_narrow_channel():
    # the learned codec should lift I/O where the interface is the
    # bottleneck (few read channels) — the regime real MEAs live in.
    # Per-seed results are noisy; assert on the multi-seed mean.
    from bench.codec import EncodedSubstrate
    from bench.substrates.snn_sim import SimSNN
    kw = dict(n_classes=8, trials_per=16)
    a = np.mean([PROBES["io_bandwidth"].run(
        SimSNN(n_outputs=4, seed=s), seed=s, **kw)
        .metrics["bits_per_write"] for s in (0, 1, 2)])
    b = np.mean([PROBES["io_bandwidth"].run(
        EncodedSubstrate(SimSNN(n_outputs=4, seed=s), seed=s), seed=s, **kw)
        .metrics["bits_per_write"] for s in (0, 1, 2)])
    assert b > a
