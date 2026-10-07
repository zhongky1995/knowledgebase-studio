#!/usr/bin/env python3
"""Validate explanatory visual assets declared by Knowledgebase Studio."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FORMATS = {"svg", "png", "gif", "mp4", "webm"}
PURPOSES = {"mechanism", "relationship", "flow", "hierarchy", "state-change", "comparison"}


def issue(collection, kind, path, detail):
    collection.append({"kind": kind, "path": str(path), "detail": detail})


def inside(root, candidate):
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def project_path(root, value, errors, label, *, required=True):
    if not isinstance(value, str) or not value.strip():
        if required:
            issue(errors, "path-field", label, "Path is missing.")
        return None
    candidate = (root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    if not inside(root, candidate):
        issue(errors, "escaping-path", label, value)
        return None
    if not candidate.is_file():
        issue(errors, "missing-file", label, value)
        return None
    if candidate.stat().st_size <= 0:
        issue(errors, "empty-file", label, value)
        return None
    return candidate


def skip_subblocks(data, position):
    while position < len(data):
        size = data[position]
        position += 1
        if size == 0:
            return position
        position += size
        if position > len(data):
            raise ValueError("truncated GIF sub-block")
    raise ValueError("unterminated GIF sub-block")


def probe_gif(path):
    data = path.read_bytes()
    if len(data) < 13 or data[:6] not in {b"GIF87a", b"GIF89a"}:
        raise ValueError("invalid GIF header")
    width, height = struct.unpack_from("<HH", data, 6)
    packed = data[10]
    position = 13
    if packed & 0x80:
        position += 3 * (2 ** ((packed & 0x07) + 1))
    frames = 0
    duration_ms = 0
    loop = None
    while position < len(data):
        marker = data[position]
        position += 1
        if marker == 0x3B:
            break
        if marker == 0x21:
            if position >= len(data):
                raise ValueError("truncated GIF extension")
            label = data[position]
            position += 1
            if label == 0xF9:
                if position + 6 > len(data) or data[position] != 4:
                    raise ValueError("invalid GIF graphic control extension")
                duration_ms += struct.unpack_from("<H", data, position + 2)[0] * 10
                position += 6
            elif label == 0xFF:
                if position >= len(data):
                    raise ValueError("truncated GIF application extension")
                size = data[position]
                position += 1
                application = data[position:position + size]
                position += size
                if application.startswith(b"NETSCAPE") and position + 5 <= len(data):
                    block_size = data[position]
                    if block_size >= 3 and data[position + 1] == 1:
                        loop = struct.unpack_from("<H", data, position + 2)[0]
                position = skip_subblocks(data, position)
            else:
                position = skip_subblocks(data, position)
        elif marker == 0x2C:
            if position + 9 > len(data):
                raise ValueError("truncated GIF image descriptor")
            descriptor_packed = data[position + 8]
            position += 9
            if descriptor_packed & 0x80:
                position += 3 * (2 ** ((descriptor_packed & 0x07) + 1))
            if position >= len(data):
                raise ValueError("truncated GIF image data")
            position += 1
            position = skip_subblocks(data, position)
            frames += 1
        else:
            raise ValueError(f"unknown GIF block marker 0x{marker:02x}")
    return {"width": width, "height": height, "frames": frames, "durationMs": duration_ms, "loop": loop}


def probe_png(path):
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("invalid PNG header")
    width, height = struct.unpack(">II", data[16:24])
    return {"width": width, "height": height, "frames": 1}


def numeric_svg_value(value):
    if value is None:
        return None
    match = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)", str(value))
    return float(match.group(1)) if match else None


def probe_svg(path):
    root = ET.parse(path).getroot()
    if not root.tag.lower().endswith("svg"):
        raise ValueError("root element is not SVG")
    width = numeric_svg_value(root.get("width"))
    height = numeric_svg_value(root.get("height"))
    viewbox = root.get("viewBox") or root.get("viewbox")
    if (not width or not height) and viewbox:
        values = [float(value) for value in re.split(r"[\s,]+", viewbox.strip()) if value]
        if len(values) == 4:
            width, height = values[2], values[3]
    if not width or not height:
        raise ValueError("SVG needs width/height or a valid viewBox")
    return {"width": width, "height": height, "frames": 1}


def probe_media(path, media_format, validation):
    if media_format == "gif":
        return probe_gif(path)
    if media_format == "png":
        return probe_png(path)
    if media_format == "svg":
        return probe_svg(path)
    probe = validation.get("mediaProbe") or {}
    required = ("width", "height", "durationSeconds", "frames")
    if not all(isinstance(probe.get(key), (int, float)) and probe.get(key) > 0 for key in required):
        raise ValueError("MP4/WebM requires positive width, height, durationSeconds, and frames in validation.mediaProbe")
    return {key: probe[key] for key in required}


DESIGN_DIMENSIONS = {"hierarchy", "legibility", "colorSemantics", "connections", "composition", "mechanismVisibility", "sourceBoundary"}


def positive_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def validate_design_review(root, item, errors, label):
    review = item.get("designReview")
    if not isinstance(review, dict):
        issue(errors, "visual-design-review", label, "Schema 2 requires designReview with real rendered evidence.")
        return
    for field in ("pattern", "designSystem"):
        if not isinstance(review.get(field), str) or not review[field].strip():
            issue(errors, "visual-design-field", label, f"Missing {field}.")
    target = review.get("minLabelPxTarget")
    if not positive_number(target):
        issue(errors, "visual-label-target", label, "Declare a positive minimum rendered label size.")
    elif target < 14 and not str(review.get("smallLabelReason") or "").strip():
        issue(errors, "visual-label-exception", label, "Explain and review a label target below the 14px default.")
    hashes = review.get("assetSha256")
    hashes = hashes if isinstance(hashes, dict) else {}
    for field in ("assetPath", "fallbackPath"):
        value = item.get(field)
        if field == "fallbackPath" and item.get("mode") != "animated":
            continue
        asset = project_path(root, value, errors, f"{label}.{field}")
        if asset and hashes.get(value) != hashlib.sha256(asset.read_bytes()).hexdigest():
            issue(errors, "visual-design-stale", label, f"Review must match the current {field} bytes.")
    dimensions = review.get("dimensions")
    dimensions = dimensions if isinstance(dimensions, dict) else {}
    for key in sorted(DESIGN_DIMENSIONS):
        check = dimensions.get(key)
        if not isinstance(check, dict) or check.get("status") != "pass" or not str(check.get("observation") or "").strip():
            issue(errors, "visual-design-dimension", label, f"{key} needs a passed, specific observation.")
    viewports = review.get("viewports")
    viewports = viewports if isinstance(viewports, list) else []
    mobile = desktop = False
    for index, entry in enumerate(viewports):
        location = f"{label}.designReview.viewports[{index}]"
        if not isinstance(entry, dict):
            issue(errors, "visual-viewport", location, "Expected an evidence record.")
            continue
        width = entry.get("viewportWidth")
        rendered = entry.get("renderedWidth")
        minimum = entry.get("minLabelPx")
        scale = entry.get("captureScale")
        if not all(positive_number(n) for n in (width, rendered, minimum, scale)):
            issue(errors, "visual-viewport", location, "Positive viewportWidth, renderedWidth, minLabelPx and captureScale required.")
            continue
        mobile |= width <= 480
        desktop |= width >= 960
        if rendered > width:
            issue(errors, "visual-overflow", location, "Main explanation must fit the viewport.")
        if positive_number(target) and minimum < target:
            issue(errors, "visual-small-label", location, "Rendered labels fall below the declared minimum.")
        screenshot = project_path(root, entry.get("screenshotPath"), errors, location)
        if screenshot:
            try:
                metadata = probe_png(screenshot)
                if abs(metadata["width"] - rendered * scale) > 2:
                    issue(errors, "visual-capture-size", location, "Use a complete figure crop matching renderedWidth and captureScale.")
            except (ValueError, OSError) as error:
                issue(errors, "visual-screenshot", location, str(error))
            if entry.get("screenshotSha256") != hashlib.sha256(screenshot.read_bytes()).hexdigest():
                issue(errors, "visual-screenshot-stale", location, "Screenshot hash does not match the evidence file.")
    if not mobile or not desktop:
        issue(errors, "visual-viewports", label, "Design review requires mobile (<=480px) and desktop (>=960px) figure captures.")


def validate_item(root, item, errors, warnings, stats, label, schema_version=1):
    for field in ("id", "unitId", "pagePath", "purpose", "learningJob", "misconception", "mode", "format", "metaphor", "assetPath", "embedLocation", "altText"):
        if not str(item.get(field, "")).strip():
            issue(errors, "visual-field", label, f"Missing {field}.")

    purpose = item.get("purpose")
    if purpose not in PURPOSES:
        issue(errors, "visual-purpose", label, str(purpose))
    mode = item.get("mode")
    if mode not in {"static", "animated"}:
        issue(errors, "visual-mode", label, str(mode))
    media_format = item.get("format")
    if media_format not in FORMATS:
        issue(errors, "visual-format", label, str(media_format))
    elif mode == "static" and media_format not in {"svg", "png"}:
        issue(errors, "static-format", label, "Static explanations must use SVG or PNG.")
    elif mode == "animated" and media_format not in {"gif", "mp4", "webm"}:
        issue(errors, "animated-format", label, "Animated explanations must use GIF, MP4, or WebM.")

    facts = item.get("essentialFacts") or []
    if not 1 <= len(facts) <= 5 or any(not str(value).strip() for value in facts):
        issue(errors, "essential-facts", label, "Use one to five non-empty essential facts.")
    source_refs = item.get("sourceRefs") or []
    if not source_refs or any(not str(value).strip() for value in source_refs):
        issue(errors, "visual-source-refs", label, "At least one source or internal-standard reference is required.")

    storyboard = item.get("storyboard") or []
    if mode == "animated" and not 4 <= len(storyboard) <= 6:
        issue(errors, "animated-storyboard", label, "Animated explanations require four to six beats.")
    if mode == "static" and not 1 <= len(storyboard) <= 4:
        issue(errors, "static-storyboard", label, "Static explanations require one to four reading beats.")
    for index, beat in enumerate(storyboard):
        if not str(beat.get("job", "")).strip() or not str(beat.get("state", "")).strip():
            issue(errors, "storyboard-field", f"{label}.storyboard[{index}]", "Each beat needs job and state.")

    page = project_path(root, item.get("pagePath"), errors, f"{label}.pagePath")
    asset = project_path(root, item.get("assetPath"), errors, f"{label}.assetPath")
    if asset and media_format in FORMATS:
        if asset.suffix.lower().lstrip(".") != media_format:
            issue(errors, "format-extension", label, f"Declared {media_format}, found {asset.suffix or 'no extension'}.")
        try:
            metadata = probe_media(asset, media_format, item.get("validation") or {})
        except (OSError, ValueError, ET.ParseError) as error:
            issue(errors, "media-probe", asset, str(error))
        else:
            if metadata.get("width", 0) <= 0 or metadata.get("height", 0) <= 0:
                issue(errors, "media-dimensions", asset, str(metadata))
            if mode == "animated" and metadata.get("frames", 0) < 2:
                issue(errors, "animation-frames", asset, "Animated asset has fewer than two frames.")
            if media_format == "gif" and metadata.get("durationMs", 0) <= 0:
                issue(errors, "animation-duration", asset, "GIF duration metadata is missing or zero.")
            if item.get("loopRequired") and media_format == "gif" and metadata.get("loop") != 0:
                issue(errors, "animation-loop", asset, "Loop-required GIF needs infinite-loop metadata.")
            stats["media"][item.get("id") or label] = metadata

    embed = str(item.get("embedLocation", "")).strip()
    if page and embed:
        text = page.read_text(encoding="utf-8", errors="replace")
        asset_name = Path(str(item.get("assetPath", ""))).name
        if embed not in text:
            issue(errors, "missing-embed-location", page, f"Could not find declared embedLocation: {embed}")
        if asset_name and asset_name not in text:
            issue(errors, "asset-not-embedded", page, f"Could not find asset filename: {asset_name}")
        if alt_text := str(item.get("altText", "")).strip():
            if alt_text not in text:
                issue(errors, "alt-text-not-embedded", page, "Declared alternative text is not present at the embed location.")

    alt_text = str(item.get("altText", "")).strip()
    if alt_text and alt_text == Path(str(item.get("assetPath", ""))).name:
        issue(errors, "filename-alt-text", label, "Alternative text must explain the mechanism, not repeat the filename.")

    validation = item.get("validation") or {}
    if schema_version == 2:
        validate_design_review(root, item, errors, label)
    if validation.get("status") != "pass":
        issue(errors, "visual-validation-status", label, str(validation.get("status")))
    for field in ("sourceFidelityChecked", "readabilityChecked", "embedChecked"):
        if validation.get(field) is not True:
            issue(errors, "visual-validation-field", label, f"{field} must be true.")

    if mode == "animated":
        fallback = project_path(root, item.get("fallbackPath"), errors, f"{label}.fallbackPath")
        if fallback and fallback.suffix.lower() not in {".svg", ".png"}:
            issue(errors, "fallback-format", fallback, "Animated fallback must be SVG or PNG.")
        for field in ("fallbackChecked", "meaningfulStateChange", "reducedMotionChecked"):
            if validation.get(field) not in {True, "pass"}:
                issue(errors, "animation-validation-field", label, f"{field} must pass.")
        if item.get("loopRequired") and validation.get("loopChecked") not in {True, "pass"}:
            issue(errors, "animation-validation-field", label, "loopChecked must pass when loopRequired is true.")


def check_visuals(root, manifest_path=None, required_ids=None):
    root = Path(root).expanduser().resolve()
    manifest_path = Path(manifest_path) if manifest_path else root / "_kb-control" / "visual-explanations.json"
    manifest_path = manifest_path.resolve() if manifest_path.is_absolute() else (root / manifest_path).resolve()
    errors = []
    warnings = []
    required_ids = set(required_ids or [])
    if not inside(root, manifest_path):
        issue(errors, "escaping-path", manifest_path, "Manifest must stay inside the knowledge-base root.")
        document = {}
    elif not manifest_path.is_file():
        issue(errors, "missing-manifest", manifest_path, "Missing visual explanation manifest.")
        document = {}
    else:
        try:
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            issue(errors, "invalid-json", manifest_path, str(error))
            document = {}

    if document and document.get("schemaVersion") not in {1, 2}:
        issue(errors, "visual-schema", manifest_path, "schemaVersion must be 1 or 2.")
    elif document.get("schemaVersion") == 1:
        issue(warnings, "legacy-visual-design", manifest_path, "Schema 1 does not establish rendered design review; use schema 2 for new or redesigned visuals.")
    if document and document.get("status") != "pass":
        issue(errors, "visual-manifest-status", manifest_path, str(document.get("status")))
    if document.get("checksNotRun"):
        issue(errors, "visual-checks-not-run", manifest_path, ", ".join(map(str, document["checksNotRun"])))

    items = document.get("items") or []
    ids = [item.get("id") for item in items]
    for value in sorted({item for item in ids if item and ids.count(item) > 1}):
        issue(errors, "duplicate-visual-id", manifest_path, value)
    missing = sorted(required_ids - set(ids))
    if missing:
        issue(errors, "visual-coverage", manifest_path, f"Missing required visual IDs: {', '.join(missing)}")

    selected = [item for item in items if not required_ids or item.get("id") in required_ids]
    stats = {"declared": len(items), "validated": len(selected), "animated": 0, "formats": {}, "media": {}}
    for index, item in enumerate(selected):
        validate_item(root, item, errors, warnings, stats, f"items[{index}]", document.get("schemaVersion"))
        if item.get("mode") == "animated":
            stats["animated"] += 1
        media_format = item.get("format")
        stats["formats"][media_format] = stats["formats"].get(media_format, 0) + 1

    return {
        "schemaVersion": 1,
        "status": "fail" if errors else "pass",
        "root": str(root),
        "manifest": str(manifest_path),
        "requiredIds": sorted(required_ids),
        "declaredIds": sorted(value for value in ids if value),
        "stats": stats,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="Knowledge-base root")
    parser.add_argument("--manifest", help="Manifest path, relative to the root by default")
    parser.add_argument("--id", action="append", dest="required_ids", default=[], help="Require and validate one visual ID; repeatable")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": f"Knowledge-base root is not a directory: {root}"}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    report = check_visuals(root, args.manifest, args.required_ids)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output).expanduser()
        output = output.resolve() if output.is_absolute() else (root / output).resolve()
        if not inside(root, output):
            print(json.dumps({"status": "error", "message": "Output must stay inside the knowledge-base root."}, ensure_ascii=False, indent=2))
            raise SystemExit(2)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    raise SystemExit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
