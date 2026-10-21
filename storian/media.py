"""Deterministic media work: probing, log-aware keyframe extraction, contact sheets, motion signals.

Everything here is cheap. Keyframes are decoded with `-skip_frame nokey`, so a 4K long-GOP
clip costs well under a second regardless of bitrate. No full decode of raw footage ever happens
until a shot is actually chosen for a preview.
"""

import json
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FRAME_WIDTH = 480
SHEET_COLS = 4
SHEET_MAX_FRAMES = 12
SHEET_TILE_W = 320

LOG_GAMMAS = ("s-log3", "slog3")


def run(cmd, check=True):
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


# ---------------------------------------------------------------- probe

def probe(path: Path) -> dict:
    """Container/stream facts plus camera metadata (gamma, lens, body, record time)."""
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    info = json.loads(out.stdout)
    v = next((s for s in info["streams"] if s.get("codec_type") == "video"), {})
    a = next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    num, den = (v.get("r_frame_rate") or "0/1").split("/")
    clip = {
        "id": path.stem,
        "path": str(path),
        "size_bytes": int(info["format"].get("size", 0)),
        "duration": round(float(info["format"].get("duration", 0)), 3),
        "codec": v.get("codec_name"),
        "width": v.get("width"),
        "height": v.get("height"),
        "fps": round(int(num) / int(den), 3) if int(den) else None,
        "pix_fmt": v.get("pix_fmt"),
        "has_audio": a is not None,
    }
    clip.update(camera_meta(path))
    return clip


def camera_meta(path: Path) -> dict:
    """Pull gamma/lens/body/time from the embedded Sony XML (and generic tags) via exiftool."""
    try:
        out = run(["exiftool", "-j", "-n", "-CaptureGammaEquation", "-AcquisitionRecordGroupItemValue",
                   "-AcquisitionRecordGroupItemName", "-LensModelName", "-LensModel", "-DeviceModelName",
                   "-Model", "-CreationDateValue", "-CreateDate", "-GPSLatitude", "-GPSLongitude", str(path)],
                  check=False)
        tags = json.loads(out.stdout)[0] if out.stdout.strip() else {}
    except (FileNotFoundError, json.JSONDecodeError, IndexError):
        return {}
    gamma = None
    names = tags.get("AcquisitionRecordGroupItemName")
    values = tags.get("AcquisitionRecordGroupItemValue")
    if isinstance(names, list) and isinstance(values, list):
        gamma = dict(zip(names, values)).get("CaptureGammaEquation")
    elif names == "CaptureGammaEquation":
        gamma = values
    meta = {
        "gamma": gamma or tags.get("CaptureGammaEquation"),
        "lens": tags.get("LensModelName") or tags.get("LensModel"),
        "camera": tags.get("DeviceModelName") or tags.get("Model"),
        "recorded_at": str(tags.get("CreationDateValue") or tags.get("CreateDate") or "") or None,
    }
    if "GPSLatitude" in tags:
        meta["gps"] = [tags["GPSLatitude"], tags.get("GPSLongitude")]
    return {k: v for k, v in meta.items() if v is not None}


def is_log(clip: dict) -> bool:
    g = (clip.get("gamma") or "").lower().replace(" ", "")
    return any(x in g for x in LOG_GAMMAS)


def keyframe_times(path: Path) -> list[float]:
    """Keyframe PTS from the packet index (no decoding)."""
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
               "packet=pts_time,flags", "-of", "csv=p=0", str(path)])
    times = []
    for line in out.stdout.splitlines():
        parts = line.split(",")
        if len(parts) >= 2 and "K" in parts[1] and parts[0] not in ("", "N/A"):
            times.append(float(parts[0]))
    return sorted(times)


# ---------------------------------------------------------------- log -> display

def write_slog3_lut(path: Path, size: int = 33):
    """Sony S-Log3 / S-Gamut3.Cine -> Rec.709 display LUT for previews (not a grade)."""
    g = np.linspace(0, 1, size)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")  # .cube wants red fastest
    rgb = np.stack([r, gg, b], axis=-1).reshape(-1, 3)
    cv = 64 + rgb * 876  # ffmpeg maps legal range to 0..1; S-Log3 is defined on 10-bit code values
    lin = np.where(cv >= 171.2102946929,
                   (10 ** ((cv - 420) / 261.5)) * 0.19 - 0.01,
                   (cv - 95) * 0.01125 / (171.2102946929 - 95))
    m = np.array([[1.6269474, -0.5401385, -0.0868089],
                  [-0.1785155, 1.4179409, -0.2394254],
                  [-0.0444361, -0.1959199, 1.2403560]])
    lin = np.clip(lin @ m.T, 0, None) * 0.9
    tone = (lin * (2.51 * lin + 0.03)) / (lin * (2.43 * lin + 0.59) + 0.14)  # ACES-ish filmic
    out = np.clip(tone, 0, 1) ** (1 / 2.2)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(f"TITLE \"storian slog3->709 preview\"\nLUT_3D_SIZE {size}\n")
        for row in out:
            f.write(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}\n")


def display_filter(clip: dict, lut: Path, width: int) -> str:
    vf = f"scale={width}:-2"
    if is_log(clip):
        vf += f",format=rgb48le,lut3d='{lut}'"
    return vf


# ---------------------------------------------------------------- frames + signals

def extract_keyframes(clip: dict, out_dir: Path, lut: Path) -> list[dict]:
    """One display-ready JPEG per keyframe (~1/s on most cameras), named by timestamp."""
    out_dir.mkdir(parents=True, exist_ok=True)
    src = Path(clip["path"])
    times = keyframe_times(src)
    tmp = out_dir / "_k_%05d.jpg"
    cmd = ["ffmpeg", "-v", "fatal", "-y", "-skip_frame", "nokey", "-hwaccel", "videotoolbox",
           "-i", str(src), "-vf", display_filter(clip, lut, FRAME_WIDTH), "-fps_mode", "passthrough",
           "-q:v", "3", str(tmp)]
    r = run(cmd, check=False)
    if r.returncode != 0:  # no hardware decoder for this codec: fall back to software
        cmd.remove("-hwaccel"); cmd.remove("videotoolbox")
        run(cmd)
    files = sorted(out_dir.glob("_k_*.jpg"))
    if len(times) != len(files):  # odd streams: spread evenly
        times = list(np.linspace(0, clip["duration"], len(files), endpoint=False))
    frames = []
    for t, f in zip(times, files):
        name = f"t{t:09.3f}.jpg"
        f.replace(out_dir / name)
        frames.append({"t": round(float(t), 3), "file": name})
    return frames


def frame_signals(frame_paths: list[Path]) -> list[dict]:
    """Per-frame brightness, sharpness, change vs previous, and global shift (pan/tilt hint)."""
    sig, prev = [], None
    for p in frame_paths:
        im = Image.open(p).convert("L").resize((128, 72))
        a = np.asarray(im, dtype=np.float32) / 255.0
        lap = a[1:-1, 1:-1] * 4 - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]
        s = {"brightness": round(float(a.mean()), 3), "sharpness": round(float(lap.var() * 1000), 2)}
        if prev is not None:
            s["change"] = round(float(np.abs(a - prev).mean()), 3)
            dx, dy = phase_shift(prev, a)
            s["shift"] = [dx, dy]
        sig.append(s)
        prev = a
    return sig


def phase_shift(a, b):
    """How far image content moved from a to b, in pixels (+x right, +y down)."""
    fa, fb = np.fft.fft2(a - a.mean()), np.fft.fft2(b - b.mean())
    r = fa * np.conj(fb)
    r /= np.abs(r) + 1e-9
    corr = np.abs(np.fft.ifft2(r))
    y, x = np.unravel_index(np.argmax(corr), corr.shape)
    h, w = a.shape
    if y > h // 2: y -= h
    if x > w // 2: x -= w
    return int(-x), int(-y)


def summarize_motion(sig: list[dict]) -> dict:
    changes = [s["change"] for s in sig if "change" in s]
    shifts = [s["shift"] for s in sig if "shift" in s]
    if not changes:
        return {"activity": 0.0, "camera_hint": "static"}
    sx = float(np.median([s[0] for s in shifts]))
    sy = float(np.median([s[1] for s in shifts]))
    act = float(np.mean(changes))
    if abs(sx) >= 3 and abs(sx) >= abs(sy):  # content drifting left means the camera pans right
        hint = "pan-left" if sx > 0 else "pan-right"
    elif abs(sy) >= 3:
        hint = "tilt-up" if sy > 0 else "tilt-down"
    elif act < 0.02:
        hint = "static"
    else:
        hint = "moving"
    return {"activity": round(act, 3), "camera_hint": hint,
            "dark": float(np.mean([s["brightness"] for s in sig])) < 0.12,
            "soft": float(np.median([s["sharpness"] for s in sig])) < 1.0}


# ---------------------------------------------------------------- contact sheets

def _font(size):
    for name in ("/System/Library/Fonts/SFNSMono.ttf", "/System/Library/Fonts/Menlo.ttc",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(clip: dict, frames: list[dict], frame_dir: Path, out: Path):
    """Grid of evenly sampled frames with timestamps: what the labeling agent looks at."""
    if not frames:
        return
    n = min(SHEET_MAX_FRAMES, len(frames))
    idx = np.linspace(0, len(frames) - 1, n).round().astype(int)
    picks = [frames[i] for i in idx]
    first = Image.open(frame_dir / picks[0]["file"])
    tw = SHEET_TILE_W
    th = round(first.height * tw / first.width)
    cols = min(SHEET_COLS, n)
    rows = (n + cols - 1) // cols
    head = 34
    sheet = Image.new("RGB", (cols * tw, head + rows * th), (12, 12, 12))
    d = ImageDraw.Draw(sheet)
    d.text((10, 8), f"{clip['id']}  {clip['duration']:.1f}s  {clip.get('lens', '')}", fill=(255, 255, 255), font=_font(18))
    small = _font(15)
    for i, fr in enumerate(picks):
        im = Image.open(frame_dir / fr["file"]).resize((tw, th))
        x, y = (i % cols) * tw, head + (i // cols) * th
        sheet.paste(im, (x, y))
        label = f"{fr['t']:.1f}s"
        d.rectangle([x, y, x + 8 + 9 * len(label), y + 20], fill=(0, 0, 0))
        d.text((x + 4, y + 2), label, fill=(255, 209, 71), font=small)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=85)


# ---------------------------------------------------------------- previews

def render_preview(clip: dict, t_in: float, t_out: float, out: Path, lut: Path, width=960):
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-hwaccel", "videotoolbox", "-ss", f"{t_in:.3f}", "-i", clip["path"],
           "-t", f"{max(0.1, t_out - t_in):.3f}", "-vf", display_filter(clip, lut, width) + ",format=yuv420p",
           "-c:v", "h264_videotoolbox", "-b:v", "4M", "-c:a", "aac", "-b:a", "128k", "-ac", "2",
           "-movflags", "+faststart", str(out)]
    r = run(cmd, check=False)
    if r.returncode != 0:
        cmd = [c for c in cmd if c not in ("-hwaccel", "videotoolbox")]
        cmd[cmd.index("h264_videotoolbox")] = "libx264"
        run(cmd)


def parse_tc(value) -> float:
    """Accept seconds (float) or "mm:ss.s" / "hh:mm:ss.s"."""
    if isinstance(value, (int, float)):
        return float(value)
    parts = [float(p) for p in re.split(r":", str(value))]
    t = 0.0
    for p in parts:
        t = t * 60 + p
    return t
