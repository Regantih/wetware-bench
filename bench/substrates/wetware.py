"""Wetware driver: FinalSpark NeuroPlatform (neuroplatformv2 SDK).

Implements the bench.Substrate contract against living brain organoids on a
microelectrode array. The SDK is async and talks to real lab hardware, so
this driver:

  * stays lazily connected — constructing it touches nothing, the SDK is
    imported and params uploaded on first stimulate()/reward() call
  * defaults to "trigger" mode: each input dimension owns one pre-uploaded
    StimParam (fixed amplitude, own trigger key), so stimulate() is a single
    trigger send + spike count — no re-upload, no mandatory 5s settle
  * offers "analog" mode: amplitude-modulated StimParams uploaded per call.
    Accurate but slow (>=5s settle per call). Only use for small probes.

Interface mapping:
  stimulate(x) -> fire triggers for active dims, count spikes on readout
                 channels for `window_ms`, return per-channel counts
  reward(r)    -> DishBrain scheme: r>0 fires the fixed "predictable"
                 trigger, r<0 fires a random-electrode "punishment" trigger
  reset()      -> drains the spike-count buffer and marks a trial boundary;
                 the culture itself cannot be reset — it's alive
  perturb()    -> no-op: living tissue drifts on its own overnight. That IS
                 what the stability probe measures.

Setup (required before import of the SDK — set these env vars):
  DB_PORT=8086  INTAN_SOFTWARE_IP=...  TRIGGER_IP=...  (values come with access)
  TOTAL_ELECTRODES=64  if your MEA is 64-channel (default 32)

Driver config via env vars (with defaults):
  FS_NAME        dataset/organoid identifier, e.g. "fs511"   (required)
  FS_STIM_ELECTRODES  comma list, default "0,1,2,3,4,5"
  FS_READ_CHANNELS    comma list, default "0,1,2,3,4,5,6,7"
  FS_WINDOW_MS        readout window after trigger, default "200"
  FS_MODE             "trigger" (default) or "analog"
  FS_STIM_UA          weak-pulse amplitude for trigger mode, default "3.0"
"""

import asyncio
import os
import time

import numpy as np

from ..substrate import Substrate

# Trigger allocation (16 max: keys 0-15). Layout for n_inputs=6:
#   0..5   = weak stim per input dim
#   6..11  = strong stim per input dim
#   12     = reward (predictable fixed pulse)
#   13     = punishment (random electrode)
#   14,15  = reserved (e.g. a pure read/count trigger)
REWARD_KEY = 12
PUNISH_KEY = 13
MAX_TRIGGERS = 16


class WetwareDriver(Substrate):
    name = "wetware"
    roles = {"open_loop", "closed_loop"}

    def __init__(self, n_inputs: int = 6, n_outputs: int = 8,
                 seed: int = 0, **_):
        env = os.environ
        self.fsname = env.get("FS_NAME", "")
        self.mode = env.get("FS_MODE", "trigger")
        self.window_ms = int(env.get("FS_WINDOW_MS", "200"))
        self.stim_ua = float(env.get("FS_STIM_UA", "3.0"))
        self.stim_electrodes = _csv(env.get("FS_STIM_ELECTRODES",
                                            "0,1,2,3,4,5"))
        self.read_channels = _csv(env.get("FS_READ_CHANNELS",
                                          "0,1,2,3,4,5,6,7"))
        self.n_inputs = min(n_inputs, len(self.stim_electrodes),
                            (MAX_TRIGGERS - 4) // 2)
        self.n_outputs = min(n_outputs, len(self.read_channels))
        self._rng = np.random.default_rng(seed)
        self._sdk = None  # populated by _connect()

    # -- connection ---------------------------------------------------

    def _connect(self) -> None:
        if self._sdk is not None:
            return
        if not self.fsname:
            raise RuntimeError(
                "FS_NAME not set. Apply for FinalSpark access first "
                "(docs/finalspark_application.md), then set env vars.")
        try:
            from neuroplatformv2.core.intan import IntanController
            from neuroplatformv2.core.trigger import TriggerController
            from neuroplatformv2.core.database import DatabaseController
            from neuroplatformv2.utils import schemas, enumerations
        except ImportError as e:
            raise RuntimeError(
                "neuroplatformv2 SDK not installed. Clone the NeuroPlatform "
                "repo and `python -m pip install -e .`, and set DB_PORT, "
                "INTAN_SOFTWARE_IP, TRIGGER_IP before importing.") from e
        self._sdk = {
            "intan": IntanController, "trig": TriggerController,
            "db": DatabaseController, "schemas": schemas,
            "enums": enumerations,
        }
        self._register_triggers()

    @staticmethod
    def _run(coro):
        """The SDK is async; the Substrate contract is sync. One event loop
        per call is wasteful but safe at the Hz-scale rates this hardware
        allows."""
        return asyncio.run(coro)

    # -- hardware primitives -------------------------------------------

    def _register_triggers(self) -> None:
        """Upload the fixed StimParam set once per session (trigger mode).

        dims 0..n-1 -> weak pulse on electrode i, trigger i
        dims 0..n-1 -> strong pulse on electrode i, trigger n+i
        key 12 -> reward pulse, key 13 -> punishment (electrode chosen per
        call), keys 14-15 left free.
        """
        s, e = self._sdk["schemas"], self._sdk["enums"]

        def pulse(index, key, ua):
            return s.StimParam(
                index=index, enable=True, trigger_key=key,
                stim_shape=e.StimShape.Biphasic,
                polarity=e.StimPolarity.NegativeFirst,
                phase_duration1=100.0, phase_duration2=100.0,
                phase_amplitude1=ua, phase_amplitude2=ua, nb_pulse=0)

        n = self.n_inputs
        params = [
            pulse(self.stim_electrodes[i], i, self.stim_ua)
            for i in range(n)
        ] + [
            pulse(self.stim_electrodes[i], n + i, 2 * self.stim_ua)
            for i in range(n)
        ] + [
            pulse(self.stim_electrodes[0], REWARD_KEY, self.stim_ua),
        ]
        self._run(self._sdk["intan"].send_stimparam(params))
        self._run(self._sdk["intan"].upload_stimparam(self.stim_electrodes))
        time.sleep(5)  # mandatory: recording halts during upload
        self._punish_uploaded = False

    def _fire(self, keys: list[int]) -> None:
        pattern = [0] * MAX_TRIGGERS
        for k in keys:
            pattern[k] = 1
        self._run(self._sdk["trig"].trigger_a_sender(pattern))

    def _counts(self) -> np.ndarray:
        """Spike counts per readout channel over the response window."""
        req = self._sdk["schemas"].CountDurationRequest(duration=self.window_ms)
        counts = np.asarray(
            self._run(self._sdk["intan"].count_spike(req)), dtype=float)
        return counts[np.asarray(self.read_channels[:self.n_outputs])]

    # -- Substrate interface --------------------------------------------

    def stimulate(self, x: np.ndarray) -> np.ndarray:
        self._connect()
        x = np.asarray(x, dtype=float)
        if self.mode == "analog":
            self._stimulate_analog(x)
        else:
            self._stimulate_triggers(x)
        return self._counts()

    def _stimulate_triggers(self, x: np.ndarray) -> None:
        """Ternary spatial encoding, no re-upload: |x|<1/3 -> rest,
        <2/3 -> weak trigger, else strong trigger on that dim's electrode."""
        keys = []
        n = self.n_inputs
        for i in range(n):
            a = abs(x[i])
            if a > 2 / 3:
                keys.append(n + i)     # strong
            elif a > 1 / 3:
                keys.append(i)         # weak
        if keys:
            self._fire(keys)

    def _stimulate_analog(self, x: np.ndarray) -> None:
        """Amplitude-modulated encoding; needs re-upload (+5s) every call."""
        s, e = self._sdk["schemas"], self._sdk["enums"]
        params = []
        for i in range(self.n_inputs):
            ua = float(np.clip(abs(x[i]), 0, 1)) * 2 * self.stim_ua
            if ua < 0.5:
                continue
            params.append(s.StimParam(
                index=self.stim_electrodes[i], enable=True, trigger_key=0,
                stim_shape=e.StimShape.Biphasic,
                polarity=e.StimPolarity.NegativeFirst,
                phase_duration1=100.0, phase_duration2=100.0,
                phase_amplitude1=ua, phase_amplitude2=ua, nb_pulse=0))
        self._run(self._sdk["intan"].send_stimparam(params))
        self._run(self._sdk["intan"].upload_stimparam(self.stim_electrodes))
        time.sleep(5)
        self._fire([0])

    def reward(self, r: float) -> None:
        self._connect()
        if r > 0:
            self._fire([REWARD_KEY])          # predictable pulse
        elif r < 0:
            # punishment: random electrode, re-uploaded ad hoc (rare events)
            s, e = self._sdk["schemas"], self._sdk["enums"]
            el = int(self._rng.choice(self.stim_electrodes))
            param = s.StimParam(
                index=el, enable=True, trigger_key=PUNISH_KEY,
                stim_shape=e.StimShape.Biphasic,
                polarity=e.StimPolarity.NegativeFirst,
                phase_duration1=100.0, phase_duration2=100.0,
                phase_amplitude1=self.stim_ua,
                phase_amplitude2=self.stim_ua, nb_pulse=0)
            self._run(self._sdk["intan"].send_stimparam([param]))
            self._run(self._sdk["intan"].upload_stimparam([el]))
            time.sleep(5)
            self._fire([PUNISH_KEY])

    def reset(self) -> None:
        # the culture is persistent; just mark a boundary by draining the
        # count buffer so stale spikes don't bleed into the next trial
        if self._sdk is not None:
            self._counts()

    def perturb(self, sigma: float) -> None:
        pass  # living tissue drifts by itself — that's the measurement

    def close(self) -> None:
        if self._sdk is not None:
            self._run(self._sdk["intan"].disable_all_stim())


def _csv(s: str) -> list[int]:
    return [int(v) for v in s.split(",") if v.strip()]
