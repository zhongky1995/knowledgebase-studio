#!/usr/bin/env python3

import argparse
import json
import math
import os
import re
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from urllib.parse import unquote


DEFAULT_IGNORE_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "learning-content",
}
IGNORE_PREFIXES = ("_archive", "_course-control", "_kb-control", "_meta", "_planning")
APP_FILENAMES = {"app.js", "routes.js", "content.js"}
ALLOWED_REPEATED_HEADINGS = {"contents", "目录", "references", "参考资料", "sources", "来源"}

PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME|XXX)\b|待补充(?:内容)?|待完善(?:内容)?|这里补充|占位内容", re.I)
CONDESCENDING_RE = re.compile(r"很菜|傻瓜式|零基础(?:也能)?秒懂|小白也能秒懂")
NARRATION_RE = re.compile(
    r"本(?:章|节|部分)(?:将|会|主要)|在本(?:章|节|部分)中|通过本(?:章|节)(?:的学习)?|"
    r"前面我们(?:已经|曾经)?|接下来我们(?:将|会|来|再)?|下面我们(?:将|会|来|再)?|"
    r"回顾(?:上一章|上一节|前文)|需要(?:特别)?注意的是|值得(?:特别)?注意的是|"
    r"总的来说|综上所述|最后我们(?:再|来)?"
)
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
APP_ROUTE_RE = re.compile(r'''["']([^"'\n]+\.md(?:#[^"'\n]*)?)["']''')
HEADING_RE = re.compile(r"^#{2,6}\s+(.+?)\s*$", re.M)
READING_TIME_RE = re.compile(r"(?:预计阅读时间|阅读时间|预计用时)\s*[:：]?\s*(\d{1,3})\s*分钟")


def fail(message, code=2):
    print(json.dumps({"status": "error", "message": message}, ensure_ascii=False, indent=2))
    raise SystemExit(code)


def load_config(root):
    path = root / ".knowledgebase-audit.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"Invalid audit config {path}: {error}")


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False)
    temp_path = Path(handle.name)
    try:
        with handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def mask_preserving_lines(text, pattern):
    return pattern.sub(lambda match: re.sub(r"[^\n]", "", match.group(0)), text)


def prose_only(text):
    text = mask_preserving_lines(text, re.compile(r"\A---\r?\n[\s\S]*?\r?\n---\r?\n"))
    text = mask_preserving_lines(text, re.compile(r"```[\s\S]*?```"))
    text = mask_preserving_lines(text, re.compile(r"<!--[\s\S]*?-->"))
    return text


def visible_text(text):
    text = prose_only(text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[#>*_`|\[\]()!~-]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_block(block):
    block = re.sub(r"!?\[([^\]]*)\]\([^)]+\)", r"\1", block)
    block = re.sub(r"^#{1,6}\s+", "", block, flags=re.M)
    block = re.sub(r"^[-*+>]\s+", "", block, flags=re.M)
    return re.sub(r"\s+", " ", block).strip().lower()


def character_ngrams(text, size=7):
    normalized = re.sub(r"[^\w\u3400-\u9fff]+", "", visible_text(text).lower())
    if len(normalized) < size:
        return Counter()
    return Counter(normalized[index : index + size] for index in range(len(normalized) - size + 1))


def set_similarity(left, right):
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def cosine_similarity(left, right):
    if not left or not right:
        return 0.0
    shared = set(left) & set(right)
    dot = sum(left[key] * right[key] for key in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def normalized_outline(text):
    result = []
    for heading in HEADING_RE.findall(text):
        value = re.sub(r"^\d+(?:\.\d+)*[.、：:]?\s*", "", re.sub(r"[`*_]", "", heading))
        value = re.sub(r"\s+", " ", value).strip().lower()
        if value:
            result.append(value)
    return result


def line_at(text, index):
    return text.count("\n", 0, max(0, index)) + 1


def strip_target(raw):
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = re.sub(r'''\s+["'][^"']*["']\s*$''', "", target)
    return unquote(target.split("#", 1)[0].split("?", 1)[0].strip())


def external_or_dynamic(target):
    return (
        not target
        or target.startswith("#")
        or re.match(r"^(?:https?:|mailto:|tel:|data:|javascript:)", target, re.I)
        or any(character in target for character in "{}$")
    )


def resolved_target(root, source, raw):
    target = strip_target(raw)
    if external_or_dynamic(target):
        return None
    if target.startswith("/"):
        return (root / target.lstrip("/")).resolve()
    return (source.parent / target).resolve()


def configured_scan_roots(root, config):
    values = config.get("publicRoots") or ["."]
    scan_roots = []
    for value in values:
        candidate = (root / value).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            fail(f"publicRoots entry escapes the knowledge-base root: {value}")
        if not candidate.exists():
            fail(f"publicRoots entry does not exist: {value}")
        scan_roots.append(candidate)
    return scan_roots


def scan_files(root, config):
    ignore_dirs = DEFAULT_IGNORE_DIRS | set(config.get("ignoreDirs", []))
    ignore_paths = set(config.get("ignorePaths", []))
    ignore_paths.update(config.get("archiveRoots", []))
    ignore_paths.update(config.get("internalRoots", []))
    if not config.get("includeGenerated", False):
        ignore_paths.update(config.get("generatedRoots", []))
    markdown = []
    app_files = []
    candidates = set()
    for scan_root in configured_scan_roots(root, config):
        if scan_root.is_file():
            candidates.add(scan_root)
        else:
            candidates.update(scan_root.rglob("*"))
    for path in sorted(candidates):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        parts = rel.parts[:-1]
        if any(part in ignore_dirs or part.startswith(IGNORE_PREFIXES) for part in parts):
            continue
        rel_string = str(rel)
        if any(rel_string == item or rel_string.startswith(f"{item}{os.sep}") for item in ignore_paths):
            continue
        if path.suffix.lower() == ".md":
            markdown.append(path)
        if path.name in APP_FILENAMES:
            app_files.append(path)
    return sorted(markdown), sorted(app_files)


def audit(root, strict=False, fail_severity="warning"):
    config = load_config(root)
    long_paragraph_limit = int(config.get("longParagraphCharacters", 450))
    reading_characters_per_minute = int(config.get("readingCharactersPerMinute", 350))
    learner_forbidden_markers = [str(item) for item in config.get("learnerForbiddenMarkers", []) if str(item)]
    markdown_files, app_files = scan_files(root, config)
    errors = []
    warnings = []
    lengths = []
    sections = defaultdict(lambda: {"files": 0, "characters": 0})
    heading_files = defaultdict(set)
    block_files = defaultdict(set)
    file_metrics = []
    page_ngrams = {}
    page_outlines = {}
    stats = {
        "markdownFiles": len(markdown_files),
        "totalCharacters": 0,
        "medianCharacters": 0,
        "shortPagesUnder400Characters": 0,
        "longProseParagraphs": 0,
        "pagesWithLongProseParagraphs": 0,
        "processNarrationPhrases": 0,
        "pagesWithHighNarrationDensity": 0,
        "localMarkdownLinksChecked": 0,
        "appMarkdownPathsChecked": 0,
        "repeatedHeadings": 0,
        "repeatedBlocks": 0,
        "readingTimeMismatches": 0,
        "internalControlMarkers": 0,
    }

    for path in markdown_files:
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8", errors="replace")
        prose = prose_only(text)
        length = len(visible_text(text))
        lengths.append(length)
        stats["totalCharacters"] += length
        if length < 400:
            stats["shortPagesUnder400Characters"] += 1
        section = Path(rel).parts[0] if len(Path(rel).parts) > 1 else "_root"
        sections[section]["files"] += 1
        sections[section]["characters"] += length

        long_count = 0
        cursor = 0
        for block in re.split(r"\n\s*\n", prose):
            index = prose.find(block, cursor)
            cursor = max(cursor, index + len(block))
            trimmed = block.strip()
            if not trimmed or re.match(r"^(?:#{1,6}\s|[-*+>]\s|\d+[.)、]\s|\|)", trimmed):
                continue
            paragraph = normalize_block(trimmed)
            if len(paragraph) > long_paragraph_limit:
                long_count += 1
                stats["longProseParagraphs"] += 1
                warnings.append({
                    "type": "long-prose-paragraph",
                    "file": rel,
                    "line": line_at(prose, index),
                    "characters": len(paragraph),
                    "detail": paragraph[:180],
                })
        if long_count:
            stats["pagesWithLongProseParagraphs"] += 1

        narration = NARRATION_RE.findall(prose)
        stats["processNarrationPhrases"] += len(narration)
        density = len(narration) / max(1, length / 1000)
        if len(narration) >= 3 and density >= 2.5:
            stats["pagesWithHighNarrationDensity"] += 1
            warnings.append({
                "type": "high-process-narration-density",
                "file": rel,
                "occurrences": len(narration),
                "perThousandCharacters": round(density, 1),
                "detail": sorted(set(narration))[:8],
            })

        for pattern_name, pattern in (("placeholder", PLACEHOLDER_RE), ("condescending-audience-label", CONDESCENDING_RE)):
            for match in pattern.finditer(text):
                warnings.append({"type": pattern_name, "file": rel, "line": line_at(text, match.start()), "detail": match.group(0)})

        for marker in learner_forbidden_markers:
            cursor = 0
            while True:
                index = text.find(marker, cursor)
                if index < 0:
                    break
                stats["internalControlMarkers"] += 1
                warnings.append({
                    "type": "internal-control-marker",
                    "file": rel,
                    "line": line_at(text, index),
                    "detail": marker,
                })
                cursor = index + len(marker)

        for match in READING_TIME_RE.finditer(prose):
            advertised = int(match.group(1))
            estimated = max(1, math.ceil(length / max(1, reading_characters_per_minute)))
            if advertised < max(1, math.floor(estimated * 0.65)):
                stats["readingTimeMismatches"] += 1
                warnings.append({
                    "type": "reading-time-mismatch",
                    "file": rel,
                    "line": line_at(prose, match.start()),
                    "advertisedMinutes": advertised,
                    "estimatedReadingMinutes": estimated,
                    "detail": "Advertised time is materially below the configured reading-speed estimate; tables and practice may require additional time.",
                })

        for match in LINK_RE.finditer(text):
            raw_target = match.group(1)
            if external_or_dynamic(raw_target.strip()):
                continue
            stats["localMarkdownLinksChecked"] += 1
            target = resolved_target(root, path, raw_target)
            if target is not None and not target.exists():
                errors.append({
                    "type": "missing-markdown-link",
                    "file": rel,
                    "line": line_at(text, match.start()),
                    "detail": strip_target(raw_target),
                })

        seen_headings = set()
        for heading in HEADING_RE.findall(text):
            normalized = re.sub(r"^\d+(?:\.\d+)*[.、：:]?\s*", "", re.sub(r"[`*_]", "", heading))
            normalized = re.sub(r"\s+", " ", normalized).strip().lower()
            if normalized and normalized not in seen_headings:
                heading_files[normalized].add(rel)
                seen_headings.add(normalized)

        for block in re.split(r"\n\s*\n", prose):
            normalized = normalize_block(block)
            if 100 <= len(normalized) <= 1200:
                block_files[normalized].add(rel)

        file_metrics.append({
            "path": rel,
            "section": section,
            "characters": length,
            "longParagraphs": long_count,
            "processNarrationPhrases": len(narration),
        })
        grams = character_ngrams(text)
        if length >= int(config.get("nearDuplicateMinimumCharacters", 600)) and grams:
            page_ngrams[rel] = grams
        outline = normalized_outline(text)
        if len(outline) >= int(config.get("repeatedOutlineMinimumHeadings", 4)):
            page_outlines[rel] = outline

    for path in app_files:
        rel = str(path.relative_to(root))
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in APP_ROUTE_RE.finditer(text):
            target_text = strip_target(match.group(1))
            stats["appMarkdownPathsChecked"] += 1
            root_target = (root / target_text.lstrip("/")).resolve()
            app_target = (path.parent / target_text).resolve()
            if not root_target.exists() and not app_target.exists():
                errors.append({
                    "type": "missing-app-path",
                    "file": rel,
                    "line": line_at(text, match.start()),
                    "detail": target_text,
                })

    threshold = max(4, int(len(markdown_files) * 0.2 + 0.999))
    allowed_headings = ALLOWED_REPEATED_HEADINGS | {
        str(item).strip().lower() for item in config.get("allowedRepeatedHeadings", [])
    }
    repeated_headings = sorted(
        ((heading, files) for heading, files in heading_files.items() if heading not in allowed_headings and len(files) >= threshold),
        key=lambda item: len(item[1]),
        reverse=True,
    )[:20]
    for heading, files in repeated_headings:
        warnings.append({"type": "repeated-heading-pattern", "occurrences": len(files), "files": sorted(files)[:8], "detail": heading})

    repeated_blocks = sorted(
        ((block, files) for block, files in block_files.items() if len(files) >= 3),
        key=lambda item: len(item[1]),
        reverse=True,
    )[:20]
    for block, files in repeated_blocks:
        warnings.append({"type": "repeated-content-block", "occurrences": len(files), "files": sorted(files)[:8], "detail": block[:180]})

    near_duplicate_threshold = float(config.get("nearDuplicateThreshold", 0.72))
    near_duplicate_pairs = []
    for left, right in combinations(sorted(page_ngrams), 2):
        similarity = cosine_similarity(page_ngrams[left], page_ngrams[right])
        if similarity >= near_duplicate_threshold:
            near_duplicate_pairs.append((similarity, left, right))
    for similarity, left, right in sorted(near_duplicate_pairs, reverse=True)[:30]:
        warnings.append({
            "type": "near-duplicate-page",
            "similarity": round(similarity, 3),
            "files": [left, right],
            "detail": "Pages may be template variants or retain a shared body beneath customized openings.",
        })

    outline_threshold = float(config.get("repeatedOutlineThreshold", 0.8))
    outline_containment_threshold = float(config.get("repeatedOutlineContainmentThreshold", 0.5))
    outline_minimum_shared = int(config.get("repeatedOutlineMinimumSharedHeadings", 4))
    repeated_outline_pairs = []
    for left, right in combinations(sorted(page_outlines), 2):
        left_set = set(page_outlines[left])
        right_set = set(page_outlines[right])
        shared = len(left_set & right_set)
        similarity = set_similarity(left_set, right_set)
        containment = shared / min(len(left_set), len(right_set)) if left_set and right_set else 0.0
        if similarity >= outline_threshold or (shared >= outline_minimum_shared and containment >= outline_containment_threshold):
            repeated_outline_pairs.append((containment, similarity, shared, left, right))
    for containment, similarity, shared, left, right in sorted(repeated_outline_pairs, reverse=True)[:30]:
        warnings.append({
            "type": "repeated-outline-pattern",
            "similarity": round(similarity, 3),
            "containment": round(containment, 3),
            "sharedHeadings": shared,
            "files": [left, right],
            "detail": "Highly similar outlines require a page-job review; do not force one lesson template across the corpus.",
        })

    stats["medianCharacters"] = round(statistics.median(lengths)) if lengths else 0
    stats["repeatedHeadings"] = len(repeated_headings)
    stats["repeatedBlocks"] = len(repeated_blocks)
    stats["nearDuplicatePairs"] = len(near_duplicate_pairs)
    stats["repeatedOutlinePairs"] = len(repeated_outline_pairs)
    default_severity = {
        "placeholder": "error",
        "condescending-audience-label": "warning",
        "long-prose-paragraph": "warning",
        "high-process-narration-density": "warning",
        "repeated-heading-pattern": "warning",
        "repeated-content-block": "warning",
        "near-duplicate-page": "warning",
        "repeated-outline-pattern": "warning",
        "internal-control-marker": "error",
        "reading-time-mismatch": "warning",
    }
    severity_overrides = config.get("severityByType", {})
    severity_rank = {"info": 0, "warning": 1, "error": 2}
    for warning in warnings:
        warning["severity"] = severity_overrides.get(warning["type"], default_severity.get(warning["type"], "warning"))
    blocking_warnings = [
        warning for warning in warnings
        if severity_rank.get(warning.get("severity"), 1) >= severity_rank[fail_severity]
    ]
    status = "failed" if errors or (strict and blocking_warnings) else "ok"
    return {
        "root": str(root),
        "status": status,
        "strict": strict,
        "failSeverity": fail_severity if strict else None,
        "scope": {
            "publicRoots": config.get("publicRoots") or ["."],
            "archiveRoots": config.get("archiveRoots", []),
            "internalRoots": config.get("internalRoots", []),
            "generatedRoots": config.get("generatedRoots", []),
        },
        "stats": stats,
        "sections": dict(sorted(sections.items())),
        "files": file_metrics,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Deterministic knowledge-base audit")
    parser.add_argument("root")
    parser.add_argument("--output")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--fail-severity", choices=["info", "warning", "error"], default="warning")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        fail(f"Knowledge-base root is not a directory: {root}")
    report = audit(root, strict=args.strict, fail_severity=args.fail_severity)
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = root / output
        output = output.resolve()
        try:
            output.relative_to(root)
        except ValueError:
            fail(f"Audit output must stay inside the knowledge-base root: {output}")
        atomic_write(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
