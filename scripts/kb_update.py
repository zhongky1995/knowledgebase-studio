#!/usr/bin/env python3
"""Plan and verify a scoped update without changing the full workflow verdict."""

import argparse
import hashlib
import json
from pathlib import Path

from kb_content_check import validate as check_content, check_manuscript
from kb_explanation import require_promise_review
from kb_reader_probe import reader_probe_paths
from kb_execution import evidence_paths as execution_paths, required_pages as execution_required_pages, gate as execution_gate, batches as execution_batches, STATE as EXECUTION_STATE
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


def scoped_contracts(root, pages):
    """Project existing records onto the selected content; no parallel state store."""
    documents = {}
    for name in CONTRACTS:
        path = root / '_kb-control' / name
        if path.suffix == '.json' and path.exists():
            value = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(value, dict):
                raise ValueError(f'Expected an object: {path}')
            documents[name] = value
    units = documents.get('knowledge-model.json', {}).get('units', [])
    ids = {u.get('id') for u in units if u.get('canonicalOwner') in pages}
    while True:
        deps = {d for u in units if u.get('id') in ids for d in u.get('dependencies', [])}
        if deps.issubset(ids):
            break
        ids.update(deps)
    references = {str(r).split('#')[0] for u in units if u.get('id') in ids for r in u.get('sourceRefs', [])}
    projected = {}
    for name, document in documents.items():
        value = {k: v for k, v in document.items() if k not in {'status', 'updatedAt'}}
        if name == 'knowledge-model.json':
            value['units'] = [u for u in units if u.get('id') in ids]
            value['progressions'] = [dict(p, unitIds=[u for u in p.get('unitIds', []) if u in ids]) for p in value.get('progressions', []) if set(p.get('unitIds', [])) & ids]
        elif name == 'content-coverage.json':
            value['pages'] = [{k: v for k, v in p.items() if k != 'comprehensionReview'} for p in value.get('pages', []) if p.get('path') in pages]
        elif name == 'learning-design.json':
            value['lessons'] = [p for p in value.get('lessons', []) if p.get('unitId') in ids]
        elif name == 'source-understanding.json' and units:
            value['sources'] = [s for s in value.get('sources', []) if s.get('id') in references]
        elif name in {'learning-activities.json', 'visual-explanations.json'}:
            value['items'] = [p for p in value.get('items', []) if p.get('pagePath') in pages]
        elif name == 'app-validation.json':
            value['learningActivities'] = [p for p in value.get('learningActivities', []) if set(p.get('pagePaths', [])) & set(pages)]
        projected[name] = value
    return projected


def plan_update(root, changed_paths, *, pages=(), delivery_paths=(), release_paths=(), schema_version=3, change_kind="content", context_paths=()):
    root = Path(root).resolve()
    if schema_version not in {1, 2, 3}:
        raise ValueError('Unsupported scoped plan version.')
    if change_kind not in {"content", "rendering"}:
        raise ValueError("change_kind must be content or rendering")
    changed = sorted({normalize(root, value) for value in changed_paths})
    if not changed:
        raise ValueError("At least one changed path is required.")
    coverage = read_json_if_possible(root / "_kb-control/content-coverage.json")
    public_pages = [page.get("path") for page in coverage.get("pages", []) if isinstance(page, dict) and page.get("path")]
    if schema_version == 3:
        from kb_audit import scan_files, load_config
        public_pages = sorted(set(public_pages) | {str(p.relative_to(root)) for p in scan_files(root, load_config(root))[0]})
    requested = {normalize(root, value) for value in pages}
    app = read_json_if_possible(root / "_kb-control/app-validation.json")
    deliveries = {normalize(root, value) for value in delivery_paths}
    deliveries.update(normalize(root, value) for value in app.get("appPaths", []) if isinstance(value, str) and (root / value).exists())
    releases = {normalize(root, value) for value in release_paths}
    affected = set(requested)
    affected.update(value for value in changed if value.endswith(".md") and not value.startswith("_")
                    and (schema_version == 1 or not any(value == output or value.startswith(output + "/") for output in deliveries | releases)))
    reviewed = set(affected)
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
    # Media owns meaning even when a shared renderer changes in the same update.
    visual_assets = {}
    if schema_version >= 2:
        visuals = read_json_if_possible(root / "_kb-control/visual-explanations.json")
        for item in visuals.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("pagePath"), str):
                for field in ("assetPath", "fallbackPath"):
                    if item.get(field):
                        visual_assets.setdefault(normalize(root, item[field]), set()).add(normalize(root, item["pagePath"]))
    for value in changed:
        for asset, owners in visual_assets.items():
            if asset == value or asset.startswith(value + "/"):
                affected.update(owners)
                reviewed.update(owners)
    shared_app_changed = False
    for value in changed:
        owned_pages = {page for asset, owners in activity_assets.items() if asset == value or asset.startswith(value + "/") for page in owners}
        affected.update(owned_pages)
        reviewed.update(owned_pages)
        candidate = root / value
        files = candidate.rglob("*") if candidate.is_dir() else [candidate]
        for changed_file in files:
            if changed_file.suffix in {".js", ".mjs", ".css", ".html", ".ts", ".tsx", ".jsx", ".vue", ".svelte"}:
                if normalize(root, str(changed_file)) not in activity_assets:
                    shared_app_changed = True
    for page in public_pages:
        candidate = root / normalize(root, page)
        if (structure_changed and (schema_version < 3 or not requested)) or unscoped_control or shared_app_changed or any(page == value or page.startswith(value + "/") for value in changed):
            affected.add(page)
        elif candidate.is_file():
            text = candidate.read_text(encoding="utf-8", errors="replace")
            if any(Path(value).name in text for value in changed):
                affected.add(page)
                reviewed.add(page)
    if not requested and (structure_changed or unscoped_control or (shared_app_changed and change_kind != "rendering")):
        reviewed.update(public_pages)
    if schema_version == 3 and change_kind == 'content':
        model_units = read_json_if_possible(root / '_kb-control/knowledge-model.json').get('units', [])
        # A changed prerequisite affects its actual consumers, not every chapter.
        affected_ids = {u.get('id') for u in model_units if u.get('canonicalOwner') in reviewed}
        while True:
            dependents = {u.get('id') for u in model_units if set(u.get('dependencies', [])) & affected_ids}
            if dependents.issubset(affected_ids):
                break
            affected_ids.update(dependents)
        consumers = {u['canonicalOwner'] for u in model_units if u.get('id') in affected_ids and isinstance(u.get('canonicalOwner'), str)}
        affected.update(consumers)
        reviewed.update(consumers)
    if not affected:
        raise ValueError("No affected pages found; provide --page for the learner-facing scope.")
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
        if isinstance(check, dict) and (schema_version < 3 or set(check.get('pagePaths', [])) & affected):
            tracked.update(normalize(root, value) for value in check.get("evidencePaths", []) if isinstance(value, str))
    visual_ids = None
    if schema_version == 3:
        visual_ids = [v.get('id') for v in read_json_if_possible(root / '_kb-control/visual-explanations.json').get('items', []) if v.get('pagePath') in affected]
    for path in learning_asset_paths(root, affected) + visual_asset_paths(root, visual_ids=visual_ids, include_manifest=schema_version < 3):
        tracked.add(normalize(root, str(path)))
    for path in reader_probe_paths(root, affected) if schema_version < 3 else []:
        tracked.add(normalize(root, str(path)))
    for path in execution_paths(root, reviewed):
        tracked.add(normalize(root, str(path)))
    editor_pages = set(reviewed)
    if schema_version == 3 and (root / EXECUTION_STATE).exists():
        # The decision stored with an actual editorial run is already the editor
        # record. Do not require a second report saying the same thing.
        owners = {p: b for b in execution_batches(root)['batches'] for p in b['pages']}
        editor_pages -= {p for p, b in owners.items() if b.get('reviewMode') == 'editorial'}
    required = ["editor-review"] if editor_pages or schema_version == 1 else []
    if structure_changed and schema_version < 3:
        required.append("architecture-review")
    interactive = any(item.get("mode") == "interactive" and item.get("pagePath") in affected for item in manifest.get("items", []) if isinstance(item, dict))
    if deliveries or shared_app_changed or interactive:
        required.append("browser")
    if releases:
        required.append("release")
    contexts = set()
    projections = {}
    if schema_version == 3:
        contexts = {normalize(root, p) for p in context_paths}
        if not contexts and (root / '_kb-control/reader-brief.md').exists():
            contexts.add('_kb-control/reader-brief.md')
        if reviewed and not contexts and not (root / '_kb-control/project-contract.yaml').exists():
            raise ValueError('Supply --context with the existing reader brief/intent and relevant sources; do not invent a second plan.')
        projections = scoped_contracts(root, affected)
        tracked -= {f'_kb-control/{name}' for name in projections}
        tracked.update(contexts)
        from kb_audit import LINK_RE, resolved_target
        for value in affected:
            page = root / value
            if page.is_file():
                for match in LINK_RE.finditer(page.read_text(encoding='utf-8')):
                    target = resolved_target(root, page, match.group(1))
                    if target is not None:
                        tracked.add(normalize(root, str(target)))
        if releases:
            tracked.add('_kb-control/knowledgebase-release.json')
        for source in projections.get('source-understanding.json', {}).get('sources', []):
            value = source.get('path')
            if isinstance(value, str) and not value.startswith(('http:', 'https:')) and (root / value).is_file():
                tracked.add(normalize(root, value))
    result = {
        "schemaVersion": schema_version, "scope": "incremental", "changedPaths": changed,
        "affectedPages": sorted(affected), "deliveryPaths": sorted(deliveries), "releasePaths": sorted(releases),
        "inputDigests": {value: fingerprint(root, value) for value in sorted(tracked)},
        "requiredChecks": required, "checks": [], "globalWorkflow": global_state(root),
    }
    if schema_version >= 2:
        result.update(changeKind=change_kind, requestedPages=sorted(requested), reviewPages=sorted(reviewed),
                      regressionPages=sorted(affected),
                      checkScopes={kind: sorted(editor_pages if kind == "editor-review" else affected) for kind in required})
    if schema_version == 3:
        result.update(contextPaths=sorted(contexts), contractDigests={name: hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest() for name, value in projections.items()})
    result['independentReaderPages'] = execution_required_pages(root, reviewed, legacy=schema_version < 3)
    result['independentReaderRequired'] = bool(result['independentReaderPages'])
    return result


def check_update(root, plan):
    root = Path(root).resolve()
    errors = []
    schema_version = plan.get("schemaVersion")
    if schema_version not in {1, 2, 3} or plan.get("scope") != "incremental":
        issue(errors, "update-schema", "plan", "Expected incremental schema version 1, 2 or 3.")
    changed = strings(plan.get("changedPaths"), errors, "changedPaths")
    pages = strings(plan.get("affectedPages"), errors, "affectedPages")
    requested = strings(plan.get("requestedPages", []), errors, "requestedPages", required=False) if schema_version >= 2 else pages
    deliveries = strings(plan.get("deliveryPaths", []), errors, "deliveryPaths", required=False)
    releases = strings(plan.get("releasePaths", []), errors, "releasePaths", required=False)
    if errors:
        return {"status": "fail", "scope": "incremental", "errors": errors}
    change_kind = plan.get("changeKind", "content") if schema_version >= 2 else "content"
    if change_kind not in {"content", "rendering"}:
        return {"status": "fail", "errors": [{"kind": "update-change-kind", "path": "changeKind", "detail": "Expected content or rendering."}]}
    expected = plan_update(root, changed, pages=requested, delivery_paths=deliveries, release_paths=releases, schema_version=schema_version, change_kind=change_kind, context_paths=plan.get('contextPaths', []))
    if schema_version >= 2:
        for field in ("reviewPages", "regressionPages", "checkScopes"):
            if plan.get(field) != expected[field]:
                issue(errors, "update-scope-gap", field, "Review scopes must match the current changed inputs and declared pages.")
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
    if schema_version == 3 and plan.get('contractDigests') != expected['contractDigests']:
        issue(errors, 'update-stale-contract', 'contractDigests', 'Relevant intent, sources, content ownership or dependencies changed; reread the affected work.')
    if expected['independentReaderRequired']:
        errors.extend(execution_gate(root, expected['independentReaderPages']))
    for kind in expected["requiredChecks"]:
        receipt = next((item for item in checks if item.get("kind") == kind), {})
        if receipt.get("status") != "pass":
            issue(errors, "update-check-missing", kind, "A current passed check is required.")
        if schema_version >= 2 and receipt.get("pagePaths") != expected["checkScopes"][kind]:
            issue(errors, "update-check-scope", kind, "Receipt pagePaths must name the scope actually checked.")
        if receipt.get("inputDigests") != planned:
            issue(errors, "update-check-stale", kind, "Check evidence must name the exact inputDigests it actually reviewed.")
        if schema_version == 3 and receipt.get('contractDigests') != plan.get('contractDigests'):
            issue(errors, 'update-check-stale', kind, 'Review must bind the relevant contract projection it actually used.')
        if schema_version == 3 and kind == 'editor-review':
            if not isinstance(receipt.get('summary'), str) or not receipt['summary'].strip():
                issue(errors, 'editor-reading-missing', kind, 'Record the responsible editor reading/use judgment and any disposition in this receipt; no separate report is needed.')
        else:
            for value in strings(receipt.get("evidencePaths"), errors, kind):
                file_in_root(root, value, errors, kind)
    control = root / "_kb-control"
    content = (check_manuscript(root, pages) if schema_version == 3 else
               check_content(root, control / "source-understanding.json", control / "knowledge-model.json", control / "content-coverage.json", page_paths=pages,
                             review_page_paths=expected.get("reviewPages", pages)))
    errors.extend(content["errors"])
    missing_reviews = set(content["comprehensionEvidence"]["missingPages"])
    for value in sorted(missing_reviews & set(expected.get("reviewPages", pages))):
        issue(errors, "page-comprehension-required", value,
              "This novice page is in the editorial update scope; record current page comprehension evidence before claiming the explanation was reviewed.")
    editorial_novice_pages = set(content["comprehensionEvidence"]["requiredPages"]) & set(expected.get("reviewPages", pages)) if schema_version < 3 else set()
    coverage = read_json_if_possible(control / "content-coverage.json")
    for page in coverage.get("pages", []):
        if isinstance(page, dict) and page.get("path") in editorial_novice_pages:
            require_promise_review(page.get("comprehensionReview"), errors, page.get("path"), root=root, pages=[page.get("path")])
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
    if schema_version == 3 and releases:
        from kb_release_check import check_release, DEFAULTS
        config_path = control / 'knowledgebase-release.json'
        release_config = read_object(config_path, errors)
        if release_config:
            for value in releases:
                errors.extend(check_release(root / value, dict(DEFAULTS, **release_config), config_path)['errors'])
    evidence_digests = {}
    for receipt in checks:
        for value in receipt.get("evidencePaths", []):
            if isinstance(value, str):
                evidence_digests[value] = fingerprint(root, normalize(root, value))
    return {
        "schemaVersion": 1, "status": "fail" if errors else "pass", "scope": "incremental",
        "claim": "selected-update-only", "affectedPages": pages,
        "reviewPages": expected.get("reviewPages", pages),
        "regressionPages": expected.get("regressionPages", pages),
        "comprehensionEvidence": content["comprehensionEvidence"],
        "inputDigests": expected["inputDigests"], "contractDigests": expected.get('contractDigests', {}), "evidenceDigests": evidence_digests,
        "learningActivities": learning["validatedIds"], "globalWorkflow": global_state(root),
        "errors": errors, "warnings": content["warnings"] + learning["warnings"],
    }


def record_check(root, plan, kind, summary, *, status='pass', evidence_paths=()):
    """Bind a performed check to current inputs, without hand-copying fingerprints."""
    root = Path(root).resolve()
    if plan.get('schemaVersion') != 3 or plan.get('scope') != 'incremental':
        raise ValueError('Record is for a newly generated schema 3 scoped plan.')
    expected = plan_update(root, plan['changedPaths'], pages=plan.get('requestedPages', []),
                           delivery_paths=plan.get('deliveryPaths', []), release_paths=plan.get('releasePaths', []),
                           change_kind=plan.get('changeKind', 'content'), context_paths=plan.get('contextPaths', []))
    for field in ('inputDigests', 'contractDigests', 'checkScopes', 'requiredChecks'):
        if plan.get(field) != expected[field]:
            raise ValueError('Inputs or required scope changed; reread/recheck before recording against a new plan.')
    if kind not in expected['requiredChecks'] or status not in {'pass', 'needs_work'}:
        raise ValueError('Choose a required check and an actual pass/needs_work result.')
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError('Record the actual observation/editor judgment, not only a status.')
    evidence = [normalize(root, value) for value in evidence_paths]
    if kind != 'editor-review' and not evidence:
        raise ValueError('Browser/release checks need actual evidence paths.')
    if any(not (root / value).is_file() for value in evidence):
        raise ValueError('Evidence files must exist inside the project.')
    receipt = {'kind': kind, 'status': status, 'summary': summary.strip(), 'pagePaths': expected['checkScopes'][kind],
               'inputDigests': expected['inputDigests'], 'contractDigests': expected['contractDigests'], 'evidencePaths': evidence}
    return dict(plan, checks=[c for c in plan.get('checks', []) if c.get('kind') != kind] + [receipt])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "record", "check"])
    parser.add_argument("--root", required=True)
    parser.add_argument("--path", action="append", default=[], dest="changed")
    parser.add_argument("--page", action="append", default=[])
    parser.add_argument("--change-kind", choices=["content", "rendering"], default="content", help="Use rendering only after establishing that shared app edits preserve meaning/behavior promises")
    parser.add_argument("--schema-version", type=int, choices=[1, 2, 3], default=3, help="3 uses scoped editorial review; 1/2 retain legacy receipt contracts")
    parser.add_argument("--context", action="append", default=[], help="Existing reader brief or relevant source file; repeatable")
    parser.add_argument("--delivery-path", action="append", default=[])
    parser.add_argument("--release-path", action="append", default=[])
    parser.add_argument("--plan")
    parser.add_argument('--kind', choices=['editor-review', 'browser', 'release'])
    parser.add_argument('--summary', help='Actual reading/use judgment or check observation')
    parser.add_argument('--status', choices=['pass', 'needs_work'], default='pass')
    parser.add_argument('--evidence', action='append', default=[])
    parser.add_argument("--output")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        parser.error("root must be an existing directory")
    try:
        if args.command == "plan":
            result = plan_update(root, args.changed, pages=args.page, delivery_paths=args.delivery_path, release_paths=args.release_path, change_kind=args.change_kind, schema_version=args.schema_version, context_paths=args.context)
        else:
            if not args.plan:
                parser.error("check requires --plan")
            errors = []
            plan = read_object(root / normalize(root, args.plan), errors)
            if errors:
                result = {'status': 'fail', 'errors': errors}
            elif args.command == 'record':
                result = record_check(root, plan, args.kind, args.summary, status=args.status, evidence_paths=args.evidence)
            else:
                result = check_update(root, plan)
        rendered = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            output = root / normalize(root, args.output)
            if args.command != 'record' and args.plan and output == root / normalize(root, args.plan):
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
