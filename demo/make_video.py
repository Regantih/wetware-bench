"""Render the narrated demo video.

Scenes are timed to their narration clip (Windows SAPI -> WAV -> ffmpeg
mux). All on-screen computation is live: the SNN really runs, the paddle
really is driven by it, the scoreboard is the real results file.

    python -m demo.make_video        -> demo/wetware_bench.mp4
    python -m demo.train_pong        # optional: retrain warm-start first
"""

import json
import os
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from bench.envs import MiniPong
from bench.probes import PROBES
from bench.substrates import make

W, H, FPS = 1280, 720, 24
OUT = Path(__file__).parent
FRAMES = OUT / "_frames"
AUDIO = OUT / "_audio"

BG = (13, 17, 23)
FG = (201, 209, 217)
DIM = (110, 118, 129)
GREEN = (63, 185, 80)
BLUE = (88, 166, 255)
ORANGE = (240, 136, 62)
PURPLE = (188, 140, 255)

FONT_PATHS = ["C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/cour.ttf",
              "C:/Windows/Fonts/CascadiaMono.ttf"]
F_TITLE, F_H, F_M, F_S = None, None, None, None


def _fonts():
    global F_TITLE, F_H, F_M, F_S
    for p in FONT_PATHS:
        if Path(p).exists():
            F_TITLE, F_H, F_M, F_S = (ImageFont.truetype(p, s)
                                      for s in (64, 34, 22, 16))
            return
    F_TITLE = F_H = F_M = F_S = ImageFont.load_default()


def frame():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def text_c(d, y, s, f, color=FG):
    d.text(((W - d.textlength(s, font=f)) / 2, y), s, font=f, fill=color)


def save(img, n):
    img.save(FRAMES / f"f{n:05d}.png")
    return n + 1


# ------------------------------------------------------------ narration

NARRATION = {
    # 1. introduce the concept + why it has potential
    "title": (
        "Your laptop boots from a BIOS. This is a biOS — a biological "
        "intelligence operating system. The C L One, from Cortical Labs: "
        "living human neurons wired to silicon electrodes. Why does it "
        "matter? Your brain does supercomputer work on twenty watts. "
        "Data centers burn megawatts imitating it."),
    # 2. the mechanism — one contract for every substrate
    "raster": (
        "One contract drives it all: stimulate with a pattern, read the "
        "spikes back. This is a simulated reservoir of two hundred and "
        "forty neurons, live. Swap it for an organoid on FinalSpark's "
        "platform, and the same code drives real human neurons."),
    # 3. closed loop — where SBI gets interesting
    "pong": (
        "Close the loop and it gets interesting. Ball position goes in "
        "as stimulation, spike counts vote on the paddle move. Hits "
        "reward, misses punish — synaptic plasticity, the same mechanism "
        "your own brain uses. It's the DishBrain experiment Cortical "
        "Labs made famous."),
    # 4. the learned codec — attack the real bottleneck
    "codec": (
        "But here's the twist: the bottleneck probably isn't the neurons, "
        "it's the interface. So we built a learned codec. It calibrates "
        "the channel, then writes every pattern in the directions the "
        "substrate hears best. On a narrow channel, write bandwidth "
        "nearly doubles — on a living electrode array, that's the difference "
        "between whispering and speaking clearly."),
    # 5. what we built
    "scoreboard": (
        "What we built: a benchmark suite — the field's missing ruler. "
        "Seven probes: memory, compute, I O bandwidth, plasticity, "
        "learning speed, stability, energy. Every number tests a claim. "
        "The simulator sets the floor. Living neurons have to beat it."),
    # 6. what's next
    "end": (
        "What's next? FinalSpark access, one driver swap, and every "
        "probe runs unchanged on living neurons — the first "
        "standardized numbers for a biological computer."),
}

_VOICE = OUT / "voices" / "en_US-lessac-medium.onnx"


def tts(text: str, path: Path) -> float:
    """Text-to-speech -> WAV (22050 Hz mono). Returns clip duration (s).

    Priority: ElevenLabs (if ELEVENLABS_API_KEY set) -> Piper (local
    neural voice) -> edge-tts -> Windows SAPI.
    """
    fns = ([_elevenlabs_tts] if os.environ.get("ELEVENLABS_API_KEY") else [])
    fns += [_piper_tts, _edge_tts, _sapi_tts]
    for fn in fns:
        try:
            fn(text, path)
            break
        except Exception as e:
            print(f"  {fn.__name__} failed ({type(e).__name__})")
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def _elevenlabs_tts(text: str, path: Path) -> None:
    """ElevenLabs TTS. Needs ELEVENLABS_API_KEY; optional ELEVENLABS_VOICE
    (default: Rachel) and ELEVENLABS_MODEL (default: eleven_multilingual_v2)."""
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    audio = client.text_to_speech.convert(
        text=text,
        voice_id=os.environ.get("ELEVENLABS_VOICE", "21m00Tcm4TlvDq8ikWAM"),
        model_id=os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
        output_format="mp3_22050_32",
    )
    mp3 = path.with_suffix(".mp3")
    mp3.write_bytes(b"".join(audio))
    subprocess.run(["ffmpeg", "-y", "-i", str(mp3),
                    "-ar", "22050", "-ac", "1", str(path)],
                   check=True, capture_output=True)


def _piper_tts(text: str, path: Path) -> None:
    global _voice
    try:
        _voice
    except NameError:
        from piper import PiperVoice
        _voice = PiperVoice.load(str(_VOICE))
    with wave.open(str(path), "wb") as w:
        _voice.synthesize_wav(text, w)


def _edge_tts(text: str, path: Path) -> None:
    import asyncio
    import edge_tts
    mp3 = path.with_suffix(".mp3")

    async def go():
        await edge_tts.Communicate(
            text, voice="en-US-AndrewNeural", rate="-5%").save(str(mp3))
    asyncio.run(go())
    subprocess.run(["ffmpeg", "-y", "-i", str(mp3),
                    "-ar", "22050", "-ac", "1", str(path)],
                   check=True, capture_output=True)


def _sapi_tts(text: str, path: Path) -> None:
    ps = ("Add-Type -AssemblyName System.Speech; "
          "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
          "$s.Rate=-1; $s.SelectVoice('Microsoft Zira Desktop'); "
          "$s.SetOutputToWaveFile($env:NARR_OUT); "
          "$s.Speak($env:NARR_TEXT); $s.Dispose()")
    env = {**os.environ, "NARR_TEXT": text, "NARR_OUT": str(path)}
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   env=env, check=True, capture_output=True)


def stitch(clips: list[Path], out: Path, gap: float = 0.35) -> None:
    """Concatenate WAV clips with short silence gaps."""
    params, data = None, []
    sr = 0
    for c in clips:
        with wave.open(str(c)) as w:
            params, sr = w.getparams(), w.getframerate()
            data.append(w.readframes(w.getnframes()))
            data.append(b"\x00" * int(gap * sr * params.sampwidth
                                    * params.nchannels))
    with wave.open(str(out), "wb") as w:
        w.setparams(params)
        w.writeframes(b"".join(data))


# ---------------------------------------------------------------- scenes

def scene_title(n, steps):
    for i in range(steps):
        img, d = frame()
        a = min(1.0, i / (FPS * 0.8))
        col = tuple(int(c * a) for c in FG)
        text_c(d, 250, "wetware bench", F_TITLE, col)
        text_c(d, 350, "measuring the potential of synthetic "
               "biological intelligence", F_M,
               tuple(int(c * a) for c in DIM))
        if i > FPS * 1.2:
            text_c(d, 470, "one interface  ·  seven probes  ·  any substrate",
                   F_M, tuple(int(c * a) for c in BLUE))
        n = save(img, n)
    return n


def scene_raster(n, steps):
    snn = make("snn")
    rng = np.random.default_rng(1)
    n_show, hist_w = 96, 520
    raster = np.zeros((n_show, hist_w))
    for t in range(steps):
        ph = t % 96
        x = np.zeros(snn.n_inputs)
        if ph < 24:
            x[rng.integers(0, 2)] = 1.0 * (1 if (t // 96) % 2 else -1)
        elif 48 <= ph < 60:
            x[2:4] = 0.8
        s = snn._step(x)
        raster = np.roll(raster, -1, axis=1)
        raster[:, -1] = s[:n_show]

        img, d = frame()
        text_c(d, 40, "the contract: stimulate(x) → spikes", F_H)
        code = [
            "class Substrate:", "",
            "  stimulate(x) -> counts",
            "  reward(r)",
            "  reset()      # trial boundary",
            "  perturb(s)   # overnight drift", "",
            f"> x = {np.array2string(x[:4], precision=1)}",
            "> substrate.stimulate(x)",
            f"  # {int(s.sum())} neurons fired this step",
        ]
        for j, ln in enumerate(code):
            d.text((60, 140 + j * 34), ln, font=F_M,
                   fill=GREEN if ln.startswith((">", "  #")) else FG)
        rx, ry, rh = 640, 140, 480
        d.rectangle([rx - 2, ry - 2, rx + hist_w + 2, ry + rh + 2],
                    outline=DIM)
        cell = rh / n_show
        ys, xs = np.nonzero(raster)
        for yy, xx in zip(ys, xs):
            d.rectangle([rx + xx, ry + yy * cell, rx + xx,
                         ry + (yy + 1) * cell], fill=BLUE)
        d.text((rx, ry + rh + 14),
               "live spikes · 240-neuron LIF reservoir", font=F_S, fill=DIM)
        n = save(img, n)
    return n


def scene_pong(n, steps):
    snn = make("snn", seed=3)
    rng = np.random.default_rng(3)
    enc = rng.normal(0, 1, (snn.n_inputs, 5))
    brain = OUT / "pong_brain.npz"
    trained = brain.exists()
    if trained:
        b = np.load(brain)
        enc, snn.W_act = b["enc"], b["W_act"]
        snn.W_rec, snn.bias = b["W_rec"], b["bias"]
    env = MiniPong(3, shape=0.05)
    half = snn.n_outputs // 2
    FIELD = 300

    for t in range(steps):
        x = np.clip(enc @ env.obs(), -1, 1)
        r = snn.stimulate(x)
        act = 0 if r[:half].sum() >= r[half:].sum() else 1
        rew = env.step(act)
        snn.reward(rew)

        img, d = frame()
        text_c(d, 40, "closed loop: the SNN plays Pong", F_H)
        label = ("policy layer warm-started · live reward plasticity on"
                 if trained else "cold reservoir — no training")
        d.text((W - d.textlength(label, font=F_S) - 60, 95),
               label, font=F_S, fill=GREEN if trained else ORANGE)

        fx, fy = 110, 140
        d.rectangle([fx, fy, fx + FIELD, fy + FIELD], outline=DIM)
        bx, by = fx + env.bx * FIELD, fy + env.by * FIELD
        d.ellipse([bx - 6, by - 6, bx + 6, by + 6], fill=ORANGE)
        ph = env.paddle_h * FIELD
        py = fy + env.py * FIELD
        d.rectangle([fx - 10, py - ph / 2, fx - 2, py + ph / 2], fill=GREEN)

        barx = fx + FIELD + 80
        d.text((barx, fy - 30), "readout neurons (up | down)",
               font=F_S, fill=DIM)
        m = max(1.0, r.max())
        for i in range(16):
            val = r[i * (snn.n_outputs // 16):
                    (i + 1) * (snn.n_outputs // 16)].sum()
            hgt = int(120 * val / (m * (snn.n_outputs // 16)))
            c = BLUE if i < 8 else PURPLE
            d.rectangle([barx + i * 32, fy + 140 - hgt,
                         barx + i * 32 + 24, fy + 140], fill=c)
        d.line([barx + 8 * 32 - 4, fy, barx + 8 * 32 - 4, fy + 140],
               fill=DIM)

        rate = env.hits / max(env.arrivals, 1)
        d.text((fx, fy + FIELD + 30),
               f"action: {'UP' if act == 0 else 'DOWN'}   "
               f"hits {env.hits} / arrivals {env.arrivals}   "
               f"hit rate {rate:.2f}", font=F_M, fill=FG)
        if rew > 0:
            d.text((fx + FIELD - 40, fy + FIELD + 30), "+1", font=F_H,
                   fill=GREEN)
        n = save(img, n)
    return n


def scene_codec(n, steps):
    """Plain vs encoded response patterns on a narrow channel — real data
    from a live 4-readout SNN, projected to 2D."""
    from bench.codec import EncodedSubstrate
    from bench.substrates.snn_sim import SimSNN

    plain = SimSNN(n_outputs=4, seed=0)
    enc = EncodedSubstrate(SimSNN(n_outputs=4, seed=0))
    rng = np.random.default_rng(7)
    P = rng.choice([-1.0, 1.0], (8, plain.n_inputs))
    z = np.zeros(plain.n_inputs)
    rp, re = [], []
    for p in P:
        for _ in range(2):
            plain.stimulate(z)
            enc.stimulate(z)
        rp.append(plain.stimulate(p))
        re.append(enc.stimulate(p))
    allr = np.vstack([rp, re])
    allr -= allr.mean(0)
    _, _, vt = np.linalg.svd(allr, full_matrices=False)
    Pp, Pe = np.asarray(rp) @ vt[:2].T, np.asarray(re) @ vt[:2].T

    # real measured numbers for the labels
    kw = dict(n_classes=8, trials_per=8)
    a = PROBES["io_bandwidth"].run(
        SimSNN(n_outputs=4, seed=0), **kw).metrics["bits_per_write"]
    b = PROBES["io_bandwidth"].run(
        EncodedSubstrate(SimSNN(n_outputs=4, seed=0)), **kw
    ).metrics["bits_per_write"]

    colors = [(88, 166, 255), (240, 136, 62), (63, 185, 80), (248, 81, 73),
              (188, 140, 255), (255, 200, 60), (80, 220, 220), (230, 120, 160)]

    def panel(d, x0, y0, pw, ph, pts, upto, title, metric):
        d.rectangle([x0, y0, x0 + pw, y0 + ph], outline=DIM)
        d.text((x0, y0 - 28), title, font=F_M, fill=FG)
        if pts.shape[0]:
            lo, hi = pts.min(0), pts.max(0)
            sp = (hi - lo)
            sp[sp < 1e-9] = 1
            for i in range(min(upto, len(pts))):
                px = x0 + 30 + (pts[i, 0] - lo[0]) / sp[0] * (pw - 60)
                py = y0 + 30 + (pts[i, 1] - lo[1]) / sp[1] * (ph - 60)
                r = 9
                d.ellipse([px - r, py - r, px + r, py + r], fill=colors[i])
        d.text((x0, y0 + ph + 14), metric, font=F_M, fill=GREEN)

    for t in range(steps):
        img, d = frame()
        text_c(d, 40, "the learned codec: same neurons, better encoding",
               F_H)
        d.text((120, 105), "8 stimulation patterns → 4-channel response "
               "(PCA projection)", font=F_S, fill=DIM)
        upto = int(8 * min(1.0, t / (steps * 0.45)))
        show_metric = t > steps * 0.5
        panel(d, 120, 160, 480, 400, Pp, upto, "raw stimulation",
              f"{a:.2f} bits/write" if show_metric else "")
        panel(d, 680, 160, 480, 400, Pe, upto, "codec-encoded",
              f"{b:.2f} bits/write" if show_metric else "")
        n = save(img, n)
    return n


def scene_scoreboard(n, steps):
    results = json.loads(
        (OUT.parent / "results" / "results.json").read_text())
    subs = ["snn", "tapdelay", "linear_pg"]
    seen = {}
    for r in results:
        key = PROBES[r["probe"]].HEADLINE
        if key in r["metrics"]:
            seen.setdefault(r["probe"], {})[r["substrate"]] = \
                r["metrics"][key]
    probes = list(seen)
    reveal = max(1, steps // (len(probes) + 1))
    for t in range(steps):
        img, d = frame()
        text_c(d, 50, "the scoreboard", F_H)
        x0, y0, cw, rh = 120, 150, 260, 44
        d.text((x0, y0), "probe", font=F_M, fill=DIM)
        for j, s in enumerate(subs):
            d.text((x0 + 260 + j * cw, y0), s, font=F_M, fill=DIM)
        for i, p in enumerate(probes):
            if t < i * reveal:
                break
            y = y0 + 40 + i * rh
            d.text((x0, y), p, font=F_M, fill=FG)
            for j, s in enumerate(subs):
                v = seen[p].get(s)
                d.text((x0 + 260 + j * cw, y),
                       "—" if v is None else f"{v:.3g}",
                       font=F_M, fill=BLUE if v is not None else DIM)
        n = save(img, n)
    return n


def scene_end(n, steps):
    hold = steps - int(FPS * 1.5)          # last 1.5s = fade to black
    for i in range(steps):
        img, d = frame()
        if i >= hold:                       # fade out over the tail
            a = max(0.0, 1.0 - (i - hold) / (steps - hold))
            fgc = tuple(int(c * a) for c in FG)
            dim = tuple(int(c * a) for c in DIM)
        else:
            fgc, dim = FG, DIM
        text_c(d, 280, "swap in living neurons.", F_H, fgc)
        text_c(d, 350, "the probes don't change.", F_H, dim)
        text_c(d, 460, "github.com/FinalSpark-np  ·  Cortical-Labs/cl-api-doc",
               F_S, dim)
        n = save(img, n)
    return n


# -------------------------------------------------------------------- main

def main():
    _fonts()
    FRAMES.mkdir(exist_ok=True)
    AUDIO.mkdir(exist_ok=True)
    for old in FRAMES.glob("f*.png"):      # stale frames corrupt the render
        old.unlink()

    scenes = [("title", scene_title), ("raster", scene_raster),
              ("pong", scene_pong), ("codec", scene_codec),
              ("scoreboard", scene_scoreboard), ("end", scene_end)]

    # 1. synthesize narration, measure each clip
    clips, durs = [], []
    for name, _ in scenes:
        p = AUDIO / f"{name}.wav"
        dur = tts(NARRATION[name], p)
        clips.append(p)
        durs.append(dur + 0.5)          # trailing beat before cut
        print(f"narration {name}: {dur:.1f}s")
    durs[-1] += 1.5                     # end card: hold past final words

    # 2. render frames per scene, timed to its clip
    n = 0
    for (name, fn), dur in zip(scenes, durs):
        steps = int(dur * FPS)
        print(f"scene {name}: {steps} frames")
        n = fn(n, steps)

    # 3. stitch narration, encode video, mux
    narration = AUDIO / "narration.wav"
    stitch(clips, narration)
    silent = OUT / "_silent.mp4"
    out = OUT / "wetware_bench.mp4"
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS),
                    "-i", str(FRAMES / "f%05d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                    str(silent)], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-i", str(silent), "-i", str(narration),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                    str(out)], check=True, capture_output=True)
    print(f"wrote {out} ({n} frames + narration)")


if __name__ == "__main__":
    main()
