"""Regression contracts from beginner explanation failures, not learner studies."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from kb_content_check import validate as check_content
from kb_stage_check import validate_learning_design, validate_pilot
from test_knowledgebase_studio import (
    SCRIPT_DIR, valid_content_coverage, valid_knowledge_model, valid_learning_design,
    valid_pilot_verdict, write_locked_contract, write_valid_audit_artifacts,
)


class NoviceExplanationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.control = self.root / "_kb-control"
        self.control.mkdir()
        write_locked_contract(self.root)
        write_valid_audit_artifacts(self.root)
        self.model = valid_knowledge_model()
        self.design = valid_learning_design()
        self.design["schemaVersion"] = 3
        self.design["lessons"][0].update(learningTaskType="concept", activityIds=[])
        self.coverage = valid_content_coverage()
        self.verdict = valid_pilot_verdict()
        self.fragments = json.loads((SCRIPT_DIR.parent / "assets/control-templates/novice-mental-model.json").read_text())
        self.design.update(copy.deepcopy(self.fragments["learningDesign"]))
        for step in self.design["scenarioSpine"]["steps"]:
            step["unitId"] = "unit.one"
        self.design["scenarioSpine"]["everydayQuestions"][0]["unitIds"] = ["unit.one"]
        self.verdict["comprehensionReview"] = copy.deepcopy(self.fragments["comprehensionReview"])
        # Synthetic receipts exercise validation, never claim observed comprehension.
        for check in self.verdict["comprehensionReview"]["checks"]:
            check.update(status="pass", rationale="Synthetic editorial fixture, not a learner observation.")
        self.page = self.root / "lesson.md"
        self.page.write_text(self.page.read_text() + "\n" + self.verdict["comprehensionReview"]["checks"][0]["excerpt"])
        (self.control / "pilot-review.md").write_text("Synthetic editorial review fixture. " * 30)
        self.save()

    def save(self):
        for name, value in [("knowledge-model", self.model), ("learning-design", self.design),
                            ("content-coverage", self.coverage), ("pilot-verdict", self.verdict)]:
            (self.control / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False))

    def stage(self, phase):
        self.save()
        errors = []
        (validate_learning_design if phase == "architecture" else validate_pilot)(self.root, errors, [], {})
        return errors

    def content(self):
        self.save()
        return check_content(self.root, self.control / "source-understanding.json",
                             self.control / "knowledge-model.json", self.control / "content-coverage.json")["errors"]

    def assert_error(self, errors, kind):
        self.assertIn(kind, {e["kind"] for e in errors}, errors)

    def mechanism_example(self):
        lesson = self.design["lessons"][0]
        lesson["workedExampleRequired"] = True
        lesson["exampleContract"] = copy.deepcopy(self.fragments["lessonExampleContract"])
        example = dict(required=True, pattern="mechanism_trace", kind="fictional")
        for field in ("input", "participants", "trace", "output", "boundary", "transfer"):
            example[f"{field}Location"] = lesson["exampleContract"][field]
        self.coverage["pages"][0]["workedExample"] = example
        self.page.write_text(self.page.read_text() + "\n" + "\n".join(v for k, v in example.items() if k.endswith("Location")))

    def test_complete_novice_design_and_editorial_pilot_pass(self):
        self.assertEqual(self.stage("architecture"), [])
        self.assertEqual(self.stage("pilot"), [])

    def test_novice_profile_cannot_pass_without_whole_scenario(self):
        self.design.pop("scenarioSpine")
        self.assert_error(self.stage("architecture"), "scenario-spine")

    def test_spine_requires_the_handoff_not_only_topic_names(self):
        self.design["scenarioSpine"]["steps"][0].pop("handoff")
        self.assert_error(self.stage("architecture"), "scenario-step")

    def test_everyday_question_cannot_point_to_unknown_unit(self):
        self.design["scenarioSpine"]["everydayQuestions"][0]["unitIds"] = ["missing"]
        self.assert_error(self.stage("architecture"), "scenario-unit")

    def test_profile_typo_cannot_silently_disable_gate(self):
        self.design["explanationProfile"] = "novice_mental_models"
        self.assert_error(self.stage("architecture"), "explanation-profile")

    def test_legacy_project_does_not_acquire_new_profile_requirements(self):
        self.design.pop("explanationProfile")
        self.design.pop("scenarioSpine")
        self.verdict.pop("comprehensionReview")
        self.assertEqual(self.stage("architecture"), [])
        self.assertEqual(self.stage("pilot"), [])

    def test_pilot_pass_flags_alone_do_not_satisfy_profile(self):
        self.verdict.pop("comprehensionReview")
        self.assert_error(self.stage("pilot"), "comprehension-review")

    def test_all_comprehension_dimensions_need_review(self):
        self.verdict["comprehensionReview"]["checks"].pop()
        self.assert_error(self.stage("pilot"), "comprehension-missing-dimension")

    def test_deleted_excerpt_invalidates_review(self):
        self.page.write_text("# The reviewed explanation was removed.")
        self.assert_error(self.stage("pilot"), "comprehension-excerpt")

    def test_unreviewed_pilot_page_cannot_hide_behind_one_good_page(self):
        (self.root / "second.md").write_text("# Another pilot page")
        self.verdict["representativePaths"].append("second.md")
        self.assert_error(self.stage("pilot"), "comprehension-page-coverage")

    def test_failed_comprehension_cannot_be_overridden_by_top_level_pass(self):
        self.verdict["comprehensionReview"]["checks"][0]["status"] = "fail"
        self.assert_error(self.stage("pilot"), "comprehension-not-passed")

    def test_observed_learner_claim_requires_evidence(self):
        self.verdict["comprehensionReview"]["reviewType"] = "learner_observed"
        self.assert_error(self.stage("pilot"), "comprehension-observation")

    def test_observation_path_cannot_escape_project(self):
        self.verdict["comprehensionReview"].update(reviewType="learner_observed", observationEvidencePaths=["../external.md"])
        self.assert_error(self.stage("pilot"), "explanation-path")

    def test_mechanism_example_needs_no_artificial_draft_revision(self):
        self.mechanism_example()
        self.assertEqual(self.stage("architecture"), [])
        self.assertEqual(self.content(), [])

    def test_mechanism_example_requires_actual_intermediate_trace(self):
        self.mechanism_example()
        self.design["lessons"][0]["exampleContract"].pop("trace")
        self.assert_error(self.stage("architecture"), "learning-example-field")
        self.coverage["pages"][0]["workedExample"].pop("traceLocation")
        self.assert_error(self.content(), "worked-example-field")

    def test_mechanism_locations_must_exist_in_real_page(self):
        self.mechanism_example()
        self.coverage["pages"][0]["workedExample"]["boundaryLocation"] = "An invented missing passage."
        self.assert_error(self.content(), "worked-example-location-not-found")

    def test_page_cannot_silently_change_example_pattern(self):
        self.mechanism_example()
        self.coverage["pages"][0]["workedExample"]["pattern"] = "judgment_revision"
        self.assert_error(self.content(), "worked-example-pattern-mismatch")

    def test_unknown_example_pattern_fails(self):
        self.mechanism_example()
        self.design["lessons"][0]["exampleContract"]["pattern"] = "brief_summary"
        self.assert_error(self.stage("architecture"), "example-pattern")


if __name__ == "__main__":
    unittest.main()
