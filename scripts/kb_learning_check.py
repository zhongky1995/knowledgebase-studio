#!/usr/bin/env python3
"""Check operational walkthroughs and teaching interactions, not learning efficacy."""

import argparse
import json
import re
from pathlib import Path

KINDS = {"concept", "judgment", "operation", "troubleshooting", "creation"}
METHODS = {"editor-review", "simulated-walkthrough", "learner-study"}


def issue(errors, kind, path, detail):
    errors.append({"kind": kind, "path": str(path), "detail": detail})


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def read_object(path, errors, *, optional=False):
    if optional and not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object.")
        return value
    except (OSError, ValueError) as error:
        issue(errors, "learning-json", path, str(error))
        return {}


def records(value, errors, label):
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        issue(errors, "learning-records", label, "Expected a list of objects.")
        return []
    return value


def strings(value, errors, label, *, required=True):
    if not isinstance(value, list) or any(not nonempty(item) for item in value) or (required and not value):
        issue(errors, "learning-list", label, "Expected a list of non-empty strings.")
        return []
    return value


def file_in_root(root, value, errors, label):
    if not nonempty(value):
        issue(errors, "learning-path", label, "Missing file path.")
        return None
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        issue(errors, "escaping-path", label, value)
        return None
    if not path.is_file() or path.stat().st_size == 0:
        issue(errors, "learning-missing-file", label, value)
        return None
    return path


def locator(text, value, errors, label):
    if not nonempty(value) or value not in text:
        issue(errors, "learning-location", label, "A non-empty locator must appear in the learner-facing page.")


def required_fields(item, fields, errors, label):
    for field in fields:
        if not nonempty(item.get(field)):
            issue(errors, "learning-field", label, f"Missing {field}.")


def review_evidence(root, review, errors, label):
    if not isinstance(review, dict):
        issue(errors, "learning-review", label, "Missing review evidence.")
        return
    if review.get("status") != "pass" or review.get("method") not in METHODS:
        issue(errors, "learning-review", label, "Review needs pass and an explicit editor-review, simulated-walkthrough, or learner-study method.")
    for value in strings(review.get("evidencePaths"), errors, label):
        file_in_root(root, value, errors, label)
    study_status = review.get("learnerStudyStatus")
    if study_status not in {"not_run", "completed"}:
        issue(errors, "learning-study-status", label, "Record learnerStudyStatus as not_run or completed.")
    if review.get("method") == "learner-study" and study_status != "completed":
        issue(errors, "learning-study-method", label, "A learner-study review requires a completed study.")
    if study_status == "completed":
        for value in strings(review.get("learnerStudyEvidencePaths"), errors, label):
            file_in_root(root, value, errors, label)


def activity_contracts(root, errors):
    design = read_object(root / "_kb-control/learning-design.json", errors, optional=True)
    result = {}
    for lesson in records(design.get("lessons", []), errors, "lessons"):
        if not nonempty(lesson.get("unitId")):
            issue(errors, "learning-unit-id", "lessons", "Each lesson needs a unitId.")
            continue
        if design.get("schemaVersion") == 3:
            if lesson.get("learningTaskType") not in KINDS:
                issue(errors, "learning-task-type", lesson["unitId"], "Choose the lesson's learning task type.")
            strings(lesson.get("activityIds"), errors, lesson["unitId"], required=lesson.get("learningTaskType") in {"operation", "troubleshooting"})
        for activity_id in strings(lesson.get("activityIds", []), errors, "activityIds", required=False):
            if activity_id in result:
                issue(errors, "duplicate-activity-contract", activity_id, "An activity has one owning lesson.")
            result[activity_id] = lesson.get("unitId")
    return result


def validate_activity(root, item, errors, *, phase):
    label = item.get("id", "activity")
    required_fields(item, ("id", "unitId", "pagePath", "learningGoal", "misconception"), errors, label)
    if item.get("kind") not in KINDS or item.get("mode") not in {"text", "interactive"}:
        issue(errors, "learning-activity-mode", label, "Choose a learning kind and text or interactive mode.")
    if item.get("provenance") not in {"real", "anonymized", "composite", "fictional"}:
        issue(errors, "learning-provenance", label, "Declare the case provenance.")
    page = file_in_root(root, item.get("pagePath"), errors, label)
    text = page.read_text(encoding="utf-8", errors="replace") if page else ""
    locator(text, item.get("provenanceLocation"), errors, f"{label}.provenanceLocation")
    for value in strings(item.get("sourceRefs"), errors, f"{label}.sourceRefs"):
        source_id, _, claim_id = value.partition("#")
        source_doc = read_object(root / "_kb-control/source-understanding.json", errors)
        sources = records(source_doc.get("sources", []), errors, "sources")
        source = next((source for source in sources if source.get("id") == source_id), None)
        if not source or (claim_id and claim_id not in {claim.get("id") for claim in source.get("coreClaims", []) if isinstance(claim, dict)}):
            issue(errors, "learning-source-ref", label, value)

    steps = records(item.get("steps", []), errors, f"{label}.steps")
    if item.get("kind") in {"operation", "troubleshooting"} and not steps:
        issue(errors, "operation-walkthrough", label, "Operational lessons need concrete steps, including text-only lessons.")
    for index, step in enumerate(steps):
        step_label = f"{label}.steps[{index}]"
        required_fields(step, ("precondition", "action", "input", "check", "recovery"), errors, step_label)
        locator(text, step.get("location"), errors, step_label)
        outcomes = records(step.get("possibleResults", []), errors, step_label)
        if not outcomes:
            issue(errors, "operation-results", step_label, "Describe possible observable results and how to continue.")
        for outcome in outcomes:
            required_fields(outcome, ("result", "nextAction"), errors, step_label)

    cases = records(item.get("cases", []), errors, f"{label}.cases")
    by_id = {}
    for case in cases:
        if not nonempty(case.get("id")) or case.get("id") in by_id:
            issue(errors, "learning-case-id", label, "Case IDs must be unique and non-empty.")
        else:
            by_id[case["id"]] = case
        if case.get("role") not in {"guided", "transfer"}:
            issue(errors, "learning-case-role", label, str(case.get("role")))
        required_fields(case, ("expectedOutcome",), errors, label)
        for field in ("materialLocation", "taskLocation", "feedbackLocation", "evidenceLocation"):
            locator(text, case.get(field), errors, f"{label}.{field}")
    for case in cases:
        if case.get("role") != "transfer":
            continue
        original = by_id.get(case.get("comparedWith")) if nonempty(case.get("comparedWith")) else None
        required_fields(case, ("changedCondition", "transferRationale"), errors, label)
        if not original or original.get("role") != "guided":
            issue(errors, "learning-transfer-source", label, "A transfer case must reference a guided case.")
        if case.get("expectedChange") not in {"different", "same"}:
            issue(errors, "learning-transfer-change", label, "Declare whether the expected outcome changes or stays the same, and why.")
        elif original and case.get("expectedChange") == "different" and case.get("expectedOutcome") == original.get("expectedOutcome"):
            issue(errors, "learning-transfer-answer", label, "Changed evidence was declared to change the outcome, but the expected answer is unchanged.")
        elif original and case.get("expectedChange") == "same" and case.get("expectedOutcome") != original.get("expectedOutcome"):
            issue(errors, "learning-transfer-answer", label, "The declared invariant outcome differs from the guided case.")
        if original and case.get("materialLocation") == original.get("materialLocation"):
            issue(errors, "learning-transfer-material", label, "Locate the changed material separately.")

    if item.get("mode") == "interactive":
        interaction = item.get("interaction")
        if not isinstance(interaction, dict):
            issue(errors, "learning-interaction", label, "Missing interaction design and implementation.")
            interaction = {}
        for value in strings(interaction.get("assetPaths"), errors, label):
            file_in_root(root, value, errors, label)
        for field in ("entryLocation", "fallbackLocation", "draftPolicyLocation"):
            locator(text, interaction.get(field), errors, f"{label}.{field}")
        if interaction.get("feedbackMode") not in {"rule-based", "rubric", "human-review"}:
            issue(errors, "learning-feedback-mode", label, "Choose rule-based, rubric, or human-review; field completeness is not semantic feedback.")
        if interaction.get("resultMode") not in {"scripted", "live"}:
            issue(errors, "learning-result-mode", label, "Declare scripted or live results.")
        if interaction.get("resultMode") == "scripted":
            locator(text, interaction.get("simulationLabelLocation"), errors, f"{label}.simulationLabelLocation")
        if interaction.get("skipAllowed") is not True:
            contract_path = root / "_kb-control/project-contract.yaml"
            contract_text = contract_path.read_text(encoding="utf-8") if contract_path.is_file() else ""
            posture = re.search(r"(?m)^product_posture:\s*['\"]?reading_manual\b", contract_text)
            optional_practice = re.search(r"(?m)^exercise_policy:\s*['\"]?optional_after_reading\b", contract_text)
            if posture or optional_practice:
                issue(errors, "learning-reading-gate", label, "Optional/reader-led practice must allow skipping.")
        hints = records(interaction.get("hints", []), errors, f"{label}.hints")
        if not hints:
            issue(errors, "learning-hints", label, "Provide an optional hint or worked demonstration.")
        for hint in hints:
            if hint.get("level") not in {"attention", "criterion", "worked-example"}:
                issue(errors, "learning-hint-level", label, str(hint.get("level")))
            locator(text, hint.get("location"), errors, label)
        if not {"guided", "transfer"}.issubset({case.get("role") for case in cases}):
            issue(errors, "learning-case-coverage", label, "A teaching interaction needs guided and transfer cases.")
        if phase in {"app", "qc"}:
            app = read_object(root / "_kb-control/app-validation.json", errors)
            checks = records(app.get("learningActivities", []), errors, "app.learningActivities")
            checked = next((check for check in checks if check.get("id") == label), {})
            if checked.get("status") != "pass":
                issue(errors, "learning-browser-status", label, "No passed browser check for this activity.")
            widths = checked.get("viewportWidths", [])
            widths = [value for value in widths if isinstance(value, (int, float)) and not isinstance(value, bool)] if isinstance(widths, list) else []
            if not any(0 < value <= 480 for value in widths) or not any(value >= 1000 for value in widths):
                issue(errors, "learning-browser-widths", label, "Check desktop and mobile reading.")
            behaviors = strings(checked.get("behaviors", []), errors, label)
            if not {"feedback", "retry", "transfer", "fallback", "keyboard", "mobile-reading"}.issubset(behaviors):
                issue(errors, "learning-browser-behaviors", label, "Check feedback, retry, transfer, fallback, keyboard, and mobile-reading.")
            for value in strings(checked.get("evidencePaths"), errors, label):
                file_in_root(root, value, errors, label)
    review_evidence(root, item.get("review"), errors, label)


def check_learning(root, *, phase="content", required_ids=None, page_paths=None):
    root = Path(root).resolve()
    errors = []
    contracts = activity_contracts(root, errors)
    scoped_pages = set(page_paths) if page_paths is not None else None
    model = read_object(root / "_kb-control/knowledge-model.json", errors, optional=True)
    owners = {unit.get("id"): unit.get("canonicalOwner") for unit in records(model.get("units", []), errors, "units") if nonempty(unit.get("id"))}
    required = set(required_ids) if required_ids is not None else {
        key for key, unit in contracts.items() if scoped_pages is None or owners.get(unit) in scoped_pages
    }
    manifest_path = root / "_kb-control/learning-activities.json"
    manifest = read_object(manifest_path, errors, optional=not required)
    if manifest and manifest.get("schemaVersion") != 1:
        issue(errors, "learning-schema", manifest_path, "schemaVersion must be 1.")
    items = records(manifest.get("items", []), errors, "items")
    valid_items = []
    for item in items:
        if not all(nonempty(item.get(key)) for key in ("id", "unitId", "pagePath")):
            issue(errors, "learning-activity-id", manifest_path, "Activity id, unitId, and pagePath must be non-empty strings.")
        else:
            valid_items.append(item)
    items = valid_items
    ids = [item.get("id") for item in items if nonempty(item.get("id"))]
    for activity_id in set(ids):
        if ids.count(activity_id) > 1:
            issue(errors, "duplicate-learning-activity", activity_id, "Each activity ID must be unique.")
    for activity_id in sorted(required - set(ids)):
        issue(errors, "missing-learning-activity", activity_id, "A declared lesson activity is missing.")
    selected = [item for item in items if (
        item.get("id") in required_ids if required_ids is not None else
        scoped_pages is None or item.get("pagePath") in scoped_pages or item.get("id") in required
    )]
    if selected and manifest.get("status") != "pass" and required_ids is None and scoped_pages is None:
        issue(errors, "learning-manifest-status", manifest_path, "Complete and review the selected activities before passing.")
    for item in selected:
        expected_unit = contracts.get(item.get("id"))
        if expected_unit is None:
            issue(errors, "learning-undeclared-activity", item["id"], "Declare the activity ID on its owning lesson in learning-design.json.")
        if expected_unit is not None and expected_unit != item.get("unitId"):
            issue(errors, "learning-unit-mismatch", item.get("id"), str(expected_unit))
        if owners.get(item.get("unitId")) != item.get("pagePath"):
            issue(errors, "learning-page-owner", item.get("id"), "Activity must live on its unit's canonical page.")
        validate_activity(root, item, errors, phase=phase)
    design = read_object(root / "_kb-control/learning-design.json", errors, optional=True)
    selected_ids = {item["id"] for item in selected}
    for lesson in records(design.get("lessons", []), errors, "lessons"):
        task = lesson.get("learningTaskType")
        lesson_ids = strings(lesson.get("activityIds", []), errors, "activityIds", required=False)
        relevant = set(lesson_ids) & (required | selected_ids)
        if task in {"operation", "troubleshooting"} and relevant:
            if not any(item["id"] in relevant and item.get("kind") == task for item in selected):
                issue(errors, "learning-task-activity-mismatch", lesson.get("unitId"), "The declared operational activity must match the lesson's task type, not just a judgment or concept activity.")
    coverage = read_object(root / "_kb-control/content-coverage.json", errors, optional=True)
    if coverage:
        pages = records(coverage.get("pages", []), errors, "pages")
        for item in selected:
            page = next((page for page in pages if page.get("path") == item["pagePath"]), {})
            if item["id"] not in strings(page.get("activityIds", []), errors, item["pagePath"], required=False):
                issue(errors, "learning-page-coverage", item["pagePath"], "Record the activity ID in its page's content coverage.")
    return {
        "schemaVersion": 1, "status": "fail" if errors else "pass",
        "claim": "structural-and-evidence-check-only", "phase": phase,
        "validatedIds": [item.get("id") for item in selected],
        "interactiveIds": [item.get("id") for item in selected if item.get("mode") == "interactive"],
        "errors": errors, "warnings": [],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--phase", choices=["content", "app", "qc"], default="content")
    parser.add_argument("--id", action="append", dest="ids")
    parser.add_argument("--page", action="append", dest="pages")
    parser.add_argument("--output")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        parser.error("root must be an existing directory")
    report = check_learning(root, phase=args.phase, required_ids=args.ids, page_paths=args.pages)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = (root / args.output).resolve()
        if not output.is_relative_to(root):
            parser.error("output must be inside the knowledge-base root")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    raise SystemExit(bool(report["errors"]))


if __name__ == "__main__":
    main()
