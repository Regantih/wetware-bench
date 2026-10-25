# Field notes — SBI / biocomputing literature log

Running log, ~1 paper/week. Each entry: what they did, what it implies
for the benchmark, and whether it moves the needle on the megaplan's
decision criteria (docs/megaplan.md).

## Template

```
### YYYY-MM-DD — <title> (<authors/venue/year>)
- **What:** 1-2 sentence summary.
- **Numbers that matter:** key quantitative claims (hit rates, neuron
  counts, energy figures, drift timescales).
- **Implication for the bench:** does this change a probe, a baseline,
  or an assumption?
- **Decision-criteria impact:** does it push any signal toward
  green/yellow/red?
- **Skeptic's note:** what's weakest about the claim?
```

## Reading queue

- [ ] Kagan et al., "In vitro neurons learn and exhibit sentience when
      embodied in a simulated game-world" (DishBrain, Neuron 2022) —
      the fast-learning claim the learning_speed probe tests.
- [ ] FinalSpark neuroplatform paper(s) — organoid on MEA, platform
      architecture, stimulation protocols.
- [ ] Cortical Labs CL1 / biOS documentation and any published
      characterization.
- [ ] Reservoir computing reviews (Jaeger, Lukoševičius) — memory
      capacity + NARMA methodology grounding.
- [ ] MEA interface/bandwidth literature — the codec's core assumption
      is that electrodes, not neurons, are the bottleneck.
- [ ] Brain organoid criticality/avalanche literature — informs the
      recorded-data analysis in Phase 2.

## Log

### `criticality` is now a first-class probe (cycle 3)

- **What:** `bench/probes/criticality.py` — drives any substrate with
  zero input, measures avalanche branching σ and size exponent α on
  spontaneous activity. 8th probe; identical contract on wetware later.
- **Numbers that matter:** sim reads σ=1.01±0.0003 via the probe vs.
  σ=1.64 via the fine-binned realdata pipeline — σ is
  binning/threshold-sensitive, so the probe and the offline analyzer
  answer slightly different questions (readout-channel excursions vs.
  raw-electrode avalanches).
- **Implication:** the suite now measures the thing the literature
  claims matters most (near-critical dynamics), portably.
- **Skeptic's note:** probe σ ~1 could partly reflect threshold tuning
  (thresh = mean population rate); on wetware, report both σ and the
  raw avalanche counts so reviewers can re-derive it.

### Criticality + directed connectivity on real organoids (cycle 2)

- **What:** added order-1 binary transfer entropy and avalanche
  statistics (branching σ, size-distribution exponent α) to
  `bench/realdata.py`; ran on all 4 fs363 organoids at 50 ms bins.
- **Numbers that matter:** real σ = 1.11–1.22, α = 1.83–2.58,
  TE mean 0.001–0.006 bits/bin, avalanches ~1–1.7k per 10 min with
  median size 1 and max ~1200 spikes.
- **Implication for the bench:** the organoids sit slightly
  *supercritical* (σ>1, literature target for mature cultures ≈1.0,
  α≈1.5). Our sim overshoots (σ=1.64 — bursts self-amplify too much)
  and produces ~3× fewer, ~25× chunkier avalanches — real avalanches
  are dominated by tiny events, ours by scripted big ones.
- **Decision-criteria impact:** near-critical dynamics is the strongest
  "real potential" signal so far — criticality is where computational
  properties (dynamic range, memory, susceptibility) are theorized to
  peak. Worth a dedicated probe eventually.
- **Skeptic's note:** TE at 50 ms bins is weak everywhere (max ~0.017
  bits) — directed coupling may need finer bins or longer recordings;
  and σ>1 could partly reflect finite-size effects on 8 channels.

### Burst dynamics added to the sim (agent loop, cycle 1)

- **What:** SimSNN now has (a) tonic rest drive on hidden neurons and
  (b) network bursts — ~50% of the network recruited for ~45 steps,
  with variable recruitment per event.
- **Numbers that matter:** sim now lands inside the measured real
  ranges — Fano 21.7 (real: 15–65), mean |channel corr| 0.39
  (0.23–0.66), drift similarity 0.94 (0.76–0.99), rate ~0.7 Hz (~1–2).
  Only miss: max channel corr 0.61 vs real ~0.98 (no tight pairs yet).
- **Implication for the bench:** bursts are *interference* — they cost
  io_bandwidth (3.0→2.86 bits) and memory (0.72→0.64). This is the honest
  physics: living substrates compute around bursts, not instead of them.
- **Decision-criteria impact:** makes the sim floor *harder* — wetware
  now has to beat a substrate with realistic noise, not a clean toy.
- **Skeptic's note:** bursts here are externally scripted (Poisson
  onsets, fixed drive) — real bursts are self-organized. A truer model
  would get criticality dynamics, not injected events.

### 2025-… — Zenodo organoid dataset first pass (Itatani, record 18298694)

Not a paper — first real-data observation, full table in
`docs/real_data_report.md`.

- **What:** 4 forebrain organoids (fs363), 8-ch MEA, ~10 min spontaneous
  recordings, vs. our SimSNN resting state.
- **Numbers that matter:** Fano factor 15–65 (real) vs 0.08 (sim);
  max channel corr ~0.98 vs 0.29; mean rates 0.9–2 Hz vs 0.33 Hz;
  drift similarity 0.76–0.99 over 10 min.
- **Implication for the bench:** our sim lacks network bursts and
  channel coupling — the two dominant features of real MEA activity.
  Adding burst dynamics is now a Phase 1 task, or every wetware
  comparison will be sim-vs-fantasy.
- **Decision-criteria impact:** strengthens the "stability" concern —
  org2's firing pattern decorrelated measurably inside 10 minutes.
- **Skeptic's note:** 4 organoids, spontaneous only — no stim-response
  pairs yet, so I/O claims still untested on real tissue.
