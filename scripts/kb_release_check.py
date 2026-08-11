#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


DEFAULTS = {
    "distributionMode": "local_entrypoint",
    "audienceScope": "internal",
    "entrypoint": "index.html",
    "requiredFiles": [],
    "expectedMarkdownFiles": None,
    "licensePolicy": "internal_only",
    "licenseFiles": [],
    "forbiddenPaths": [
        "_kb-control",
        "_task-control",
        "_meta",
        "_archive",
        "_archive-v1",
        ".git",
        "node_modules",
        "__pycache__",
        "test-results",
        "playwright-report",
    ],
    "forbiddenMarkers": [
        "/Users/",
        "C:\\Users\\",
        "/private/var/folders/",
        "_kb-control",
        "_task-control",
    ],
    "markerScanExcludes": [
        "scripts/check-release.mjs",
        "scripts/kb_release_check.py"
    ],
    "textExtensions": [
        ".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".json", ".md", ".txt", ".xml", ".svg"
    ],
}

SECRET_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "secrets.json",
}

SECRET_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel", "data", "javascript", "blob"}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
CSS_URL = re.compile(r"url\(\s*(['\"]?)([^)'\"]+)\1\s*\)", re.IGNORECASE)


class LocalReferenceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"href", "src", "poster"} and value:
                self.references.append(value)


def add_issue(collection, kind, path, detail):
    collection.append({"kind": kind, "path": str(path), "detail": detail})


def inside(root, candidate):
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def normalized_relative(value):
    return Path(str(value).replace("\\", "/"))


def forbidden_path_matches(relative, forbidden_paths):
    value = relative.as_posix().strip("/")
    parts = set(relative.parts)
    return sorted(
        item for item in forbidden_paths
        if item in parts or value == item or value.startswith(f"{item}/")
    )


def resolve_local_reference(root, source, raw):
    value = str(raw or "").strip().strip("<>")
    if not value or value.startswith("#") or "${" in value or "{{" in value:
        return None
    split = urlsplit(value)
    if split.scheme.lower() in EXTERNAL_SCHEMES or split.netloc:
        return None
    local_path = unquote(split.path)
    if not local_path:
        return None
    candidate = root / local_path.lstrip("/") if local_path.startswith("/") else source.parent / local_path
    candidate = candidate.resolve()
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate


def extract_references(path, text):
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        for match in MARKDOWN_LINK.finditer(text):
            target = match.group(1).strip()
            if " " in target and not target.startswith("<"):
                target = target.split()[0]
            yield target
    elif suffix in {".html", ".htm"}:
        parser = LocalReferenceParser()
        parser.feed(text)
        yield from parser.references
    elif suffix == ".css":
        for match in CSS_URL.finditer(text):
            yield match.group(2)


def load_config(path):
    config = dict(DEFAULTS)
    if path:
        try:
            user = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            print(json.dumps({"status": "error", "message": f"Cannot read release config: {error}"}, ensure_ascii=False, indent=2))
            raise SystemExit(2)
        config.update(user)
    return config


def check_release(root, config, config_path=None):
    errors = []
    warnings = []
    distribution = config.get("distributionMode")
    audience = config.get("audienceScope")
    license_policy = config.get("licensePolicy")

    if distribution not in {"local_entrypoint", "single_file", "static_site", "archive"}:
        add_issue(errors, "distribution-mode", ".", f"Unsupported distributionMode: {distribution}")
    if audience not in {"internal", "public"}:
        add_issue(errors, "audience-scope", ".", f"Unsupported audienceScope: {audience}")
    if audience == "internal" and license_policy != "internal_only":
        add_issue(errors, "license-policy", ".", "Internal releases must use internal_only.")
    if audience == "public" and license_policy not in {"all_rights_reserved", "explicit_files"}:
        add_issue(
            errors,
            "license-policy",
            ".",
            "Public releases require an explicit all_rights_reserved or explicit_files decision; the checker never chooses a license.",
        )

    entrypoint = root / normalized_relative(config.get("entrypoint", "index.html"))
    if not entrypoint.exists() or not entrypoint.is_file():
        add_issue(errors, "missing-entrypoint", config.get("entrypoint", "index.html"), "Entrypoint does not exist.")

    required = list(config.get("requiredFiles") or [])
    for value in required:
        candidate = (root / normalized_relative(value)).resolve()
        if not inside(root, candidate) or not candidate.exists():
            add_issue(errors, "missing-required-file", value, "Required release file does not exist inside the release root.")

    license_files = list(config.get("licenseFiles") or [])
    if license_policy == "explicit_files":
        if not license_files:
            add_issue(errors, "license-policy", ".", "explicit_files requires at least one license file.")
        for value in license_files:
            candidate = (root / normalized_relative(value)).resolve()
            if not inside(root, candidate) or not candidate.is_file():
                add_issue(errors, "missing-license-file", value, "Declared license file is missing.")

    forbidden_paths = {str(item).strip("/\\") for item in config.get("forbiddenPaths", []) if str(item).strip("/\\")}
    forbidden_markers = [str(item) for item in config.get("forbiddenMarkers", []) if str(item)]
    marker_scan_excludes = {str(item).replace("\\", "/").lstrip("./") for item in config.get("markerScanExcludes", [])}
    text_extensions = {str(item).lower() for item in config.get("textExtensions", [])}
    files = []
    text_files = 0
    markdown_files = 0
    local_references = 0

    candidates = []
    for current, directories, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_directories = []
        for name in directories:
            candidate = current_path / name
            relative = candidate.relative_to(root)
            if candidate.is_symlink():
                target = candidate.resolve()
                if not inside(root, target):
                    add_issue(errors, "external-symlink", relative, f"Symlink resolves outside release root: {target}")
                continue
            blocked = forbidden_path_matches(relative, forbidden_paths)
            if blocked:
                add_issue(errors, "forbidden-path", relative, f"Contains forbidden release path: {', '.join(blocked)}")
                continue
            kept_directories.append(name)
        directories[:] = kept_directories
        for name in names:
            candidates.append(current_path / name)

    for candidate in sorted(candidates):
        relative = candidate.relative_to(root)
        if candidate.is_symlink():
            target = candidate.resolve()
            if not inside(root, target):
                add_issue(errors, "external-symlink", relative, f"Symlink resolves outside release root: {target}")
            continue
        if config_path and candidate.resolve() == config_path.resolve():
            continue
        files.append(candidate)
        blocked = forbidden_path_matches(relative, forbidden_paths)
        if blocked:
            add_issue(errors, "forbidden-path", relative, f"Contains forbidden release path: {', '.join(blocked)}")
            continue
        lower_name = candidate.name.lower()
        if lower_name in SECRET_NAMES or candidate.suffix.lower() in SECRET_SUFFIXES:
            add_issue(errors, "secret-like-file", relative, "Secret-like files must not be included in a release package.")
        if candidate.suffix.lower() in {".md", ".markdown"}:
            markdown_files += 1
        if candidate.suffix.lower() not in text_extensions:
            continue
        text_files += 1
        try:
            text = candidate.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            add_issue(warnings, "non-utf8-text", relative, "Configured text file is not UTF-8 and was not scanned.")
            continue
        if relative.as_posix() not in marker_scan_excludes:
            for marker in forbidden_markers:
                if marker in text:
                    add_issue(errors, "forbidden-marker", relative, f"Contains forbidden marker: {marker}")
        for raw in extract_references(candidate, text):
            resolved = resolve_local_reference(root, candidate, raw)
            if resolved is None:
                continue
            local_references += 1
            if not inside(root, resolved):
                add_issue(errors, "escaping-link", relative, f"Local reference escapes release root: {raw}")
            elif not resolved.exists():
                add_issue(errors, "broken-local-link", relative, f"Local reference does not resolve: {raw}")

    expected_markdown = config.get("expectedMarkdownFiles")
    if expected_markdown is not None and markdown_files != expected_markdown:
        add_issue(
            errors,
            "markdown-count",
            ".",
            f"Expected {expected_markdown} Markdown files, found {markdown_files}.",
        )

    if distribution == "single_file":
        if entrypoint.suffix.lower() not in {".html", ".htm"}:
            add_issue(errors, "single-file-entrypoint", config.get("entrypoint"), "A single-file release must use an HTML entrypoint.")
        if len(files) != 1 or (files and files[0].resolve() != entrypoint.resolve()):
            add_issue(
                errors,
                "single-file-assets",
                ".",
                f"A single-file release must embed all runtime assets; found {len(files)} package files.",
            )

    return {
        "status": "fail" if errors else "pass",
        "root": str(root),
        "scope": {
            "distributionMode": distribution,
            "audienceScope": audience,
            "entrypoint": config.get("entrypoint"),
            "licensePolicy": license_policy,
        },
        "stats": {
            "files": len(files),
            "textFiles": text_files,
            "markdownFiles": markdown_files,
            "localReferences": local_references,
        },
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate an isolated knowledge-base release package without publishing it.")
    parser.add_argument("root", help="Release package or static-site root")
    parser.add_argument("--config", help="Release JSON contract")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(json.dumps({"status": "error", "message": f"Release root is not a directory: {root}"}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    config_path = Path(args.config).expanduser().resolve() if args.config else None
    config = load_config(config_path)
    report = check_release(root, config, config_path)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    raise SystemExit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
