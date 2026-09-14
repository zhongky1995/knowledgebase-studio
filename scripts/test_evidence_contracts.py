"""Behavioral tests for optional quantitative evidence and comparison contracts."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from kb_content_check import validate
from kb_evidence import check_measurement
from kb_update import plan_update
from test_knowledgebase_studio import (
    valid_content_coverage, valid_knowledge_model, valid_learning_design,
    valid_source_understanding, write_locked_contract, write_valid_audit_artifacts,
)


def measurement():
    return {
        "value": 20, "unit": "%", "measureKind": "proportion", "basis": "12 completed tasks / 60 observed tasks",
        "population": "Fictional extraction tasks", "period": "2026-08", "analysisLevel": "task",
        "sampleSize": {"status": "known", "value": 60}, "citationMode": "direct",
        "verification": {"status": "verified", "reviewer": "Synthetic fixture reviewer", "locator": "Fixture row 1", "basis": "Synthetic contract fixture, not empirical research"},
    }


class MeasurementTests(unittest.TestCase):
    def check(self, value):
        errors, warnings = [], []
        check_measurement(value, errors, warnings, "fixture")
        return errors, warnings

    def test_complete_context_passes(self):
        self.assertEqual(self.check(measurement()), ([], []))

    def test_missing_numeric_value_is_not_zero(self):
        for invalid in (None, True, float("nan"), float("inf"), "20%"):
            with self.subTest(value=invalid):
                item = measurement()
                item["value"] = invalid
                errors, _ = self.check(item)
                self.assertIn("measurement-value", {error["kind"] for error in errors})

    def test_zero_and_negative_values_remain_distinct(self):
        for amount in (0, -11):
            item = measurement()
            item.update(value=amount, measureKind="relative-change")
            self.assertEqual(self.check(item)[0], [])
            self.assertEqual(item["value"], amount)

    def test_growth_is_not_a_proportion(self):
        item = measurement()
        item["value"] = 150
        self.assertTrue(self.check(item)[0])
        item["measureKind"] = "relative-change"
        self.assertEqual(self.check(item)[0], [])

    def test_subgroup_context_cannot_be_omitted(self):
        for field in ("basis", "period", "population", "analysisLevel", "unit"):
            with self.subTest(field=field):
                item = measurement()
                del item[field]
                self.assertIn("measurement-context", {error["kind"] for error in self.check(item)[0]})

    def test_unknown_sample_size_is_explicit_not_invented(self):
        item = measurement()
        item["sampleSize"] = {"status": "not_reported", "reason": "The inspected source omits the subgroup count."}
        self.assertEqual(self.check(item)[0], [])
        item["sampleSize"]["value"] = 60
        self.assertTrue(self.check(item)[0])

    def test_price_does_not_need_fabricated_sample_size(self):
        item = measurement()
        item.update(value=19.5, measureKind="continuous", unit="USD/month", basis="Published monthly list price")
        item["sampleSize"] = {"status": "not_applicable", "reason": "A published price, not a sampled survey finding."}
        self.assertEqual(self.check(item)[0], [])

    def test_verified_flag_needs_actual_review_details(self):
        item = measurement()
        item["verification"] = {"status": "verified"}
        errors, _ = self.check(item)
        self.assertEqual(len(errors), 3)

    def test_unverified_status_keeps_warning(self):
        item = measurement()
        item["verification"] = {"status": "unverified", "reason": "Original not accessible."}
        errors, warnings = self.check(item)
        self.assertEqual(errors, [])
        self.assertEqual(warnings[0]["kind"], "measurement-unverified")

    def test_secondary_citation_records_origin(self):
        item = measurement()
        item["citationMode"] = "secondary"
        self.assertTrue(self.check(item)[0])
        item["originalSource"] = "Unidentified in the inspected secondary source; cannot establish independent replication."
        self.assertEqual(self.check(item)[0], [])

    def test_malformed_fields_fail_without_crashing(self):
        for field in ("measureKind", "citationMode", "sampleSize", "verification"):
            with self.subTest(field=field):
                item = measurement()
                item[field] = {"status": []}
                self.assertTrue(self.check(item)[0])


class EvidenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.control = self.root / "_kb-control"
        self.control.mkdir()
        write_locked_contract(self.root)
        write_valid_audit_artifacts(self.root)
        self.source = valid_source_understanding()
        self.source["sources"][0]["coreClaims"][0]["measurement"] = measurement()
        self.model = valid_knowledge_model()
        self.coverage = valid_content_coverage()

    def check(self, phase="content", pages=None):
        for name, value in (("source-understanding.json", self.source), ("knowledge-model.json", self.model), ("content-coverage.json", self.coverage), ("learning-design.json", valid_learning_design())):
            (self.control / name).write_text(json.dumps(value), encoding="utf-8")
        return validate(self.root, self.control / "source-understanding.json", self.control / "knowledge-model.json", self.control / "content-coverage.json", phase=phase, page_paths=pages)

    def compare(self):
        second = copy.deepcopy(self.source["sources"][0]["coreClaims"][0])
        second["id"] = "claim.two"
        second["measurement"].update(value=30, period="2026-09")
        self.source["sources"][0]["coreClaims"].append(second)
        self.model["units"][0]["sourceRefs"].append("source.one#claim.two")
        entry = {"claimRefs": ["source.one#claim.one", "source.one#claim.two"], "conclusion": "Fictional observed rate differs across periods.", "remainingLimitations": "Cannot establish a cause or organization-wide impact.", "alignmentNotes": {}}
        self.model["units"][0]["comparisons"] = [entry]
        return entry

    def test_valid_quantity_runs_through_existing_content_checker(self):
        self.assertEqual(self.check()["status"], "pass")

    def test_audit_checks_declared_quantity(self):
        self.source["sources"][0]["coreClaims"][0]["measurement"]["basis"] = ""
        self.assertEqual(self.check(phase="audit")["status"], "fail")

    def test_verified_page_cannot_rely_on_unverified_measurement(self):
        self.source["sources"][0]["coreClaims"][0]["measurement"]["verification"] = {"status": "unverified", "reason": "Not checked."}
        report = self.check()
        self.assertIn("page-unverified-measurement", {item["kind"] for item in report["errors"]})
        self.coverage["pages"][0]["evidenceStatus"] = "unresolved"
        self.assertEqual(self.check()["status"], "pass")

    def test_scope_difference_needs_alignment(self):
        comparison = self.compare()
        report = self.check()
        self.assertIn("comparison-alignment", {item["kind"] for item in report["errors"]})
        comparison["alignmentNotes"]["period"] = "The period change is the intended contrast; no causal identification."
        self.assertEqual(self.check()["status"], "pass")

    def test_task_and_organization_measures_cannot_silently_compare(self):
        comparison = self.compare()
        comparison["alignmentNotes"]["period"] = "Different periods."
        self.source["sources"][0]["coreClaims"][1]["measurement"]["analysisLevel"] = "organization"
        report = self.check()
        self.assertTrue(any("analysisLevel" in item["detail"] for item in report["errors"]))

    def test_unknown_comparison_claim_cannot_pass(self):
        comparison = self.compare()
        comparison["claimRefs"][1] = "source.missing#claim.missing"
        self.assertIn("comparison-refs", {item["kind"] for item in self.check()["errors"]})

    def test_scoped_content_keeps_quantitative_checks(self):
        self.compare()
        self.assertEqual(self.check(pages=["lesson.md"])["status"], "fail")

    def test_raw_markdown_directory_does_not_require_a_browser(self):
        self.check()
        materials = self.root / "_materials"
        materials.mkdir()
        (materials / "source.md").write_text("Fictional source notes.", encoding="utf-8")
        plan = plan_update(self.root, ["lesson.md", "_materials"], pages=["lesson.md"])
        self.assertNotIn("browser", plan["requiredChecks"])
        self.assertIn("_materials", plan["inputDigests"])

    def test_frontend_directory_still_requires_browser_checks(self):
        self.check()
        app = self.root / "app"
        app.mkdir()
        (app / "entry.tsx").write_text("export default function App() { return null; }", encoding="utf-8")
        plan = plan_update(self.root, ["lesson.md", "app"], pages=["lesson.md"])
        self.assertIn("browser", plan["requiredChecks"])


if __name__ == "__main__":
    unittest.main()
