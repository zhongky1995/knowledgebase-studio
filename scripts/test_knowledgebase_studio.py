#!/usr/bin/env python3

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
WORKFLOW = SCRIPT_DIR / "kb_workflow.py"
AUDIT = SCRIPT_DIR / "kb_audit.py"
RELEASE_CHECK = SCRIPT_DIR / "kb_release_check.py"
CONTENT_CHECK = SCRIPT_DIR / "kb_content_check.py"
STAGE_CHECK = SCRIPT_DIR / "kb_stage_check.py"


def run(*args, expected=0):
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode != expected:
        raise AssertionError(
            f"Expected exit {expected}, got {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return json.loads(result.stdout)


def write_locked_contract(
    root,
    *,
    app_required="no",
    package_required="false",
    distribution_mode="local_entrypoint",
    release_root="",
):
    (root / "_kb-control" / "project-contract.yaml").write_text(
        """schema_version: 3
status: locked
goal: Build a calm internal reading manual
primary_mode: learning
product_posture: reading_manual
audiences:
  - novice staff
reader_moment: first visit before work
default_user_action: start reading
first_success: understand one useful model
catalog_visibility: progressive_disclosure
exercise_policy: optional_after_reading
progress_semantics: resume_position_only
pressure_policy: no_required_output
source_presentation: internal_only
intent_mirror: Approving this means a reader can begin without completing a task.
top_tasks:
  - understand the standard
public_root: .
public_paths:
  - README.md
canonical_sources: []
preserve: []
allowed_changes: []
forbidden_changes: []
anti_goals:
  - no task gate before reading
acceptance:
  entry: one calm reading action
assumptions: []
app_required: {app_required}
package_required: {package_required}
distribution_mode: {distribution_mode}
audience_scope: internal
release_root: "{release_root}"
external_publish_authorized: false
license_policy: internal_only
license_files: []
""".format(
            app_required=app_required,
            package_required=package_required,
            distribution_mode=distribution_mode,
            release_root=release_root,
        ),
        encoding="utf-8",
    )


def valid_source_understanding():
    return {
        "schemaVersion": 1,
        "sources": [{
            "id": "source.one",
            "path": "internal-standard",
            "role": "internal-standard",
            "authority": "internal",
            "summary": "Defines one useful internal rule.",
            "coreClaims": [{
                "id": "claim.one",
                "statement": "A useful rule.",
                "evidence": "Approved internal standard.",
                "confidence": "high",
            }],
            "mechanisms": [],
            "boundaries": [],
            "conflicts": [],
            "unknowns": [],
        }],
    }


def valid_knowledge_model():
    return {
        "schemaVersion": 1,
        "units": [{
            "id": "unit.one",
            "question": "What is the rule?",
            "answer": "A useful rule.",
            "readerChange": "Can explain the rule.",
            "mechanism": "The reason the rule works.",
            "boundaries": ["Not universal."],
            "sourceRefs": ["source.one#claim.one"],
            "dependencies": [],
            "canonicalOwner": "lesson.md",
            "role": "main-path",
        }],
        "progressions": [{
            "id": "core",
            "audience": "novice staff",
            "unitIds": ["unit.one"],
            "logic": "The only main-path unit establishes the first useful model.",
        }],
    }


def valid_inventory():
    return {
        "schemaVersion": 1,
        "publicCorpusCount": 1,
        "items": [{
            "path": "lesson.md",
            "visibility": "public",
            "section": "root",
            "pageType": "main-path",
            "primaryJob": "Teach one useful rule.",
            "recommendedAction": "keep",
            "confidence": "high",
        }],
    }


def valid_learning_design():
    return {
        "schemaVersion": 1,
        "productPosture": "reading_manual",
        "learnerVisibleUnitCount": 1,
        "routes": [{
            "id": "core",
            "title": "Core",
            "role": "core",
            "continuous": True,
            "entryPath": "lesson.md",
            "unitIds": ["unit.one"],
        }],
        "lessons": [{
            "unitId": "unit.one",
            "startingState": "The reader does not know the rule.",
            "learningResult": "Can explain and apply the rule.",
            "prerequisiteUnitIds": [],
            "newTerms": [],
            "likelyMisconception": "The rule is universal.",
            "workedExampleRequired": False,
            "practicePolicy": "optional_after_reading",
            "transferEvidence": "Classifies a second case.",
            "estimatedReadingMinutes": 5,
        }],
    }


def write_valid_audit_artifacts(root, *, source=None):
    control = root / "_kb-control"
    body = "\n\n".join(f"Useful explanation with a concrete boundary and example {index}." for index in range(12))
    (root / "lesson.md").write_text("# Lesson\n\n" + body + "\n", encoding="utf-8")
    (control / "content-inventory.json").write_text(json.dumps(valid_inventory()), encoding="utf-8")
    (control / "audit-report.md").write_text("# Audit\n\n" + "Evidence-backed audit conclusion. " * 30, encoding="utf-8")
    (control / "source-understanding.json").write_text(
        json.dumps(source if source is not None else valid_source_understanding()), encoding="utf-8"
    )


def valid_pilot_verdict():
    return {
        "schemaVersion": 1,
        "status": "pass",
        "scaleApproved": True,
        "representativePaths": ["lesson.md"],
        "assumptionsTested": [{"id": "hardest", "result": "pass", "evidence": "lesson.md"}],
        "dimensions": {
            "posture": "pass",
            "sourceFidelity": "pass",
            "usefulness": "pass",
            "distinctivePageJobs": "pass",
            "exampleDepth": "pass",
            "progression": "pass",
            "transfer": "pass",
            "navigation": "pass",
        },
        "counterReview": {"status": "pass", "reviewedRisks": ["abstract example"]},
        "criticalIssues": [],
        "unresolvedRisks": [],
    }


def valid_content_coverage():
    return {
        "schemaVersion": 1,
        "pages": [{
            "path": "lesson.md",
            "pageType": "main-path",
            "primaryQuestion": "What is the useful rule?",
            "readerChange": "Can explain and apply the useful rule.",
            "knowledgeUnitIds": ["unit.one"],
            "essentialPoints": ["The useful rule remains intact."],
            "fidelityChecks": [{
                "point": "The useful rule remains intact.",
                "status": "preserved",
                "location": "Useful explanation with a concrete boundary and example 0.",
            }],
            "distinctiveValue": "Owns the rule mechanism and boundary.",
            "workedExample": {"required": False},
            "practice": {
                "policy": "optional_after_reading",
                "output": "Optional classification result.",
                "feedback": "Compare against the stated boundary.",
            },
            "estimatedReadingMinutes": 5,
            "preservedFrom": ["lesson.md"],
            "evidenceStatus": "verified",
        }],
    }


class WorkflowTests(unittest.TestCase):
    def test_intake_rejects_unresolved_product_posture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run("python3", str(WORKFLOW), "init", "--root", str(root), "--goal", "test")
            result = subprocess.run(
                ["python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "intake"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("product_posture", result.stdout)

    def test_changed_dependency_makes_downstream_evidence_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run("python3", str(WORKFLOW), "init", "--root", str(root), "--goal", "test")
            write_locked_contract(root)
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "intake")

            control = root / "_kb-control"
            write_valid_audit_artifacts(root)
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "audit")

            (control / "architecture-decision.md").write_text("# Architecture\n\n" + "Approved architecture decision. " * 30, encoding="utf-8")
            (control / "migration-map.yaml").write_text(
                "migrations:\n  - id: one\n    old_path: lesson.md\n    action: keep\n    target_path: lesson.md\n    canonical_owner: lesson.md\n    preservation_status: preserved\n",
                encoding="utf-8",
            )
            (control / "knowledge-model.json").write_text(
                json.dumps(valid_knowledge_model()), encoding="utf-8"
            )
            (control / "learning-design.json").write_text(json.dumps(valid_learning_design()), encoding="utf-8")
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "architecture")

            (control / "audit-report.md").write_text("# Audit changed\n", encoding="utf-8")
            checked = run("python3", str(WORKFLOW), "check", "--root", str(root), expected=1)
            self.assertEqual(checked["status"], "stale")
            self.assertEqual(checked["stale"][0]["stage"], "audit")
            self.assertTrue(any(item["stage"] == "architecture" for item in checked["stale"]))
            reconciled = run("python3", str(WORKFLOW), "reconcile", "--root", str(root), "--apply")
            self.assertEqual(reconciled["from_stage"], "audit")
            self.assertEqual(reconciled["next"]["stage"], "audit")

    def test_source_presentation_feedback_returns_to_intake(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run("python3", str(WORKFLOW), "init", "--root", str(root), "--goal", "test")
            write_locked_contract(root)
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "intake")
            result = run(
                "python3", str(WORKFLOW), "feedback", "--root", str(root),
                "--kind", "source-presentation", "--reason", "make evidence internal only",
            )
            self.assertEqual(result["from_stage"], "intake")
            self.assertEqual(result["next"]["stage"], "intake")

    def test_public_contract_rejects_implicit_license_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run("python3", str(WORKFLOW), "init", "--root", str(root), "--goal", "public site")
            write_locked_contract(root)
            contract = root / "_kb-control" / "project-contract.yaml"
            text = contract.read_text(encoding="utf-8").replace(
                "audience_scope: internal", "audience_scope: public"
            )
            contract.write_text(text, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "intake"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("license_policy", result.stdout)

    def test_audit_cannot_pass_with_empty_source_understanding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run("python3", str(WORKFLOW), "init", "--root", str(root), "--goal", "test")
            write_locked_contract(root)
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "intake")
            write_valid_audit_artifacts(root, source={"sources": []})
            result = subprocess.run(
                ["python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "audit"],
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("empty-source-understanding", result.stdout)

    def test_full_workflow_requires_and_accepts_current_semantic_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run("python3", str(WORKFLOW), "init", "--root", str(root), "--goal", "full", "--app", "yes")
            write_locked_contract(
                root,
                app_required="yes",
                package_required="true",
                distribution_mode="static_site",
                release_root="release",
            )
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "intake")
            control = root / "_kb-control"
            write_valid_audit_artifacts(root)
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "audit")

            (control / "architecture-decision.md").write_text("# Architecture\n\n" + "Approved decision. " * 40, encoding="utf-8")
            (control / "migration-map.yaml").write_text(
                "migrations:\n  - id: one\n    old_path: lesson.md\n    action: keep\n    target_path: lesson.md\n    canonical_owner: lesson.md\n    preservation_status: preserved\n",
                encoding="utf-8",
            )
            (control / "knowledge-model.json").write_text(json.dumps(valid_knowledge_model()), encoding="utf-8")
            (control / "learning-design.json").write_text(json.dumps(valid_learning_design()), encoding="utf-8")
            navigation = {
                "schemaVersion": 1,
                "primaryPath": {"from": "home", "label": "Start", "destination": "lesson.md", "maxClicks": 1},
                "directEntries": [{"id": "route.one", "label": "Lesson", "destination": "lesson.md", "maxClicks": 1}],
                "catalog": {"defaultState": "collapsed", "purpose": "browse"},
            }
            (control / "navigation-contract.json").write_text(json.dumps(navigation), encoding="utf-8")
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "architecture")

            (control / "pilot-review.md").write_text("# Pilot\n\n" + "Pilot evidence. " * 50, encoding="utf-8")
            (control / "pilot-verdict.json").write_text(json.dumps(valid_pilot_verdict()), encoding="utf-8")
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "pilot")

            (control / "content-build-report.md").write_text("# Content\n\n" + "Content evidence. " * 50, encoding="utf-8")
            (control / "content-coverage.json").write_text(json.dumps(valid_content_coverage()), encoding="utf-8")
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "content")

            app = root / "app"
            app.mkdir()
            (app / "index.html").write_text("<h1>App</h1>", encoding="utf-8")
            (control / "app-validation.md").write_text("# App\n\n" + "Browser evidence. " * 50, encoding="utf-8")
            app_validation = {
                "schemaVersion": 1,
                "status": "pass",
                "appPaths": ["app"],
                "build": {"status": "pass", "commands": ["fixture"]},
                "browser": {
                    "status": "pass",
                    "testedEntrypoints": ["app/index.html"],
                    "viewportWidths": [1440, 390],
                    "checks": ["console", "overflow", "links"],
                },
                "navigation": {
                    "primaryPath": {"clickable": True, "keyboard": True, "maxClicks": 1},
                    "directEntries": [{
                        "id": "route.one",
                        "label": "Lesson",
                        "destination": "lesson.md",
                        "maxClicks": 1,
                        "clickable": True,
                        "keyboard": True,
                    }],
                },
                "checksNotRun": [],
                "remainingRisks": [],
            }
            (control / "app-validation.json").write_text(json.dumps(app_validation), encoding="utf-8")
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "app")

            (control / "qc-report.md").write_text("# QC\n\n" + "Independent evidence. " * 50, encoding="utf-8")
            qc_verdict = {
                "schemaVersion": 1,
                "status": "pass",
                "overallClaim": "pass",
                "dimensions": {
                    "corpusIntegrity": "pass",
                    "productArchitecture": "pass",
                    "contentQuality": "pass",
                    "learningTransfer": "pass",
                    "evidence": "pass",
                    "appExperience": "pass",
                },
                "evidence": {
                    "corpusIntegrity": ["_kb-control/content-audit-metrics.json"],
                    "productArchitecture": ["_kb-control/architecture-decision.md"],
                    "contentQuality": ["_kb-control/content-integrity.json"],
                    "learningTransfer": ["_kb-control/pilot-verdict.json"],
                    "evidence": ["_kb-control/source-understanding.json"],
                    "appExperience": ["_kb-control/app-validation.json"],
                },
                "checksNotRun": [],
                "criticalIssues": [],
            }
            (control / "qc-verdict.json").write_text(json.dumps(qc_verdict), encoding="utf-8")
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "qc")

            release = root / "release"
            release.mkdir()
            (release / "index.html").write_text("<h1>Release</h1>", encoding="utf-8")
            release_config = {
                "distributionMode": "static_site",
                "audienceScope": "internal",
                "entrypoint": "index.html",
                "requiredFiles": [],
                "licensePolicy": "internal_only",
                "licenseFiles": [],
            }
            (control / "knowledgebase-release.json").write_text(json.dumps(release_config), encoding="utf-8")
            (control / "release-report.md").write_text("# Release\n\n" + "Release evidence. " * 50, encoding="utf-8")
            release_verdict = {
                "schemaVersion": 1,
                "status": "pass",
                "releaseRoot": "release",
                "releaseConfig": "_kb-control/knowledgebase-release.json",
                "browser": {"status": "pass", "testedEntrypoints": ["release/index.html"], "viewportWidths": [1440, 390]},
                "checksNotRun": [],
                "externalPublicationPerformed": False,
            }
            (control / "release-verdict.json").write_text(json.dumps(release_verdict), encoding="utf-8")
            completed = run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "release")
            self.assertEqual(completed["next"]["action"], "complete")
            checked = run("python3", str(WORKFLOW), "check", "--root", str(root))
            self.assertEqual(checked["status"], "ok")


class AuditTests(unittest.TestCase):
    def test_explicit_public_roots_exclude_archives(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "public").mkdir()
            (root / "history").mkdir()
            (root / "public" / "README.md").write_text("# Current\n\n面向小白读者的 useful text.\n", encoding="utf-8")
            (root / "history" / "old.md").write_text("# Old\n\nTODO\n", encoding="utf-8")
            (root / ".knowledgebase-audit.json").write_text(
                json.dumps({"publicRoots": ["public"], "archiveRoots": ["history"]}),
                encoding="utf-8",
            )
            report = run("python3", str(AUDIT), str(root))
            self.assertEqual(report["stats"]["markdownFiles"], 1)
            self.assertEqual(report["scope"]["publicRoots"], ["public"])
            self.assertFalse(report["warnings"])

    def test_near_duplicate_pages_are_flagged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shared = "这是用于解释机制、边界、条件和应用判断的完整段落。" * 40
            (root / "one.md").write_text(f"# One\n\n{shared}\n", encoding="utf-8")
            (root / "two.md").write_text(f"# Two\n\n{shared}少量不同结尾。\n", encoding="utf-8")
            report = run("python3", str(AUDIT), str(root))
            self.assertTrue(any(item["type"] == "near-duplicate-page" for item in report["warnings"]))

    def test_forced_shared_outline_is_flagged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shared = "\n\n".join(
                f"## {heading}\n\n{heading} 的独立说明。"
                for heading in ["这一讲解决什么问题", "机制", "常见错误", "练习", "验收标准"]
            )
            (root / "one.md").write_text(f"# One\n\n{shared}\n\n## 独有 A\n\nA。\n", encoding="utf-8")
            (root / "two.md").write_text(f"# Two\n\n{shared}\n\n## 独有 B\n\nB。\n", encoding="utf-8")
            report = run("python3", str(AUDIT), str(root))
            self.assertTrue(any(item["type"] == "repeated-outline-pattern" for item in report["warnings"]))


class StageGateTests(unittest.TestCase):
    def test_empty_inventory_cannot_pass_audit_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / "_kb-control"
            control.mkdir()
            (control / "audit-metrics.json").write_text(
                json.dumps({"status": "ok", "stats": {"markdownFiles": 0}, "errors": [], "warnings": []}),
                encoding="utf-8",
            )
            (control / "content-inventory.json").write_text("{}\n", encoding="utf-8")
            (control / "audit-report.md").write_text("# Audit\n\n" + "Evidence. " * 80, encoding="utf-8")
            report = run("python3", str(STAGE_CHECK), str(root), "--stage", "audit", expected=1)
            self.assertTrue(any(item["kind"] == "empty-inventory" for item in report["errors"]))

    def test_empty_migration_map_cannot_pass_architecture_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / "_kb-control"
            control.mkdir()
            (root / "lesson.md").write_text("# Lesson\n", encoding="utf-8")
            (control / "content-inventory.json").write_text(json.dumps(valid_inventory()), encoding="utf-8")
            (control / "architecture-decision.md").write_text("# Architecture\n\n" + "Decision. " * 80, encoding="utf-8")
            (control / "migration-map.yaml").write_text("migrations: []\n", encoding="utf-8")
            report = run("python3", str(STAGE_CHECK), str(root), "--stage", "architecture", expected=1)
            self.assertTrue(any(item["kind"] == "empty-migration-map" for item in report["errors"]))

    def test_pilot_requires_counter_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / "_kb-control"
            control.mkdir()
            (root / "lesson.md").write_text("# Lesson\n", encoding="utf-8")
            (control / "pilot-review.md").write_text("# Pilot\n\n" + "Evidence. " * 80, encoding="utf-8")
            verdict = valid_pilot_verdict()
            verdict["counterReview"] = {"status": "not_run", "reviewedRisks": []}
            (control / "pilot-verdict.json").write_text(json.dumps(verdict), encoding="utf-8")
            report = run("python3", str(STAGE_CHECK), str(root), "--stage", "pilot", expected=1)
            self.assertTrue(any(item["kind"] == "pilot-counter-review" for item in report["errors"]))

    def test_app_requires_real_browser_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = root / "_kb-control"
            control.mkdir()
            app = root / "app"
            app.mkdir()
            (control / "app-validation.md").write_text("# App\n\n" + "Evidence. " * 80, encoding="utf-8")
            result = {
                "status": "pass",
                "appPaths": ["app"],
                "browser": {"status": "not_run", "viewportWidths": [], "checks": []},
                "navigation": {"primaryPath": {"clickable": True, "keyboard": True, "maxClicks": 1}},
                "checksNotRun": ["browser"],
            }
            (control / "app-validation.json").write_text(json.dumps(result), encoding="utf-8")
            report = run("python3", str(STAGE_CHECK), str(root), "--stage", "app", expected=1)
            self.assertTrue(any(item["kind"] == "browser-not-run" for item in report["errors"]))

    def test_content_mutation_makes_passed_pilot_and_content_stale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run("python3", str(WORKFLOW), "init", "--root", str(root), "--goal", "test")
            write_locked_contract(root)
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "intake")
            control = root / "_kb-control"
            write_valid_audit_artifacts(root)
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "audit")
            (control / "architecture-decision.md").write_text("# Architecture\n\n" + "Approved decision. " * 40, encoding="utf-8")
            (control / "migration-map.yaml").write_text(
                "migrations:\n  - id: one\n    old_path: lesson.md\n    action: keep\n    target_path: lesson.md\n    canonical_owner: lesson.md\n    preservation_status: preserved\n",
                encoding="utf-8",
            )
            (control / "knowledge-model.json").write_text(json.dumps(valid_knowledge_model()), encoding="utf-8")
            (control / "learning-design.json").write_text(json.dumps(valid_learning_design()), encoding="utf-8")
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "architecture")
            (control / "pilot-review.md").write_text("# Pilot\n\n" + "Pilot evidence. " * 50, encoding="utf-8")
            (control / "pilot-verdict.json").write_text(json.dumps(valid_pilot_verdict()), encoding="utf-8")
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "pilot")
            (control / "content-build-report.md").write_text("# Content\n\n" + "Content evidence. " * 50, encoding="utf-8")
            (control / "content-coverage.json").write_text(json.dumps(valid_content_coverage()), encoding="utf-8")
            run("python3", str(WORKFLOW), "complete", "--root", str(root), "--stage", "content")
            lesson = root / "lesson.md"
            lesson.write_text(lesson.read_text(encoding="utf-8") + "\nChanged after pass.\n", encoding="utf-8")
            checked = run("python3", str(WORKFLOW), "check", "--root", str(root), expected=1)
            self.assertEqual(checked["status"], "stale")
            self.assertTrue(any(item["stage"] == "pilot" for item in checked["stale"]))
            self.assertTrue(any(item["stage"] == "content" for item in checked["stale"]))


class ReleaseCheckTests(unittest.TestCase):
    def write_config(self, path, **overrides):
        config = {
            "distributionMode": "static_site",
            "audienceScope": "internal",
            "entrypoint": "index.html",
            "requiredFiles": ["styles.css"],
            "licensePolicy": "internal_only",
            "licenseFiles": [],
        }
        config.update(overrides)
        path.write_text(json.dumps(config), encoding="utf-8")

    def test_clean_static_site_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            release = base / "release"
            release.mkdir()
            (release / "assets").mkdir()
            (release / "index.html").write_text(
                '<link rel="stylesheet" href="styles.css"><a href="guide.md">Guide</a>',
                encoding="utf-8",
            )
            (release / "styles.css").write_text("body { color: #111; }\n", encoding="utf-8")
            (release / "guide.md").write_text("# Guide\n\n![Diagram](assets/pic.png)\n", encoding="utf-8")
            (release / "assets" / "pic.png").write_bytes(b"png")
            config = base / "release.json"
            self.write_config(config)
            report = run("python3", str(RELEASE_CHECK), str(release), "--config", str(config))
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["stats"]["markdownFiles"], 1)

    def test_internal_marker_and_absolute_path_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            release = base / "release"
            release.mkdir()
            (release / "index.html").write_text(
                '<p>See /Users/example/_kb-control/qc-report.md</p>', encoding="utf-8"
            )
            (release / "styles.css").write_text("", encoding="utf-8")
            config = base / "release.json"
            self.write_config(config)
            report = run(
                "python3", str(RELEASE_CHECK), str(release), "--config", str(config), expected=1
            )
            self.assertEqual(report["status"], "fail")
            self.assertTrue(any(item["kind"] == "forbidden-marker" for item in report["errors"]))

    def test_public_release_requires_explicit_license_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            release = base / "release"
            release.mkdir()
            (release / "index.html").write_text("<h1>Public</h1>", encoding="utf-8")
            (release / "styles.css").write_text("", encoding="utf-8")
            config = base / "release.json"
            self.write_config(config, audienceScope="public", licensePolicy="internal_only")
            report = run(
                "python3", str(RELEASE_CHECK), str(release), "--config", str(config), expected=1
            )
            self.assertEqual(report["status"], "fail")
            self.assertTrue(any(item["kind"] == "license-policy" for item in report["errors"]))

    def test_public_release_with_declared_license_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            release = base / "release"
            release.mkdir()
            (release / "index.html").write_text('<a href="LICENSE.md">License</a>', encoding="utf-8")
            (release / "styles.css").write_text("", encoding="utf-8")
            (release / "LICENSE.md").write_text("# User-selected license\n", encoding="utf-8")
            config = base / "release.json"
            self.write_config(
                config,
                audienceScope="public",
                licensePolicy="explicit_files",
                licenseFiles=["LICENSE.md"],
            )
            report = run("python3", str(RELEASE_CHECK), str(release), "--config", str(config))
            self.assertEqual(report["status"], "pass")

    def test_single_file_rejects_sidecar_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            release = base / "release"
            release.mkdir()
            (release / "index.html").write_text('<link rel="stylesheet" href="styles.css">', encoding="utf-8")
            (release / "styles.css").write_text("", encoding="utf-8")
            config = base / "release.json"
            self.write_config(config, distributionMode="single_file")
            report = run(
                "python3", str(RELEASE_CHECK), str(release), "--config", str(config), expected=1
            )
            self.assertTrue(any(item["kind"] == "single-file-assets" for item in report["errors"]))


class ContentCheckTests(unittest.TestCase):
    def write_contracts(self, root, *, cycle=False, omit_fidelity=False):
        control = root / "_kb-control"
        control.mkdir()
        (root / "lesson.md").write_text("# Lesson\n\nUseful explanation.\n", encoding="utf-8")
        source = {
            "schemaVersion": 1,
            "sources": [{
                "id": "source.one",
                "path": "source.md",
                "role": "internal-standard",
                "authority": "internal",
                "summary": "Defines the internal rule and why it exists.",
                "coreClaims": [{
                    "id": "claim.one",
                    "statement": "A useful claim.",
                    "evidence": "Internal policy section 1.",
                    "confidence": "high",
                }],
                "mechanisms": [{"id": "mechanism.one", "description": "Cause and effect."}],
                "boundaries": ["Not for high-risk decisions."],
                "conflicts": [],
                "unknowns": [],
            }],
        }
        model = {
            "schemaVersion": 1,
            "units": [{
                "id": "unit.one",
                "question": "What should the reader understand?",
                "answer": "The useful claim.",
                "readerChange": "Can explain and apply the rule.",
                "mechanism": "Cause and effect.",
                "boundaries": ["Not for high-risk decisions."],
                "sourceRefs": ["source.one#claim.one"],
                "dependencies": ["unit.one"] if cycle else [],
                "canonicalOwner": "lesson.md",
                "role": "main-path",
            }],
            "progressions": [],
        }
        point = "The claim and its boundary remain intact."
        coverage = {
            "schemaVersion": 1,
            "pages": [{
                "path": "lesson.md",
                "pageType": "main-path",
                "primaryQuestion": "What should the reader understand?",
                "readerChange": "Can explain and apply the rule.",
                "knowledgeUnitIds": ["unit.one"],
                "essentialPoints": [point],
                "fidelityChecks": [] if omit_fidelity else [{
                    "point": point,
                    "status": "preserved",
                    "location": "Useful explanation",
                }],
                "distinctiveValue": "Owns the rule mechanism and boundary.",
                "preservedFrom": [],
                "evidenceStatus": "verified",
            }],
        }
        (control / "source-understanding.json").write_text(json.dumps(source), encoding="utf-8")
        (control / "knowledge-model.json").write_text(json.dumps(model), encoding="utf-8")
        (control / "content-coverage.json").write_text(json.dumps(coverage), encoding="utf-8")

    def test_content_understanding_chain_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_contracts(root)
            report = run("python3", str(CONTENT_CHECK), str(root))
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["stats"]["fidelityChecks"], 1)

    def test_missing_fidelity_check_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_contracts(root, omit_fidelity=True)
            report = run("python3", str(CONTENT_CHECK), str(root), expected=1)
            self.assertTrue(any(item["kind"] == "missing-fidelity-check" for item in report["errors"]))

    def test_dependency_cycle_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_contracts(root, cycle=True)
            report = run("python3", str(CONTENT_CHECK), str(root), expected=1)
            self.assertTrue(any(item["kind"] == "dependency-cycle" for item in report["errors"]))


if __name__ == "__main__":
    unittest.main()
