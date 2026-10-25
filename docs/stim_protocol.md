# Stim-response protocol (Phase 3, Week 2)

The data audit (docs/designs/stim_response_characterization.md) found
no free stimulation datasets — this protocol is the guaranteed
deliverable instead. Run it in this order on first FinalSpark access.

## 1. Read-only baseline (before any stimulation)

- `get_spike_event` on each of the 4 shared organoids, ≥30 min.
- Baseline: per-channel rate, burst structure (reuse
  `bench/realdata.py analyze`).
- Record the organoid IDs (`fsname`) — they change when organoids are
  swapped on the MEA.

## 2. Single-electrode stim validation (safety first)

- Pick the healthiest organoid (highest stable baseline rate).
- One electrode, lowest StimParam amplitude, 10+ repeated pulses,
  ≥5 s apart. Confirm evoked activity via `count_spike`.
- Escalate amplitude in ~3–5 levels → dose-response via
  `realdata.stim_response()`.
- Watch for the dynamic-threshold artifact: if evoked counts *drop* as
  amplitude rises, that's the detector saturating, not the tissue —
  the analyzer already normalizes by pre-stim rate.

## 3. Codec assumptions test

- Single-electrode dose-response → monotonic + roughly linear?
  (kill thresholds in the design doc)
- Then the real codec test: simultaneous multi-electrode patterns —
  does the joint response ≈ sum of singles? (superposition)
- If yes → run `io_bandwidth` plain vs `wetware+enc`. If the channel is
  superposition-linear, the learned codec should lift real bandwidth
  the way it does on narrow sim channels (+30–80%).

## 4. Multi-session

- Same battery daily → `stability` gets real overnight drift numbers.
- `bench.checkpoint.save_session()` after every learned-state run.
