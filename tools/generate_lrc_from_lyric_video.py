#!/usr/bin/env python3
"""Create a review-required LRC draft from a SUNO-style lyric video.

The source video already contains the owner's synchronized lyric presentation.
This tool samples the highlighted caption, performs local OCR, and writes a
same-name (or explicitly selected) .lrc file for the in-game Media Deck.
No audio, image, lyric text, or API key leaves the computer.

OCR is not authoritative for sung lyrics. The output is a local editing aid and
must be reviewed line by line before it is copied into a release music folder.
"""

from __future__ import annotations

import argparse
import re
import shutil
from difflib import SequenceMatcher
from pathlib import Path

import cv2
import pytesseract


STATIC_TEXT = (
    "MADE WITH SUNO",
    "LYRICS VIDEO",
)


def clean_line(value: str) -> str:
    value = value.replace("|", " ").replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip(" -—–·|_.,")
    if len(re.sub(r"[^A-Za-z0-9]", "", value)) < 2:
        return ""
    if any(marker in value.upper() for marker in STATIC_TEXT):
        return ""
    return value


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def active_caption(frame, debug: bool = False) -> str:
    height, width = frame.shape[:2]
    # SUNO lyric videos keep the bold active line in a narrow, fixed band;
    # the dim previous/next lines sit immediately outside it. Keeping this
    # crop tight is materially more accurate than OCR over the whole caption
    # stack, especially when the active lyric is only one or two words.
    crop_top = int(height * 0.56)
    crop = frame[crop_top : int(height * 0.70), 0:width]
    enlarged = cv2.resize(crop, None, fx=6, fy=6, interpolation=cv2.INTER_LANCZOS4)
    enlarged_gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(enlarged_gray, 230, 255, cv2.THRESH_BINARY)
    data = pytesseract.image_to_data(enlarged, config="--psm 11", output_type=pytesseract.Output.DICT)
    grouped: dict[tuple[int, int, int], list[int]] = {}
    for index, text in enumerate(data["text"]):
        if not text.strip():
            continue
        key = (data["block_num"][index], data["par_num"][index], data["line_num"][index])
        grouped.setdefault(key, []).append(index)
    lines: list[dict[str, object]] = []
    for indexes in grouped.values():
        text = clean_line(" ".join(data["text"][index] for index in indexes))
        if not text:
            continue
        left = min(data["left"][index] for index in indexes)
        top = min(data["top"][index] for index in indexes)
        right = max(data["left"][index] + data["width"][index] for index in indexes)
        bottom = max(data["top"][index] + data["height"][index] for index in indexes)
        ink = cv2.countNonZero(binary[top:bottom, left:right]) / max(1, (right - left) * (bottom - top))
        lines.append({"text": text, "center": (top + bottom) / 2.0, "ink": ink, "height": bottom - top})
    if not lines:
        return ""

    target = (height * 0.62 - crop_top) * 6.0
    if debug:
        print({"target": target, "lines": lines})
    central = [line for line in lines if abs(float(line["center"]) - target) <= 210.0] or lines
    primary = min(
        central,
        key=lambda line: (abs(float(line["center"]) - target), -float(line["height"]) * float(line["ink"])),
    )
    selected = [primary]
    # The bottom row is anchored at a fixed y-position. When it is a short or
    # lower-case continuation, the line immediately above belongs to the same
    # highlighted caption. Otherwise that upper row is dim prior context.
    primary_text = str(primary["text"])
    compact = re.sub(r"[^A-Za-z0-9]", "", primary_text)
    continuation = (primary_text[:1].islower() or len(compact) < 15) and not primary_text.startswith("[")
    if continuation:
        prior = [
            line
            for line in lines
            if float(line["center"]) < float(primary["center"])
            and float(primary["center"]) - float(line["center"]) <= 240.0
        ]
        if prior:
            selected.append(max(prior, key=lambda line: float(line["center"])))
    selected.sort(key=lambda line: float(line["center"]))
    return " ".join(str(line["text"]) for line in selected)


def lrc_stamp(seconds: float) -> str:
    hundredths = max(0, int(round(seconds * 100)))
    minutes, hundredths = divmod(hundredths, 6000)
    whole_seconds, fraction = divmod(hundredths, 100)
    return f"[{minutes:02d}:{whole_seconds:02d}.{fraction:02d}]"


def generate(video: Path, output: Path, step: float) -> tuple[int, float]:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"OpenCV could not open {video}")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
    duration = frame_count / fps if fps > 0 else 0.0
    if duration <= 0.0:
        raise RuntimeError("The video duration could not be measured.")

    cues: list[tuple[float, str]] = []
    previous = ""
    sample_time = 0.0
    while sample_time < duration:
        capture.set(cv2.CAP_PROP_POS_MSEC, sample_time * 1000.0)
        ok, frame = capture.read()
        if not ok:
            sample_time += step
            continue
        caption = active_caption(frame)
        if caption:
            current_key = normalized(caption)
            previous_key = normalized(previous)
            similarity = SequenceMatcher(None, previous_key, current_key).ratio() if previous_key else 0.0
            if not previous_key or similarity < 0.76:
                cues.append((sample_time, caption))
                previous = caption
        sample_time += step
    capture.release()

    # Remove one-sample OCR glitches sandwiched between the same stable line.
    filtered: list[tuple[float, str]] = []
    for index, cue in enumerate(cues):
        if 0 < index < len(cues) - 1:
            before = normalized(cues[index - 1][1])
            after = normalized(cues[index + 1][1])
            if SequenceMatcher(None, before, after).ratio() >= 0.88 and cues[index + 1][0] - cues[index][0] <= step * 1.5:
                continue
        filtered.append(cue)

    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "[by:Barro's Pizza Creator local lyric-video OCR]",
        "[re:DRAFT - HUMAN REVIEW REQUIRED]",
    ]
    lines.extend(f"{lrc_stamp(seconds)}{text}" for seconds, text in filtered)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(filtered), duration


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--step", type=float, default=1.0, help="Seconds between local OCR samples (default: 1.0)")
    parser.add_argument("--tesseract", default="")
    args = parser.parse_args()
    if not args.video.is_file():
        parser.error(f"video not found: {args.video}")
    if args.step < 0.25 or args.step > 5.0:
        parser.error("--step must be between 0.25 and 5 seconds")

    candidates = [
        args.tesseract,
        shutil.which("tesseract") or "",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    executable = next((value for value in candidates if value and Path(value).is_file()), "")
    if not executable:
        parser.error("Tesseract OCR was not found. Install it or pass --tesseract with the exact executable path.")
    pytesseract.pytesseract.tesseract_cmd = executable

    output = args.output or args.video.with_suffix(".lrc")
    count, duration = generate(args.video.resolve(), output.resolve(), args.step)
    print(f"Wrote {count} synchronized lyric cues for {duration:.1f}s to {output}")
    print("DRAFT ONLY: review every timestamp and lyric before release use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
