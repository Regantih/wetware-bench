# Megaplan: exploring the potential of synthetic biological intelligence

A 12-month, solo, zero-budget research program. Goal: generate enough
evidence for a team decision on whether SBI/wetware is worth real
investment — and where exactly the potential is.

## Constraints & assets

- Solo effort, ~5–8 hrs/week, free/shared access only, 6–12 months.
- Already built: this benchmark suite (7 probes, substrate-agnostic),
  the learned codec (`bench/codec.py`), the FinalSpark driver
  (`bench/substrates/wetware.py`), application draft
  (`docs/finalspark_application.md`), narrated demo video (`demo/`).
- Access paths confirmed (as of writing):
  - FinalSpark shared plan: 4 shared organoids, 1 user, Python API,
    ~$500/mo academic or **free for selected projects**.
  - FinalSpark recorded-activity archive: 30 TB+, free to researchers.
  - Open organoid spike datasets on Zenodo (8-ch MEA, 10 kHz,
    600–1800 s recordings).
  - NeuroBridge (neurocomputers.io): built-in 118-hour FinalSpark
    recording, free analysis endpoints.
  - Cortical Cloud ~$300/week — fallback only, outside assumed budget.

## Strategic logic

Three escalating evidence tiers, each independently valuable if the
next is blocked:

1. **Simulation** (done, needs hardening) — establishes the floor and
   the measurement method.
2. **Recorded biological data** (free, no access needed) — first real
   biological numbers: what living networks actually look like vs. sim.
3. **Live wetware experiments** (shared plan, free if approved) — the
   actual answer to "does it compute/learn?"

Each phase ends at a **gate** with explicit advance/pivot/stop criteria.

---

## Phase 1 — Harden the instrument (months 0–2)

*You can't trust wetware numbers until you trust the suite.*

Code work:

- [x] **Stats layer** — `bench/stats.py`: run any probe N seeds →
      mean, std, 95% CI, per-seed table. Wire into scoreboard as
      `--seeds N`. All future claims reported as mean±CI.
- [x] **Stronger sim substrates** — `snn_stdp.py` (spike-timing-dependent
      plasticity instead of eligibility traces) + optionally an
      echo-state/LSM variant. The floor must be respectable or beating
      it means nothing.
- [x] **Codec visibility** — `--compare-codec` flag on scoreboard
      producing plain-vs-encoded column pairs.
- [x] **Session checkpointing** — `bench/checkpoint.py`: save/load
      substrate state + probe results with timestamps; needed for
      multi-day wetware runs.
- [ ] **Docs** — keep `docs/field_notes.md` literature log (~1
      paper/week: Kagan et al. DishBrain, FinalSpark organoid papers,
      reservoir computing surveys, MEA interface limits).

Actions:

- [ ] Finalize + **submit the FinalSpark application**
      (`docs/finalspark_application.md`) — long lead time, do it early.
- [ ] Open a Cortical Cloud inquiry to learn access terms (no commitment).

**Gate 1 → proceed when:** suite produces multi-seed scoreboards; sim
floor is non-trivial (snn_stdp learning_speed clearly above random);
FinalSpark application submitted.

---

## Phase 2 — Free biological data (months 1–3, parallel with Phase 1)

*First contact with real neurons — no access required.*

- [x] Acquire data: FinalSpark 30 TB archive (free request), Zenodo
      organoid datasets, NeuroBridge's built-in 118-hr `fs437` recording.
      → **Zenodo record 18298694 downloaded** (45 organoid .mat files,
      8-ch MEA, 10 kHz). FinalSpark archive request still open.
- [x] **Real-data analysis** — `bench/realdata.py` loads .mat/CSV spike
      data and measures burstiness (Fano), drift, channel correlation;
      `docs/real_data_report.md` compares 4 real organoids vs. the sim.
      First finding: **the sim is ~200× too regular** (Fano 0.08 vs
      15–65) and ~4× too uncorrelated — bursts and co-activation are
      the dominant real dynamics our sim lacks.
- [x] Connectivity/criticality: transfer entropy + avalanche analysis
      (branching σ, size exponent α) in `bench/realdata.py`. Finding:
      real organoids are slightly supercritical (σ 1.1–1.2); sim
      overshoots (σ 1.64) — tunable via burst strength.
- [ ] Remaining: stim-response characterization from recorded
      stimulation sessions; port avalanche pipeline to a probe so
      criticality becomes a first-class metric.
- [ ] **Characterize the channel** — from any recorded stimulation
      sessions: stim→response latency, dose-response, channel noise.
      Calibrates expectations for live runs + validates codec assumptions.
- [x] Deliverable: `docs/real_data_report.md` — confirmed the
      predicted finding: sim is too clean (no bursts, weak coupling).
      Next: add burst dynamics to the sim to match measured biology.

**Gate 2 → proceed when:** ≥1 real dataset analyzed; sim updated to
reflect measured biological noise/drift; FinalSpark access granted (or
explicit decision to proceed on datasets alone).

---

## Phase 3 — First live runs (months 3–6, gated on access)

*Discipline: read-only first, per FinalSpark's own recommendation.*

- [ ] Week 1 (read-only): `DatabaseController` queries — spontaneous
      activity, verify `fsname`/channels, baseline rates, burst
      structure. Fix `wetware.py` helpers (`_connect`/`_fire`/`_counts`)
      against real return shapes — expect small corrections.
- [ ] Week 2 (stimulation validation): single-electrode stim → evoked
      latency; dose-response curve across amplitudes; pick healthiest
      of the 4 shared organoids.
- [ ] Probes in cost order: `io_bandwidth`, `plasticity` →
      `memory_capacity`, `narma`, `codec`. `learning_speed` last — needs
      proven closed-loop timing.
- [ ] **Multi-session protocol:** identical probe battery daily/weekly
      → real `stability` numbers across days (the thing nobody
      systematically measures).
- [ ] Log every failure mode: bursts swamping reads, dead channels,
      organoid health decline.

**Gate 3 → proceed when:** stim→response loop verified; io_bandwidth +
plasticity completed ≥1× on living tissue.

---

## Phase 4 — The core experiment (months 6–9)

- [ ] **Full suite on wetware** — every probe, N≥5 sessions, mean±CI.
- [ ] **The codec hypothesis** — does learned encoding lift real-channel
      I/O? The experiment this whole project builds toward: if the
      electrode interface is the bottleneck, the codec is the unlock.
- [ ] **learning_speed on wetware vs sim vs silicon baseline** —
      directly tests the DishBrain "learns in minutes" claim under a
      controlled protocol.
- [ ] **Codec transfer** — calibrate on organoid A, test on B: does the
      learned channel generalize?

**Gate 4 decision point** — scoreboard now has a real biological
column; judge against pre-registered criteria below.

---

## Phase 5 — Synthesis & verdict (months 9–12)

- [ ] If promising: **one harder probe** — closed-loop task or
      classifier on wetware (spectrogram→stim, or MiniPong if loop
      timing allows).
- [ ] **Energy estimate** — platform power draw ÷ measured operations;
      the honest version of the "20-watt brain" claim.
- [ ] **`docs/verdict.md`** — the decision memo: where SBI showed real
      potential, where it's hype, what the bottleneck actually is
      (I/O vs. neurons vs. stability), recommendation:
      invest / keep watching / drop.
- [ ] Optional: open-source the suite + findings. "MLPerf for wetware"
      is unclaimed territory.

---

## Pre-registered decision criteria

Defined now, judged later — so the verdict can't be rationalized.

| signal | green (real potential) | yellow | red (hype/stop) |
|---|---|---|---|
| learning | wetware > sim floor on learning_speed or plasticity | matches sim | below sim / no measurable plasticity |
| stability | multi-day experiments reproducible | works, needs daily recalibration | drift kills same-week reproducibility |
| I/O | codec lifts bandwidth ≥30% on real channel | modest gain | channel too lossy for any encoding |
| compute | memory_capacity/NARMA above linear baseline | comparable | below tap-delay baseline |

**Kill criteria:** access denied twice + datasets show dynamics
incompatible with closed-loop work → verdict = "premature field,
revisit in ~2 years". That is itself a valid team answer.

## Risks & mitigations

- **Access denied/delayed** → Phase 2 datasets still yield real
  biological analysis (Zenodo + NeuroBridge need no approval).
- **Shared-plan scheduling contention** → probes designed to run
  unattended/queued; batch stimulation sessions.
- **Culture death mid-run** → 4 organoids on shared plan; session
  checkpointing lets probes resume.
- **Solo time sink** → serialized phases; each phase's code work is
  1–3 days of agent-assisted implementation.
- **Sim floor too weak** → Phase 1 adds STDP + tuned baselines before
  any biological comparison.

## Cost summary

- Required: **$0** — free datasets + free-for-researchers shared plan.
- Contingency only: FinalSpark shared ~$500/mo if application rejected;
  Cortical Cloud ~$300/wk. Both are explicit decision points, not
  assumed.
