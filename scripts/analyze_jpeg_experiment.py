#!/usr/bin/env python3
"""Analyze two PC3 Pizza Creator native saved JPEGs.

This tool is deliberately evidence-oriented. It never promotes a research gate;
it emits measurements used by contracts/jpeg-reverse-engineering.acceptance.json.

Always available (stdlib only):
- SHA-256 / byte size / exact byte equality
- JPEG SOF dimensions/components/sampling factors
- DQT quantization tables
- DHT payload fingerprints
- APP/COM marker fingerprints
- progressive/baseline classification
- restart interval

When Pillow is installed:
- decoded dimensions/mode
- exact decoded-pixel equality
- MAE/MSE/RMSE/PSNR
- changed-pixel bounding box
- diff PNG

When scikit-image + numpy are installed:
- SSIM using Wang-compatible settings where image dimensions permit

When ImageMagick 7 (`magick`) is on PATH:
- external RMSE/PSNR/SSIM/PHASH attempts are recorded without making them
  required for the report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


SOF_NAMES = {
    0xC0: "SOF0_baseline_dct",
    0xC1: "SOF1_extended_sequential_dct",
    0xC2: "SOF2_progressive_dct",
    0xC3: "SOF3_lossless_sequential",
    0xC5: "SOF5_differential_sequential_dct",
    0xC6: "SOF6_differential_progressive_dct",
    0xC7: "SOF7_differential_lossless",
    0xC9: "SOF9_extended_sequential_arithmetic",
    0xCA: "SOF10_progressive_arithmetic",
    0xCB: "SOF11_lossless_arithmetic",
    0xCD: "SOF13_differential_sequential_arithmetic",
    0xCE: "SOF14_differential_progressive_arithmetic",
    0xCF: "SOF15_differential_lossless_arithmetic",
}

STANDALONE = {0x01, *range(0xD0, 0xD8), 0xD8, 0xD9}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_optional_json(path: Optional[Path]) -> Optional[Any]:
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_jpeg(path: Path) -> Dict[str, Any]:
    data = path.read_bytes()
    result: Dict[str, Any] = {
        "valid_soi": data[:2] == b"\xff\xd8",
        "valid_eoi": data[-2:] == b"\xff\xd9" if len(data) >= 2 else False,
        "frame": None,
        "quantization_tables": {},
        "huffman_tables": [],
        "restart_interval": None,
        "app_markers": [],
        "comments": [],
        "scan_count": 0,
        "marker_sequence": [],
    }
    if not result["valid_soi"]:
        return result

    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            # Entropy-coded bytes after SOS. Find the next non-stuffed marker.
            i += 1
            continue
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            break
        marker = data[i]
        i += 1
        if marker == 0x00:
            continue
        result["marker_sequence"].append(f"FF{marker:02X}")
        if marker == 0xD9:
            break
        if marker in STANDALONE:
            continue
        if i + 2 > len(data):
            break
        seg_len = int.from_bytes(data[i:i + 2], "big")
        if seg_len < 2 or i + seg_len > len(data):
            result.setdefault("parse_warnings", []).append(
                f"Invalid segment length {seg_len} at offset {i - 2}"
            )
            break
        payload = data[i + 2:i + seg_len]
        i += seg_len

        if marker in SOF_NAMES and len(payload) >= 6:
            precision = payload[0]
            height = int.from_bytes(payload[1:3], "big")
            width = int.from_bytes(payload[3:5], "big")
            count = payload[5]
            components: List[Dict[str, Any]] = []
            p = 6
            for _ in range(count):
                if p + 3 > len(payload):
                    break
                cid = payload[p]
                sampling = payload[p + 1]
                qtable = payload[p + 2]
                components.append({
                    "id": cid,
                    "h_sampling": sampling >> 4,
                    "v_sampling": sampling & 0x0F,
                    "quant_table": qtable,
                })
                p += 3
            result["frame"] = {
                "marker": f"FF{marker:02X}",
                "kind": SOF_NAMES[marker],
                "precision_bits": precision,
                "width": width,
                "height": height,
                "components": components,
            }

        elif marker == 0xDB:  # DQT
            p = 0
            while p < len(payload):
                spec = payload[p]
                p += 1
                precision = spec >> 4
                table_id = spec & 0x0F
                value_bytes = 128 if precision else 64
                if p + value_bytes > len(payload):
                    result.setdefault("parse_warnings", []).append("Truncated DQT")
                    break
                if precision:
                    values = [
                        int.from_bytes(payload[p + k:p + k + 2], "big")
                        for k in range(0, value_bytes, 2)
                    ]
                else:
                    values = list(payload[p:p + value_bytes])
                p += value_bytes
                result["quantization_tables"][str(table_id)] = {
                    "precision_bits": 16 if precision else 8,
                    "values_zigzag_order": values,
                    "sha256": sha256_bytes(bytes().join(
                        int(v).to_bytes(2 if precision else 1, "big") for v in values
                    )),
                }

        elif marker == 0xC4:  # DHT
            result["huffman_tables"].append({
                "length": len(payload),
                "sha256": sha256_bytes(payload),
            })

        elif marker == 0xDD and len(payload) >= 2:  # DRI
            result["restart_interval"] = int.from_bytes(payload[:2], "big")

        elif 0xE0 <= marker <= 0xEF:  # APPn
            result["app_markers"].append({
                "marker": f"APP{marker - 0xE0}",
                "length": len(payload),
                "sha256": sha256_bytes(payload),
                "prefix_ascii": payload[:32].decode("latin-1", errors="replace"),
            })

        elif marker == 0xFE:  # COM
            result["comments"].append({
                "length": len(payload),
                "sha256": sha256_bytes(payload),
                "text": payload.decode("latin-1", errors="replace"),
            })

        elif marker == 0xDA:  # SOS
            result["scan_count"] += 1
            # Skip entropy data until the next true marker. 0xFF00 is stuffed data;
            # RST markers are standalone and can occur inside entropy data.
            while i < len(data) - 1:
                if data[i] != 0xFF:
                    i += 1
                    continue
                j = i + 1
                while j < len(data) and data[j] == 0xFF:
                    j += 1
                if j >= len(data):
                    i = j
                    break
                code = data[j]
                if code == 0x00:
                    i = j + 1
                    continue
                if 0xD0 <= code <= 0xD7:
                    i = j + 1
                    continue
                # Let the outer loop consume this marker.
                i = i
                break
            # Outer loop expects i to point at 0xFF.

    frame = result.get("frame")
    if frame:
        result["is_progressive"] = frame["marker"] in {"FFC2", "FFC6", "FFCA", "FFCE"}
    else:
        result["is_progressive"] = None
    return result


def file_record(path: Path) -> Dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "jpeg": parse_jpeg(path),
    }


def pillow_metrics(a: Path, b: Path, out_dir: Path, threshold: int) -> Dict[str, Any]:
    try:
        from PIL import Image, ImageChops  # type: ignore
    except Exception as exc:
        return {"available": False, "reason": f"Pillow unavailable: {exc}"}

    try:
        ia = Image.open(a).convert("RGB")
        ib = Image.open(b).convert("RGB")
    except Exception as exc:
        return {"available": False, "reason": f"Pillow decode failed: {exc}"}

    result: Dict[str, Any] = {
        "available": True,
        "a_size": list(ia.size),
        "b_size": list(ib.size),
        "same_size": ia.size == ib.size,
    }
    if ia.size != ib.size:
        return result

    pa = list(ia.getdata())
    pb = list(ib.getdata())
    total_abs = 0
    total_sq = 0
    max_abs = 0
    changed = 0
    min_x = ia.width
    min_y = ia.height
    max_x = -1
    max_y = -1

    for index, (ca, cb) in enumerate(zip(pa, pb)):
        diffs = [abs(int(ca[k]) - int(cb[k])) for k in range(3)]
        total_abs += sum(diffs)
        total_sq += sum(d * d for d in diffs)
        local_max = max(diffs)
        max_abs = max(max_abs, local_max)
        if local_max > threshold:
            changed += 1
            x = index % ia.width
            y = index // ia.width
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

    samples = ia.width * ia.height * 3
    mae = total_abs / samples if samples else 0.0
    mse = total_sq / samples if samples else 0.0
    rmse = math.sqrt(mse)
    psnr = float("inf") if mse == 0 else 20.0 * math.log10(255.0 / rmse)

    result.update({
        "decoded_pixel_equal": mse == 0,
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "psnr_db": psnr,
        "max_channel_abs_error": max_abs,
        "changed_pixel_threshold": threshold,
        "changed_pixels": changed,
        "changed_fraction": changed / (ia.width * ia.height) if ia.width and ia.height else 0.0,
        "difference_bbox_xyxy": None if changed == 0 else [min_x, min_y, max_x, max_y],
    })

    diff = ImageChops.difference(ia, ib)
    diff_path = out_dir / "decoded-difference.png"
    diff.save(diff_path)
    result["difference_image"] = str(diff_path.resolve())

    try:
        import numpy as np  # type: ignore
        from skimage.metrics import structural_similarity  # type: ignore
        aa = np.asarray(ia)
        bb = np.asarray(ib)
        min_dim = min(ia.size)
        if min_dim >= 11:
            ssim = structural_similarity(
                aa,
                bb,
                data_range=255,
                channel_axis=2,
                gaussian_weights=True,
                sigma=1.5,
                use_sample_covariance=False,
            )
            result["ssim_wang_compatible"] = float(ssim)
        else:
            result["ssim_wang_compatible"] = None
            result["ssim_note"] = "Image too small for standard 11x11 Wang-style window"
    except Exception as exc:
        result["ssim_wang_compatible"] = None
        result["ssim_note"] = f"numpy/scikit-image unavailable or failed: {exc}"

    return result


def run_magick_metric(metric: str, a: Path, b: Path) -> Dict[str, Any]:
    magick = shutil.which("magick")
    if not magick:
        return {"available": False, "reason": "magick not on PATH"}
    command = [magick, "compare", "-metric", metric, str(a), str(b), "null:"]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=60)
        # ImageMagick compare normally returns 1 when images differ, so do not treat
        # return code 1 as execution failure.
        output = (proc.stderr or proc.stdout).strip()
        return {
            "available": proc.returncode in (0, 1),
            "returncode": proc.returncode,
            "raw": output,
            "command": command,
        }
    except Exception as exc:
        return {"available": False, "reason": str(exc), "command": command}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_a", type=Path, help="Baseline/native JPEG A")
    parser.add_argument("image_b", type=Path, help="Variant/native JPEG B")
    parser.add_argument("--model-a", type=Path, default=None, help="Optional model/signature JSON for A")
    parser.add_argument("--model-b", type=Path, default=None, help="Optional model/signature JSON for B")
    parser.add_argument("--label-a", default="A")
    parser.add_argument("--label-b", default="B")
    parser.add_argument("--experiment-id", default="manual-pair")
    parser.add_argument("--threshold", type=int, default=0, help="Per-channel absolute diff threshold for changed-pixel bbox")
    parser.add_argument("--out", type=Path, default=Path("jpeg-analysis"), help="Output directory")
    args = parser.parse_args()

    for path in (args.image_a, args.image_b):
        if not path.is_file():
            parser.error(f"JPEG not found: {path}")

    args.out.mkdir(parents=True, exist_ok=True)

    record_a = file_record(args.image_a)
    record_b = file_record(args.image_b)
    report: Dict[str, Any] = {
        "schema_version": "1.0",
        "kind": "pc3-creator-native-jpeg-pair-analysis",
        "experiment_id": args.experiment_id,
        "truth_note": "Measurements only. This report does not promote a JPEG reverse-engineering gate.",
        "a": {"label": args.label_a, **record_a},
        "b": {"label": args.label_b, **record_b},
        "exact_file_equal": record_a["sha256"] == record_b["sha256"],
        "model_a": load_optional_json(args.model_a),
        "model_b": load_optional_json(args.model_b),
        "decoded_metrics": pillow_metrics(args.image_a, args.image_b, args.out, args.threshold),
        "imagemagick": {
            metric: run_magick_metric(metric, args.image_a, args.image_b)
            for metric in ("RMSE", "PSNR", "SSIM", "PHASH")
        },
    }

    ja = record_a["jpeg"]
    jb = record_b["jpeg"]
    report["jpeg_structure_equal"] = {
        "frame": ja.get("frame") == jb.get("frame"),
        "quantization_tables": ja.get("quantization_tables") == jb.get("quantization_tables"),
        "huffman_tables": ja.get("huffman_tables") == jb.get("huffman_tables"),
        "restart_interval": ja.get("restart_interval") == jb.get("restart_interval"),
        "app_markers": ja.get("app_markers") == jb.get("app_markers"),
        "scan_count": ja.get("scan_count") == jb.get("scan_count"),
    }

    report_path = args.out / "analysis.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    summary = {
        "experiment_id": args.experiment_id,
        "exact_file_equal": report["exact_file_equal"],
        "jpeg_structure_equal": report["jpeg_structure_equal"],
        "decoded_metrics": report["decoded_metrics"],
        "report": str(report_path.resolve()),
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
