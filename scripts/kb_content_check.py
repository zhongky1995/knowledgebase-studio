#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

from kb_evidence import check_comparisons, check_measurement
from kb_explanation import example_fields, validate_page_comprehension
from kb_work_comparison import validate_work_comparison
from kb_reader_probe import JOBS


CONTENT_ROLES = {"main-path", "reference", "rule", "tool", "case"}
PAGE_TYPES = CONTENT_ROLES | {"navigation"}
EVIDENCE_STATUSES = {"verified", "internal-default", "inference", "unresolved"}
FIDELITY_STATUSES = {"preserved", "intentionally-changed", "unresolved"}
LEARNING_POSTURES = {"reading_manual", "guided_learning", "practice_workbench", "hybrid"}


def issue(collection, kind, path, detail):
    collection.append({"kind": kind, "path": str(path), "detail": detail})


def read_json(path, errors, kind):
    if not path.exists():
        issue(errors, "missing-contract", path, f"Missing {kind} contract.")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        issue(errors, "invalid-json", path, str(error))
        return {}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def contract_posture(root):
    path = root / "_kb-control" / "project-contract.yaml"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"(?m)^product_posture:\s*(.*?)\s*$", text)
    return match.group(1).strip().strip("\"'") if match else None


def duplicate_values(items, key):
    seen = {}
    duplicates = []
    for index, item in enumerate(items):
        value = item.get(key)
        if not nonempty(value):
            continue
        normalized = " ".join(value.lower().split())
        if normalized in seen:
            duplicates.append((value, seen[normalized], index))
        else:
            seen[normalized] = index
    return duplicates


def dependency_cycles(units_by_id):
    cycles = []
    state = {}
    stack = []

    def visit(unit_id):
        if state.get(unit_id) == 1:
            start = stack.index(unit_id) if unit_id in stack else 0
            cycles.append(stack[start:] + [unit_id])
            return
        if state.get(unit_id) == 2:
            return
        state[unit_id] = 1
        stack.append(unit_id)
        for dependency in units_by_id[unit_id].get("dependencies") or []:
            if dependency in units_by_id:
                visit(dependency)
        stack.pop()
        state[unit_id] = 2

    for unit_id in units_by_id:
        visit(unit_id)
    return cycles


def validate(root, source_path, model_path, coverage_path, phase="content", page_paths=None, review_page_paths=None):
    errors = []
    warnings = []
    sources_document = read_json(source_path, errors, "source-understanding")
    model_document = read_json(model_path, errors, "knowledge-model") if phase in {"architecture", "content"} else {}
    coverage_document = read_json(coverage_path, errors, "content-coverage") if phase == "content" else {}

    sources = sources_document.get("sources") or []
    units = model_document.get("units") or []
    progressions = model_document.get("progressions") or []
    pages = coverage_document.get("pages") or []
    if page_paths is not None and phase == "content":
        requested = set(page_paths)
        missing = requested - {page.get("path") for page in pages}
        for value in sorted(missing):
            issue(errors, "scoped-page-coverage", coverage_path, f"Update content coverage for changed page: {value}")
        pages = [page for page in pages if page.get("path") in requested]
        selected_ids = {value for page in pages for value in page.get("knowledgeUnitIds", [])}
        while True:
            dependencies = {value for unit in units if unit.get("id") in selected_ids for value in unit.get("dependencies", [])}
            if dependencies.issubset(selected_ids):
                break
            selected_ids.update(dependencies)
        units = [unit for unit in units if unit.get("id") in selected_ids]
        source_ids = {str(value).split("#")[0] for unit in units for value in unit.get("sourceRefs", [])}
        sources = [source for source in sources if source.get("id") in source_ids]
        progressions = [dict(item, unitIds=[value for value in item.get("unitIds", []) if value in selected_ids]) for item in progressions]
        progressions = [item for item in progressions if item["unitIds"]]
    posture = contract_posture(root)
    learning_design = {}
    if phase == "content" and posture in LEARNING_POSTURES:
        learning_design = read_json(root / "_kb-control" / "learning-design.json", errors, "learning-design")
    example_required_units = {
        item.get("unitId")
        for item in learning_design.get("lessons") or []
        if item.get("workedExampleRequired") is True
    }
    if not sources:
        issue(errors, "empty-source-understanding", source_path, "At least one canonical, supporting, corpus, or internal source must be understood.")
    if phase in {"architecture", "content"} and not units:
        issue(errors, "empty-knowledge-model", model_path, "At least one knowledge unit is required.")
    if phase == "content" and not pages:
        issue(errors, "empty-content-coverage", coverage_path, "At least one target page is required.")

    sources_by_id = {}
    claims_by_source = {}
    measurements = {}
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        source_id = source.get("id")
        if not nonempty(source_id):
            issue(errors, "source-field", label, "Missing source id.")
            continue
        if source_id in sources_by_id:
            issue(errors, "duplicate-source-id", label, source_id)
            continue
        sources_by_id[source_id] = source
        for field in ("path", "role", "authority", "summary"):
            if not nonempty(source.get(field)):
                issue(errors, "source-field", label, f"Missing {field}.")
        if source.get("role") not in {"canonical", "supporting", "existing-corpus", "internal-standard"}:
            issue(errors, "source-role", label, f"Unsupported role: {source.get('role')}")
        if source.get("authority") not in {"primary", "secondary", "internal", "unknown"}:
            issue(errors, "source-authority", label, f"Unsupported authority: {source.get('authority')}")
        claims = source.get("coreClaims") or []
        if not claims:
            issue(errors, "source-claims", label, "Source has no coreClaims.")
        claim_ids = set()
        for claim_index, claim in enumerate(claims):
            claim_label = f"{label}.coreClaims[{claim_index}]"
            claim_id = claim.get("id")
            if not nonempty(claim_id) or not nonempty(claim.get("statement")):
                issue(errors, "source-claim-field", claim_label, "Claims require id and statement.")
            elif claim_id in claim_ids:
                issue(errors, "duplicate-claim-id", claim_label, claim_id)
            else:
                claim_ids.add(claim_id)
            if not nonempty(claim.get("evidence")):
                issue(warnings, "claim-evidence-gap", claim_label, "Claim evidence or a locatable basis is missing.")
            if claim.get("confidence") not in {"high", "medium", "low"}:
                issue(errors, "claim-confidence", claim_label, "Confidence must be high, medium, or low.")
            if "measurement" in claim:
                check_measurement(claim["measurement"], errors, warnings, claim_label)
                if nonempty(claim_id):
                    measurements[f"{source_id}#{claim_id}"] = claim["measurement"]
        claims_by_source[source_id] = claim_ids

    units_by_id = {}
    for index, unit in enumerate(units):
        label = f"units[{index}]"
        unit_id = unit.get("id")
        if not nonempty(unit_id):
            issue(errors, "unit-field", label, "Missing unit id.")
            continue
        if unit_id in units_by_id:
            issue(errors, "duplicate-unit-id", label, unit_id)
            continue
        units_by_id[unit_id] = unit
        for field in ("question", "answer", "readerChange", "mechanism", "canonicalOwner"):
            if not nonempty(unit.get(field)):
                issue(errors, "unit-field", label, f"Missing {field}.")
        if unit.get("role") not in CONTENT_ROLES:
            issue(errors, "unit-role", label, f"Unsupported role: {unit.get('role')}")
        refs = unit.get("sourceRefs") or []
        if not refs:
            issue(errors, "unit-source-gap", label, "Every knowledge unit must trace to at least one understood source or internal standard.")
        for ref in refs:
            source_id, separator, claim_id = str(ref).partition("#")
            if source_id not in sources_by_id:
                issue(errors, "unknown-source-ref", label, str(ref))
            elif separator and claim_id not in claims_by_source.get(source_id, set()):
                issue(errors, "unknown-claim-ref", label, str(ref))
        if unit.get("role") in {"main-path", "rule", "tool"} and not (unit.get("boundaries") or []):
            issue(errors, "unit-boundary-gap", label, "Main-path, rule, and tool units require at least one boundary or misuse condition.")
        check_comparisons(unit, measurements, errors, label)

    for unit_id, unit in units_by_id.items():
        for dependency in unit.get("dependencies") or []:
            if dependency not in units_by_id:
                issue(errors, "unknown-dependency", unit_id, str(dependency))
    for cycle in dependency_cycles(units_by_id):
        issue(errors, "dependency-cycle", "knowledge-model", " -> ".join(cycle))

    if phase in {"architecture", "content"}:
        learning_product = posture in LEARNING_POSTURES
        if learning_product and not progressions and any(unit.get("role") == "main-path" for unit in units):
            issue(errors, "empty-learning-progression", model_path, "Learning products require an explicit main-path progression.")
        progression_ids = set()
        flattened = []
        for index, progression in enumerate(progressions):
            label = f"progressions[{index}]"
            progression_id = progression.get("id")
            if not nonempty(progression_id):
                issue(errors, "progression-field", label, "Missing id.")
            elif progression_id in progression_ids:
                issue(errors, "duplicate-progression-id", label, progression_id)
            else:
                progression_ids.add(progression_id)
            for field in ("audience", "logic"):
                if not nonempty(progression.get(field)):
                    issue(errors, "progression-field", label, f"Missing {field}.")
            unit_ids = progression.get("unitIds") or []
            if not unit_ids:
                issue(errors, "empty-progression", label, "Progression has no knowledge units.")
            for unit_id in unit_ids:
                if unit_id not in units_by_id:
                    issue(errors, "unknown-progression-unit", label, str(unit_id))
                flattened.append(unit_id)

        # Routes can reuse canonical units; only repetition inside a route is an error.
        for progression in progressions:
            unit_ids = progression.get("unitIds") or []
            for value in sorted({value for value in unit_ids if unit_ids.count(value) > 1}):
                issue(errors, "duplicate-progression-unit", progression.get("id", "knowledge-model"), value)
            local_order = {value: index for index, value in enumerate(unit_ids)}
            for unit_id in unit_ids:
                for dependency in units_by_id.get(unit_id, {}).get("dependencies") or []:
                    if dependency in local_order and local_order[dependency] >= local_order[unit_id]:
                        issue(errors, "progression-order", unit_id, f"Dependency {dependency} must appear before {unit_id} in {progression.get('id')}.")
        if learning_product:
            main_ids = {unit_id for unit_id, unit in units_by_id.items() if unit.get("role") == "main-path"}
            missing = sorted(main_ids - set(flattened))
            if missing:
                issue(errors, "progression-coverage-gap", "knowledge-model", ", ".join(missing))
            # Preserve the earlier core -> advanced ordering check for split routes.
            # Later reuse must not overwrite a unit's first introduction.
            order = {}
            for index, unit_id in enumerate(flattened):
                order.setdefault(unit_id, index)
            for unit_id in main_ids:
                if unit_id not in order:
                    continue
                for dependency in units_by_id[unit_id].get("dependencies") or []:
                    if dependency in main_ids and dependency in order and order[dependency] >= order[unit_id]:
                        issue(errors, "progression-order", unit_id, f"Dependency {dependency} must appear before {unit_id}.")

    pages_by_path = {}
    comprehension_required, comprehension_recorded, comprehension_valid = [], [], []
    promise_receipts, legacy_receipts = [], []
    for index, page in enumerate(pages):
        label = f"pages[{index}]"
        value = page.get("path")
        if not nonempty(value):
            issue(errors, "page-field", label, "Missing path.")
            continue
        if value in pages_by_path:
            issue(errors, "duplicate-page-path", label, value)
            continue
        pages_by_path[value] = page
        if page.get("pageType") not in PAGE_TYPES:
            issue(errors, "page-type", label, f"Unsupported pageType: {page.get('pageType')}")
        for field in ("primaryQuestion", "readerChange", "distinctiveValue"):
            if not nonempty(page.get(field)):
                issue(errors, "page-field", label, f"Missing {field}.")
        if "readerJob" in page and (not isinstance(page["readerJob"], str) or page["readerJob"] not in JOBS):
            issue(errors, "page-reader-job", label, "Choose understand, perform, judge or retrieve from the page's actual promise.")
        candidate = (root / value).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            issue(errors, "escaping-page-path", label, value)
            continue
        else:
            if not candidate.is_file():
                issue(errors, "missing-page", label, value)
        if phase == "content":
            validate_work_comparison(root, page, errors, measurements)
            novice_page = (learning_design.get("explanationProfile") == "novice_mental_model"
                           and page.get("pageType") in {"main-path", "case"})
            if novice_page:
                comprehension_required.append(value)
            if "comprehensionReview" in page:
                comprehension_recorded.append(value)
                receipt_errors = []
                validate_page_comprehension(root, page, receipt_errors, warnings,
                                            strict_shortcuts=review_page_paths is None or value in review_page_paths)
                errors.extend(receipt_errors)
                if not receipt_errors:
                    comprehension_valid.append(value)
                    if page["comprehensionReview"].get("schemaVersion", 1) == 2:
                        promise_receipts.append(value)
                    else:
                        legacy_receipts.append(value)
                        issue(warnings, "page-comprehension-legacy-promises", value,
                              "This schema 1 receipt remains valid historical evidence, but does not record version 2 promise coverage. Reread before renewing a semantic review.")
            elif novice_page:
                issue(warnings, "page-comprehension-missing", value,
                      "Legacy coverage remains structurally valid, but no page comprehension receipt establishes editorial review. Add one when authoring or revising this explanation.")
        unit_ids = page.get("knowledgeUnitIds") or []
        if page.get("pageType") != "navigation" and not unit_ids:
            issue(errors, "page-unit-gap", label, "Reader-facing content pages require at least one knowledge unit.")
        for unit_id in unit_ids:
            if unit_id not in units_by_id:
                issue(errors, "unknown-page-unit", label, str(unit_id))
        essential = page.get("essentialPoints") or []
        if page.get("pageType") != "navigation" and not essential:
            issue(errors, "essential-point-gap", label, "Content pages require preserved essential points.")
        fidelity = page.get("fidelityChecks") or []
        fidelity_by_point = {item.get("point"): item for item in fidelity if isinstance(item, dict)}
        for point in essential:
            check = fidelity_by_point.get(point)
            if not check:
                issue(errors, "missing-fidelity-check", label, str(point))
                continue
            if check.get("status") not in FIDELITY_STATUSES:
                issue(errors, "fidelity-status", label, f"{point}: {check.get('status')}")
            if check.get("status") == "preserved" and not nonempty(check.get("location")):
                issue(errors, "fidelity-location", label, f"Preserved point has no output location: {point}")
            if check.get("status") == "preserved" and nonempty(check.get("location")):
                try:
                    page_text = candidate.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    page_text = ""
                if check.get("location") not in page_text:
                    issue(errors, "fidelity-location-not-found", label, f"Locator is not present in the output page: {check.get('location')}")
        if page.get("evidenceStatus") not in EVIDENCE_STATUSES:
            issue(errors, "evidence-status", label, f"Unsupported evidenceStatus: {page.get('evidenceStatus')}")
        if page.get("evidenceStatus") == "verified":
            referenced = {str(ref) for unit_id in unit_ids for ref in (units_by_id.get(unit_id, {}).get("sourceRefs") or [])}
            for ref, measurement in measurements.items():
                if ref in referenced or ref.split("#")[0] in referenced:
                    review = measurement.get("verification") if isinstance(measurement, dict) else None
                    if isinstance(review, dict) and review.get("status") == "unverified":
                        issue(errors, "page-unverified-measurement", label, f"Page marked verified relies on an unverified value: {ref}")
        if phase == "content" and posture in LEARNING_POSTURES and page.get("pageType") == "main-path":
            minutes = page.get("estimatedReadingMinutes")
            if not isinstance(minutes, (int, float)) or minutes <= 0:
                issue(errors, "page-reading-time", label, "Learning main-path pages require a positive estimatedReadingMinutes value.")
            practice = page.get("practice") or {}
            if practice.get("policy") not in {"optional_after_reading", "guided", "required", "none"}:
                issue(errors, "page-practice-policy", label, "Learning pages require an explicit practice policy.")
            if not nonempty(practice.get("output")) or not nonempty(practice.get("feedback")):
                issue(errors, "page-practice-contract", label, "Practice policy requires an observable output statement and feedback route, including when policy is none.")
        if phase == "content" and (example_required_units & set(unit_ids) or (page.get("workedExample") or {}).get("required") is True):
            example = page.get("workedExample") or {}
            if example.get("required") is not True:
                issue(errors, "worked-example-required", label, "The learning design requires a worked example on this page, including cases and labs.")
            modern = learning_design.get("schemaVersion") == 3 or coverage_document.get("schemaVersion") == 2
            fields = ["kind"] + [f"{field}Location" for field in example_fields(example, errors, label, modern=modern)]
            for lesson in learning_design.get("lessons") or []:
                if lesson.get("unitId") in unit_ids and lesson.get("workedExampleRequired"):
                    expected = (lesson.get("exampleContract") or {}).get("pattern", "judgment_revision")
                    if example.get("pattern", "judgment_revision") != expected:
                        issue(errors, "worked-example-pattern-mismatch", label, "Page example pattern differs from its learning contract.")
            if example.get("kind") not in {"real", "anonymized", "composite", "fictional"}:
                issue(errors, "worked-example-kind", label, "Case provenance must be explicit.")
            for field in fields:
                if not nonempty(example.get(field)):
                    issue(errors, "worked-example-field", label, f"Missing {field}.")
                elif field.endswith("Location") and candidate.is_file():
                    page_text = candidate.read_text(encoding="utf-8", errors="replace")
                    if example[field] not in page_text:
                        issue(errors, "worked-example-location-not-found", label, f"{field}: {example[field]}")

    if phase == "content":
        content_pages = [page for page in pages if page.get("pageType") != "navigation"]
        for field, kind in (("primaryQuestion", "duplicate-primary-question"), ("distinctiveValue", "duplicate-distinctive-value")):
            for value, first, second in duplicate_values(content_pages, field):
                issue(errors, kind, f"pages[{first}],pages[{second}]", value)

        for unit_id, unit in units_by_id.items():
            owner = unit.get("canonicalOwner")
            if page_paths is not None and owner not in set(page_paths):
                continue
            page = pages_by_path.get(owner)
            if not page:
                issue(errors, "missing-canonical-owner", unit_id, str(owner))
            elif unit_id not in (page.get("knowledgeUnitIds") or []):
                issue(errors, "owner-coverage-gap", unit_id, f"Canonical owner {owner} does not declare this unit.")

    return {
        "status": "fail" if errors else "pass",
        "validationKind": "structural_integrity",
        "comprehensionEvidence": {
            "status": ("incomplete" if set(comprehension_required) - set(comprehension_valid)
                       or set(comprehension_recorded) - set(comprehension_valid)
                       else "receipts_valid" if comprehension_recorded else "not_requested"),
            "requiredPages": sorted(comprehension_required),
            "recordedPages": sorted(comprehension_recorded),
            "validReceiptPages": sorted(comprehension_valid),
            "missingPages": sorted(set(comprehension_required) - set(comprehension_recorded)),
            "promiseCoverage": {
                "status": ("legacy" if legacy_receipts else "recorded" if promise_receipts else "not_recorded"),
                "version2Pages": sorted(promise_receipts),
                "legacyPages": sorted(legacy_receipts),
                "limitation": "Declared promise coverage only. The checker cannot discover omitted promises or judge whether the basis explains the claim.",
            },
            "limitation": "Receipt integrity only; editorial reasoning and actual reader understanding require separate review.",
        },
        "phase": phase,
        "scope": "selected-pages-and-prerequisites" if page_paths is not None else "full",
        "selectedPages": sorted(page_paths) if page_paths is not None else None,
        "root": str(root),
        "contracts": {
            "sourceUnderstanding": str(source_path),
            "knowledgeModel": str(model_path),
            "contentCoverage": str(coverage_path),
        },
        "stats": {
            "sources": len(sources_by_id),
            "claims": sum(len(value) for value in claims_by_source.values()),
            "knowledgeUnits": len(units_by_id),
            "progressions": len(progressions),
            "pages": len(pages_by_path),
            "fidelityChecks": sum(len(page.get("fidelityChecks") or []) for page in pages),
        },
        "errors": errors,
        "warnings": warnings,
    }


def check_manuscript(root, page_paths):
    """Check actual scoped content without requiring duplicate author self-reviews.

    This does not establish the legacy model/coverage contract or renew an old
    comprehension receipt. Existing declared calculations remain enforceable.
    """
    from kb_audit import audit
    root = Path(root).resolve()
    errors, warnings = [], []
    report = audit(root, page_paths=page_paths)
    errors.extend(report['errors'])
    warnings.extend(report['warnings'])
    control = root / '_kb-control'
    coverage = read_json(control / 'content-coverage.json', errors, 'coverage') if (control / 'content-coverage.json').exists() else {}
    sources = read_json(control / 'source-understanding.json', errors, 'sources') if (control / 'source-understanding.json').exists() else {}
    model = read_json(control / 'knowledge-model.json', errors, 'knowledge model') if (control / 'knowledge-model.json').exists() else {}
    units = model.get('units', [])
    selected = {u.get('id') for u in units if u.get('canonicalOwner') in page_paths}
    while True:
        dependencies = {v for u in units if u.get('id') in selected for v in u.get('dependencies', [])}
        if dependencies.issubset(selected):
            break
        selected.update(dependencies)
    source_ids = {s.get('id'): {c.get('id') for c in s.get('coreClaims', [])} for s in sources.get('sources', [])}
    referenced = {str(ref) for u in units if u.get('id') in selected for ref in u.get('sourceRefs', [])}
    for ref in referenced:
        source_id, separator, claim_id = ref.partition('#')
        if source_id not in source_ids or (separator and claim_id not in source_ids[source_id]):
            issue(errors, 'unknown-source-ref', ref, 'An existing declared source/claim must still resolve; a scoped editorial judgment cannot replace it.')
    measurements = {f'{s.get("id")}#{c.get("id")}': c['measurement']
                    for s in sources.get('sources', []) for c in s.get('coreClaims', []) if 'measurement' in c}
    for ref, measurement in measurements.items():
        if ref in referenced or ref.split('#')[0] in referenced:
            check_measurement(measurement, errors, warnings, ref)
    for page in coverage.get('pages', []):
        if page.get('path') not in page_paths:
            continue
        validate_work_comparison(root, page, errors, measurements)
        if 'comprehensionReview' in page:
            issue(warnings, 'historical-self-review', page['path'],
                  'Author-filled comprehension evidence is retained as history, not renewed or claimed by this scoped editorial check.')
    return {'status': 'fail' if errors else 'pass', 'validationKind': 'scoped-manuscript-integrity',
            'comprehensionEvidence': {'status': 'not_assessed', 'missingPages': [], 'requiredPages': [],
                                      'limitation': 'Current editorial judgment is in the scoped decision or actual execution result, not a per-page self-certificate.'},
            'errors': errors, 'warnings': warnings}


def main():
    parser = argparse.ArgumentParser(description="Validate source understanding, knowledge units, and page-level fidelity coverage.")
    parser.add_argument("root", help="Knowledge-base root")
    parser.add_argument("--source-understanding", default="_kb-control/source-understanding.json")
    parser.add_argument("--knowledge-model", default="_kb-control/knowledge-model.json")
    parser.add_argument("--content-coverage", default="_kb-control/content-coverage.json")
    parser.add_argument("--phase", choices=["audit", "architecture", "content"], default="content")
    parser.add_argument("--output")
    parser.add_argument("--page", action="append", dest="pages", help="Check a changed page and its knowledge prerequisites; repeatable")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "message": f"Knowledge-base root is not a directory: {root}"}, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    def contract_path(value):
        path = Path(value).expanduser()
        return path.resolve() if path.is_absolute() else (root / path).resolve()

    report = validate(
        root,
        contract_path(args.source_understanding),
        contract_path(args.knowledge_model),
        contract_path(args.content_coverage),
        args.phase,
        args.pages,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output = contract_path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    raise SystemExit(1 if report["errors"] else 0)


if __name__ == "__main__":
    main()
