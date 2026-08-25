#!/usr/bin/env python3
"""Fit PC3 Pizza Creator world X/Z -> native JPEG pixel u/v mappings.

Input CSV columns:
    label,x,z,u,v

Fits:
- 2D affine mapping (6 parameters)
- planar projective homography (8 free parameters, H[2,2]=1)

The report includes fit residuals and leave-one-out residuals where possible.
Classification is deliberately heuristic; use it to guide reverse engineering, not as
proof that the game uses a specific camera projection.

Requires numpy. The JPEG research tooling setup creates an isolated environment that
includes numpy/scikit-image/Pillow.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

try:
    import numpy as np
except Exception as exc:  # pragma: no cover - runtime dependency boundary
    raise SystemExit(
        "numpy is required. Run DOWNLOAD_JPEG_RESEARCH_TOOLS.bat or install numpy "
        f"in the research analysis environment. Details: {exc}"
    )


def read_points(path: Path) -> List[Dict[str, Any]]:
    points: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"x", "z", "u", "v"}
        fields = set(reader.fieldnames or [])
        missing = required - fields
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
        for index, row in enumerate(reader):
            points.append(
                {
                    "label": row.get("label") or f"p{index}",
                    "x": float(row["x"]),
                    "z": float(row["z"]),
                    "u": float(row["u"]),
                    "v": float(row["v"]),
                }
            )
    return points


def affine_fit(points: Sequence[Dict[str, Any]]) -> np.ndarray:
    if len(points) < 3:
        raise ValueError("Affine mapping requires at least 3 points")
    rows = []
    values = []
    for p in points:
        x, z, u, v = p["x"], p["z"], p["u"], p["v"]
        rows.append([x, z, 1.0, 0.0, 0.0, 0.0])
        values.append(u)
        rows.append([0.0, 0.0, 0.0, x, z, 1.0])
        values.append(v)
    matrix = np.asarray(rows, dtype=float)
    target = np.asarray(values, dtype=float)
    params, _, rank, _ = np.linalg.lstsq(matrix, target, rcond=None)
    if rank < 6:
        raise ValueError("Affine calibration points are degenerate/collinear")
    return params.reshape(2, 3)


def affine_predict(model: np.ndarray, x: float, z: float) -> Tuple[float, float]:
    out = model @ np.asarray([x, z, 1.0], dtype=float)
    return float(out[0]), float(out[1])


def normalize_xy(values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    center = values.mean(axis=0)
    centered = values - center
    distances = np.sqrt((centered * centered).sum(axis=1))
    mean_distance = float(distances.mean())
    scale = 1.0 if mean_distance <= 1e-12 else math.sqrt(2.0) / mean_distance
    transform = np.asarray(
        [[scale, 0.0, -scale * center[0]], [0.0, scale, -scale * center[1]], [0.0, 0.0, 1.0]],
        dtype=float,
    )
    homogeneous = np.column_stack([values, np.ones(len(values))])
    normalized = (transform @ homogeneous.T).T
    return normalized[:, :2] / normalized[:, 2:3], transform


def homography_fit(points: Sequence[Dict[str, Any]]) -> np.ndarray:
    if len(points) < 4:
        raise ValueError("Homography requires at least 4 points")

    src = np.asarray([[p["x"], p["z"]] for p in points], dtype=float)
    dst = np.asarray([[p["u"], p["v"]] for p in points], dtype=float)
    src_n, ts = normalize_xy(src)
    dst_n, td = normalize_xy(dst)

    rows = []
    for (x, z), (u, v) in zip(src_n, dst_n):
        rows.append([-x, -z, -1.0, 0.0, 0.0, 0.0, u * x, u * z, u])
        rows.append([0.0, 0.0, 0.0, -x, -z, -1.0, v * x, v * z, v])
    a = np.asarray(rows, dtype=float)
    _, _, vt = np.linalg.svd(a)
    h = vt[-1].reshape(3, 3)
    h = np.linalg.inv(td) @ h @ ts
    if abs(h[2, 2]) > 1e-12:
        h = h / h[2, 2]
    else:
        norm = np.linalg.norm(h)
        if norm <= 1e-12:
            raise ValueError("Degenerate homography")
        h = h / norm
    return h


def homography_predict(model: np.ndarray, x: float, z: float) -> Tuple[float, float]:
    out = model @ np.asarray([x, z, 1.0], dtype=float)
    if abs(out[2]) <= 1e-12:
        raise ValueError("Homography predicts a point at infinity")
    return float(out[0] / out[2]), float(out[1] / out[2])


def residual_report(points: Sequence[Dict[str, Any]], predictor) -> Dict[str, Any]:
    records = []
    sq = []
    for p in points:
        pu, pv = predictor(p["x"], p["z"])
        du = pu - p["u"]
        dv = pv - p["v"]
        distance = math.hypot(du, dv)
        sq.append(distance * distance)
        records.append(
            {
                "label": p["label"],
                "observed": [p["u"], p["v"]],
                "predicted": [pu, pv],
                "du": du,
                "dv": dv,
                "distance_px": distance,
            }
        )
    rms = math.sqrt(sum(sq) / len(sq)) if sq else None
    return {
        "rms_px": rms,
        "max_px": max((math.sqrt(x) for x in sq), default=None),
        "points": records,
    }


def leave_one_out(points: Sequence[Dict[str, Any]], kind: str) -> Dict[str, Any]:
    minimum_fit = 3 if kind == "affine" else 4
    if len(points) <= minimum_fit:
        return {"available": False, "reason": "not enough points for leave-one-out validation"}
    records = []
    squares = []
    failures = []
    for index, held in enumerate(points):
        train = [p for i, p in enumerate(points) if i != index]
        try:
            if kind == "affine":
                model = affine_fit(train)
                pu, pv = affine_predict(model, held["x"], held["z"])
            else:
                model = homography_fit(train)
                pu, pv = homography_predict(model, held["x"], held["z"])
            distance = math.hypot(pu - held["u"], pv - held["v"])
            squares.append(distance * distance)
            records.append({"label": held["label"], "predicted": [pu, pv], "observed": [held["u"], held["v"]], "distance_px": distance})
        except Exception as exc:
            failures.append({"label": held["label"], "error": str(exc)})
    if not squares:
        return {"available": False, "reason": "all leave-one-out fits failed", "failures": failures}
    return {
        "available": True,
        "rms_px": math.sqrt(sum(squares) / len(squares)),
        "max_px": max(math.sqrt(x) for x in squares),
        "points": records,
        "failures": failures,
    }


def heuristic_classification(affine_loo: Dict[str, Any], homography_loo: Dict[str, Any]) -> Dict[str, Any]:
    if not affine_loo.get("available") or not homography_loo.get("available"):
        return {
            "classification": "insufficient_validation_data",
            "truth_note": "Projection class remains unknown until held-out validation is available."
        }
    a = float(affine_loo["rms_px"])
    h = float(homography_loo["rms_px"])
    if a <= 0.25 and h <= max(0.25, a * 1.10):
        label = "affine_is_sufficient_at_current_measurement_precision"
    elif h + 0.25 < a and h <= a * 0.60:
        label = "projective_model_materially_better"
    elif h < a:
        label = "projective_model_somewhat_better_inconclusive"
    else:
        label = "affine_equal_or_better_inconclusive"
    return {
        "classification": label,
        "affine_loo_rms_px": a,
        "homography_loo_rms_px": h,
        "homography_over_affine_ratio": None if a == 0 else h / a,
        "truth_note": "Heuristic guidance only. Confirm camera type with source/runtime/RenderDoc evidence."
    }


def matrix_to_list(model: np.ndarray) -> List[List[float]]:
    return [[float(value) for value in row] for row in model]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("points_csv", type=Path)
    parser.add_argument("--out", type=Path, default=Path("camera-mapping.json"))
    args = parser.parse_args()

    points = read_points(args.points_csv)
    if len(points) < 4:
        parser.error("Provide at least 4 non-degenerate calibration points")

    affine = affine_fit(points)
    homography = homography_fit(points)

    affine_residual = residual_report(points, lambda x, z: affine_predict(affine, x, z))
    homography_residual = residual_report(points, lambda x, z: homography_predict(homography, x, z))
    affine_loo = leave_one_out(points, "affine")
    homography_loo = leave_one_out(points, "homography")

    report = {
        "schema_version": "1.0",
        "kind": "pc3-creator-world-to-native-jpeg-camera-fit",
        "source_csv": str(args.points_csv.resolve()),
        "point_count": len(points),
        "points": points,
        "affine": {
            "matrix_2x3": matrix_to_list(affine),
            "fit_residual": affine_residual,
            "leave_one_out": affine_loo,
        },
        "homography": {
            "matrix_3x3": matrix_to_list(homography),
            "fit_residual": homography_residual,
            "leave_one_out": homography_loo,
        },
        "projection_guidance": heuristic_classification(affine_loo, homography_loo),
        "truth_note": "Mathematical fit only. It does not prove which Unity Camera/API generated the JPEG; bind the result to static/runtime render-path evidence."
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "out": str(args.out.resolve()),
        "affine_fit_rms_px": affine_residual["rms_px"],
        "homography_fit_rms_px": homography_residual["rms_px"],
        "guidance": report["projection_guidance"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
