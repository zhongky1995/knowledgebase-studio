"""Executable review regressions. No fixture claims observed learner effectiveness."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from kb_explanation import review_shortcuts
from kb_reader_probe import prepare, validate_probe, reader_probe_paths, sanitized_svg
from kb_work_comparison import compute, render, validate_work_comparison
from kb_workflow import stage_deliverable_digests
from kb_update import plan_update


class ReaderProbeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.control = self.root / "_kb-control"
        self.control.mkdir()
        self.page = self.root / "lesson.md"
        self.page.write_text("# 怎样调整岗位\n\n## 输入\n客户变更消息。\n\n## 分派\n由销售补缺项。\n\n## 完成后的约定\n齐备件交业务负责人；缺项退回销售，保留未确认状态。\n![分支](figure.svg)\n")
        self.asset = self.root / "figure.svg"
        self.asset.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200"><defs><marker id="arrow"><path d="M0 0 L4 2 L0 4Z"/></marker></defs><rect x="10" y="10" width="60" height="40"/><text x="20" y="30">客户消息</text><path d="M70 30 L140 30" style="marker-end:url(\'#arrow\')"/></svg>')
        self.coverage = {"pages": [{"path": "lesson.md", "readerJob": "perform", "primaryQuestion": "如何调整岗位？", "readerChange": "能完成一次安排。", "comprehensionReview": {"checks": [{"expectedExplanation": "SECRET AUTHOR ANSWER"}]}}]}
        self.save()

    def save(self):
        (self.control / "content-coverage.json").write_text(json.dumps(self.coverage))

    def packet(self):
        result = prepare(self.root, ["lesson.md"])
        self.reference = result["readerProbe"]
        self.path = self.root / self.reference["packetPath"]
        return result

    def errors(self, pages=("lesson.md",)):
        errors = []
        validate_probe(self.root, self.reference, pages, errors, required=True)
        return errors

    def test_material_uses_whole_page_later_section_but_no_author_answers(self):
        result = self.packet()
        reader = (self.root / result["readerPath"]).read_text()
        self.assertIn("完成后的约定", reader)
        self.assertIn("0001 | # 怎样调整岗位", reader)
        self.assertNotIn("SECRET AUTHOR ANSWER", reader)
        self.assertEqual(result["readiness"], "not_assessed")
        self.assertEqual(self.errors(), [])

    def test_reader_job_cannot_silently_default_to_concepts(self):
        self.coverage["pages"][0].pop("readerJob")
        self.save()
        with self.assertRaises(ValueError):
            self.packet()
        self.assertEqual(prepare(self.root, ["lesson.md"], job="judge")["status"], "prepared")

    def test_mask_removes_labels_preserves_geometry_and_original_file(self):
        before = self.asset.read_bytes()
        self.packet()
        packet = json.loads(self.path.read_text())
        masked = self.path.parent / packet["figures"][0]["maskedPath"]
        tree = ET.fromstring(masked.read_bytes())
        self.assertEqual(len(tree.findall('.//{http://www.w3.org/2000/svg}text')), 0)
        self.assertEqual(len(tree.findall('.//{http://www.w3.org/2000/svg}path')), 2)
        self.assertIn("marker-end", masked.read_text())
        self.assertEqual(before, self.asset.read_bytes())

    def test_svg_active_content_is_not_copied_into_review(self):
        result = sanitized_svg(b'<svg xmlns="http://www.w3.org/2000/svg" onload="evil()"><script>evil()</script><image href="https://invalid.example/private"/><text>label</text></svg>')
        self.assertNotIn(b"evil", result)
        self.assertNotIn(b"https://", result)
        self.assertIn(b"label", result)

    def test_preview_that_removes_foreign_content_reports_its_limit(self):
        self.asset.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><foreignObject><div>HTML labels</div></foreignObject></svg>')
        result = self.packet()
        self.assertTrue(result["warnings"])
        self.assertIn("foreignObject", (self.root / result["figureSheetPath"]).read_text())

    def test_text_change_anywhere_stales_review_material(self):
        self.packet()
        self.page.write_text(self.page.read_text() + "\nAn unquoted conclusion changed.")
        self.assertIn("reader-probe-stale", {e["kind"] for e in self.errors()})

    def test_figure_change_stales_review_material(self):
        self.packet()
        self.asset.write_text(self.asset.read_text().replace('width="60"', 'width="80"'))
        self.assertIn("reader-probe-stale", {e["kind"] for e in self.errors()})

    def test_prepared_material_cannot_be_edited_to_supply_hidden_steps(self):
        self.packet()
        (self.path.parent / "reader.md").write_text("Invented instructions.")
        self.assertIn("reader-probe-material-changed", {e["kind"] for e in self.errors()})

    def test_another_page_cannot_borrow_this_packet(self):
        self.packet()
        self.assertIn("reader-probe-coverage", {e["kind"] for e in self.errors(["other.md"])})

    def test_changing_page_job_invalidates_old_material(self):
        self.packet()
        self.coverage["pages"][0]["readerJob"] = "understand"
        self.save()
        self.assertIn("reader-probe-job-changed", {e["kind"] for e in self.errors()})

    def test_prerequisites_are_available_and_fingerprinted(self):
        (self.root / "prior.md").write_text("# Prior\nEstablished prerequisite.")
        model = {"units": [{"id": "one", "canonicalOwner": "lesson.md", "dependencies": ["prior"]}, {"id": "prior", "canonicalOwner": "prior.md", "dependencies": []}]}
        (self.control / "knowledge-model.json").write_text(json.dumps(model))
        self.coverage["pages"][0]["knowledgeUnitIds"] = ["one"]
        self.save()
        result = self.packet()
        self.assertIn("Established prerequisite", (self.root / result["readerPath"]).read_text())
        (self.root / "prior.md").write_text("# Changed prerequisite")
        self.assertIn("reader-probe-stale", {e["kind"] for e in self.errors()})

    def test_unrelated_model_and_update_metadata_do_not_widen_a_scoped_review(self):
        (self.control / "knowledge-model.json").write_text(json.dumps({"units": []}))
        (self.control / "project-contract.yaml").write_text("product_posture: reading_manual\naudiences:\n  - managers\ncurrent_update: first\n")
        self.packet()
        (self.control / "knowledge-model.json").write_text(json.dumps({"units": [{"id": "unrelated", "dependencies": [], "canonicalOwner": "other.md"}]}))
        (self.control / "project-contract.yaml").write_text("product_posture: reading_manual\naudiences:\n  - managers\ncurrent_update: second\n")
        self.assertEqual(self.errors(), [])

    def test_audience_changes_do_invalidate_reader_material(self):
        (self.control / "project-contract.yaml").write_text("audiences:\n  - managers\n")
        self.packet()
        (self.control / "project-contract.yaml").write_text("audiences:\n  - engineers\n")
        self.assertIn("reader-probe-job-changed", {e["kind"] for e in self.errors()})

    def test_removing_the_page_intent_does_not_make_a_packet_current(self):
        self.packet()
        (self.control / "content-coverage.json").unlink()
        self.assertIn("reader-probe-job-changed", {e["kind"] for e in self.errors()})

    def test_review_paths_join_existing_stage_and_incremental_fingerprints(self):
        self.packet()
        self.coverage["pages"][0]["comprehensionReview"]["readerProbe"] = self.reference
        self.save()
        paths = reader_probe_paths(self.root)
        self.assertIn(self.path, paths)
        self.assertIn(self.path, reader_probe_paths(self.root, ["lesson.md"]))
        digests = stage_deliverable_digests(self.root, "content")
        self.assertIn(str(self.path.relative_to(self.root)), digests)
        plan = plan_update(self.root, ["lesson.md"])
        self.assertIn(str(self.path.relative_to(self.root)), plan["inputDigests"])

    def test_path_traversal_and_external_pages_are_refused(self):
        for path in ("../outside.md", "https://example.invalid/page.md"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                prepare(self.root, [path], job="understand")

    def test_legacy_read_does_not_require_a_packet_but_new_approval_does(self):
        errors = []
        validate_probe(self.root, None, ["lesson.md"], errors)
        self.assertEqual(errors, [])
        validate_probe(self.root, None, ["lesson.md"], errors, required=True)
        self.assertEqual(errors[0]["kind"], "reader-probe-required")


class ReviewShortcutTests(unittest.TestCase):
    def check(self, checks):
        errors, warnings = [], []
        review_shortcuts({"checks": checks}, errors, warnings)
        return errors, warnings

    def base(self):
        return {"dimension": "causalContinuity", "path": "lesson.md", "question": "为什么价值不同？", "expectedExplanation": "核对和维护改变总成本。", "rationale": "Synthetic reason."}

    def test_gaidn_relabeling_pattern_is_rejected(self):
        first = self.base()
        second = dict(first, dimension="scenarioApplication")
        errors, _ = self.check([first, second])
        self.assertEqual(errors[0]["kind"], "comprehension-relabeled-check")

    def test_cosmetic_changes_do_not_create_a_different_test(self):
        first = self.base()
        second = dict(first, dimension="scenarioApplication", question="为 什 么 价 值 不 同?", expectedExplanation="核对和维护改变总成本!")
        self.assertTrue(self.check([first, second])[0])

    def test_different_condition_and_answer_can_reuse_one_excerpt(self):
        first = self.base()
        second = dict(first, dimension="scenarioApplication", question="任务量从60降到10时怎样？", expectedExplanation="维护分摊由1变6分钟。")
        self.assertEqual(self.check([first, second])[0], [])

    def test_normalization_does_not_confuse_different_numeric_answers(self):
        first = dict(self.base(), expectedExplanation="1.5分钟")
        second = dict(first, dimension="scenarioApplication", expectedExplanation="15分钟")
        self.assertEqual(self.check([first, second])[0], [])

    def test_repeated_reason_is_a_warning_not_a_wording_diversity_gate(self):
        checks = [dict(self.base(), question=f"Question {i}") for i in range(3)]
        errors, warnings = self.check(checks)
        self.assertEqual(errors, [])
        self.assertEqual(warnings[0]["kind"], "comprehension-repeated-rationale")


class WorkComparisonTests(unittest.TestCase):
    def setUp(self):
        self.model = json.loads((Path(__file__).resolve().parent.parent / "assets/control-templates/work-comparison.json").read_text())

    def test_ordinary_software_and_ai_contributions_are_separate(self):
        result = compute(self.model)
        self.assertEqual([result["totals"][m]["perTaskMinutes"] for m in ("manual", "software", "ai")], [15, 13, 10])
        self.assertEqual(result["overallSavingMinutes"], 5)
        self.assertEqual(result["incrementalAiSavingMinutes"], 3)
        self.assertEqual(result["sensitivity"][0]["totals"]["ai"], 15)

    def test_low_volume_can_make_ai_more_work_without_changing_the_program(self):
        self.model["volume"] = 5
        result = compute(self.model)
        self.assertEqual(result["totals"]["ai"]["perTaskMinutes"], 21)
        self.assertEqual(result["overallSavingMinutes"], -6)
        self.assertIn("AI 方案每笔增加 6 分钟", render(self.model))

    def test_omitting_work_is_not_zero_cost(self):
        self.model["methods"][2]["allocations"].pop()
        with self.assertRaises(ValueError):
            compute(self.model)

    def test_missing_software_baseline_cannot_establish_ai_increment(self):
        self.model["methods"][1]["id"] = "another-ai"
        with self.assertRaises(ValueError):
            compute(self.model)

    def test_invalid_costs_and_zero_volume_fail(self):
        for value in (-1, True, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model = copy.deepcopy(self.model)
                model["methods"][0]["fixedHumanMinutes"] = value
                compute(model)
        self.model["volume"] = 0
        with self.assertRaises(ValueError):
            compute(self.model)

    def test_generated_block_detects_manual_total_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root / "lesson.md"
            block = render(self.model)
            path.write_text("# Case\n" + block + "\nOrdinary prose.")
            page = {"path": "lesson.md", "workedExample": {"workComparison": self.model}}
            errors = []
            validate_work_comparison(root, page, errors)
            self.assertEqual(errors, [])
            path.write_text(path.read_text().replace("相对普通软件方案，每笔减少 3 分钟", "相对普通软件方案，每笔减少 8 分钟"))
            validate_work_comparison(root, page, errors)
            self.assertEqual(errors[0]["kind"], "work-comparison-stale")

    def test_cli_updates_only_existing_comparison_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "_kb-control").mkdir()
            page = {"path": "lesson.md", "workedExample": {"workComparison": self.model}}
            (root / "_kb-control/content-coverage.json").write_text(json.dumps({"pages": [page]}))
            owner = root / "lesson.md"
            owner.write_text("BEFORE\n<!-- kb-work-comparison:order-preparation -->\n<!-- /kb-work-comparison:order-preparation -->\nAFTER\n")
            run = subprocess.run([sys.executable, str(Path(__file__).with_name("kb_work_comparison.py")), str(root), "--page", "lesson.md", "--write"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(owner.read_text(), "BEFORE\n" + render(self.model) + "\nAFTER\n")

    def test_computed_overflow_is_rejected(self):
        for row in self.model["methods"][0]["allocations"]:
            row.update(handler="human", humanMinutes=1e308)
        with self.assertRaises(ValueError):
            compute(self.model)

    def test_measured_label_requires_real_numeric_source_alignment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.model.update(basisKind="measured", measurementRefs={"volume": "source#volume"})
            (root / "lesson.md").write_text(render(self.model))
            errors = []
            validate_work_comparison(root, {"path": "lesson.md", "workedExample": {"workComparison": self.model}}, errors,
                                     {"source#volume": {"value": 600, "unit": "tasks", "verification": {"status": "verified"}}})
            self.assertEqual(errors[0]["kind"], "work-comparison-invalid")
            self.assertIn("differs from its source", errors[0]["detail"])

    def test_verified_measurements_with_matching_units_support_the_calculation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            refs, measurements = {}, {}

            def bind(key, value, unit):
                ref = "source#" + key
                refs[key] = ref
                measurements[ref] = {"value": value, "unit": unit, "verification": {"status": "verified"}}

            bind("volume", self.model["volume"], "tasks")
            for method in self.model["methods"]:
                bind(f'{method["id"]}.fixedHumanMinutes', method["fixedHumanMinutes"], "minutes")
                for row in method["allocations"]:
                    if row["handler"] != "not_needed":
                        bind(f'{method["id"]}.{row["activityId"]}.humanMinutes', row["humanMinutes"], "minutes")
            self.model.update(basisKind="measured", measurementRefs=refs)
            (root / "lesson.md").write_text(render(self.model))
            errors = []
            validate_work_comparison(root, {"path": "lesson.md", "workedExample": {"workComparison": self.model}}, errors, measurements)
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
