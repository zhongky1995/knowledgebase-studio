"""Regression contracts from beginner explanation failures, not learner studies."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from kb_content_check import validate as check_content
from kb_stage_check import validate_learning_design, validate_pilot, validate_content, validate_qc, run_comprehension_gate
from kb_update import check_update, plan_update
from functools import partial

# Preserve the original versioned contract in these compatibility regressions.
plan_update = partial(plan_update, schema_version=2)
from kb_reader_probe import prepare
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
        self.page.write_text(self.page.read_text() + "\n" + "\n".join(
            check["excerpt"] for check in self.verdict["comprehensionReview"]["checks"]))
        (self.control / "pilot-review.md").write_text("Synthetic editorial review fixture. " * 30)
        self.save()
        self.attach_probe(self.verdict["comprehensionReview"])

    def attach_probe(self, review):
        self.save()
        review["readerProbe"] = prepare(self.root, ["lesson.md"], job="understand")["readerProbe"]

    def save(self):
        for name, value in [("knowledge-model", self.model), ("learning-design", self.design),
                            ("content-coverage", self.coverage), ("pilot-verdict", self.verdict)]:
            (self.control / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False))

    def stage(self, phase):
        self.save()
        errors = []
        (validate_learning_design if phase == "architecture" else validate_pilot)(self.root, errors, [], {})
        return errors

    def content_report(self, page_paths=None):
        self.save()
        return check_content(self.root, self.control / "source-understanding.json",
                             self.control / "knowledge-model.json", self.control / "content-coverage.json",
                             page_paths=page_paths)

    def content(self):
        return self.content_report()["errors"]

    def page_review(self):
        review = copy.deepcopy(self.fragments["pageComprehensionReview"])
        review["contentSha256"] = hashlib.sha256(self.page.read_bytes()).hexdigest()
        for check in review["checks"]:
            check.update(status="pass", rationale="Synthetic editorial receipt, not learner evidence.")
        self.coverage["pages"][0]["comprehensionReview"] = review
        self.attach_probe(review)
        return review

    def update_plan(self, changed, **kwargs):
        self.save()
        (self.control / "update-review.md").write_text("Synthetic review evidence, not a real learner study.")
        plan = plan_update(self.root, changed, **kwargs)
        plan["checks"] = [{"kind": kind, "status": "pass", "inputDigests": copy.deepcopy(plan["inputDigests"]),
                           "pagePaths": plan["checkScopes"][kind], "evidencePaths": ["_kb-control/update-review.md"]}
                          for kind in plan["requiredChecks"]]
        return plan

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

    def test_legacy_novice_coverage_reports_missing_review_without_rejecting_structure(self):
        report = self.content_report()
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["validationKind"], "structural_integrity")
        self.assertEqual(report["comprehensionEvidence"]["status"], "incomplete")
        self.assertEqual(report["comprehensionEvidence"]["missingPages"], ["lesson.md"])

    def test_current_page_receipt_passes_without_claiming_learning(self):
        self.page_review()
        report = self.content_report()
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["comprehensionEvidence"]["status"], "receipts_valid")
        self.assertEqual(report["comprehensionEvidence"]["validReceiptPages"], ["lesson.md"])

    def test_edit_outside_review_excerpt_invalidates_whole_page_receipt(self):
        self.page_review()
        self.page.write_text(self.page.read_text() + "\nA later mechanism changed after review.")
        report = self.content_report()
        self.assert_error(report["errors"], "page-comprehension-stale")
        self.assertEqual(report["comprehensionEvidence"]["status"], "incomplete")

    def test_digest_cannot_replace_missing_excerpt_evidence(self):
        review = self.page_review()
        self.page.write_text("# Changed page\nOnly a conclusion remains.\n")
        review["contentSha256"] = hashlib.sha256(self.page.read_bytes()).hexdigest()
        self.assert_error(self.content(), "comprehension-excerpt")

    def test_page_pass_cannot_override_unresolved_explanation_gap(self):
        review = self.page_review()
        review["unresolvedGaps"] = ["The article does not explain how the recipient is identified."]
        self.assert_error(self.content(), "page-comprehension-unresolved")

    def test_omitted_gap_review_is_not_an_empty_gap_list(self):
        review = self.page_review()
        review.pop("unresolvedGaps")
        self.assert_error(self.content(), "page-comprehension-gaps")

    def test_one_good_page_cannot_supply_another_pages_receipt(self):
        review = self.page_review()
        (self.root / "second.md").write_text(self.page.read_text())
        review["checks"][0]["path"] = "second.md"
        self.assert_error(self.content(), "comprehension-pilot-path")

    def test_page_review_needs_transfer_and_honest_observation_status(self):
        review = self.page_review()
        review["checks"].pop()
        review["reviewType"] = "learner_observed"
        errors = self.content()
        self.assert_error(errors, "comprehension-missing-dimension")
        self.assert_error(errors, "comprehension-observation")

    def test_declared_malformed_review_is_not_silently_ignored(self):
        self.coverage["pages"][0]["comprehensionReview"] = "pass"
        self.assert_error(self.content(), "page-comprehension-review")

    def test_non_novice_content_keeps_its_existing_requirements(self):
        self.design.pop("explanationProfile")
        report = self.content_report()
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["comprehensionEvidence"]["status"], "not_requested")

    def test_scoped_review_does_not_require_receipts_on_unselected_pages(self):
        self.page_review()
        extra = copy.deepcopy(self.coverage["pages"][0])
        extra.update(path="other.md", primaryQuestion="A different question")
        extra.pop("comprehensionReview")
        self.coverage["pages"].append(extra)
        (self.root / "other.md").write_text("# Other page\n")
        report = self.content_report(page_paths=["lesson.md"])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["comprehensionEvidence"]["requiredPages"], ["lesson.md"])
        self.assertEqual(report["comprehensionEvidence"]["missingPages"], [])

    def test_content_and_qc_cannot_promote_pilot_evidence_to_corpus_review(self):
        self.assertEqual(self.stage("pilot"), [])
        for validate in (validate_content, validate_qc):
            with self.subTest(stage=validate.__name__):
                errors = []
                validate(self.root, errors, [], {})
                self.assert_error(errors, "page-comprehension-required")

    def test_full_comprehension_gate_reads_current_bytes_not_cached_pass(self):
        self.page_review()
        self.save()
        errors = []
        run_comprehension_gate(self.root, errors, {})
        self.assertEqual(errors, [])
        self.page.write_text(self.page.read_text() + "\nLater changes.")
        run_comprehension_gate(self.root, errors, {})
        self.assert_error(errors, "page-comprehension-stale")

    def test_novice_content_update_requires_page_evidence_even_with_generic_pass(self):
        report = check_update(self.root, self.update_plan(["lesson.md"]))
        self.assert_error(report["errors"], "page-comprehension-required")
        self.page_review()
        report = check_update(self.root, self.update_plan(["lesson.md"]))
        self.assertEqual({e['kind'] for e in report['errors']}, {'execution-required'})
        self.assertEqual(report["status"], "fail")  # Author-filled evidence is no longer enough.

    def test_renderer_only_novice_update_preserves_missing_editorial_evidence(self):
        (self.root / "renderer.js").write_text("// Synthetic presentation-only repair")
        plan = self.update_plan(["renderer.js"], change_kind="rendering")
        report = check_update(self.root, plan)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["reviewPages"], [])
        self.assertEqual(report["comprehensionEvidence"]["status"], "incomplete")
        self.assertEqual(report["claim"], "selected-update-only")

    def test_version_two_requires_a_real_promise_inventory(self):
        review = self.page_review()
        for value in (None, [], "reviewed", [None], [{"id": []}]):
            with self.subTest(value=value):
                review["promises"] = value
                self.assertTrue(self.content())

    def test_a_later_independent_promise_cannot_hide_behind_two_opening_checks(self):
        review = self.page_review()
        claim = "同一任务重试不会另建一条正式记录。"
        self.page.write_text(self.page.read_text() + "\n" + claim)
        review["contentSha256"] = hashlib.sha256(self.page.read_bytes()).hexdigest()
        review["promises"].append({"id": "retry", "path": "lesson.md", "claim": claim})
        self.assert_error(self.content(), "comprehension-promise-unreviewed")

    def test_a_later_mechanism_can_supply_its_own_causal_evidence(self):
        review = self.page_review()
        claim = "同一任务重试使用原来的结果。"
        basis = "服务把操作编号和任务一起保存，编号在该账号下唯一；重试读到已有任务，就返回它的结果。"
        self.page.write_text(self.page.read_text() + "\n" + claim + "\n" + basis)
        review["contentSha256"] = hashlib.sha256(self.page.read_bytes()).hexdigest()
        review["promises"].append({"id": "retry", "path": "lesson.md", "claim": claim})
        review["checks"].append({"dimension": "causalContinuity", "status": "pass", "path": "lesson.md",
                                 "question": "重试怎样找到原任务？", "expectedExplanation": basis,
                                 "excerpt": basis, "basisExcerpt": basis, "promiseIds": ["retry"],
                                 "rationale": "Synthetic local uniqueness example; external effects are outside this claim."})
        self.attach_probe(review)
        self.assertEqual(self.content(), [])

    def test_changed_condition_alone_does_not_cover_the_normal_mechanism(self):
        review = self.page_review()
        review["checks"][0]["dimension"] = "conceptBoundaries"
        self.assert_error(self.content(), "comprehension-promise-unreviewed")

    def test_duplicate_promise_ids_do_not_silently_replace_a_later_claim(self):
        review = self.page_review()
        review["promises"].append(copy.deepcopy(review["promises"][0]))
        self.assert_error(self.content(), "comprehension-promise-duplicate")

    def test_promised_claim_must_be_in_the_published_page(self):
        review = self.page_review()
        review["promises"][0]["claim"] = "An invented guarantee absent from the page."
        self.assert_error(self.content(), "comprehension-promise-claim")

    def test_review_cannot_point_a_promise_at_an_unreviewed_file(self):
        review = self.page_review()
        (self.root / "other.md").write_text(self.page.read_text())
        review["promises"][0]["path"] = "other.md"
        self.assert_error(self.content(), "comprehension-promise-path")

    def test_promises_on_another_representative_page_need_their_own_checks(self):
        from kb_explanation import validate_comprehension
        review = self.page_review()
        (self.root / "other.md").write_text(self.page.read_text())
        review["promises"].append({"id": "other-promise", "path": "other.md",
                                   "claim": review["promises"][0]["claim"]})
        review["checks"][0]["promiseIds"].append("other-promise")
        errors = []
        validate_comprehension(self.root, self.design,
                               {"representativePaths": ["lesson.md", "other.md"], "comprehensionReview": review},
                               errors, required_dimensions={"causalContinuity", "scenarioApplication"})
        self.assert_error(errors, "comprehension-promise-reference")
        self.assert_error(errors, "comprehension-promise-unreviewed")

    def test_basis_cannot_live_only_in_the_expected_answer(self):
        review = self.page_review()
        check = review["checks"][0]
        check["basisExcerpt"] = check["expectedExplanation"] = "The missing association is explained only in this answer."
        self.assert_error(self.content(), "comprehension-basis-excerpt")

    def test_check_needs_known_well_formed_promise_references(self):
        review = self.page_review()
        for value in (None, [], "favorite-retained", [[]], ["missing"]):
            with self.subTest(value=value):
                review["checks"][0]["promiseIds"] = value
                self.assert_error(self.content(), "comprehension-promise-reference")

    def test_unknown_receipt_versions_fail_instead_of_dropping_new_checks(self):
        review = self.page_review()
        for version in (0, 3, "2", [], True, 2.0):
            with self.subTest(version=version):
                review["schemaVersion"] = version
                self.assert_error(self.content(), "comprehension-version")

    def test_legacy_receipt_stays_readable_without_claiming_promise_coverage(self):
        review = self.page_review()
        review.pop("schemaVersion")
        review.pop("promises")
        for check in review["checks"]:
            check.pop("promiseIds")
            check.pop("basisExcerpt")
        report = self.content_report()
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["comprehensionEvidence"]["promiseCoverage"]["legacyPages"], ["lesson.md"])
        self.assertEqual(report["comprehensionEvidence"]["promiseCoverage"]["version2Pages"], [])

    def test_current_receipt_reports_declared_promise_coverage(self):
        self.page_review()
        report = self.content_report()
        self.assertEqual(report["comprehensionEvidence"]["promiseCoverage"]["status"], "recorded")
        self.assertEqual(report["comprehensionEvidence"]["promiseCoverage"]["version2Pages"], ["lesson.md"])

    def test_new_full_approvals_cannot_reuse_a_legacy_receipt(self):
        review = self.page_review()
        review.pop("schemaVersion")
        review.pop("promises")
        self.save()
        errors = []
        run_comprehension_gate(self.root, errors, {})
        self.assert_error(errors, "comprehension-promises-required")
        self.verdict["comprehensionReview"].pop("schemaVersion")
        self.assert_error(self.stage("pilot"), "comprehension-promises-required")

    def test_scoped_editorial_approval_needs_v2_but_rendering_does_not(self):
        review = self.page_review()
        review.pop("schemaVersion")
        review.pop("promises")
        report = check_update(self.root, self.update_plan(["lesson.md"]))
        self.assert_error(report["errors"], "comprehension-promises-required")
        (self.root / "renderer.js").write_text("// Presentation-only fixture")
        report = check_update(self.root, self.update_plan(["renderer.js"], change_kind="rendering"))
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["comprehensionEvidence"]["promiseCoverage"]["legacyPages"], ["lesson.md"])

    def test_structural_promise_coverage_is_deliberately_not_a_semantic_approval(self):
        review = self.page_review()
        # An editor must reject this circular explanation. The validator checks provenance,
        # not whether arbitrary prose explains a mechanism; do not fake a keyword classifier.
        sentence = "系统会自动处理，所以结果正确。"
        self.page.write_text(self.page.read_text() + "\n" + sentence)
        review["contentSha256"] = hashlib.sha256(self.page.read_bytes()).hexdigest()
        review["promises"] = [{"id": "circular", "path": "lesson.md", "claim": sentence}]
        for check in review["checks"]:
            check.update(promiseIds=["circular"], excerpt=sentence, basisExcerpt=sentence)
        self.attach_probe(review)
        self.assertEqual(self.content_report()["status"], "pass")

    def test_new_approvals_need_prepared_material_not_only_self_reported_checks(self):
        review = self.page_review()
        review.pop("readerProbe")
        self.assertEqual(self.content_report()["status"], "pass")  # Historical receipt read.
        self.save()
        errors = []
        run_comprehension_gate(self.root, errors, {})
        self.assert_error(errors, "reader-probe-required")
        report = check_update(self.root, self.update_plan(["lesson.md"]))
        self.assert_error(report["errors"], "reader-probe-required")
        self.verdict["comprehensionReview"].pop("readerProbe")
        self.assert_error(self.stage("pilot"), "reader-probe-required")

    def test_copy_shortcuts_are_errors_in_editorial_scope_warnings_in_rendering_regression(self):
        review = self.page_review()
        second = copy.deepcopy(review["checks"][0])
        second["dimension"] = "scenarioApplication"
        review["checks"].append(second)
        report = check_update(self.root, self.update_plan(["lesson.md"]))
        self.assert_error(report["errors"], "comprehension-relabeled-check")
        (self.root / "renderer.js").write_text("// Layout only")
        report = check_update(self.root, self.update_plan(["renderer.js"], change_kind="rendering"))
        self.assertEqual(report["errors"], [])
        self.assertIn("comprehension-relabeled-check", {w["kind"] for w in report["warnings"]})


if __name__ == "__main__":
    unittest.main()
