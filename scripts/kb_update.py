#!/usr/bin/env python3
"""Plan and verify a scoped update without changing the full workflow verdict."""

import argparse
import hashlib
import json
from pathlib import Path

from kb_content_check import validate as check_content
from kb_learning_check import check_learning, file_in_root, issue, read_object, records, strings
from kb_workflow import read_json_if_possible, stale_stage_reasons, learning_asset_paths, visual_asset_paths

CONTRACTS = ("project-contract.yaml", "source-understanding.json", "knowledge-model.json", "learning-design.json", "content-coverage.json", "navigation-contract.json", "learning-activities.json", "visual-explanations.json", "app-validation.json")
STRUCTURAL_CONTRACTS = {"project-contract.yaml", "knowledge-model.json", "navigation-contract.json"}


def normalize(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError(f"Choose a scoped path inside the knowledge base: {value}")
    return str(path.relative_to(root))


def fingerprint(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path escapes knowledge base: {value}")
    if not path.exists():
        return None
    digest = hashlib.sha256()
    files = [path] if path.is_file() else sorted(path.rglob("*"))
    for child in files:
        if any(part in {".git", "__pycache__", "node_modules"} for part in child.relative_to(root).parts):
            continue
        resolved = child.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError(f"Linked file escapes knowledge base: {child}")
        if child.is_file():
            digest.update(str(child.relative_to(root)).encode())
            digest.update(b"\0")
            digest.update(child.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def global_state(root):
    state = read_json_if_possible(root / "_kb-control/workflow.json")
    if not state:
        return {"status": "uninitialized", "staleStages": []}
    stale = stale_stage_reasons(root, state)
    return {"status": "stale" if stale else state.get("status", "unknown"), "staleStages": [item["stage"] for item in stale]}


def plan_update(root, changed_paths, *, pages=(), delivery_paths=(), release_paths=()):
    root = Path(root).resolve()
    changed = sorted({normalize(root, value) for value in changed_paths})
    if not changed:
        raise ValueError("At least one changed path is required.")
    coverage = read_json_if_possible(root / "_kb-control/content-coverage.json")
    public_pages = [page.get("path") for page in coverage.get("pages", []) if isinstance(page, dict) and page.get("path")]
    affected = {normalize(root, value) for value in pages}
    affected.update(value for value in changed if value.endswith(".md") and not value.startswith("_"))
    structure_changed = any(value.startswith("_kb-control/") and Path(value).name in STRUCTURAL_CONTRACTS for value in changed)
    unscoped_control = not pages and any(value.startswith("_kb-control/") and Path(value).name in CONTRACTS for value in changed)
    manifest = read_json_if_possible(root / "_kb-control/learning-activities.json")
    activity_assets = {}
    for item in manifest.get("items", []):
        if not isinstance(item, dict) or not isinstance(item.get("interaction"), dict):
            continue
        for value in item["interaction"].get("assetPaths", []):
            if isinstance(value, str) and isinstance(item.get("pagePath"), str):
                activity_assets.setdefault(normalize(root, value), set()).add(normalize(root, item["pagePath"]))
    shared_app_changed = False
    for value in changed:
        owned_pages = {page for asset, owners in activity_assets.items() if asset == value or asset.startswith(value + "/") for page in owners}
        affected.update(owned_pages)
        candidate = root / value
        files = candidate.rglob("*") if candidate.is_dir() else [candidate]
        for changed_file in files:
            if changed_file.suffix in {".js", ".mjs", ".css", ".html", ".ts", ".tsx", ".jsx", ".vue", ".svelte"}:
                if normalize(root, str(changed_file)) not in activity_assets:
                    shared_app_changed = True
    for page in public_pages:
        candidate = root / normalize(root, page)
        if structure_changed or unscoped_control or shared_app_changed or any(page == value or page.startswith(value + "/") for value in changed):
            affected.add(page)
        elif candidate.is_file():
            text = candidate.read_text(encoding="utf-8", errors="replace")
            if any(Path(value).name in text for value in changed):
                affected.add(page)
    if not affected:
        raise ValueError("No affected pages found; provide --page for the learner-facing scope.")
    app = read_json_if_possible(root / "_kb-control/app-validation.json")
    deliveries = {normalize(root, value) for value in delivery_paths}
    deliveries.update(normalize(root, value) for value in app.get("appPaths", []) if isinstance(value, str) and (root / value).exists())
    releases = {normalize(root, value) for value in release_paths}
    tracked = set(changed) | affected | deliveries | releases
    tracked.update(f"_kb-control/{name}" for name in CONTRACTS if (root / "_kb-control" / name).is_file())
    model = read_json_if_possible(root / "_kb-control/knowledge-model.json")
    units = [unit for unit in model.get("units", []) if isinstance(unit, dict)]
    required_units = {unit.get("id") for unit in units if unit.get("canonicalOwner") in affected}
    while True:
        dependencies = {value for unit in units if unit.get("id") in required_units for value in unit.get("dependencies", [])}
        if dependencies.issubset(required_units):
            break
        required_units.update(dependencies)
    tracked.update(normalize(root, unit["canonicalOwner"]) for unit in units if unit.get("id") in required_units and isinstance(unit.get("canonicalOwner"), str))
    for check in app.get("learningActivities", []):
        if isinstance(check, dict):
            tracked.update(normalize(root, value) for value in check.get("evidencePaths", []) if isinstance(value, str))
    for path in learning_asset_paths(root, affected) + visual_asset_paths(root, include_manifest=True):
        tracked.add(normalize(root, str(path)))
    required = ["editor-review"]
    if structure_changed:
        required.append("architecture-review")
    interactive = any(item.get("mode") == "interactive" and item.get("pagePath") in affected for item in manifest.get("items", []) if isinstance(item, dict))
    if deliveries or shared_app_changed or interactive:
        required.append("browser")
    if releases:
        required.append("release")
    return {
        "schemaVersion": 1, "scope": "incremental", "changedPaths": changed,
        "affectedPages": sorted(affected), "deliveryPaths": sorted(deliveries), "releasePaths": sorted(releases),
        "inputDigests": {value: fingerprint(root, value) for value in sorted(tracked)},
        "requiredChecks": required, "checks": [], "globalWorkflow": global_state(root),
    }


def check_update(root, plan):
    root = Path(root).resolve()
    errors = []
    if plan.get("schemaVersion") != 1 or plan.get("scope") != "incremental":
        issue(errors, "update-schema", "plan", "Expected incremental schema version 1.")
    changed = strings(plan.get("changedPaths"), errors, "changedPaths")
    pages = strings(plan.get("affectedPages"), errors, "affectedPages")
    deliveries = strings(plan.get("deliveryPaths", []), errors, "deliveryPaths", required=False)
    releases = strings(plan.get("releasePaths", []), errors, "releasePaths", required=False)
    if errors:
        return {"status": "fail", "scope": "incremental", "errors": errors}
    expected = plan_update(root, changed, pages=pages, delivery_paths=deliveries, release_paths=releases)
    planned = plan.get("inputDigests") or {}
    if not isinstance(planned, dict):
        return {"status": "fail", "scope": "incremental", "errors": [{"kind": "update-digests", "path": "inputDigests", "detail": "Expected an object of tracked input fingerprints."}]}
    for value, digest in expected["inputDigests"].items():
        if digest is None:
            issue(errors, "update-missing-input", value, "A tracked input or deliverable is missing.")
        elif planned.get(value) != digest:
            issue(errors, "update-stale-input", value, "Rebuild the update plan and rerun affected checks for the changed inputs.")
    if set(expected["affectedPages"]) != set(pages):
        issue(errors, "update-scope-gap", "affectedPages", "The changed dependencies affect additional pages.")
    checks = records(plan.get("checks", []), errors, "checks")
    for kind in expected["requiredChecks"]:
        receipt = next((item for item in checks if item.get("kind") == kind), {})
        if receipt.get("status") != "pass":
            issue(errors, "update-check-missing", kind, "A current passed check is required.")
        if receipt.get("inputDigests") != planned:
            issue(errors, "update-check-stale", kind, "Check evidence must name the exact inputDigests it actually reviewed.")
        for value in strings(receipt.get("evidencePaths"), errors, kind):
            file_in_root(root, value, errors, kind)
    control = root / "_kb-control"
    content = check_content(root, control / "source-understanding.json", control / "knowledge-model.json", control / "content-coverage.json", page_paths=pages)
    errors.extend(content["errors"])
    learning = check_learning(root, phase="app" if "browser" in expected["requiredChecks"] else "content", page_paths=pages)
    errors.extend(learning["errors"])
    visual_manifest = read_json_if_possible(control / "visual-explanations.json")
    visual_ids = [item.get("id") for item in visual_manifest.get("items", []) if isinstance(item, dict) and item.get("pagePath") in pages and item.get("id")]
    design = read_json_if_possible(control / "learning-design.json")
    model = read_json_if_possible(control / "knowledge-model.json")
    units = {item.get("id") for item in model.get("units", []) if item.get("canonicalOwner") in pages}
    visual_ids.extend((item.get("visualExplanation") or {}).get("id") for item in design.get("lessons", []) if item.get("unitId") in units and (item.get("visualExplanation") or {}).get("required"))
    if visual_ids:
        from kb_visual_check import check_visuals
        errors.extend(check_visuals(root, required_ids=[value for value in visual_ids if value])["errors"])
    evidence_digests = {}
    for receipt in checks:
        for value in receipt.get("evidencePaths", []):
            if isinstance(value, str):
                evidence_digests[value] = fingerprint(root, normalize(root, value))
    return {
        "schemaVersion": 1, "status": "fail" if errors else "pass", "scope": "incremental",
        "claim": "selected-update-only", "affectedPages": pages,
        "inputDigests": expected["inputDigests"], "evidenceDigests": evidence_digests,
        "learningActivities": learning["validatedIds"], "globalWorkflow": global_state(root),
        "errors": errors, "warnings": content["warnings"] + learning["warnings"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "check"])
    parser.add_argument("--root", required=True)
    parser.add_argument("--path", action="append", default=[], dest="changed")
    parser.add_argument("--page", action="append", default=[])
    parser.add_argument("--delivery-path", action="append", default=[])
    parser.add_argument("--release-path", action="append", default=[])
    parser.add_argument("--plan")
    parser.add_argument("--output")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        parser.error("root must be an existing directory")
    try:
        if args.command == "plan":
            result = plan_update(root, args.changed, pages=args.page, delivery_paths=args.delivery_path, release_paths=args.release_path)
        else:
            if not args.plan:
                parser.error("check requires --plan")
            errors = []
            plan = read_object(root / normalize(root, args.plan), errors)
            result = {"status": "fail", "errors": errors} if errors else check_update(root, plan)
        rendered = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            output = root / normalize(root, args.output)
            if args.plan and output == root / normalize(root, args.plan):
                parser.error("output must not overwrite the input plan")
            for value in result.get("inputDigests", {}):
                tracked = root / value
                if output == tracked or (tracked.is_dir() and output.is_relative_to(tracked)):
                    parser.error("output must not overwrite or be inside a tracked input")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        raise SystemExit(result.get("status") == "fail")
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
