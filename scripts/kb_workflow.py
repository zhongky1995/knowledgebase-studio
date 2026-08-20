#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 3
SUPPORTED_SCHEMA_VERSIONS = {1, 2, 3}
CONTRACT_SCHEMA_MAJOR = "3"
CONTROL_DIR = "_kb-control"
STATE_FILE = "workflow.json"
ALLOWED_BLOCKERS = {
    "missing-source",
    "scope-conflict",
    "destructive-approval",
    "external-auth",
    "external-publish",
    "repeated-failure",
}

PRODUCT_POSTURES = {
    "reading_manual",
    "guided_learning",
    "practice_workbench",
    "operations_manual",
    "reference_library",
    "hybrid",
}

DISTRIBUTION_MODES = {
    "local_entrypoint",
    "single_file",
    "static_site",
    "archive",
}

AUDIENCE_SCOPES = {"internal", "public"}

LICENSE_POLICIES = {
    "internal_only",
    "all_rights_reserved",
    "explicit_files",
}

FEEDBACK_STAGE = {
    "intent": "intake",
    "audience": "intake",
    "product-posture": "intake",
    "navigation": "architecture",
    "catalog-pressure": "architecture",
    "content-depth": "pilot",
    "example-depth": "pilot",
    "learning-progression": "architecture",
    "learning-transfer": "pilot",
    "visual-explanation": "pilot",
    "tone": "content",
    "source-presentation": "intake",
    "distribution": "intake",
    "public-scope": "intake",
    "license": "intake",
    "rendering": "app",
    "visual-rendering": "app",
    "interaction": "app",
    "responsive": "app",
    "validation": "qc",
    "packaging": "release",
}

VALIDATION_ARTIFACTS = {
    "audit": f"{CONTROL_DIR}/stage-check-audit.json",
    "architecture": f"{CONTROL_DIR}/stage-check-architecture.json",
    "pilot": f"{CONTROL_DIR}/stage-check-pilot.json",
    "content": f"{CONTROL_DIR}/stage-check-content.json",
    "app": f"{CONTROL_DIR}/stage-check-app.json",
    "qc": f"{CONTROL_DIR}/stage-check-qc.json",
    "release": f"{CONTROL_DIR}/stage-check-release.json",
}

STAGE_DEFINITIONS = [
    {
        "id": "intake",
        "name": "Scope and source lock",
        "skill": "structured-knowledgebase-builder",
        "depends_on": [],
        "required_artifacts": [f"{CONTROL_DIR}/project-contract.yaml"],
        "optional": False,
    },
    {
        "id": "audit",
        "name": "Repository and content audit",
        "skill": "knowledgebase-auditor",
        "depends_on": ["intake"],
        "required_artifacts": [
            f"{CONTROL_DIR}/content-inventory.json",
            f"{CONTROL_DIR}/audit-report.md",
            f"{CONTROL_DIR}/source-understanding.json",
            f"{CONTROL_DIR}/audit-metrics.json",
        ],
        "optional": False,
    },
    {
        "id": "architecture",
        "name": "Architecture and content allocation",
        "skill": "knowledgebase-architect",
        "depends_on": ["audit"],
        "required_artifacts": [
            f"{CONTROL_DIR}/architecture-decision.md",
            f"{CONTROL_DIR}/migration-map.yaml",
            f"{CONTROL_DIR}/knowledge-model.json",
        ],
        "optional": False,
    },
    {
        "id": "pilot",
        "name": "Representative pilot slice",
        "skill": "knowledgebase-content-builder",
        "depends_on": ["architecture"],
        "required_artifacts": [
            f"{CONTROL_DIR}/pilot-review.md",
            f"{CONTROL_DIR}/pilot-verdict.json",
        ],
        "optional": False,
    },
    {
        "id": "content",
        "name": "Full content production",
        "skill": "knowledgebase-content-builder",
        "depends_on": ["pilot"],
        "required_artifacts": [
            f"{CONTROL_DIR}/content-build-report.md",
            f"{CONTROL_DIR}/content-coverage.json",
            f"{CONTROL_DIR}/content-integrity.json",
        ],
        "optional": False,
    },
    {
        "id": "app",
        "name": "Knowledge app integration",
        "skill": "knowledgebase-app-builder",
        "depends_on": ["content"],
        "required_artifacts": [
            f"{CONTROL_DIR}/app-validation.md",
            f"{CONTROL_DIR}/app-validation.json",
        ],
        "optional": True,
    },
    {
        "id": "qc",
        "name": "Independent quality control",
        "skill": "knowledgebase-qc-release",
        "depends_on": ["content", "app"],
        "required_artifacts": [
            f"{CONTROL_DIR}/qc-report.md",
            f"{CONTROL_DIR}/qc-verdict.json",
        ],
        "optional": False,
    },
    {
        "id": "release",
        "name": "Package and release",
        "skill": "knowledgebase-qc-release",
        "depends_on": ["qc"],
        "required_artifacts": [
            f"{CONTROL_DIR}/release-report.md",
            f"{CONTROL_DIR}/release-verdict.json",
        ],
        "optional": False,
    },
]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def fail(message, code=2):
    print(json.dumps({"status": "error", "message": message}, ensure_ascii=False, indent=2))
    raise SystemExit(code)


def root_path(value):
    root = Path(value).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        fail(f"Knowledge-base root is not a directory: {root}")
    return root


def state_path(root):
    return root / CONTROL_DIR / STATE_FILE


def load_state(root):
    path = state_path(root)
    if not path.exists():
        fail(f"Workflow state not found: {path}. Run init first.")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"Cannot read workflow state: {error}")
    return state


def atomic_write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    )
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


def save_state(root, state):
    state["updated_at"] = utc_now()
    atomic_write_json(state_path(root), state)


def digest_path(path):
    if not path.exists():
        return None
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for child in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(str(child.relative_to(path)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(child.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def read_json_if_possible(path):
    if not path.exists() or not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def scoped_deliverable(root, value):
    candidate = Path(str(value))
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not is_inside(root, candidate):
        return None
    return candidate


def public_content_paths(root):
    try:
        from kb_audit import load_config, scan_files
    except ImportError:
        return []
    markdown, _ = scan_files(root, load_config(root))
    return markdown


def json_declared_paths(root, filename, key):
    document = read_json_if_possible(root / CONTROL_DIR / filename)
    values = document.get(key) or []
    return [candidate for value in values if (candidate := scoped_deliverable(root, value)) is not None]


def visual_asset_paths(root, visual_ids=None, include_manifest=False):
    manifest = root / CONTROL_DIR / "visual-explanations.json"
    document = read_json_if_possible(manifest)
    selected = set(visual_ids or [])
    paths = []
    if include_manifest and manifest.is_file():
        paths.append(manifest)
    for item in document.get("items") or []:
        if selected and item.get("id") not in selected:
            continue
        for key in ("assetPath", "fallbackPath"):
            value = item.get(key)
            if value and (candidate := scoped_deliverable(root, value)) is not None:
                paths.append(candidate)
    return paths


def stage_deliverable_paths(root, stage_id):
    paths = []
    if stage_id == "pilot":
        paths.extend(json_declared_paths(root, "pilot-verdict.json", "representativePaths"))
        verdict = read_json_if_possible(root / CONTROL_DIR / "pilot-verdict.json")
        paths.extend(visual_asset_paths(root, verdict.get("visualExplanationIds") or []))
    if stage_id in {"content", "qc"}:
        paths.extend(public_content_paths(root))
    if stage_id in {"app", "qc"}:
        paths.extend(json_declared_paths(root, "app-validation.json", "appPaths"))
    if stage_id in {"content", "app", "qc"}:
        paths.extend(visual_asset_paths(root, include_manifest=True))
    if stage_id == "release":
        verdict = read_json_if_possible(root / CONTROL_DIR / "release-verdict.json")
        value = verdict.get("releaseRoot")
        if not value:
            contract = contract_path(root)
            if contract.exists():
                value = yaml_field(contract.read_text(encoding="utf-8", errors="replace"), "release_root")
        if value:
            candidate = scoped_deliverable(root, value)
            if candidate is not None:
                paths.append(candidate)
    result = []
    seen = set()
    for candidate in paths:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            result.append(candidate)
    return result


def stage_deliverable_digests(root, stage_id):
    return {
        str(path.relative_to(root)): digest_path(path)
        for path in stage_deliverable_paths(root, stage_id)
    }


def contract_path(root):
    return root / CONTROL_DIR / "project-contract.yaml"


def yaml_field(text, key):
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    return match.group(1).strip().strip('"\'') if match else None


def yaml_section_has_content(text, key):
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    if not match:
        return False
    inline = match.group(1).strip()
    if inline and inline not in {"[]", "{}", '""', "''"}:
        return True
    remainder = text[match.end() :]
    for line in remainder.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            break
        return True
    return False


def validate_project_contract(root):
    path = contract_path(root)
    if not path.exists():
        return ["project contract is missing"]
    text = path.read_text(encoding="utf-8", errors="replace")
    issues = []
    contract_schema = yaml_field(text, "schema_version")
    if not contract_schema or contract_schema.split(".", 1)[0] != CONTRACT_SCHEMA_MAJOR:
        issues.append(
            f"unsupported project contract schema_version: {contract_schema or 'missing'}; expected major {CONTRACT_SCHEMA_MAJOR}"
        )
    required_scalars = (
        "goal",
        "primary_mode",
        "product_posture",
        "reader_moment",
        "default_user_action",
        "first_success",
        "catalog_visibility",
        "exercise_policy",
        "progress_semantics",
        "pressure_policy",
        "source_presentation",
        "intent_mirror",
        "distribution_mode",
        "audience_scope",
        "external_publish_authorized",
        "license_policy",
    )
    unresolved = {None, "", "auto", "unresolved", "draft", "[]", "{}"}
    for key in required_scalars:
        value = yaml_field(text, key)
        if value in unresolved:
            issues.append(f"project contract field is unresolved: {key}")
    posture = yaml_field(text, "product_posture")
    if posture not in PRODUCT_POSTURES:
        issues.append(f"unsupported product_posture: {posture or 'missing'}")
    distribution_mode = yaml_field(text, "distribution_mode")
    if distribution_mode not in DISTRIBUTION_MODES:
        issues.append(f"unsupported distribution_mode: {distribution_mode or 'missing'}")
    audience_scope = yaml_field(text, "audience_scope")
    if audience_scope not in AUDIENCE_SCOPES:
        issues.append(f"unsupported audience_scope: {audience_scope or 'missing'}")
    publish_authorized = yaml_field(text, "external_publish_authorized")
    if publish_authorized not in {"true", "false"}:
        issues.append("external_publish_authorized must be true or false")
    license_policy = yaml_field(text, "license_policy")
    if license_policy not in LICENSE_POLICIES:
        issues.append(f"unsupported license_policy: {license_policy or 'missing'}")
    if audience_scope == "public" and license_policy == "internal_only":
        issues.append("public audience_scope requires all_rights_reserved or explicit_files license_policy")
    if audience_scope == "internal" and license_policy != "internal_only":
        issues.append("internal audience_scope must use internal_only license_policy")
    if license_policy == "explicit_files" and not yaml_section_has_content(text, "license_files"):
        issues.append("license_files must not be empty when license_policy is explicit_files")
    package_required = yaml_field(text, "package_required")
    release_root = yaml_field(text, "release_root")
    if package_required == "true" and distribution_mode in {"single_file", "static_site", "archive"} and not release_root:
        issues.append("release_root is required for packaged distribution")
    status = yaml_field(text, "status")
    if status in unresolved:
        issues.append("project contract status must be locked or approved before intake passes")
    for key in ("anti_goals", "acceptance"):
        if not yaml_section_has_content(text, key):
            issues.append(f"project contract section must not be empty: {key}")
    return issues


def completed_timestamp(stage):
    value = stage.get("completed_at")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return None


def stage_artifact_digests(root, artifacts):
    return {value: digest_path(resolve_artifact(root, value)) for value in sorted(set(artifacts))}


def dependency_digests(root, state, stage):
    result = {}
    for dependency_id in stage["depends_on"]:
        dependency = stage_by_id(state, dependency_id)
        for value in dependency.get("artifacts", dependency.get("required_artifacts", [])):
            result[f"{dependency_id}:{value}"] = digest_path(resolve_artifact(root, value))
    return result


def stale_stage_reasons(root, state):
    stale = []
    current_contract_digest = digest_path(contract_path(root))
    for stage in state.get("stages", []):
        if stage.get("status") != "pass":
            continue
        reasons = []
        completed = completed_timestamp(stage)
        artifacts = stage.get("artifacts") or stage.get("required_artifacts", [])
        stored_artifacts = stage.get("artifact_digests", {})
        for value in artifacts:
            candidate = resolve_artifact(root, value)
            if not candidate.exists():
                reasons.append(f"missing artifact: {value}")
                continue
            current_digest = digest_path(candidate)
            if value in stored_artifacts and stored_artifacts[value] != current_digest:
                reasons.append(f"artifact changed after pass: {value}")
            elif not stored_artifacts and completed and candidate.stat().st_mtime > completed + 1:
                reasons.append(f"legacy artifact is newer than pass: {value}")

        stored_contract = stage.get("contract_digest")
        if stage["id"] != "intake":
            if stored_contract and stored_contract != current_contract_digest:
                reasons.append("project contract changed after pass")
            elif not stored_contract and completed and contract_path(root).exists() and contract_path(root).stat().st_mtime > completed + 1:
                reasons.append("legacy project contract is newer than pass")

        stored_dependencies = stage.get("dependency_digests", {})
        current_dependencies = dependency_digests(root, state, stage)
        if stored_dependencies:
            for key, value in stored_dependencies.items():
                if current_dependencies.get(key) != value:
                    reasons.append(f"dependency changed after pass: {key}")
        elif completed:
            for dependency_id in stage.get("depends_on", []):
                dependency = stage_by_id(state, dependency_id)
                dependency_completed = completed_timestamp(dependency)
                if dependency_completed and dependency_completed > completed + 1:
                    reasons.append(f"dependency stage is newer than pass: {dependency_id}")
                for value in dependency.get("artifacts", dependency.get("required_artifacts", [])):
                    candidate = resolve_artifact(root, value)
                    if candidate.exists() and candidate.stat().st_mtime > completed + 1:
                        reasons.append(f"legacy dependency artifact is newer than pass: {dependency_id}:{value}")

        validation_artifact = VALIDATION_ARTIFACTS.get(stage["id"])
        if validation_artifact:
            candidate = resolve_artifact(root, validation_artifact)
            if validation_artifact not in artifacts or not candidate.exists():
                reasons.append(f"stage lacks current semantic gate evidence: {validation_artifact}")

        if stage["id"] in {"pilot", "content", "app", "qc", "release"}:
            stored_deliverables = stage.get("deliverable_digests")
            if not stored_deliverables:
                reasons.append("stage lacks learner-facing deliverable fingerprints")
            else:
                current_deliverables = stage_deliverable_digests(root, stage["id"])
                for key in sorted(set(stored_deliverables) | set(current_deliverables)):
                    if stored_deliverables.get(key) != current_deliverables.get(key):
                        reasons.append(f"learner-facing deliverable changed after pass: {key}")
        if reasons:
            stale.append({"stage": stage["id"], "reasons": sorted(set(reasons))})
    return stale


def invalidate_state_from(state, stage_id, reason):
    start = stage_index(state, stage_id)
    invalidated = []
    for stage in state["stages"][start:]:
        invalidated.append(stage["id"])
        stage["status"] = "pending"
        stage["attempts"] = 0
        stage["started_at"] = None
        stage["completed_at"] = None
        stage["artifacts"] = []
        stage.pop("artifact_digests", None)
        stage.pop("dependency_digests", None)
        stage.pop("deliverable_digests", None)
        stage.pop("contract_digest", None)
        stage["notes"].append(f"Invalidated in revision {state['revision'] + 1}: {reason}")
    state["revision"] += 1
    state["status"] = "active"
    state["current_stage"] = None
    state["blocker"] = None
    return invalidated


def stage_by_id(state, stage_id):
    for stage in state["stages"]:
        if stage["id"] == stage_id:
            return stage
    fail(f"Unknown stage: {stage_id}")


def stage_index(state, stage_id):
    for index, stage in enumerate(state["stages"]):
        if stage["id"] == stage_id:
            return index
    fail(f"Unknown stage: {stage_id}")


def record_history(state, event, **details):
    state["history"].append({"at": utc_now(), "event": event, **details})


def is_inside(root, candidate):
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_artifact(root, value):
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()
    if not is_inside(root, candidate):
        fail(f"Artifact must stay inside the knowledge-base root: {candidate}")
    return candidate


def public_artifact(root, candidate):
    return str(candidate.relative_to(root))


def dependencies_pass(state, stage):
    for dependency in stage["depends_on"]:
        status = stage_by_id(state, dependency)["status"]
        if status not in {"pass", "skipped"}:
            return False
    return True


def detect_app(root):
    markers = [
        root / "local-learning-app",
        root / "docs" / ".vitepress",
        root / "mkdocs.yml",
        root / "docusaurus.config.js",
    ]
    if any(marker.exists() for marker in markers):
        return True
    return (root / "index.html").exists() and any(
        (root / name).exists() for name in ("app.js", "main.js", "package.json")
    )


def action_for(stage, state):
    return {
        "action": "execute-stage",
        "workflow_status": state["status"],
        "revision": state["revision"],
        "stage": stage["id"],
        "stage_name": stage["name"],
        "skill": stage["skill"],
        "attempt": stage["attempts"],
        "required_artifacts": stage["required_artifacts"],
        "continue_without_confirmation": state["execution_policy"]["continue_without_confirmation"],
    }


def next_action(root, state, claim=False):
    if state["status"] == "blocked":
        return {
            "action": "blocked",
            "workflow_status": "blocked",
            "blocker": state.get("blocker"),
        }
    stale = stale_stage_reasons(root, state)
    if stale:
        return {
            "action": "stale",
            "workflow_status": "stale",
            "earliest_stage": stale[0]["stage"],
            "stale": stale,
            "needed": "Run reconcile --apply before continuing.",
        }
    if state["status"] == "complete":
        return {"action": "complete", "workflow_status": "complete", "revision": state["revision"]}

    current_id = state.get("current_stage")
    if current_id:
        current = stage_by_id(state, current_id)
        if current["status"] in {"in_progress", "needs_work"}:
            return action_for(current, state)

    while True:
        eligible = None
        for stage in state["stages"]:
            if stage["status"] == "pending" and dependencies_pass(state, stage):
                eligible = stage
                break

        if eligible is None:
            incomplete = [
                stage for stage in state["stages"] if stage["status"] not in {"pass", "skipped"}
            ]
            if incomplete:
                return {
                    "action": "gate-blocked",
                    "workflow_status": state["status"],
                    "stages": [{"id": stage["id"], "status": stage["status"]} for stage in incomplete],
                }
            state["status"] = "complete"
            state["current_stage"] = None
            record_history(state, "workflow-complete", revision=state["revision"])
            save_state(root, state)
            return {"action": "complete", "workflow_status": "complete", "revision": state["revision"]}

        if eligible["id"] == "app" and state["app_required"] == "no":
            eligible["status"] = "skipped"
            eligible["completed_at"] = utc_now()
            eligible["notes"].append("Automatically skipped: no app detected or required.")
            record_history(state, "stage-skipped", stage="app", reason="app_required=no")
            save_state(root, state)
            continue

        if not claim:
            return action_for(eligible, state)

        if eligible["attempts"] >= state["execution_policy"]["max_stage_attempts"]:
            eligible["status"] = "blocked"
            state["status"] = "blocked"
            state["current_stage"] = eligible["id"]
            state["blocker"] = {
                "kind": "repeated-failure",
                "stage": eligible["id"],
                "reason": "Stage exceeded the configured attempt limit.",
                "created_at": utc_now(),
            }
            record_history(state, "workflow-blocked", **state["blocker"])
            save_state(root, state)
            return {"action": "blocked", "workflow_status": "blocked", "blocker": state["blocker"]}

        eligible["status"] = "in_progress"
        eligible["attempts"] += 1
        eligible["started_at"] = eligible["started_at"] or utc_now()
        state["current_stage"] = eligible["id"]
        record_history(state, "stage-claimed", stage=eligible["id"], attempt=eligible["attempts"])
        save_state(root, state)
        return action_for(eligible, state)


def write_project_contract(root, goal, mode, posture, app_required):
    path = root / CONTROL_DIR / "project-contract.yaml"
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f'''schema_version: 3
status: draft
goal: {json.dumps(goal, ensure_ascii=False)}
primary_mode: {mode if mode != "auto" else "unresolved"}
product_posture: {posture}
audiences: []
reader_moment: ""
default_user_action: ""
first_success: ""
catalog_visibility: unresolved
exercise_policy: unresolved
progress_semantics: unresolved
pressure_policy: unresolved
source_presentation: unresolved
intent_mirror: ""
top_tasks: []
public_root: {json.dumps(str(root), ensure_ascii=False)}
public_paths: []
app_paths: []
generated_paths: []
canonical_sources: []
preserve: []
allowed_changes: []
forbidden_changes: []
anti_goals: []
acceptance: []
assumptions: []
app_required: {app_required}
package_required: false
distribution_mode: local_entrypoint
audience_scope: internal
release_root: ""
external_publish_authorized: false
license_policy: internal_only
license_files: []
'''
    path.write_text(content, encoding="utf-8")


def command_init(args):
    root = root_path(args.root)
    path = state_path(root)
    if path.exists() and not args.force:
        state = load_state(root)
        print(json.dumps({"status": "exists", "state": state, "next": next_action(root, state)}, ensure_ascii=False, indent=2))
        return

    detected_app = detect_app(root)
    app_required = args.app
    if app_required == "auto":
        app_required = "yes" if detected_app else "no"

    stages = []
    for definition in STAGE_DEFINITIONS:
        stages.append(
            {
                **definition,
                "status": "pending",
                "attempts": 0,
                "started_at": None,
                "completed_at": None,
                "artifacts": [],
                "notes": [],
            }
        )

    state = {
        "schema_version": SCHEMA_VERSION,
        "revision": 1,
        "project_root": str(root),
        "goal": args.goal,
        "mode": args.mode,
        "product_posture": args.posture,
        "app_required": app_required,
        "status": "active",
        "current_stage": None,
        "blocker": None,
        "execution_policy": {
            "continue_without_confirmation": args.execution_policy == "autonomous",
            "mode": args.execution_policy,
            "max_stage_attempts": args.max_stage_attempts,
            "stop_only_for_defined_blockers": True,
        },
        "stages": stages,
        "history": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    write_project_contract(root, args.goal, args.mode, args.posture, app_required)
    record_history(state, "workflow-initialized", goal=args.goal, mode=args.mode, product_posture=args.posture, app_required=app_required)
    save_state(root, state)
    action = next_action(root, state, claim=True)
    print(json.dumps({"status": "initialized", "next": action}, ensure_ascii=False, indent=2))


def command_status(args):
    root = root_path(args.root)
    state = load_state(root)
    print(json.dumps({"state": state, "next": next_action(root, state)}, ensure_ascii=False, indent=2))


def command_next(args):
    root = root_path(args.root)
    state = load_state(root)
    print(json.dumps(next_action(root, state, claim=args.claim), ensure_ascii=False, indent=2))


def validate_required_artifacts(root, stage, supplied):
    resolved = []
    for value in supplied or []:
        candidate = resolve_artifact(root, value)
        if not candidate.exists():
            fail(f"Artifact does not exist: {candidate}")
        resolved.append(public_artifact(root, candidate))

    missing = []
    for value in stage["required_artifacts"]:
        candidate = resolve_artifact(root, value)
        if not candidate.exists():
            missing.append(value)
        else:
            resolved.append(public_artifact(root, candidate))
    if missing:
        fail(f"Required stage artifacts are missing: {', '.join(missing)}")
    return sorted(set(resolved))


def validate_semantic_stage(root, stage_id):
    generated = []
    control = root / CONTROL_DIR

    if stage_id in {"audit", "content", "qc"}:
        try:
            from kb_audit import audit as run_audit
        except ImportError as error:
            fail(f"Cannot load deterministic knowledge-base auditor: {error}")
        strict = stage_id in {"content", "qc"}
        audit_report = run_audit(root, strict=strict, fail_severity="warning")
        audit_names = {
            "audit": "audit-metrics.json",
            "content": "content-audit-metrics.json",
            "qc": "qc-audit-metrics.json",
        }
        audit_path = control / audit_names[stage_id]
        atomic_write_json(audit_path, audit_report)
        generated.append(public_artifact(root, audit_path))
        if audit_report["status"] == "failed":
            fail(
                f"Deterministic {stage_id} audit failed with {len(audit_report['errors'])} error(s) "
                f"and {len(audit_report['warnings'])} warning(s)."
            )

    phases = {"audit": "audit", "architecture": "architecture", "content": "content"}
    phase = phases.get(stage_id)
    if phase:
        try:
            from kb_content_check import validate as validate_content
        except ImportError as error:
            fail(f"Cannot load semantic content validator: {error}")
        report = validate_content(
            root,
            control / "source-understanding.json",
            control / "knowledge-model.json",
            control / "content-coverage.json",
            phase,
        )
        report_names = {
            "audit": "source-understanding-check.json",
            "architecture": "knowledge-model-check.json",
            "content": "content-integrity.json",
        }
        report_path = control / report_names[phase]
        atomic_write_json(report_path, report)
        generated.append(public_artifact(root, report_path))
        if report["errors"]:
            first = report["errors"][0]
            fail(
                f"Semantic {phase} gate failed with {len(report['errors'])} issue(s): "
                f"{first['kind']} at {first['path']}: {first['detail']}"
            )

    validation_artifact = VALIDATION_ARTIFACTS.get(stage_id)
    if validation_artifact:
        try:
            from kb_stage_check import validate_stage
        except ImportError as error:
            fail(f"Cannot load stage evidence validator: {error}")
        stage_report = validate_stage(root, stage_id)
        stage_report_path = resolve_artifact(root, validation_artifact)
        atomic_write_json(stage_report_path, stage_report)
        generated.append(validation_artifact)
        release_check = control / "release-check.json"
        if stage_id == "release" and release_check.exists():
            generated.append(public_artifact(root, release_check))
        if stage_report["errors"]:
            first = stage_report["errors"][0]
            fail(
                f"Stage {stage_id} evidence gate failed with {len(stage_report['errors'])} issue(s): "
                f"{first['kind']} at {first['path']}: {first['detail']}"
            )
    return sorted(set(generated))


def command_complete(args):
    root = root_path(args.root)
    state = load_state(root)
    stage = stage_by_id(state, args.stage)
    if stage["status"] not in {"in_progress", "needs_work"}:
        fail(f"Stage {args.stage} is not active: {stage['status']}")
    if state.get("current_stage") != args.stage:
        fail(f"Stage {args.stage} is not the current stage: {state.get('current_stage')}")

    if args.stage == "intake" and args.decision == "pass":
        contract_issues = validate_project_contract(root)
        if contract_issues:
            fail("Project contract is not ready: " + "; ".join(contract_issues))

    if args.decision == "needs-work":
        stage["status"] = "pending"
        stage["notes"].append(args.notes or "Validation failed; repair required.")
        state["current_stage"] = None
        record_history(state, "stage-needs-work", stage=args.stage, notes=args.notes or "")
        save_state(root, state)
        action = next_action(root, state, claim=True)
        print(json.dumps({"status": "needs-work", "next": action}, ensure_ascii=False, indent=2))
        return

    generated_artifacts = validate_semantic_stage(root, args.stage)
    artifacts = validate_required_artifacts(root, stage, [*args.artifact, *generated_artifacts])
    stage["status"] = "pass"
    stage["completed_at"] = utc_now()
    stage["artifacts"] = artifacts
    stage["artifact_digests"] = stage_artifact_digests(root, artifacts)
    stage["dependency_digests"] = dependency_digests(root, state, stage)
    stage["deliverable_digests"] = stage_deliverable_digests(root, args.stage)
    stage["contract_digest"] = digest_path(contract_path(root))
    if args.notes:
        stage["notes"].append(args.notes)
    state["current_stage"] = None
    record_history(state, "stage-complete", stage=args.stage, artifacts=artifacts)
    save_state(root, state)
    action = next_action(root, state, claim=True)
    print(json.dumps({"status": "pass", "completed_stage": args.stage, "next": action}, ensure_ascii=False, indent=2))


def command_skip(args):
    root = root_path(args.root)
    state = load_state(root)
    stage = stage_by_id(state, args.stage)
    if not stage["optional"]:
        fail(f"Stage is not optional and cannot be skipped: {args.stage}")
    if not dependencies_pass(state, stage):
        fail(f"Stage dependencies have not passed: {args.stage}")
    stage["status"] = "skipped"
    stage["completed_at"] = utc_now()
    stage["notes"].append(args.reason)
    if state.get("current_stage") == args.stage:
        state["current_stage"] = None
    record_history(state, "stage-skipped", stage=args.stage, reason=args.reason)
    save_state(root, state)
    action = next_action(root, state, claim=True)
    print(json.dumps({"status": "skipped", "stage": args.stage, "next": action}, ensure_ascii=False, indent=2))


def command_block(args):
    root = root_path(args.root)
    state = load_state(root)
    if args.kind not in ALLOWED_BLOCKERS:
        fail(f"Unsupported blocker kind: {args.kind}")
    stage_id = args.stage or state.get("current_stage")
    if not stage_id:
        fail("A current stage or --stage is required to block the workflow.")
    stage = stage_by_id(state, stage_id)
    stage["status"] = "blocked"
    stage["notes"].append(args.reason)
    state["status"] = "blocked"
    state["current_stage"] = stage_id
    state["blocker"] = {
        "kind": args.kind,
        "stage": stage_id,
        "reason": args.reason,
        "needed": args.needed,
        "created_at": utc_now(),
    }
    record_history(state, "workflow-blocked", **state["blocker"])
    save_state(root, state)
    print(json.dumps({"status": "blocked", "blocker": state["blocker"]}, ensure_ascii=False, indent=2))


def command_resume(args):
    root = root_path(args.root)
    state = load_state(root)
    if state["status"] != "blocked" or not state.get("blocker"):
        fail("Workflow is not blocked.")
    stage = stage_by_id(state, state["blocker"]["stage"])
    old_blocker = state["blocker"]
    stage["status"] = "in_progress"
    stage["notes"].append(f"Blocker resolution: {args.resolution}")
    state["status"] = "active"
    state["current_stage"] = stage["id"]
    state["blocker"] = None
    record_history(state, "workflow-resumed", stage=stage["id"], resolution=args.resolution, prior_blocker=old_blocker)
    save_state(root, state)
    print(json.dumps({"status": "resumed", "next": action_for(stage, state)}, ensure_ascii=False, indent=2))


def command_invalidate(args):
    root = root_path(args.root)
    state = load_state(root)
    invalidated = invalidate_state_from(state, args.from_stage, args.reason)
    record_history(state, "workflow-invalidated", from_stage=args.from_stage, reason=args.reason, invalidated=invalidated)
    save_state(root, state)
    action = next_action(root, state, claim=True)
    print(json.dumps({"status": "invalidated", "revision": state["revision"], "next": action}, ensure_ascii=False, indent=2))


def command_feedback(args):
    root = root_path(args.root)
    state = load_state(root)
    stage_id = FEEDBACK_STAGE[args.kind]
    reason = f"User feedback ({args.kind}): {args.reason}"
    invalidated = invalidate_state_from(state, stage_id, reason)
    record_history(state, "feedback-invalidated", kind=args.kind, from_stage=stage_id, reason=args.reason, invalidated=invalidated)
    save_state(root, state)
    action = next_action(root, state, claim=True)
    print(json.dumps({"status": "invalidated", "kind": args.kind, "from_stage": stage_id, "revision": state["revision"], "next": action}, ensure_ascii=False, indent=2))


def command_reconcile(args):
    root = root_path(args.root)
    state = load_state(root)
    stale = stale_stage_reasons(root, state)
    if not stale:
        print(json.dumps({"status": "current", "revision": state["revision"], "stale": []}, ensure_ascii=False, indent=2))
        return
    if not args.apply:
        print(json.dumps({"status": "stale", "earliest_stage": stale[0]["stage"], "stale": stale, "needed": "Rerun with --apply to invalidate downstream evidence."}, ensure_ascii=False, indent=2))
        return
    earliest = stale[0]["stage"]
    reason = "Freshness reconciliation: " + "; ".join(stale[0]["reasons"])
    invalidated = invalidate_state_from(state, earliest, reason)
    record_history(state, "freshness-invalidated", from_stage=earliest, stale=stale, invalidated=invalidated)
    save_state(root, state)
    action = next_action(root, state, claim=True)
    print(json.dumps({"status": "invalidated", "from_stage": earliest, "revision": state["revision"], "stale": stale, "next": action}, ensure_ascii=False, indent=2))


def command_check(args):
    root = root_path(args.root)
    state = load_state(root)
    issues = []
    if state.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        issues.append(f"Unsupported schema_version: {state.get('schema_version')}")
    if state.get("project_root") != str(root):
        issues.append("project_root does not match the requested root")
    for stage in state.get("stages", []):
        if stage["status"] == "pass":
            for artifact in stage["required_artifacts"]:
                if not resolve_artifact(root, artifact).exists():
                    issues.append(f"Passed stage {stage['id']} is missing {artifact}")
    if state.get("current_stage"):
        current = stage_by_id(state, state["current_stage"])
        if current["status"] not in {"in_progress", "needs_work", "blocked"}:
            issues.append("current_stage does not have an active status")
    stale = stale_stage_reasons(root, state)
    for item in stale:
        issues.append(f"stale stage {item['stage']}: {'; '.join(item['reasons'])}")
    result = {"status": "ok" if not issues else "stale" if stale and len(issues) == len(stale) else "failed", "issues": issues, "stale": stale}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if issues:
        raise SystemExit(1)


def build_parser():
    parser = argparse.ArgumentParser(description="Knowledgebase Studio durable workflow controller")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init")
    init.add_argument("--root", required=True)
    init.add_argument("--goal", required=True)
    init.add_argument("--mode", choices=["auto", "learning", "operations", "reference", "hybrid"], default="auto")
    init.add_argument("--posture", choices=["unresolved", *sorted(PRODUCT_POSTURES)], default="unresolved")
    init.add_argument("--app", choices=["auto", "yes", "no"], default="auto")
    init.add_argument("--execution-policy", choices=["autonomous", "checkpointed"], default="autonomous")
    init.add_argument("--max-stage-attempts", type=int, default=3)
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=command_init)

    status = subparsers.add_parser("status")
    status.add_argument("--root", required=True)
    status.set_defaults(func=command_status)

    next_parser = subparsers.add_parser("next")
    next_parser.add_argument("--root", required=True)
    next_parser.add_argument("--claim", action="store_true")
    next_parser.set_defaults(func=command_next)

    complete = subparsers.add_parser("complete")
    complete.add_argument("--root", required=True)
    complete.add_argument("--stage", required=True)
    complete.add_argument("--decision", choices=["pass", "needs-work"], default="pass")
    complete.add_argument("--artifact", action="append", default=[])
    complete.add_argument("--notes")
    complete.set_defaults(func=command_complete)

    skip = subparsers.add_parser("skip")
    skip.add_argument("--root", required=True)
    skip.add_argument("--stage", required=True)
    skip.add_argument("--reason", required=True)
    skip.set_defaults(func=command_skip)

    block = subparsers.add_parser("block")
    block.add_argument("--root", required=True)
    block.add_argument("--stage")
    block.add_argument("--kind", choices=sorted(ALLOWED_BLOCKERS), required=True)
    block.add_argument("--reason", required=True)
    block.add_argument("--needed", required=True)
    block.set_defaults(func=command_block)

    resume = subparsers.add_parser("resume")
    resume.add_argument("--root", required=True)
    resume.add_argument("--resolution", required=True)
    resume.set_defaults(func=command_resume)

    invalidate = subparsers.add_parser("invalidate")
    invalidate.add_argument("--root", required=True)
    invalidate.add_argument("--from-stage", required=True)
    invalidate.add_argument("--reason", required=True)
    invalidate.set_defaults(func=command_invalidate)

    feedback = subparsers.add_parser("feedback")
    feedback.add_argument("--root", required=True)
    feedback.add_argument("--kind", choices=sorted(FEEDBACK_STAGE), required=True)
    feedback.add_argument("--reason", required=True)
    feedback.set_defaults(func=command_feedback)

    reconcile = subparsers.add_parser("reconcile")
    reconcile.add_argument("--root", required=True)
    reconcile.add_argument("--apply", action="store_true")
    reconcile.set_defaults(func=command_reconcile)

    check = subparsers.add_parser("check")
    check.add_argument("--root", required=True)
    check.set_defaults(func=command_check)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if getattr(args, "max_stage_attempts", 1) < 1:
        fail("--max-stage-attempts must be positive")
    args.func(args)


if __name__ == "__main__":
    main()
