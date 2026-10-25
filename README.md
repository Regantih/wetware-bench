# wetware bench

A substrate-agnostic benchmark suite for biocomputing. One interface —
`stimulate(x) -> response`, optional `reward(r)` — implemented by simulated
networks, classical baselines, and (eventually) living neurons on an
electrode array. Same probes, every substrate, comparable numbers.

The point: each probe maps to a claim about biological computing's
potential (learns fast? computes? energy-efficient? still alive tomorrow?).
The scoreboard tells you which claims hold up and where the real bottleneck
is.

## Demo

<video src="https://raw.githubusercontent.com/Regantih/wetware-bench/master/demo/wetware_bench.mp4" controls></video>

Narrated walkthrough (2 min) — or download [`demo/wetware_bench.mp4`](demo/wetware_bench.mp4)

## Run it

```
pip install -r requirements.txt
python -m bench.scoreboard                 # full suite on sim + baselines
python -m bench.scoreboard --seeds 5       # mean±95%CI over fresh seeds
python -m bench.scoreboard --compare-codec # every substrate ± learned codec
python -m bench.realdata spikes.mat --sim  # real organoid data vs. sim
pytest tests/                              # smoke tests
```

Results land in `results/results.json` + `results/scoreboard.md`.

## Probes -> claims

| probe | measures | claim tested |
|---|---|---|
| `learning_speed` | hit rate on Pong, episodes-to-threshold | DishBrain's "learns faster than silicon RL" |
| `memory_capacity` | Jaeger MC: input history recoverable from responses | does it hold state at all |
| `narma` | NRMSE on NARMA-10 with linear readout | computational ceiling (standard reservoir test) |
| `io_bandwidth` | bits per write via pattern classification | is the electrode interface the bottleneck |
| `plasticity` | paired-pulse ratio, habituation | is it dynamic or a passive filter |
| `stability` | memory capacity retained after drift | "is the computer still there tomorrow" |
| `energy` | joules per sample at assumed wattage | the sustainability thesis |
| `criticality` | branching σ + avalanche α on spontaneous activity | is it near the critical point where compute peaks |

## Substrates

- `snn` — numpy LIF reservoir w/ short-term plasticity + reward-modulated Hebbian learning + an action-contingent policy layer. The wetware stand-in.
- `snn_stdp` — same reservoir, but recurrent plasticity is dopamine-gated pair-based STDP (Izhikevich-style). The "does the plasticity rule matter" control.
- `replay`/`realdata` — `bench/realdata.py` analyzes recorded MEA spike trains (.mat/.csv) vs. sim: burstiness, drift, channel coupling. Real organoid numbers in `docs/real_data_report.md`.
- `tapdelay` — tapped delay line. The "could a linear model do this?" control.
- `linear_pg` — REINFORCE linear policy. The silicon learning baseline.
- `wetware` — FinalSpark `neuroplatformv2` driver (lazy-connected, trigger-mode by default).
- **any `+enc` suffix** — wraps the substrate in the learned codec (`bench/codec.py`): calibration burst → channel model → inputs encoded into the channel's strongest response directions; discrete patterns remapped for max response-space separation. Verified on sim: **+34–35% bits/write on narrow channels** (the regime real MEAs live in), neutral on wide ones — the codec only helps where the interface is the bottleneck.

## Wiring real neurons

The FinalSpark driver (`wetware`) is implemented against the real
`neuroplatformv2` SDK — lazy-connected, trigger-mode by default (one
pre-uploaded StimParam per input dim, so `stimulate()` is a single trigger
send + spike count; `analog` mode does amplitude modulation but costs ≥5s
of re-upload settle per call).

1. **Apply for access** — draft request + env setup in
   `docs/finalspark_application.md`. The pitch is this benchmark suite itself.
2. Set env vars (`.env.example`), `pip install -e` the `neuroplatformv2` repo.
3. Validate cheaply first:
   `python -m bench.scoreboard --substrates wetware --probes io_bandwidth plasticity`
4. Then the full suite: `--substrates wetware` — probes don't change.

CL1/Cortical Cloud would be the same driver shape, different wire — UDP
spike receiver per `Cortical-Labs/cl-api-doc`.

## Roadmap

This repo is the instrument for a 12-month program to measure whether
SBI has real potential — see `docs/megaplan.md` for the full plan with
phase gates and pre-registered decision criteria. In short:

1. **Phase 1 (now):** harden the suite — multi-seed stats, stronger
   sim baselines, session checkpointing; submit the FinalSpark app.
2. **Phase 2:** analyze free recorded organoid data (FinalSpark 30 TB
   archive, Zenodo, NeuroBridge) — real biological drift/noise numbers.
3. **Phase 3–4:** live FinalSpark runs — full suite + codec on the
   real channel, multi-session stability.
4. **Phase 5:** the verdict — `docs/verdict.md` decision memo for the
   team.

Literature log lives in `docs/field_notes.md`.

## Honest limits

- The sim is a *floor*, not a ceiling — a small random reservoir, not a trained culture.
- `energy` on sim measures your CPU; on wetware, measure the rig's wall power and pass `--watts` equivalent.
- Living systems need repeated runs across days; the numbers here are single-session.
