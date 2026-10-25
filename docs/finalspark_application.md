# FinalSpark NeuroPlatform — access application draft

Apply at https://finalspark.com/neuroplatform/ (contact form) or via their
Discord. They ask what you want to do with the platform; below is a draft
project description tailored to this repo. Edit the bracketed parts.

---

## Project: a cross-substrate benchmark suite for organoid computing

**One-line summary:** We're building an open, substrate-agnostic benchmark
suite that runs identical probes on simulated networks, classical baselines,
and living organoids — to measure what wetware actually does better.

**What we'll run on the neuroplatform:**

The same seven probes our suite already runs on a simulated LIF network:

1. *Memory capacity* — Jaeger MC: drive the organoid with a random scalar
   stream on 6 stimulation electrodes, linear readout on 8 recording
   channels, measure how much input history is recoverable.
2. *NARMA-10* — standard reservoir benchmark, NRMSE on held-out series.
3. *I/O bandwidth* — N-class pattern write/read; effective bits per write.
4. *Plasticity assays* — paired-pulse ratios across ISIs; habituation over
   repeated pulses.
5. *Closed-loop Pong* — DishBrain-style; hit rate over episodes, learning
   curve vs a REINFORCE linear-policy baseline run on the same harness.
6. *Stability* — same probe re-run across days; quantifies overnight drift.
7. *Energy accounting* — samples/sec x measured rig power vs. same probes on
   a laptop CPU.

**Why it matters / what FinalSpark gets:** a public, reproducible benchmark
is the missing tooling for the field — currently every group reports
incommensurable demos. Published scores on the neuroplatform would be the
first standardized numbers for living substrates, and the harness stays
open-source.

**Requested access:** shared plan (4 shared organoids) is sufficient — all
probes need only 6 stim + 8 read channels on one organoid. Total stim time
is modest: ~[2–4] sessions/week, hours-scale, standard biphasic pulses
(≤6 µA, 100 µs/phase, negative-first).

**Data handling:** all recordings logged via your Spike DB as usual; our
result JSONs + scoreboard published openly; FinalSpark credited.

**Team:** [name, affiliation, github] — [one line on relevant experience:
Python, ML, signal processing]. Independent researcher / [student at X].

---

## Setup once approved

They provide values for the SDK env vars; put them in `.env` (gitignored):

```
DB_PORT=8086
INTAN_SOFTWARE_IP=<from FinalSpark>
TRIGGER_IP=<from FinalSpark>
TOTAL_ELECTRODES=32          # or 64 depending on assigned MEA

FS_NAME=fs<your-organoid-id>
FS_STIM_ELECTRODES=0,1,2,3,4,5
FS_READ_CHANNELS=0,1,2,3,4,5,6,7
FS_WINDOW_MS=200
FS_MODE=trigger              # 'analog' for amplitude-modulated (slow)
FS_STIM_UA=3.0
```

Then: `pip install -e <neuroplatformv2 repo>` and run
`python -m bench.scoreboard --substrates wetware`.

First real run: start with `--probes io_bandwidth plasticity` (shortest,
lowest stim count) to validate the link before the long memory/Pong runs.
