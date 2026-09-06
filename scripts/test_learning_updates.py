"""Synthetic contract regressions; fixture receipts are not real user-study evidence."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from kb_content_check import validate as check_content
from kb_learning_check import check_learning
from kb_stage_check import require_dimension
from kb_update import check_update, plan_update
from kb_workflow import stage_deliverable_digests
from test_knowledgebase_studio import (
    SCRIPT_DIR, run, valid_content_coverage, valid_knowledge_model,
    valid_learning_design, write_locked_contract, write_valid_audit_artifacts,
)


class LearningUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "_kb-control").mkdir()
        write_locked_contract(self.root)
        write_valid_audit_artifacts(self.root)
        self.model = valid_knowledge_model()
        self.design = valid_learning_design()
        self.coverage = valid_content_coverage()
        self.save_baseline()

    def write_json(self, name, value):
        (self.root / "_kb-control" / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def save_baseline(self):
        self.write_json("knowledge-model.json", self.model)
        self.write_json("learning-design.json", self.design)
        self.write_json("content-coverage.json", self.coverage)

    def add_activity(self, interactive=False):
        template = SCRIPT_DIR.parent / "assets/control-templates/learning-activities.json"
        self.manifest = json.loads(template.read_text(encoding="utf-8"))
        self.manifest["status"] = "pass"
        self.activity = self.manifest["items"][0]
        self.activity.update(id="activity.one", unitId="unit.one", sourceRefs=["source.one#claim.one"])
        self.activity["review"].update(status="pass", evidencePaths=["_kb-control/editor-review.md"])
        (self.root / "_kb-control/editor-review.md").write_text("Synthetic editorial evidence fixture.", encoding="utf-8")
        if not interactive:
            self.activity.update(kind="operation", mode="text", cases=[])
            self.activity.pop("interaction")
            self.activity["steps"] = [{
                "precondition": "Open the supported tool.", "action": "Submit supplied meeting text.",
                "input": "Fictional meeting text.", "check": "Read the generated list and compare names to source.",
                "recovery": "If text is incomplete, request the missing portion.", "location": "操作步骤示范",
                "possibleResults": [{"result": "Text appears in the reply.", "nextAction": "Copy, save, open, and check it."}],
            }]
        else:
            asset = self.root / self.activity["interaction"]["assetPaths"][0]
            asset.parent.mkdir(parents=True)
            asset.write_text("<!doctype html><title>Synthetic asset fixture</title>", encoding="utf-8")
        anchors = []

        def collect(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key.lower().endswith("location"):
                        anchors.append(item)
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)

        collect(self.activity)
        page = self.root / "lesson.md"
        page.write_text(page.read_text(encoding="utf-8") + "\n\n" + "\n\n".join(anchors), encoding="utf-8")
        self.design["schemaVersion"] = 3
        self.design["lessons"][0].update(learningTaskType=self.activity["kind"], activityIds=["activity.one"])
        self.coverage["pages"][0]["activityIds"] = ["activity.one"]
        self.save_baseline()
        self.save_activity()

    def save_activity(self):
        self.write_json("learning-activities.json", self.manifest)

    def content(self, pages=None):
        control = self.root / "_kb-control"
        return check_content(self.root, control / "source-understanding.json", control / "knowledge-model.json", control / "content-coverage.json", page_paths=pages)

    def assert_kind(self, report, kind):
        self.assertEqual(report["status"], "fail", report)
        self.assertIn(kind, {item["kind"] for item in report["errors"]}, report)

    def receipts(self, plan):
        (self.root / "_kb-control/update-evidence.md").write_text("Synthetic update check evidence.", encoding="utf-8")
        plan["checks"] = [{"kind": kind, "status": "pass", "inputDigests": copy.deepcopy(plan["inputDigests"]),
                           "evidencePaths": ["_kb-control/update-evidence.md"]} for kind in plan["requiredChecks"]]
        return plan

    def test_required_dimension_cannot_be_not_applicable(self):
        errors = []
        require_dimension({}, {"sourceFidelity": "not_applicable"}, "sourceFidelity", errors, "pilot")
        self.assertEqual(errors[0]["kind"], "dimension-not-passed")

    def test_irrelevant_dimension_can_be_explicitly_allowed(self):
        errors = []
        require_dimension({}, {"visual": "not_applicable"}, "visual", errors, "pilot", allow_not_applicable=True)
        self.assertEqual(errors, [])

    def test_case_example_promise_is_checked_outside_main_path(self):
        self.coverage["pages"][0]["pageType"] = "case"
        self.design["lessons"][0]["workedExampleRequired"] = True
        self.save_baseline()
        self.assert_kind(self.content(), "worked-example-required")

    def test_new_example_requires_first_attempt_and_revision(self):
        self.coverage["schemaVersion"] = 2
        anchor = self.coverage["pages"][0]["fidelityChecks"][0]["location"]
        self.coverage["pages"][0]["workedExample"] = dict(required=True, kind="fictional", **{field: anchor for field in ("inputLocation", "judgmentLocation", "outputLocation", "transferLocation")})
        self.save_baseline()
        report = self.content()
        self.assert_kind(report, "worked-example-field")
        self.assertIn("Missing firstAttemptLocation.", {item["detail"] for item in report["errors"]})
        self.assertIn("Missing revisionLocation.", {item["detail"] for item in report["errors"]})

    def test_text_walkthrough_needs_no_frontend(self):
        self.add_activity()
        self.assertEqual(check_learning(self.root)["status"], "pass")

    def test_operation_requires_continuation_and_recovery(self):
        self.add_activity()
        self.activity["steps"][0].pop("recovery")
        self.activity["steps"][0]["possibleResults"][0].pop("nextAction")
        self.save_activity()
        report = check_learning(self.root)
        self.assert_kind(report, "learning-field")
        self.assertEqual(len([item for item in report["errors"] if item["kind"] == "learning-field"]), 2)

    def test_operation_requires_activity_even_in_scoped_check(self):
        self.design["schemaVersion"] = 3
        self.design["lessons"][0].update(learningTaskType="operation", activityIds=[])
        self.save_baseline()
        self.assert_kind(check_learning(self.root, page_paths=["lesson.md"]), "learning-list")

    def test_declared_missing_activity_fails(self):
        self.design["lessons"][0]["activityIds"] = ["missing"]
        self.save_baseline()
        self.assert_kind(check_learning(self.root), "missing-learning-activity")

    def test_operation_cannot_be_satisfied_by_unrelated_judgment_activity(self):
        self.add_activity(interactive=True)
        self.design["lessons"][0]["learningTaskType"] = "operation"
        self.save_baseline()
        self.assert_kind(check_learning(self.root), "learning-task-activity-mismatch")

    def test_activity_must_be_in_lesson_and_page_contracts(self):
        self.add_activity()
        self.coverage["pages"][0]["activityIds"] = []
        self.save_baseline()
        self.assert_kind(check_learning(self.root), "learning-page-coverage")
        self.design["lessons"][0].update(learningTaskType="concept", activityIds=[])
        self.save_baseline()
        self.assert_kind(check_learning(self.root), "learning-undeclared-activity")

    def test_interactive_content_contract_passes(self):
        self.add_activity(interactive=True)
        self.assertEqual(check_learning(self.root)["status"], "pass")

    def test_interaction_without_real_asset_fails(self):
        self.add_activity(interactive=True)
        self.activity["interaction"]["assetPaths"] = ["assets/missing.html"]
        self.save_activity()
        self.assert_kind(check_learning(self.root), "learning-missing-file")

    def test_interaction_requires_changed_material(self):
        self.add_activity(interactive=True)
        self.activity["cases"][1]["materialLocation"] = self.activity["cases"][0]["materialLocation"]
        self.save_activity()
        self.assert_kind(check_learning(self.root), "learning-transfer-material")

    def test_transfer_expected_difference_cannot_keep_same_answer(self):
        self.add_activity(interactive=True)
        self.activity["cases"][1]["expectedOutcome"] = self.activity["cases"][0]["expectedOutcome"]
        self.save_activity()
        self.assert_kind(check_learning(self.root), "learning-transfer-answer")

    def test_transfer_can_test_invariant_rule(self):
        self.add_activity(interactive=True)
        self.activity["cases"][1].update(expectedChange="same", expectedOutcome=self.activity["cases"][0]["expectedOutcome"])
        self.save_activity()
        self.assertEqual(check_learning(self.root)["status"], "pass")

    def test_optional_practice_cannot_block_reading(self):
        self.add_activity(interactive=True)
        self.activity["interaction"]["skipAllowed"] = False
        self.save_activity()
        self.assert_kind(check_learning(self.root), "learning-reading-gate")

    def test_app_requires_browser_evidence_for_each_activity(self):
        self.add_activity(interactive=True)
        self.assert_kind(check_learning(self.root, phase="app"), "learning-browser-status")

    def test_complete_browser_contract_is_accepted(self):
        self.add_activity(interactive=True)
        self.write_json("app-validation.json", {"learningActivities": [{"id": "activity.one", "status": "pass", "viewportWidths": [390, 1440], "behaviors": ["feedback", "retry", "transfer", "fallback", "keyboard", "mobile-reading"], "evidencePaths": ["_kb-control/editor-review.md"]}]})
        self.assertEqual(check_learning(self.root, phase="app")["status"], "pass")

    def test_learner_study_requires_completed_study_evidence(self):
        self.add_activity()
        self.activity["review"]["method"] = "learner-study"
        self.save_activity()
        self.assert_kind(check_learning(self.root), "learning-study-method")
        self.activity["review"]["learnerStudyStatus"] = "completed"
        self.save_activity()
        self.assert_kind(check_learning(self.root), "learning-list")

    def test_malformed_activity_ids_fail_without_crashing(self):
        self.add_activity()
        self.activity["id"] = {"wrong": "shape"}
        self.save_activity()
        self.assert_kind(check_learning(self.root), "learning-activity-id")

    def test_scoped_pilot_can_review_completed_item_before_whole_manifest(self):
        self.add_activity()
        self.manifest["status"] = "draft"
        self.save_activity()
        self.assertEqual(check_learning(self.root, required_ids=["activity.one"])["status"], "pass")
        self.assert_kind(check_learning(self.root), "learning-manifest-status")

    def test_interaction_asset_edit_invalidates_deliverable_fingerprint(self):
        self.add_activity(interactive=True)
        before = stage_deliverable_digests(self.root, "content")
        (self.root / self.activity["interaction"]["assetPaths"][0]).write_text("Changed synthetic asset.", encoding="utf-8")
        self.assertNotEqual(before, stage_deliverable_digests(self.root, "content"))

    def test_scoped_content_ignores_unrelated_broken_page_but_requires_requested_coverage(self):
        self.coverage["pages"].append({"path": "unrelated.md"})
        self.save_baseline()
        self.assertEqual(self.content(["lesson.md"])["status"], "pass")
        self.assert_kind(self.content(["missing.md"]), "scoped-page-coverage")

    def test_update_requires_review_receipts(self):
        plan = plan_update(self.root, ["lesson.md"])
        self.assert_kind(check_update(self.root, plan), "update-check-missing")
        self.assertEqual(check_update(self.root, self.receipts(plan))["status"], "pass")

    def test_scoped_lesson_metadata_does_not_expand_unrelated_pages(self):
        self.coverage["pages"].append({"path": "unrelated.md"})
        self.save_baseline()
        plan = plan_update(self.root, ["lesson.md", "_kb-control/learning-design.json", "_kb-control/content-coverage.json"], pages=["lesson.md"])
        self.assertEqual(plan["affectedPages"], ["lesson.md"])
        self.assertNotIn("architecture-review", plan["requiredChecks"])

    def test_shared_navigation_change_expands_scope(self):
        self.coverage["pages"].append({"path": "unrelated.md"})
        self.save_baseline()
        self.write_json("navigation-contract.json", {"primaryPath": ["lesson.md"]})
        plan = plan_update(self.root, ["_kb-control/navigation-contract.json"], pages=["lesson.md"])
        self.assertIn("unrelated.md", plan["affectedPages"])
        self.assertIn("architecture-review", plan["requiredChecks"])

    def test_declared_activity_asset_maps_to_its_page(self):
        self.add_activity(interactive=True)
        self.coverage["pages"].append({"path": "unrelated.md"})
        self.save_baseline()
        plan = plan_update(self.root, self.activity["interaction"]["assetPaths"])
        self.assertEqual(plan["affectedPages"], ["lesson.md"])
        self.assertIn("browser", plan["requiredChecks"])

    def test_update_cannot_remove_required_checks(self):
        plan = plan_update(self.root, ["lesson.md"])
        plan["requiredChecks"] = []
        self.assert_kind(check_update(self.root, plan), "update-check-missing")

    def test_source_edit_invalidates_update_plan(self):
        plan = self.receipts(plan_update(self.root, ["lesson.md"]))
        page = self.root / "lesson.md"
        page.write_text(page.read_text(encoding="utf-8") + "\nChanged boundary.", encoding="utf-8")
        self.assert_kind(check_update(self.root, plan), "update-stale-input")

    def test_app_directory_edit_invalidates_update_plan(self):
        app = self.root / "app"
        app.mkdir()
        (app / "index.html").write_text("Synthetic delivery.", encoding="utf-8")
        plan = self.receipts(plan_update(self.root, ["lesson.md"], delivery_paths=["app"]))
        self.assertIn("browser", plan["requiredChecks"])
        self.assertEqual(check_update(self.root, plan)["status"], "pass")
        (app / "index.html").write_text("Changed delivery.", encoding="utf-8")
        self.assert_kind(check_update(self.root, plan), "update-stale-input")

    def test_prerequisite_page_is_fingerprinted(self):
        prior = copy.deepcopy(self.model["units"][0])
        prior.update(id="unit.prior", canonicalOwner="prior.md", question="What comes before?", readerChange="Knows prerequisite.")
        self.model["units"][0]["dependencies"] = ["unit.prior"]
        self.model["units"].append(prior)
        self.model["progressions"][0]["unitIds"] = ["unit.prior", "unit.one"]
        (self.root / "prior.md").write_text("Prerequisite material.", encoding="utf-8")
        self.save_baseline()
        plan = self.receipts(plan_update(self.root, ["lesson.md"]))
        self.assertIn("prior.md", plan["inputDigests"])
        self.assertEqual(check_update(self.root, plan)["status"], "pass")
        (self.root / "prior.md").write_text("Changed prerequisite.", encoding="utf-8")
        self.assert_kind(check_update(self.root, plan), "update-stale-input")

    def test_update_preserves_stale_global_workflow(self):
        run("python3", str(SCRIPT_DIR / "kb_workflow.py"), "init", "--root", str(self.root), "--goal", "Test", "--app", "no")
        write_locked_contract(self.root)
        run("python3", str(SCRIPT_DIR / "kb_workflow.py"), "complete", "--root", str(self.root), "--stage", "intake")
        contract = self.root / "_kb-control/project-contract.yaml"
        contract.write_text(contract.read_text(encoding="utf-8") + "\n# Changed after intake.\n", encoding="utf-8")
        state = self.root / "_kb-control/workflow.json"
        before = state.read_bytes()
        report = check_update(self.root, self.receipts(plan_update(self.root, ["lesson.md"])))
        self.assertEqual(report["status"], "pass", report)
        self.assertEqual(report["globalWorkflow"]["status"], "stale")
        self.assertEqual(state.read_bytes(), before)

    def test_update_cli_rejects_report_inside_tracked_delivery(self):
        (self.root / "app").mkdir()
        import subprocess
        result = subprocess.run(["python3", str(SCRIPT_DIR / "kb_update.py"), "plan", "--root", str(self.root), "--path", "lesson.md", "--delivery-path", "app", "--output", "app/plan.json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "app/plan.json").exists())


if __name__ == "__main__":
    unittest.main()
