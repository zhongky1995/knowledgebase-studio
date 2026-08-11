#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path


LEARNING_POSTURES = {
    "reading_manual",
    "guided_learning",
    "practice_workbench",
    "hybrid",
}

MIGRATION_ACTIONS = {
    "keep",
    "rewrite",
    "merge",
    "split",
    "move-reference",
    "archive",
    "investigate",
    "hide-compatibility",
}

PASS_VALUES = {"pass", "not_applicable"}


def issue(collection, kind, path, detail):
    collection.append({"kind": kind, "path": str(path), "detail": detail})


def read_json(path, errors, kind, required=True):
    if not path.exists():
        if required:
            issue(errors, "missing-artifact", path, f"Missing {kind} artifact.")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        issue(errors, "invalid-json", path, str(error))
        return {}


def read_text(path, errors, kind, minimum=200):
    if not path.exists():
        issue(errors, "missing-artifact", path, f"Missing {kind} artifact.")
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    visible = re.sub(r"\s+", " ", text).strip()
    if len(visible) < minimum:
        issue(errors, "thin-report", path, f"{kind} is too thin to support a stage decision ({len(visible)} characters).")
    return text


def yaml_scalar(text, key):
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    return match.group(1).strip().strip("\"'") if match else None


def contract(root):
    path = root / "_kb-control" / "project-contract.yaml"
    text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    return {
        "path": path,
        "text": text,
        "posture": yaml_scalar(text, "product_posture"),
        "app_required": yaml_scalar(text, "app_required"),
        "distribution_mode": yaml_scalar(text, "distribution_mode") or "local_entrypoint",
        "release_root": yaml_scalar(text, "release_root") or "",
        "external_publish_authorized": yaml_scalar(text, "external_publish_authorized") == "true",
    }


def inside(root, candidate):
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def checked_project_path(root, value, errors, label, require_file=False):
    if not isinstance(value, str) or not value.strip():
        issue(errors, "path-field", label, "Path is missing.")
        return None
    candidate = (root / value).resolve() if not Path(value).is_absolute() else Path(value).resolve()
    if not inside(root, candidate):
        issue(errors, "escaping-path", label, value)
        return None
    if not candidate.exists():
        issue(errors, "missing-path", label, value)
        return None
    if require_file and not candidate.is_file():
        issue(errors, "not-a-file", label, value)
        return None
    return candidate


def inventory_items(document):
    values = document.get("items")
    if not isinstance(values, list):
        values = document.get("files")
    return values if isinstance(values, list) else []


def public_inventory(root, errors):
    path = root / "_kb-control" / "content-inventory.json"
    document = read_json(path, errors, "content inventory")
    items = inventory_items(document)
    if not items:
        issue(errors, "empty-inventory", path, "The public inventory must contain one record per public document.")
        return document, []

    public = [item for item in items if item.get("visibility", "public") == "public"]
    paths = []
    seen = set()
    required = ("path", "pageType", "primaryJob", "recommendedAction", "confidence")
    for index, item in enumerate(public):
        label = f"items[{index}]"
        for field in required:
            if not str(item.get(field, "")).strip():
                issue(errors, "inventory-field", label, f"Missing {field}.")
        value = item.get("path")
        if not isinstance(value, str) or not value.strip():
            continue
        if value in seen:
            issue(errors, "duplicate-inventory-path", label, value)
            continue
        seen.add(value)
        paths.append(value)
        checked_project_path(root, value, errors, label, require_file=True)

    declared = document.get("publicCorpusCount")
    if declared is not None and declared != len(paths):
        issue(errors, "inventory-count", path, f"Declared {declared} public documents, found {len(paths)} records.")
    return document, paths


def validate_audit(root, errors, warnings, evidence):
    control = root / "_kb-control"
    metrics = read_json(control / "audit-metrics.json", errors, "audit metrics")
    if metrics and metrics.get("status") not in {"ok", "pass"}:
        issue(errors, "audit-metrics-status", control / "audit-metrics.json", str(metrics.get("status")))
    if metrics.get("errors"):
        issue(errors, "audit-errors", control / "audit-metrics.json", f"{len(metrics['errors'])} deterministic error(s).")
    _, paths = public_inventory(root, errors)
    markdown_count = (metrics.get("stats") or {}).get("markdownFiles")
    if markdown_count is not None and paths and markdown_count != len(paths):
        issue(errors, "audit-inventory-mismatch", control / "audit-metrics.json", f"Audit measured {markdown_count} Markdown files but inventory has {len(paths)} public records.")
    read_text(control / "audit-report.md", errors, "audit report", minimum=500)
    evidence.update({"publicDocuments": len(paths), "markdownFilesMeasured": markdown_count})


def migration_records(text):
    starts = list(re.finditer(r"(?m)^\s*-\s+(?:id|old_path):\s*", text))
    records = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[match.start():end]
        record = {}
        for key in ("old_path", "target_path", "action", "canonical_owner", "preservation_status"):
            value = re.search(rf"(?m)^\s+{key}:\s*(.*?)\s*$", block)
            if value:
                record[key] = value.group(1).strip().strip("\"'")
        if "old_path" in record:
            records.append(record)
    return records


def validate_learning_design(root, errors, warnings, evidence):
    control = root / "_kb-control"
    design_path = control / "learning-design.json"
    design = read_json(design_path, errors, "learning design")
    model = read_json(control / "knowledge-model.json", errors, "knowledge model")
    if not design or not model:
        return
    if design.get("schemaVersion") != 1:
        issue(errors, "learning-design-schema", design_path, "schemaVersion must be 1.")

    units = {item.get("id"): item for item in model.get("units") or [] if item.get("id")}
    main_ids = {unit_id for unit_id, item in units.items() if item.get("role") == "main-path"}
    lessons = design.get("lessons") or []
    routes = design.get("routes") or []
    if not lessons:
        issue(errors, "empty-learning-lessons", design_path, "Learning products require lesson-level learning contracts.")
    if not routes:
        issue(errors, "empty-learning-routes", design_path, "Learning products require at least one learner route.")

    lesson_ids = []
    for index, lesson in enumerate(lessons):
        label = f"lessons[{index}]"
        unit_id = lesson.get("unitId")
        lesson_ids.append(unit_id)
        if unit_id not in units:
            issue(errors, "unknown-learning-unit", label, str(unit_id))
        for field in ("startingState", "learningResult", "likelyMisconception", "transferEvidence"):
            if not str(lesson.get(field, "")).strip():
                issue(errors, "learning-field", label, f"Missing {field}.")
        minutes = lesson.get("estimatedReadingMinutes")
        if not isinstance(minutes, (int, float)) or minutes <= 0:
            issue(errors, "learning-time", label, "estimatedReadingMinutes must be a positive number.")
        if not isinstance(lesson.get("workedExampleRequired"), bool):
            issue(errors, "learning-example-policy", label, "workedExampleRequired must be true or false.")
        if lesson.get("workedExampleRequired"):
            example = lesson.get("exampleContract") or {}
            for field in ("input", "judgment", "output", "transfer"):
                if not str(example.get(field, "")).strip():
                    issue(errors, "learning-example-field", label, f"Worked examples require {field}.")
        for dependency in lesson.get("prerequisiteUnitIds") or []:
            if dependency not in units:
                issue(errors, "unknown-learning-prerequisite", label, str(dependency))

    duplicates = {value for value in lesson_ids if value and lesson_ids.count(value) > 1}
    for value in sorted(duplicates):
        issue(errors, "duplicate-learning-lesson", design_path, value)
    missing = sorted(main_ids - set(lesson_ids))
    extra = sorted(set(lesson_ids) - main_ids)
    if missing:
        issue(errors, "learning-lesson-coverage", design_path, f"Missing main-path units: {', '.join(missing)}")
    if extra:
        issue(warnings, "learning-lesson-extra", design_path, f"Non-main-path lesson contracts: {', '.join(extra)}")

    visible_units = set()
    route_ids = set()
    for index, route in enumerate(routes):
        label = f"routes[{index}]"
        route_id = route.get("id")
        if not str(route_id or "").strip():
            issue(errors, "learning-route-field", label, "Missing id.")
        elif route_id in route_ids:
            issue(errors, "duplicate-learning-route", label, str(route_id))
        route_ids.add(route_id)
        if route.get("role") not in {"orientation", "core", "advanced", "reference", "lab", "workbook", "compatibility"}:
            issue(errors, "learning-route-role", label, str(route.get("role")))
        entry = route.get("entryPath")
        if not str(entry or "").strip():
            issue(errors, "learning-route-field", label, "Missing entryPath.")
        elif not (root / entry).exists():
            issue(warnings, "future-learning-entry", label, f"Entry path does not exist yet: {entry}")
        for unit_id in route.get("unitIds") or []:
            if unit_id not in units:
                issue(errors, "unknown-route-unit", label, str(unit_id))
            if route.get("role") != "compatibility":
                visible_units.add(unit_id)

    declared = design.get("learnerVisibleUnitCount")
    if declared is not None and declared != len(visible_units):
        issue(errors, "learner-visible-count", design_path, f"Declared {declared}, mapped {len(visible_units)} unique units.")
    evidence.update({"learningLessons": len(lessons), "learningRoutes": len(routes), "learnerVisibleUnits": len(visible_units)})


def validate_architecture(root, errors, warnings, evidence):
    control = root / "_kb-control"
    read_text(control / "architecture-decision.md", errors, "architecture decision", minimum=500)
    _, public_paths = public_inventory(root, errors)
    migration_path = control / "migration-map.yaml"
    migration_text = read_text(migration_path, errors, "migration map", minimum=100)
    records = migration_records(migration_text)
    if not records:
        issue(errors, "empty-migration-map", migration_path, "Every public path must have an explicit migration action.")
    old_paths = [item.get("old_path") for item in records]
    duplicates = {value for value in old_paths if value and old_paths.count(value) > 1}
    for value in sorted(duplicates):
        issue(errors, "duplicate-migration-path", migration_path, value)
    missing = sorted(set(public_paths) - set(old_paths))
    unknown = sorted(set(old_paths) - set(public_paths))
    if missing:
        issue(errors, "migration-coverage", migration_path, f"Unmapped public paths: {', '.join(missing[:12])}")
    if unknown:
        issue(errors, "migration-unknown-path", migration_path, f"Paths not present in inventory: {', '.join(unknown[:12])}")
    for index, record in enumerate(records):
        label = f"migrations[{index}]"
        if record.get("action") not in MIGRATION_ACTIONS:
            issue(errors, "migration-action", label, str(record.get("action")))
        for field in ("target_path", "canonical_owner", "preservation_status"):
            if not str(record.get(field, "")).strip():
                issue(errors, "migration-field", label, f"Missing {field}.")

    if contract(root).get("posture") in LEARNING_POSTURES:
        validate_learning_design(root, errors, warnings, evidence)
    if contract(root).get("app_required") != "no":
        navigation_path = control / "navigation-contract.json"
        navigation = read_json(navigation_path, errors, "navigation contract")
        if navigation:
            primary = navigation.get("primaryPath") or {}
            if not str(primary.get("destination", "")).strip():
                issue(errors, "navigation-primary-destination", navigation_path, "Primary destination is missing.")
            clicks = primary.get("maxClicks")
            if not isinstance(clicks, int) or clicks < 1 or clicks > 2:
                issue(errors, "navigation-primary-depth", navigation_path, "Primary path must reach useful content in one or two clicks.")
            direct_ids = []
            for index, item in enumerate(navigation.get("directEntries") or []):
                label = f"directEntries[{index}]"
                entry_id = item.get("id")
                direct_ids.append(entry_id)
                for field in ("id", "label", "destination"):
                    if not str(item.get(field, "")).strip():
                        issue(errors, "navigation-direct-field", label, f"Missing {field}.")
                value = item.get("maxClicks")
                if not isinstance(value, int) or value < 1 or value > 2:
                    issue(errors, "navigation-direct-depth", label, "Direct entry must reach content in one or two clicks.")
            for value in sorted({item for item in direct_ids if item and direct_ids.count(item) > 1}):
                issue(errors, "duplicate-navigation-entry", navigation_path, value)
            evidence["expectedDirectEntries"] = len(direct_ids)
    evidence.update({"inventoryPaths": len(public_paths), "migrationRecords": len(records)})


def require_dimension(document, dimensions, key, errors, path):
    value = dimensions.get(key)
    if value not in PASS_VALUES:
        issue(errors, "dimension-not-passed", path, f"{key}: {value or 'missing'}")


def validate_pilot(root, errors, warnings, evidence):
    control = root / "_kb-control"
    read_text(control / "pilot-review.md", errors, "pilot review", minimum=500)
    path = control / "pilot-verdict.json"
    verdict = read_json(path, errors, "pilot verdict")
    if not verdict:
        return
    if verdict.get("status") != "pass" or verdict.get("scaleApproved") is not True:
        issue(errors, "pilot-status", path, "Pilot must pass and explicitly approve scaling.")
    representative = verdict.get("representativePaths") or []
    if not representative:
        issue(errors, "pilot-representative-paths", path, "Pilot must include representative learner-facing paths.")
    for index, value in enumerate(representative):
        checked_project_path(root, value, errors, f"representativePaths[{index}]", require_file=True)
    assumptions = verdict.get("assumptionsTested") or []
    if not assumptions:
        issue(errors, "pilot-assumptions", path, "Pilot must test the riskiest architecture and content assumptions.")
    for index, item in enumerate(assumptions):
        if item.get("result") != "pass" or not str(item.get("evidence", "")).strip():
            issue(errors, "pilot-assumption-result", f"assumptionsTested[{index}]", "Each assumption needs pass evidence.")
    counter = verdict.get("counterReview") or {}
    if counter.get("status") != "pass" or not (counter.get("reviewedRisks") or []):
        issue(errors, "pilot-counter-review", path, "A separate counter-review must challenge the pilot before scaling.")
    dimensions = verdict.get("dimensions") or {}
    required = ["posture", "sourceFidelity", "usefulness", "distinctivePageJobs", "exampleDepth", "progression", "transfer", "navigation"]
    for key in required:
        require_dimension(verdict, dimensions, key, errors, path)
    if verdict.get("criticalIssues"):
        issue(errors, "pilot-critical-issues", path, f"{len(verdict['criticalIssues'])} unresolved critical issue(s).")
    evidence.update({"representativePaths": len(representative), "assumptionsTested": len(assumptions)})


def validate_content(root, errors, warnings, evidence):
    control = root / "_kb-control"
    read_text(control / "content-build-report.md", errors, "content build report", minimum=500)
    integrity = read_json(control / "content-integrity.json", errors, "content integrity")
    if integrity and integrity.get("status") != "pass":
        issue(errors, "content-integrity-status", control / "content-integrity.json", str(integrity.get("status")))
    coverage = read_json(control / "content-coverage.json", errors, "content coverage")
    pages = coverage.get("pages") or []
    if not pages:
        issue(errors, "empty-content-coverage", control / "content-coverage.json", "Content coverage must account for every target page.")
    for index, page in enumerate(pages):
        checked_project_path(root, page.get("path"), errors, f"pages[{index}]", require_file=True)
    audit_metrics = read_json(control / "content-audit-metrics.json", errors, "post-content audit metrics")
    if audit_metrics and audit_metrics.get("status") not in {"ok", "pass"}:
        issue(errors, "post-content-audit-status", control / "content-audit-metrics.json", str(audit_metrics.get("status")))
    evidence.update({"coveredPages": len(pages), "knowledgeUnits": (integrity.get("stats") or {}).get("knowledgeUnits")})


def validate_app(root, errors, warnings, evidence):
    control = root / "_kb-control"
    read_text(control / "app-validation.md", errors, "app validation report", minimum=500)
    path = control / "app-validation.json"
    result = read_json(path, errors, "app validation")
    if not result:
        return
    if result.get("status") != "pass":
        issue(errors, "app-status", path, str(result.get("status")))
    app_paths = result.get("appPaths") or []
    if not app_paths:
        issue(errors, "app-paths", path, "appPaths must identify the validated app deliverable.")
    for index, value in enumerate(app_paths):
        checked_project_path(root, value, errors, f"appPaths[{index}]")
    browser = result.get("browser") or {}
    if browser.get("status") != "pass":
        issue(errors, "browser-not-run", path, "Real browser validation is required for an app stage pass.")
    viewports = browser.get("viewportWidths") or []
    if not any(isinstance(value, (int, float)) and value >= 1000 for value in viewports):
        issue(errors, "browser-desktop", path, "Browser evidence must include a desktop width of at least 1000px.")
    if not any(isinstance(value, (int, float)) and value <= 480 for value in viewports):
        issue(errors, "browser-mobile", path, "Browser evidence must include a mobile width of 480px or less.")
    if not (browser.get("checks") or []):
        issue(errors, "browser-checks", path, "Browser checks must be listed.")
    for index, value in enumerate(browser.get("testedEntrypoints") or []):
        checked_project_path(root, value, errors, f"testedEntrypoints[{index}]", require_file=True)
    navigation = result.get("navigation") or {}
    primary = navigation.get("primaryPath") or {}
    if not primary.get("clickable") or not primary.get("keyboard"):
        issue(errors, "primary-path-actionability", path, "The primary path must be clickable and keyboard reachable.")
    clicks = primary.get("maxClicks")
    if not isinstance(clicks, int) or clicks < 1 or clicks > 2:
        issue(errors, "primary-path-depth", path, "The primary path must reach useful content in one or two clicks.")
    actual_entries = navigation.get("directEntries") or []
    for index, item in enumerate(actual_entries):
        if not item.get("clickable") or not item.get("keyboard"):
            issue(errors, "direct-entry-actionability", f"directEntries[{index}]", "Visible route entries must be actionable by pointer and keyboard.")
        value = item.get("maxClicks")
        if not isinstance(value, int) or value < 1 or value > 2:
            issue(errors, "direct-entry-depth", f"directEntries[{index}]", "Direct entries must reach content in one or two clicks.")
        if not str(item.get("destination", "")).strip():
            issue(errors, "direct-entry-destination", f"directEntries[{index}]", "Destination is missing.")
    expected_navigation = read_json(control / "navigation-contract.json", errors, "navigation contract")
    expected_entries = expected_navigation.get("directEntries") or []
    expected_by_id = {item.get("id"): item for item in expected_entries if item.get("id")}
    actual_by_id = {item.get("id"): item for item in actual_entries if item.get("id")}
    if set(expected_by_id) != set(actual_by_id):
        issue(errors, "direct-entry-coverage", path, f"Expected IDs {sorted(expected_by_id)}, validated IDs {sorted(actual_by_id)}")
    for entry_id, expected in expected_by_id.items():
        actual = actual_by_id.get(entry_id) or {}
        if actual.get("destination") != expected.get("destination"):
            issue(errors, "direct-entry-destination-mismatch", entry_id, f"Expected {expected.get('destination')}, got {actual.get('destination')}")
    if result.get("checksNotRun"):
        issue(errors, "app-checks-not-run", path, ", ".join(map(str, result["checksNotRun"])))
    evidence.update({"appPaths": len(app_paths), "viewportWidths": viewports, "directEntries": len(navigation.get("directEntries") or [])})


def validate_qc(root, errors, warnings, evidence):
    control = root / "_kb-control"
    read_text(control / "qc-report.md", errors, "QC report", minimum=500)
    path = control / "qc-verdict.json"
    verdict = read_json(path, errors, "QC verdict")
    if not verdict:
        return
    if verdict.get("status") != "pass" or verdict.get("overallClaim") != "pass":
        issue(errors, "qc-status", path, "QC must use a scoped pass verdict before the workflow can continue.")
    dimensions = verdict.get("dimensions") or {}
    required = ["corpusIntegrity", "productArchitecture", "contentQuality", "evidence"]
    current_contract = contract(root)
    if current_contract.get("posture") in LEARNING_POSTURES:
        required.append("learningTransfer")
    if current_contract.get("app_required") != "no":
        required.append("appExperience")
    evidence_map = verdict.get("evidence") or {}
    for key in required:
        require_dimension(verdict, dimensions, key, errors, path)
        if not (evidence_map.get(key) or []):
            issue(errors, "qc-evidence-gap", path, f"No evidence recorded for {key}.")
        for index, value in enumerate(evidence_map.get(key) or []):
            checked_project_path(root, value, errors, f"evidence.{key}[{index}]")
    if verdict.get("checksNotRun"):
        issue(errors, "qc-checks-not-run", path, ", ".join(map(str, verdict["checksNotRun"])))
    if verdict.get("criticalIssues"):
        issue(errors, "qc-critical-issues", path, f"{len(verdict['criticalIssues'])} unresolved critical issue(s).")
    evidence.update({"requiredDimensions": required, "passedDimensions": sorted(key for key, value in dimensions.items() if value in PASS_VALUES)})


def validate_release(root, errors, warnings, evidence):
    control = root / "_kb-control"
    read_text(control / "release-report.md", errors, "release report", minimum=500)
    path = control / "release-verdict.json"
    verdict = read_json(path, errors, "release verdict")
    if not verdict:
        return
    current_contract = contract(root)
    if verdict.get("status") != "pass":
        issue(errors, "release-status", path, str(verdict.get("status")))
    release_root_value = verdict.get("releaseRoot") or current_contract.get("release_root")
    if not release_root_value:
        issue(errors, "release-root", path, "releaseRoot is required for a release-stage pass.")
        release_root = None
    else:
        release_root = checked_project_path(root, release_root_value, errors, "releaseRoot")
    config_value = verdict.get("releaseConfig") or "_kb-control/knowledgebase-release.json"
    config_path = checked_project_path(root, config_value, errors, "releaseConfig", require_file=True)
    browser = verdict.get("browser") or {}
    if browser.get("status") != "pass":
        issue(errors, "release-browser-not-run", path, "The final package or local entrypoint must be checked in a real browser.")
    if not (browser.get("testedEntrypoints") or []):
        issue(errors, "release-browser-entrypoint", path, "Browser evidence must identify the tested final entrypoint.")
    for index, value in enumerate(browser.get("testedEntrypoints") or []):
        checked_project_path(root, value, errors, f"releaseBrowserEntrypoints[{index}]", require_file=True)
    if not (browser.get("viewportWidths") or []):
        issue(errors, "release-browser-viewports", path, "Browser evidence must list tested viewport widths.")
    widths = browser.get("viewportWidths") or []
    if widths and not any(isinstance(value, (int, float)) and value >= 1000 for value in widths):
        issue(errors, "release-browser-desktop", path, "Final entrypoint browser evidence needs a desktop viewport.")
    if widths and not any(isinstance(value, (int, float)) and value <= 480 for value in widths):
        issue(errors, "release-browser-mobile", path, "Final entrypoint browser evidence needs a mobile viewport.")
    if verdict.get("checksNotRun"):
        issue(errors, "release-checks-not-run", path, ", ".join(map(str, verdict["checksNotRun"])))
    if verdict.get("externalPublicationPerformed") and not current_contract.get("external_publish_authorized"):
        issue(errors, "unauthorized-external-publication", path, "External publication was not authorized by the project contract.")
    if release_root and config_path:
        try:
            from kb_release_check import check_release, load_config
        except ImportError as error:
            issue(errors, "release-validator-import", path, str(error))
        else:
            release_report = check_release(release_root, load_config(config_path), config_path)
            output = control / "release-check.json"
            output.write_text(json.dumps(release_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if release_report.get("status") != "pass":
                issue(errors, "release-package-check", output, f"{len(release_report.get('errors') or [])} error(s).")
            evidence.update({"releaseRoot": str(release_root.relative_to(root)), "releaseFiles": (release_report.get("stats") or {}).get("files")})


VALIDATORS = {
    "audit": validate_audit,
    "architecture": validate_architecture,
    "pilot": validate_pilot,
    "content": validate_content,
    "app": validate_app,
    "qc": validate_qc,
    "release": validate_release,
}


def validate_stage(root, stage):
    errors = []
    warnings = []
    evidence = {}
    validator = VALIDATORS.get(stage)
    if validator:
        validator(root, errors, warnings, evidence)
    return {
        "schemaVersion": 1,
        "stage": stage,
        "status": "fail" if errors else "pass",
        "root": str(root),
        "evidence": evidence,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate Knowledgebase Studio stage evidence and prevent report-only passes.")
    parser.add_argument("root")
    parser.add_argument("--stage", choices=sorted(VALIDATORS), required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": f"Knowledge-base root is not a directory: {root}"}, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    report = validate_stage(root, args.stage)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output).expanduser()
        output = output.resolve() if output.is_absolute() else (root / output).resolve()
        if not inside(root, output):
            print(json.dumps({"status": "error", "message": "Stage-check output must stay inside the knowledge-base root."}, ensure_ascii=False, indent=2))
            raise SystemExit(2)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    raise SystemExit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
