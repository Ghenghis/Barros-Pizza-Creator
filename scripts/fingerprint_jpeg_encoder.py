#!/usr/bin/env python3
"""Fingerprint a PC3 Creator native JPEG's encoder structure.

Uses the repository's raw JPEG parser and adds:
- combined DQT/DHT/APP structural fingerprints
- exact matching against the standard IJG/libjpeg quality-table family (1..100)

An IJG quality match is evidence that the quantization tables match that standard
family; it is NOT proof that Unity/libjpeg-turbo/IJG was the actual encoder. Bind this
result to static/runtime call tracing before identifying the implementation.

Research basis:
- Jesse D. Kornblum (2008), JPEG quantization tables for software-source identification
- Remi Cogranne (2018), exact standard quality-factor determination from quantization tables
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence


LUMA_NATURAL = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
]

CHROMA_NATURAL = [
    17, 18, 24, 47, 99, 99, 99, 99,
    18, 21, 26, 66, 99, 99, 99, 99,
    24, 26, 56, 99, 99, 99, 99, 99,
    47, 66, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
]

# JPEG marker order for the 64 DCT coefficients, expressed as natural-order indexes.
ZIGZAG_NATURAL_INDEX = [
    0, 1, 8, 16, 9, 2, 3, 10,
    17, 24, 32, 25, 18, 11, 4, 5,
    12, 19, 26, 33, 40, 48, 41, 34,
    27, 20, 13, 6, 7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36,
    29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46,
    53, 60, 61, 54, 47, 55, 62, 63,
]


def load_jpeg_analyzer():
    path = Path(__file__).resolve().with_name("analyze_jpeg_experiment.py")
    spec = importlib.util.spec_from_file_location("pc3_jpeg_analyzer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not import JPEG parser: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scale_ijg_table(base: Sequence[int], quality: int) -> List[int]:
    if not 1 <= quality <= 100:
        raise ValueError("quality must be 1..100")
    scale = (5000 // quality) if quality < 50 else (200 - quality * 2)
    natural = []
    for value in base:
        q = (value * scale + 50) // 100
        q = max(1, min(255, q))
        natural.append(q)
    return [natural[index] for index in ZIGZAG_NATURAL_INDEX]


def exact_quality_matches(values: Sequence[int], base: Sequence[int]) -> List[int]:
    if len(values) != 64:
        return []
    return [quality for quality in range(1, 101) if list(values) == scale_ijg_table(base, quality)]


def hash_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fingerprint(parsed: Dict[str, Any]) -> Dict[str, Any]:
    tables = parsed.get("quantization_tables", {})
    luma = tables.get("0")
    chroma = tables.get("1")
    luma_matches = exact_quality_matches(luma.get("values_zigzag_order", []), LUMA_NATURAL) if luma else []
    chroma_matches = exact_quality_matches(chroma.get("values_zigzag_order", []), CHROMA_NATURAL) if chroma else []
    joint = sorted(set(luma_matches).intersection(chroma_matches)) if luma and chroma else []

    encoder_structure = {
        "frame": parsed.get("frame"),
        "quantization_tables": {
            key: {
                "precision_bits": value.get("precision_bits"),
                "sha256": value.get("sha256"),
            }
            for key, value in sorted(tables.items())
        },
        "huffman_tables": parsed.get("huffman_tables"),
        "restart_interval": parsed.get("restart_interval"),
        "app_markers": parsed.get("app_markers"),
        "comments": parsed.get("comments"),
        "scan_count": parsed.get("scan_count"),
        "is_progressive": parsed.get("is_progressive"),
    }
    return {
        "encoder_structure": encoder_structure,
        "encoder_structure_sha256": hash_json(encoder_structure),
        "dqt_only_sha256": hash_json(encoder_structure["quantization_tables"]),
        "dht_only_sha256": hash_json(encoder_structure["huffman_tables"]),
        "ijg_standard_quality_match": {
            "luma_table_0_candidates": luma_matches,
            "chroma_table_1_candidates": chroma_matches,
            "joint_exact_candidates": joint,
            "exact_joint_match": len(joint) > 0,
            "interpretation": (
                "Quantization tables exactly match the standard IJG quality family at the listed quality factor(s). "
                "This fingerprints table construction only; it does not identify the encoder implementation by itself."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jpeg", type=Path)
    parser.add_argument("--out", type=Path, default=Path("jpeg-encoder-fingerprint.json"))
    args = parser.parse_args()
    if not args.jpeg.is_file():
        parser.error(f"JPEG not found: {args.jpeg}")

    analyzer = load_jpeg_analyzer()
    parsed = analyzer.parse_jpeg(args.jpeg)
    result = {
        "schema_version": "1.0",
        "kind": "pc3-creator-native-jpeg-encoder-fingerprint",
        "jpeg": str(args.jpeg.resolve()),
        "jpeg_sha256": analyzer.sha256_file(args.jpeg),
        "parsed": parsed,
        **fingerprint(parsed),
        "truth_note": "Forensic fingerprint only. Static/runtime call tracing is required before naming the actual JPEG encoder implementation.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "out": str(args.out.resolve()),
        "encoder_structure_sha256": result["encoder_structure_sha256"],
        "ijg_standard_quality_match": result["ijg_standard_quality_match"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
