# Spec: stim-response characterization — discovery-first (rev 2)

*Revised after Goldfish review (design_critic + structural). Original
verdict on rev 1: proceed-with-changes — all candidate data sources were
probably spontaneous-only, and the measurement was one-sided (could
falsify the codec but never confirm it).*

## What (revised)

Two-phase deliverable:

**Phase A — data audit (mandatory first step).** Enumerate every
candidate source against a defined `stim_events` schema BEFORE writing
analysis code. A source qualifies only if it provides
(time, electrode, amplitude) with ≥10 repeated trials per level and ≥3
amplitude levels. Candidates: Zenodo 18298694 (expected FAIL — record
states recordings were "without any external stimulation"), NeuroBridge
fs437 (expected FAIL — spontaneous), FinalSpark docs examples.

**Phase B — guaranteed artifact.** If audit finds qualifying data:
run the measurement. If not (expected): deliver the fixture-tested
`stim_response()` analyzer + the Phase-3 measurement protocol, so the
tool exists the moment hardware access does.

## What it can and cannot prove

One-sided falsification ONLY: single-electrode pulse data yields
per-electrode PSTH + dose-response, which can *kill* the codec if
gain-vs-amplitude is wildly nonlinear — but can never confirm the
codec's actual risky assumption (cross-electrode superposition of
simultaneous stimulation). Superposition needs simultaneous
multi-electrode stim — Phase 3 hardware only.

## Pre-registered kill/confirm thresholds (before seeing numbers)

- Codec assumption KILLED if: dose-response is non-monotonic, or
  gain at 2× amplitude differs >5× from linear extrapolation, or
  channel-rate vector drift <0.8 similarity within one session.
- Codec assumption SURVIVES (not "confirmed") if: roughly monotonic
  dose-response, latency stable ±20ms across trials.

## Method requirements

- **Dynamic-threshold correction (REQUIRED):** FinalSpark's detection
  threshold rises during stimulation/bursts → under-counts evoked
  spikes → fake saturating dose-response. Normalize per-epoch counts
  by pre-stim detection-rate baseline, or mark stim-epoch bins invalid.
- **Event-window collisions:** the 3ms event window merges coincident
  spikes — worst in the first ~10ms post-stim where latency is
  measured. Report latencies as lower bounds when early-epoch event
  density is high.
- `stim_events` schema: `(t_seconds, electrode_idx, amplitude_ua)`;
  loader accepts FinalSpark trigger logs or a simple CSV.

## Interface

`bench/realdata.py`: `stim_response(times, chans, stim_events, pre_ms,
post_ms)` → per-channel PSTH, latency, gain-vs-amplitude, drift.
Unit-tested on synthetic fixtures (no real data needed to develop).
Output: `docs/channel_report.md` or the Phase-3 protocol in
`docs/stim_protocol.md` if the audit is empty.
