#!/usr/bin/env python3
"""Behavioral regressions for scoped editorial work; runtime calls are test doubles."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import kb_execution as execution
import kb_update as update
import kb_stage_check as stages
import test_execution as fixtures


class EditorialExecutionTests(unittest.TestCase):
    setUp = fixtures.ExecutionTests.setUp
    write = fixtures.ExecutionTests.write
    state = fixtures.ExecutionTests.state
    batch = fixtures.ExecutionTests.batch
    status = fixtures.ExecutionTests.status
    verdict = fixtures.ExecutionTests.verdict
    OLD, NEW, FIXED = fixtures.ExecutionTests.OLD, fixtures.ExecutionTests.NEW, fixtures.ExecutionTests.FIXED
    SECRET_ANSWER, SECRET_REPAIR = fixtures.ExecutionTests.SECRET_ANSWER, fixtures.ExecutionTests.SECRET_REPAIR

    def plan(self, **extra):
        return execution.init(self.root, {'schemaVersion': 2, 'batches': [{
            'id': 'one', 'pages': ['one.md'], 'briefPath': '_kb-control/reader-brief.md',
            'task': 'Read the connected passage for the intended reader.', **extra}]})

    def review(self, findings=False, missing=False):
        output = self.verdict()
        if findings:
            output['pages'][0].update(status='needs_work', gaps=[{
                'id': 'scope', 'detail': 'The chapter promises more than this handoff demonstrates.',
                'blocking': True, 'cause': 'question', 'proposal': 'replace'}])
        if missing:
            output['taskResults'][0].update(status='missing', answer='The necessary condition is absent.', basis=[])
        self.runtime.enqueue('reader', output)
        return execution.run_batch(self.root, 'one')

    def decision(self, resolutions=(), status='accepted'):
        return {'status': status, 'summary': 'I read the handoff in its current context and made the following editorial choice.',
                'basis': [{'path': 'one.md', 'quote': '收到客户消息'}], 'resolutions': list(resolutions)}

    def test_one_reader_no_writer_or_automatic_consensus_and_editor_must_decide(self):
        self.plan()
        result = self.review()
        self.assertEqual(result['status'], 'awaiting_editor', result)
        self.assertEqual([c['role'] for c in self.runtime.calls], ['reader'])
        self.assertTrue(execution.gate(self.root, ['one.md']))
        accepted = execution.decide(self.root, 'one', self.decision())
        self.assertEqual(accepted['status'], 'accepted', accepted)
        self.assertEqual(execution.gate(self.root, ['one.md']), [])

    def test_editor_can_disagree_with_reader_without_forging_its_pass(self):
        self.plan()
        self.review(findings=True)
        decision = self.decision([{'id': 'reader:scope', 'action': 'declined',
            'reason': 'The currently agreed scope is only the initial handoff, not enterprise transformation.',
            'basis': [{'path': 'one.md', 'quote': '转给负责人'}]}])
        self.assertEqual(execution.decide(self.root, 'one', decision)['status'], 'accepted')
        original = self.runtime.validate(self.runtime.calls[0]['directory'])
        self.assertEqual(original['output']['pages'][0]['status'], 'needs_work')
        self.assertEqual(len(self.runtime.calls), 1)

    def test_missing_task_or_deferred_consequential_finding_cannot_disappear(self):
        self.plan()
        self.review(findings=True, missing=True)
        with self.assertRaisesRegex(ValueError, 'every actual finding'):
            execution.decide(self.root, 'one', self.decision())
        unresolved = [{'id': key, 'action': 'deferred', 'reason': 'Still needs investigation.'}
                      for key in ('reader:scope', 'reader:task:reader-task')]
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            execution.decide(self.root, 'one', self.decision(unresolved))
        result = execution.decide(self.root, 'one', self.decision(unresolved, 'needs_work'))
        self.assertEqual(result['status'], 'needs_work')
        self.assertTrue(execution.gate(self.root, ['one.md']))

    def test_stale_text_cannot_be_accepted_with_an_editor_summary(self):
        self.plan()
        self.review()
        self.write('one.md', self.FIXED)
        with self.assertRaisesRegex(ValueError, 'stale'):
            execution.decide(self.root, 'one', self.decision())

    def test_optional_counter_reader_does_not_impose_consensus(self):
        self.plan(counterReview=True)
        output = self.verdict()
        output['pages'][0].update(status='needs_work', gaps=[{'id': 'scope', 'detail': 'Suggest a broader scenario.',
            'blocking': False, 'cause': 'example', 'proposal': 'replace'}])
        self.runtime.enqueue('reader', output)
        self.runtime.enqueue('auditor', self.verdict())
        self.assertEqual(execution.run_batch(self.root, 'one')['status'], 'awaiting_editor')
        decision = self.decision([{'id': 'reader:scope', 'action': 'declined',
            'reason': 'This section only promises to introduce the handoff; the broader scenario belongs elsewhere.'}])
        self.assertEqual(execution.decide(self.root, 'one', decision)['status'], 'accepted')
        self.assertEqual([c['role'] for c in self.runtime.calls], ['reader', 'auditor'])

    def test_accepted_execution_replaces_duplicate_editor_receipt(self):
        # An ordinary manuscript has no legacy self-review/coverage contracts.
        (self.control / 'content-coverage.json').unlink()
        self.plan()
        self.review()
        execution.decide(self.root, 'one', self.decision())
        plan = update.plan_update(self.root, ['one.md'], schema_version=3)
        self.assertEqual(plan['requiredChecks'], [])
        self.assertEqual(update.check_update(self.root, plan)['status'], 'pass')
        self.runtime.enqueue('reader', status='runtime_error')
        execution.run_batch(self.root, 'one')
        self.assertEqual(update.check_update(self.root, plan)['status'], 'fail')

    def test_editor_decision_does_not_substitute_for_actual_runtime(self):
        self.plan()
        with self.assertRaises(ValueError):
            execution.decide(self.root, 'one', self.decision())
        self.assertEqual(self.runtime.calls, [])

    def test_independent_batches_do_not_inherit_an_unrelated_failed_predecessor(self):
        self.plan()
        execution.init(self.root, {'schemaVersion': 2, 'batches': [{
            'id': 'two', 'pages': ['two.md'], 'briefPath': '_kb-control/reader-brief.md', 'task': 'Review another independent passage.'}]})
        self.assertEqual(self.batch('two')['after'], [])
        self.review(findings=True)
        self.runtime.enqueue('reader', self.verdict('two.md'))
        self.assertEqual(execution.run_batch(self.root, 'two')['status'], 'awaiting_editor')
        self.assertFalse(execution.required(self.root, ['prior.md']))

    def test_explicit_dependency_still_stops_dispatch(self):
        self.plan()
        execution.init(self.root, {'schemaVersion': 2, 'batches': [{
            'id': 'two', 'pages': ['two.md'], 'briefPath': '_kb-control/reader-brief.md', 'task': 'Extend this premise.', 'after': ['one']}]})
        self.review(findings=True)
        with self.assertRaisesRegex(ValueError, 'dependency'):
            execution.run_batch(self.root, 'two')

    def test_legacy_migration_preserves_failure_and_requires_a_new_run(self):
        execution.init(self.root, {'batches': [{'id': 'one', 'pages': ['one.md'],
            'briefPath': '_kb-control/reader-brief.md', 'task': 'Old independent review.', 'authoringMode': 'review_existing'}]})
        self.runtime.enqueue('reader', self.verdict(status='needs_work', blocking=True))
        self.runtime.enqueue('auditor', self.verdict(status='needs_work', blocking=True))
        execution.run_batch(self.root, 'one')
        original = copy.deepcopy(self.batch()['attempts'])
        result = execution.migrate_review(self.root, 'one', 'Use accountable editorial disposition for this existing scope.')
        self.assertEqual(result['retainedAttempts'], 1)
        self.assertEqual(self.batch()['attempts'], original)
        self.assertTrue(execution.gate(self.root, ['one.md']))
        with self.assertRaises(ValueError):
            execution.decide(self.root, 'one', self.decision())
        self.review()
        self.assertEqual(execution.decide(self.root, 'one', self.decision())['status'], 'accepted')
        self.assertEqual(self.batch()['attempts'][0], original[0])

    def test_bookkeeping_change_does_not_stale_editorial_reading_but_intent_does(self):
        self.write('_kb-control/project-contract.yaml', 'audiences:\n  - managers\ndelivery_target: sample\n')
        self.plan()
        self.review()
        execution.decide(self.root, 'one', self.decision())
        self.write('_kb-control/project-contract.yaml', 'audiences:\n  - managers\ndelivery_target: update\n')
        self.assertEqual(self.status(), 'accepted')
        self.write('_kb-control/project-contract.yaml', 'audiences:\n  - developers\ndelivery_target: update\n')
        self.assertEqual(self.status(), 'blocked')

    def test_historical_feedback_is_not_a_permanent_requirement(self):
        execution.save(self.control / 'workflow.json', {'history': [{'event': 'feedback-invalidated',
            'kind': 'content-depth', 'from_stage': 'pilot'}], 'stages': [{'id': 'pilot', 'status': 'pass'}]})
        self.assertFalse(execution.required(self.root, ['one.md']))
        self.assertFalse(execution.required(self.root, ['one.md'], legacy=True))


class ScopedEditorialTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        (self.root / '_kb-control').mkdir()
        self.write('one.md', '# Work\nRead the supplied material and explain its important distinction.\n')
        self.write('two.md', '# Another topic\nIndependent content.\n')
        self.write('_kb-control/reader-brief.md', 'A manager wants a clear explanation and an informed decision.')

    def write(self, name, text):
        (self.root / name).write_text(text, encoding='utf-8')

    def plan(self, **kwargs):
        return update.plan_update(self.root, ['one.md'], schema_version=3, **kwargs)

    def reviewed(self, plan):
        plan['checks'] = [{'kind': kind, 'status': 'pass', 'pagePaths': plan['checkScopes'][kind],
            'inputDigests': plan['inputDigests'], 'contractDigests': plan['contractDigests'],
            'summary': 'Read the selected explanation in context and retained the supported claim.'}
            for kind in plan['requiredChecks']]
        return plan

    def test_mature_prose_needs_one_editor_record_no_stage_or_self_review_documents(self):
        plan = self.reviewed(update.plan_update(self.root, ['one.md']))
        self.assertEqual(plan['schemaVersion'], 3)
        self.assertEqual(plan['requiredChecks'], ['editor-review'])
        self.assertFalse(plan['independentReaderRequired'])
        result = update.check_update(self.root, plan)
        self.assertEqual(result['status'], 'pass', result)
        self.assertEqual(result['globalWorkflow']['status'], 'uninitialized')
        self.assertEqual(sorted(p.name for p in (self.root / '_kb-control').iterdir()), ['reader-brief.md'])

    def test_newbie_tag_does_not_invoke_workers(self):
        execution.save(self.root / '_kb-control/learning-design.json', {'explanationProfile': 'novice_mental_model'})
        self.assertFalse(self.plan()['independentReaderRequired'])
        self.assertEqual(update.check_update(self.root, self.reviewed(self.plan()))['status'], 'pass')

    def test_omitted_editor_judgment_fails(self):
        plan = self.reviewed(self.plan())
        plan['checks'][0].pop('summary')
        result = update.check_update(self.root, plan)
        self.assertIn('editor-reading-missing', {e['kind'] for e in result['errors']})

    def test_record_binds_the_actual_editor_judgment_without_copying_metadata(self):
        plan = self.plan()
        recorded = update.record_check(self.root, plan, 'editor-review', 'Read the current passage; its distinction is supported and its scope appropriate.')
        self.assertEqual(update.check_update(self.root, recorded)['status'], 'pass')
        self.write('one.md', '# Changed\nA new unsupported guarantee.')
        with self.assertRaisesRegex(ValueError, 'Inputs'):
            update.record_check(self.root, plan, 'editor-review', 'The old review passed.')

    def test_changed_manuscript_and_changed_sources_cannot_reuse_the_old_receipt(self):
        self.write('source.md', 'Relevant original evidence.')
        plan = self.reviewed(self.plan(context_paths=['_kb-control/reader-brief.md', 'source.md']))
        self.write('source.md', 'Different evidence changes the conclusion.')
        self.assertEqual(update.check_update(self.root, plan)['status'], 'fail')
        self.write('source.md', 'Relevant original evidence.')
        self.write('one.md', '# Revised\nDifferent explanation.')
        self.assertEqual(update.check_update(self.root, plan)['status'], 'fail')

    def test_relevant_contract_projection_changes_but_unrelated_rows_do_not(self):
        coverage = {'pages': [{'path': 'one.md', 'primaryQuestion': 'Why this?'}, {'path': 'two.md', 'primaryQuestion': 'Why that?'}]}
        execution.save(self.root / '_kb-control/content-coverage.json', coverage)
        plan = self.reviewed(self.plan())
        coverage['pages'][1]['primaryQuestion'] = 'A different independent question.'
        execution.save(self.root / '_kb-control/content-coverage.json', coverage)
        self.assertEqual(update.check_update(self.root, plan)['status'], 'pass')
        coverage['pages'][0]['primaryQuestion'] = 'A different promise.'
        execution.save(self.root / '_kb-control/content-coverage.json', coverage)
        result = update.check_update(self.root, plan)
        self.assertIn('update-stale-contract', {e['kind'] for e in result['errors']})

    def test_unrelated_pending_batch_does_not_spread_but_selected_pending_batch_blocks(self):
        execution.init(self.root, {'schemaVersion': 2, 'batches': [{'id': 'two', 'pages': ['two.md'],
            'briefPath': '_kb-control/reader-brief.md', 'task': 'Independently inspect this passage.'}]})
        self.assertEqual(update.check_update(self.root, self.reviewed(self.plan()))['status'], 'pass')
        plan = update.plan_update(self.root, ['two.md'], schema_version=3)
        self.assertTrue(plan['independentReaderRequired'])
        self.assertEqual(plan['requiredChecks'], [])  # Actual editorial decision will be the record.
        self.assertEqual(update.check_update(self.root, plan)['status'], 'fail')

    def test_declared_whole_scope_independent_requirement_cannot_be_disabled(self):
        self.write('_kb-control/project-contract.yaml', 'reader_review_policy: independent\n')
        plan = self.reviewed(self.plan())
        plan['independentReaderRequired'] = False
        self.assertEqual(update.check_update(self.root, plan)['status'], 'fail')

    def test_broken_local_link_is_still_blocking(self):
        self.write('one.md', '# Work\n[Required prerequisite](missing.md)\n')
        result = update.check_update(self.root, self.reviewed(self.plan()))
        self.assertEqual(result['status'], 'fail', result)
        self.assertIn('missing-markdown-link', {e.get('type') for e in result['errors']})

    def test_embedded_asset_changes_invalidate_receipt_without_a_manifest(self):
        self.write('figure.svg', '<svg xmlns="http://www.w3.org/2000/svg"><text>A</text></svg>')
        self.write('one.md', '# Work\n![Meaning](figure.svg)\n')
        plan = self.reviewed(self.plan())
        self.assertEqual(update.check_update(self.root, plan)['status'], 'pass')
        self.write('figure.svg', '<svg xmlns="http://www.w3.org/2000/svg"><text>B</text></svg>')
        self.assertEqual(update.check_update(self.root, plan)['status'], 'fail')

    def test_unrelated_visual_failure_does_not_stale_or_block_local_prose(self):
        execution.save(self.root / '_kb-control/visual-explanations.json', {'schemaVersion': 2,
            'status': 'needs_work', 'items': [{'id': 'unrelated', 'pagePath': 'two.md', 'assetPath': 'absent.svg'}]})
        plan = self.reviewed(self.plan())
        self.assertNotIn('absent.svg', plan['inputDigests'])
        self.assertEqual(update.check_update(self.root, plan)['status'], 'pass')
        execution.save(self.root / '_kb-control/visual-explanations.json', {'schemaVersion': 2,
            'status': 'pending', 'items': [{'id': 'unrelated', 'pagePath': 'two.md', 'assetPath': 'other-absent.svg'}]})
        self.assertEqual(update.check_update(self.root, plan)['status'], 'pass')

    def test_changed_prerequisite_selects_its_consumer_but_not_an_unrelated_chapter(self):
        self.write('three.md', '# Unrelated\nSeparate explanation.')
        execution.save(self.root / '_kb-control/knowledge-model.json', {'units': [
            {'id': 'one', 'canonicalOwner': 'one.md', 'dependencies': []},
            {'id': 'two', 'canonicalOwner': 'two.md', 'dependencies': ['one']},
            {'id': 'three', 'canonicalOwner': 'three.md', 'dependencies': []}]})
        plan = self.plan()
        self.assertEqual(plan['reviewPages'], ['one.md', 'two.md'])
        self.assertNotIn('three.md', plan['inputDigests'])

    def test_legacy_global_state_is_not_promoted_by_a_scoped_pass(self):
        state = {'status': 'blocked', 'stages': [], 'blocker': {'kind': 'repeated-failure'}}
        execution.save(self.root / '_kb-control/workflow.json', state)
        before = (self.root / '_kb-control/workflow.json').read_bytes()
        result = update.check_update(self.root, self.reviewed(self.plan()))
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['globalWorkflow']['status'], 'blocked')
        self.assertEqual((self.root / '_kb-control/workflow.json').read_bytes(), before)

    def test_declared_work_comparison_is_checked_without_legacy_page_certificates(self):
        import test_reader_probes as fixtures
        from kb_work_comparison import render
        fixture = fixtures.WorkComparisonTests()
        fixture.setUp()
        model = fixture.model
        page = {'path': 'one.md', 'workedExample': {'workComparison': model}}
        execution.save(self.root / '_kb-control/content-coverage.json', {'pages': [page]})
        self.write('one.md', '# Work\n' + render(model))
        self.assertEqual(update.check_update(self.root, self.reviewed(self.plan()))['status'], 'pass')
        self.write('one.md', '# Work\n' + render(model).replace('| 每笔人工作量合计 | 15 | 13 | 10 |', '| 每笔人工作量合计 | 15 | 13 | 1 |'))
        # An editor receipt cannot override a changed published numeric result.
        self.assertEqual(update.check_update(self.root, self.reviewed(self.plan()))['status'], 'fail')

    def test_existing_source_references_do_not_disappear_with_the_self_review(self):
        execution.save(self.root / '_kb-control/knowledge-model.json', {'units': [
            {'id': 'one', 'canonicalOwner': 'one.md', 'sourceRefs': ['source#missing-claim']}]})
        execution.save(self.root / '_kb-control/source-understanding.json', {'sources': [
            {'id': 'source', 'path': 'source.md', 'coreClaims': [{'id': 'actual-claim', 'statement': 'A narrower claim.'}]}]})
        self.write('source.md', '# Source\nA narrower claim.')
        result = update.check_update(self.root, self.reviewed(self.plan()))
        self.assertIn('unknown-source-ref', {e.get('kind') for e in result['errors']})

    def test_short_specific_stage_report_is_valid_but_empty_report_is_not(self):
        self.write('report.md', 'The current entrypoint opens; the broken relative link is fixed.')
        errors = []
        stages.read_text(self.root / 'report.md', errors, 'report')
        self.assertEqual(errors, [])
        self.write('report.md', '\n  ')
        stages.read_text(self.root / 'report.md', errors, 'report')
        self.assertEqual(errors[0]['kind'], 'empty-report')


if __name__ == '__main__':
    unittest.main()
