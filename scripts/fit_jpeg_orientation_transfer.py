#!/usr/bin/env python3
"""Measure PC3 Creator topping orientation in native saved JPEGs.

Input CSV columns:
    label,yaw_degrees,image

A common minimal-dough/background JPEG is supplied separately. For each sample this
script differences the sample from the baseline, builds a weighted changed-pixel mask,
uses PCA/covariance to estimate the dominant axial image orientation, then fits the
unwrapped image orientation against native Y yaw.

This works best with one visibly asymmetric/elongated ingredient at a fixed X/Z/size.
The result is research evidence, not proof of the game's camera/render implementation.

Requires Pillow + numpy (installed by DOWNLOAD_JPEG_RESEARCH_TOOLS.bat).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import numpy as np
    from PIL import Image
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Pillow and numpy are required. Run DOWNLOAD_JPEG_RESEARCH_TOOLS.bat first. "
        f"Details: {exc}"
    )


def read_samples(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"yaw_degrees", "image"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
        for index, row in enumerate(reader):
            image = Path(row["image"])
            if not image.is_absolute():
                image = (path.parent / image).resolve()
            rows.append({
                "label": row.get("label") or f"p{index}",
                "yaw_degrees": float(row["yaw_degrees"]),
                "image": image,
            })
    return rows


def load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"), dtype=np.float32)


def robust_threshold(diff_magnitude: np.ndarray, minimum: float) -> float:
    flat = diff_magnitude.reshape(-1)
    median = float(np.median(flat))
    mad = float(np.median(np.abs(flat - median)))
    # 1.4826 scales MAD toward standard deviation for Gaussian-like noise.
    threshold = median + 6.0 * 1.4826 * mad
    return max(float(minimum), threshold)


def orientation_from_difference(baseline: np.ndarray, sample: np.ndarray, min_threshold: float, roi: Tuple[int, int, int, int] | None) -> Dict[str, Any]:
    if baseline.shape != sample.shape:
        raise ValueError(f"baseline/sample shape mismatch: {baseline.shape} vs {sample.shape}")
    diff = np.max(np.abs(sample - baseline), axis=2)
    h, w = diff.shape

    roi_mask = np.ones((h, w), dtype=bool)
    if roi is not None:
        x0, y0, x1, y1 = roi
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w - 1, x1), min(h - 1, y1)
        roi_mask[:] = False
        roi_mask[y0:y1 + 1, x0:x1 + 1] = True

    threshold = robust_threshold(diff[roi_mask], min_threshold)
    mask = (diff > threshold) & roi_mask
    ys, xs = np.nonzero(mask)
    if len(xs) < 8:
        raise ValueError(f"too few changed pixels above threshold ({len(xs)}); use a lower --min-threshold or a better baseline/ROI")

    weights = diff[ys, xs].astype(np.float64)
    weight_sum = float(weights.sum())
    if weight_sum <= 0:
        weights = np.ones_like(weights)
        weight_sum = float(len(weights))

    cx = float((xs * weights).sum() / weight_sum)
    cy = float((ys * weights).sum() / weight_sum)

    # Convert image-y-down into Cartesian y-up before covariance.
    centered_x = xs.astype(np.float64) - cx
    centered_y = -(ys.astype(np.float64) - cy)
    coords = np.column_stack([centered_x, centered_y])
    covariance = (coords * weights[:, None]).T @ coords / weight_sum
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    principal = eigenvectors[:, order[0]]
    major = float(eigenvalues[order[0]])
    minor = float(eigenvalues[order[1]]) if len(order) > 1 else 0.0
    angle = math.degrees(math.atan2(float(principal[1]), float(principal[0]))) % 180.0

    return {
        "threshold": threshold,
        "changed_pixels": int(len(xs)),
        "changed_fraction": float(len(xs) / (h * w)),
        "centroid_uv": [cx, cy],
        "bbox_xyxy": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
        "orientation_axial_degrees": angle,
        "eigenvalues": [major, minor],
        "elongation_ratio": None if minor <= 1e-12 else major / minor,
    }


def unwrap_axial(angles_degrees: np.ndarray) -> np.ndarray:
    # Axial orientations repeat every 180 degrees. Doubling converts them to circular
    # angles, standard unwrap works at 360, then divide by two.
    radians = np.deg2rad(angles_degrees * 2.0)
    return np.rad2deg(np.unwrap(radians)) / 2.0


def fit_transfer(yaws: np.ndarray, image_angles: np.ndarray) -> Dict[str, Any]:
    order = np.argsort(yaws)
    x = yaws[order]
    y_raw = image_angles[order]
    y = unwrap_axial(y_raw)
    matrix = np.column_stack([x, np.ones(len(x))])
    params, _, _, _ = np.linalg.lstsq(matrix, y, rcond=None)
    slope, intercept = float(params[0]), float(params[1])
    predicted = matrix @ params
    residual = y - predicted
    rms = float(math.sqrt(float(np.mean(residual * residual))))
    return {
        "slope_image_degrees_per_native_yaw_degree": slope,
        "intercept_degrees": intercept,
        "rms_degrees": rms,
        "ordered_native_yaw": [float(v) for v in x],
        "ordered_measured_axial_degrees": [float(v) for v in y_raw],
        "ordered_unwrapped_image_degrees": [float(v) for v in y],
        "predicted_unwrapped_degrees": [float(v) for v in predicted],
        "residual_degrees": [float(v) for v in residual],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="Minimal dough/background JPEG with no tested piece")
    parser.add_argument("samples_csv", type=Path, help="CSV: label,yaw_degrees,image")
    parser.add_argument("--out", type=Path, default=Path("orientation-transfer.json"))
    parser.add_argument("--min-threshold", type=float, default=8.0, help="Minimum RGB max-channel difference threshold")
    parser.add_argument("--roi", default="", help="Optional x0,y0,x1,y1 pixel ROI")
    args = parser.parse_args()

    roi = None
    if args.roi:
        parts = [int(value.strip()) for value in args.roi.split(",")]
        if len(parts) != 4:
            parser.error("--roi must be x0,y0,x1,y1")
        roi = tuple(parts)

    baseline = load_rgb(args.baseline)
    samples = read_samples(args.samples_csv)
    if len(samples) < 3:
        parser.error("Provide at least 3 yaw samples; 6+ spanning the full range is recommended")

    records = []
    for sample in samples:
        image = load_rgb(sample["image"])
        measured = orientation_from_difference(baseline, image, args.min_threshold, roi)
        records.append({
            "label": sample["label"],
            "yaw_degrees": sample["yaw_degrees"],
            "image": str(sample["image"]),
            **measured,
        })

    yaws = np.asarray([item["yaw_degrees"] for item in records], dtype=float)
    angles = np.asarray([item["orientation_axial_degrees"] for item in records], dtype=float)
    fit = fit_transfer(yaws, angles)

    report = {
        "schema_version": "1.0",
        "kind": "pc3-creator-native-yaw-to-jpeg-orientation-transfer",
        "baseline": str(args.baseline.resolve()),
        "samples_csv": str(args.samples_csv.resolve()),
        "roi": roi,
        "samples": records,
        "linear_axial_transfer_fit": fit,
        "interpretation": {
            "near_plus_one_slope": "image orientation follows native yaw in the same rotational sense at this location",
            "near_minus_one_slope": "image orientation follows native yaw with mirrored rotational sense at this location",
            "large_residuals": "segmentation, topping symmetry, perspective, animation, or non-rigid/native transform behavior needs investigation",
        },
        "truth_note": "Image measurement only. Confirm the actual transform/camera/render path from source/runtime evidence. Axial orientation is modulo 180 degrees and is unsuitable for rotationally symmetric toppings."
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"out": str(args.out.resolve()), "fit": fit}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
