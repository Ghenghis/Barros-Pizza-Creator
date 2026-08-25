#!/usr/bin/env python3
"""Statically trace PC3 Pizza Creator save/render/JPEG candidates in decompiled C#.

Run this against the exact decompiled Creator 0.11.272 source tree. It performs a
ranked, reproducible whole-corpus search for native save, camera/render, readback,
JPEG encoding, file-writing, path, thumbnail and event clues.

Outputs:
- candidate-methods.csv
- hits.csv
- trace.json

This is a discovery accelerator, not a decompiler replacement. Ranked candidates must
be confirmed in ILSpy/dnSpyEx and, for runtime behavior, by live tracing.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


PATTERNS: List[Tuple[str, int, re.Pattern[str]]] = [
    ("save_native", 10, re.compile(r"\bSaveCurrentPizzaToRecipes\b", re.I)),
    ("jpeg_encoder", 10, re.compile(r"\b(?:EncodeToJPG|EncodeToJPEG)\b", re.I)),
    ("jpeg_extension", 9, re.compile(r"\.(?:jpe?g)\b|\bJPEG\b|\bJPG\b", re.I)),
    ("pixel_readback", 9, re.compile(r"\bReadPixels\b", re.I)),
    ("camera_render", 9, re.compile(r"\bCamera\s*\.\s*Render\b|\.Render\s*\(\s*\)", re.I)),
    ("render_texture", 8, re.compile(r"\bRenderTexture\b|\btargetTexture\b|\bactive\s*=\s*", re.I)),
    ("graphics_blit", 8, re.compile(r"\bGraphics\s*\.\s*Blit\b", re.I)),
    ("file_write", 8, re.compile(r"\b(?:File\s*\.\s*WriteAllBytes|FileStream|BinaryWriter)\b", re.I)),
    ("texture2d", 6, re.compile(r"\bTexture2D\b", re.I)),
    ("png_encoder", 5, re.compile(r"\bEncodeToPNG\b", re.I)),
    ("screen_capture", 5, re.compile(r"\bScreenCapture\b|\bCaptureScreenshot\b", re.I)),
    ("thumbnail_preview", 5, re.compile(r"\b(?:Thumbnail|PreviewImage|PizzaImage|RecipeImage|Snapshot|Portrait|Picture|Photo)\b", re.I)),
    ("recipe_save_general", 4, re.compile(r"\bSave\w*(?:Pizza|Recipe)\w*\b|\b(?:Pizza|Recipe)\w*Save\w*\b", re.I)),
    ("path_storage", 4, re.compile(r"\bApplication\s*\.\s*(?:persistentDataPath|dataPath|streamingAssetsPath)\b", re.I)),
    ("io_path", 3, re.compile(r"\bPath\s*\.\s*(?:Combine|GetDirectoryName|GetFileName)\b", re.I)),
    ("event_publish", 3, re.compile(r"\b(?:Publish|Subscribe|OnPizza|PizzaLoaded|PizzaSaved|RecipeSaved)\b", re.I)),
    ("sprite_image", 2, re.compile(r"\bSprite\s*\.\s*Create\b|\bRawImage\b|\bUnityEngine\.UI\.Image\b", re.I)),
]

METHOD_RE = re.compile(
    r"^\s*(?:\[[^\]]+\]\s*)*(?:(?:public|private|protected|internal|static|virtual|override|sealed|async|extern|new|unsafe|partial)\s+)*"
    r"(?:[A-Za-z_][\w<>,\.\[\]\?]*(?:\s*<[^;{}]+>)?)\s+([A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?:where\s+[^{}]+)?\s*\{?\s*$"
)
CLASS_RE = re.compile(r"\b(?:class|struct|interface)\s+([A-Za-z_]\w*)")
NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z_][\w\.]*)")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def discover_cs(root: Path) -> List[Path]:
    return sorted(path for path in root.rglob("*.cs") if path.is_file())


def line_context(lines: Sequence[str], index: int, radius: int = 2) -> str:
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return "\n".join(f"{i + 1}: {lines[i].rstrip()}" for i in range(start, end))


def declarations(lines: Sequence[str]) -> Tuple[List[Optional[str]], List[Optional[str]], List[Optional[str]]]:
    namespaces: List[Optional[str]] = []
    classes: List[Optional[str]] = []
    methods: List[Optional[str]] = []
    current_namespace: Optional[str] = None
    current_class: Optional[str] = None
    current_method: Optional[str] = None
    last_method_line = -10000

    for index, line in enumerate(lines):
        namespace_match = NAMESPACE_RE.search(line)
        if namespace_match:
            current_namespace = namespace_match.group(1)
        class_match = CLASS_RE.search(line)
        if class_match:
            current_class = class_match.group(1)
        method_match = METHOD_RE.match(line)
        if method_match:
            name = method_match.group(1)
            if name not in {"if", "for", "while", "switch", "catch", "using", "lock"}:
                current_method = name
                last_method_line = index
        # Decompiled methods are generally compact enough that a 300-line carry is
        # useful. We do not claim lexical scoping from this approximation.
        if index - last_method_line > 300:
            current_method = None
        namespaces.append(current_namespace)
        classes.append(current_class)
        methods.append(current_method)
    return namespaces, classes, methods


def scan_file(root: Path, path: Path) -> Tuple[List[Dict[str, Any]], Dict[Tuple[str, str, str], Dict[str, Any]]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return [{
            "category": "read_error", "weight": 0, "file": str(path.relative_to(root)),
            "line": 0, "namespace": "", "class": "", "method": "", "match": str(exc), "context": ""
        }], {}
    lines = text.splitlines()
    namespaces, classes, methods = declarations(lines)
    hits: List[Dict[str, Any]] = []
    methods_map: Dict[Tuple[str, str, str], Dict[str, Any]] = {}

    for index, line in enumerate(lines):
        for category, weight, pattern in PATTERNS:
            for match in pattern.finditer(line):
                namespace = namespaces[index] or ""
                class_name = classes[index] or ""
                method = methods[index] or "<unknown>"
                rel = str(path.relative_to(root))
                record = {
                    "category": category,
                    "weight": weight,
                    "file": rel,
                    "line": index + 1,
                    "namespace": namespace,
                    "class": class_name,
                    "method": method,
                    "match": match.group(0),
                    "context": line_context(lines, index),
                }
                hits.append(record)
                key = (rel, class_name, method)
                candidate = methods_map.setdefault(key, {
                    "file": rel,
                    "namespace": namespace,
                    "class": class_name,
                    "method": method,
                    "categories": defaultdict(int),
                    "weight_sum": 0,
                    "hit_count": 0,
                    "first_line": index + 1,
                })
                candidate["categories"][category] += 1
                candidate["weight_sum"] += weight
                candidate["hit_count"] += 1
                candidate["first_line"] = min(candidate["first_line"], index + 1)
    return hits, methods_map


def candidate_score(candidate: Dict[str, Any]) -> float:
    categories = candidate["categories"]
    unique_bonus = 4.0 * len(categories)
    bridge_bonus = 0.0
    # Co-occurrence across stages is much more useful than many repeats of one word.
    groups = [
        {"save_native", "recipe_save_general"},
        {"camera_render", "render_texture", "graphics_blit", "pixel_readback", "texture2d"},
        {"jpeg_encoder", "jpeg_extension", "png_encoder"},
        {"file_write", "path_storage", "io_path"},
    ]
    covered = sum(1 for group in groups if set(categories).intersection(group))
    if covered >= 2:
        bridge_bonus = 12.0 * (covered - 1)
    return float(candidate["weight_sum"] + unique_bonus + bridge_bonus)


def merge_candidates(all_maps: Iterable[Dict[Tuple[str, str, str], Dict[str, Any]]]) -> List[Dict[str, Any]]:
    merged: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for mapping in all_maps:
        for key, candidate in mapping.items():
            target = merged.setdefault(key, {
                "file": candidate["file"],
                "namespace": candidate["namespace"],
                "class": candidate["class"],
                "method": candidate["method"],
                "categories": defaultdict(int),
                "weight_sum": 0,
                "hit_count": 0,
                "first_line": candidate["first_line"],
            })
            for category, count in candidate["categories"].items():
                target["categories"][category] += count
            target["weight_sum"] += candidate["weight_sum"]
            target["hit_count"] += candidate["hit_count"]
            target["first_line"] = min(target["first_line"], candidate["first_line"])

    output = []
    for candidate in merged.values():
        item = dict(candidate)
        item["categories"] = dict(sorted(candidate["categories"].items()))
        item["score"] = candidate_score(candidate)
        output.append(item)
    output.sort(key=lambda item: (-item["score"], item["file"], item["first_line"]))
    return output


def probable_call_references(root: Path, files: Sequence[Path], candidates: Sequence[Dict[str, Any]], max_methods: int = 80) -> List[Dict[str, Any]]:
    method_names = []
    for item in candidates:
        name = item["method"]
        if name and name != "<unknown>" and name not in method_names:
            method_names.append(name)
        if len(method_names) >= max_methods:
            break
    if not method_names:
        return []
    patterns = {name: re.compile(rf"\b{re.escape(name)}\s*\(") for name in method_names}
    refs: List[Dict[str, Any]] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        namespaces, classes, methods = declarations(lines)
        for index, line in enumerate(lines):
            for name, pattern in patterns.items():
                if pattern.search(line):
                    current = methods[index] or "<unknown>"
                    # Exclude the probable declaration line itself.
                    declaration = METHOD_RE.match(line)
                    if declaration and declaration.group(1) == name:
                        continue
                    refs.append({
                        "callee_name": name,
                        "caller_file": str(path.relative_to(root)),
                        "caller_class": classes[index] or "",
                        "caller_method": current,
                        "line": index + 1,
                        "text": line.strip(),
                    })
    return refs


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fields: Sequence[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            normalized = dict(row)
            if isinstance(normalized.get("categories"), dict):
                normalized["categories"] = json.dumps(normalized["categories"], sort_keys=True)
            writer.writerow(normalized)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path, help="Exact decompiled Creator C# root")
    parser.add_argument("--out", type=Path, default=Path("research/jpeg-pipeline/static-trace"))
    parser.add_argument("--top", type=int, default=120, help="Number of ranked methods to retain in candidate CSV")
    args = parser.parse_args()

    root = args.source_root.resolve()
    if not root.is_dir():
        parser.error(f"source root not found: {root}")
    files = discover_cs(root)
    if not files:
        parser.error(f"no .cs files found under: {root}")

    all_hits: List[Dict[str, Any]] = []
    maps = []
    for path in files:
        hits, mapping = scan_file(root, path)
        all_hits.extend(hits)
        maps.append(mapping)
    candidates = merge_candidates(maps)
    call_refs = probable_call_references(root, files, candidates)

    args.out.mkdir(parents=True, exist_ok=True)
    hits_csv = args.out / "hits.csv"
    candidates_csv = args.out / "candidate-methods.csv"
    calls_csv = args.out / "probable-call-references.csv"

    write_csv(hits_csv, all_hits, ["category", "weight", "file", "line", "namespace", "class", "method", "match", "context"])
    write_csv(candidates_csv, candidates[:args.top], ["score", "file", "first_line", "namespace", "class", "method", "hit_count", "weight_sum", "categories"])
    write_csv(calls_csv, call_refs, ["callee_name", "caller_file", "caller_class", "caller_method", "line", "text"])

    corpus_hash = hashlib.sha256()
    for path in files:
        rel = str(path.relative_to(root)).replace("\\", "/")
        corpus_hash.update(rel.encode("utf-8"))
        corpus_hash.update(b"\0")
        corpus_hash.update(file_sha256(path).encode("ascii"))
        corpus_hash.update(b"\n")

    category_counts: Dict[str, int] = defaultdict(int)
    for hit in all_hits:
        category_counts[hit["category"]] += 1

    report = {
        "schema_version": "1.0",
        "kind": "pc3-creator-native-jpeg-static-source-trace",
        "source_root": str(root),
        "cs_file_count": len(files),
        "corpus_identity_sha256": corpus_hash.hexdigest(),
        "hit_count": len(all_hits),
        "category_counts": dict(sorted(category_counts.items())),
        "top_candidates": candidates[:min(40, len(candidates))],
        "probable_call_reference_count": len(call_refs),
        "artifacts": {
            "hits_csv": str(hits_csv.resolve()),
            "candidate_methods_csv": str(candidates_csv.resolve()),
            "probable_call_references_csv": str(calls_csv.resolve()),
        },
        "next_actions": [
            "Open the highest-ranked candidates in ILSpy and verify actual lexical method/class boundaries.",
            "Trace SaveCurrentPizzaToRecipes outward to event subscribers/callers and inward to image/file-write operations.",
            "Set dnSpyEx tracepoints on confirmed save/render/JPEG candidates and record the live call stack/arguments.",
            "If camera/render-target state remains hidden, capture the save frame with RenderDoc.",
        ],
        "truth_note": "Textual discovery/ranking only. It does not prove a runtime call path or JPEG encoder implementation."
    }
    trace_json = args.out / "trace.json"
    trace_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "files": len(files),
        "hits": len(all_hits),
        "candidate_methods": len(candidates),
        "probable_call_references": len(call_refs),
        "trace": str(trace_json.resolve()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
