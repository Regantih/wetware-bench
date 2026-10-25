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
