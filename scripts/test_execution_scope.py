#!/usr/bin/env python3
"""Full review scope and queue projection freshness regressions."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import kb_execution as execution
import kb_stage_check as stages
import kb_workflow as workflow


class ExecutionScopeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.control = self.root / '_kb-control'
        self.control.mkdir()
        self.write('one.md', '# One\nPublished content.\n')
        self.write('two.md', '# Two\nPublished content.\n')
        self.write('_kb-control/brief.md', 'Read and explain the supplied page.')
        self.write('_kb-control/project-contract.yaml',
                   'product_posture: reference_library\napp_required: no\nreader_review_policy: independent\n')
        self.write('_kb-control/qc-report.md', 'QC evidence. ' * 50)
        keys = ['corpusIntegrity', 'productArchitecture', 'contentQuality', 'evidence']
        execution.save(self.control / 'qc-verdict.json', {
            'status': 'pass', 'overallClaim': 'pass', 'dimensions': dict.fromkeys(keys, 'pass'),
            'evidence': {key: ['one.md'] for key in keys}})
        execution.save(self.control / 'content-coverage.json', {'pages': []})

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def plan(self, identity='one'):
        execution.init(self.root, {'batches': [{
            'id': identity, 'pages': [identity + '.md'], 'briefPath': '_kb-control/brief.md',
            'task': 'Explain the page', 'authoringMode': 'review_existing', 'after': []}]})

    def pilot_state(self):
        execution.save(self.control / 'pilot-verdict.json', {'representativePaths': ['one.md']})
        artifact = '_kb-control/stage-check-pilot.json'
        execution.save(self.root / artifact, {'status': 'pass'})
        return {'stages': [{'id': 'pilot', 'status': 'pass', 'depends_on': [],
                            'artifacts': [artifact], 'required_artifacts': [artifact],
                            'artifact_digests': workflow.stage_artifact_digests(self.root, [artifact]),
                            'contract_digest': workflow.digest_path(self.control / 'project-contract.yaml'),
                            'deliverable_digests': workflow.stage_deliverable_digests(self.root, 'pilot')}]}

    def test_empty_coverage_cannot_disable_full_qc_gate(self):
        self.plan()
        result = stages.validate_stage(self.root, 'qc')
        self.assertEqual(result['status'], 'fail', result)
        self.assertTrue(any(e['kind'].startswith('execution-') for e in result['errors']))

    def test_reduced_coverage_does_not_hide_pending_page(self):
        self.plan('one')
        self.plan('two')
        execution.save(self.control / 'content-coverage.json', {'pages': [{'path': 'one.md'}]})
        # Isolate the accepted first page; the second page stays actually pending.
        original = execution.batch_status

        def status(root, state, identity, visiting=None):
            return {'status': 'accepted', 'agentId': 'first-reader'} if identity == 'one' else original(root, state, identity, visiting)

        with patch.object(execution, 'batch_status', side_effect=status):
            result = stages.validate_stage(self.root, 'qc')
        self.assertEqual(result['status'], 'fail', result)
        self.assertIn('two.md', result['evidence']['independentReaderExecution']['pages'])
        self.assertTrue(any(e['path'] == 'two.md' for e in result['errors']))

    def test_release_uses_same_full_scope(self):
        self.plan()
        with patch.dict(stages.VALIDATORS, {'release': lambda *args: None}):
            result = stages.validate_stage(self.root, 'release')
        self.assertEqual(result['status'], 'fail')
        self.assertTrue(any(e['kind'].startswith('execution-') for e in result['errors']))

    def test_discovery_exclusions_are_preserved_but_queue_is_included(self):
        self.write('_archive/old.md', 'Archived prose')
        self.write('generated/page.md', 'Generated prose')
        self.write('internal/private.md', 'Internal prose')
        execution.save(self.root / '.knowledgebase-audit.json', {
            'generatedRoots': ['generated'], 'internalRoots': ['internal'], 'ignorePaths': ['two.md']})
        self.plan('two')
        errors = []
        self.assertEqual(stages.full_execution_scope(self.root, [], errors), ['one.md', 'two.md'])
        self.assertEqual(errors, [])

    def test_legacy_qc_without_activated_execution_stays_readable(self):
        self.write('_kb-control/project-contract.yaml', 'product_posture: reference_library\napp_required: no\n')
        result = stages.validate_stage(self.root, 'qc')
        self.assertEqual(result['status'], 'pass', result)

    def test_empty_actual_scope_with_active_policy_fails(self):
        (self.root / 'one.md').unlink()
        (self.root / 'two.md').unlink()
        execution.save(self.control / 'qc-verdict.json', {
            'status': 'pass', 'overallClaim': 'pass',
            'dimensions': dict.fromkeys(['corpusIntegrity', 'productArchitecture', 'contentQuality', 'evidence'], 'pass'),
            'evidence': {key: ['_kb-control/brief.md'] for key in ['corpusIntegrity', 'productArchitecture', 'contentQuality', 'evidence']}})
        result = stages.validate_stage(self.root, 'qc')
        self.assertIn('execution-scope', {e['kind'] for e in result['errors']})

    def test_queue_only_mutation_invalidates_workflow_freshness(self):
        self.plan()
        state = self.pilot_state()
        self.assertEqual(workflow.stale_stage_reasons(self.root, state), [])
        queue = execution.batches(self.root)
        queue['batches'][0]['unexpectedStatus'] = 'runtime_error'
        execution.save(self.root / execution.STATE, queue)
        self.assertEqual(workflow.stage_deliverable_digests(self.root, 'pilot'), state['stages'][0]['deliverable_digests'])
        stale = workflow.stale_stage_reasons(self.root, state)
        self.assertTrue(any('projection' in reason for item in stale for reason in item['reasons']))

    def test_unrelated_queue_progress_does_not_invalidate_pilot(self):
        self.plan('one')
        self.plan('two')
        state = self.pilot_state()
        queue = execution.batches(self.root)
        queue['batches'][1]['unrelatedProgress'] = 'running'
        execution.save_state(self.root, queue)
        self.assertEqual(workflow.stale_stage_reasons(self.root, state), [])

    def test_pilot_checks_dependency_projections(self):
        self.plan('two')
        execution.init(self.root, {'batches': [{'id': 'one', 'pages': ['one.md'],
                       'briefPath': '_kb-control/brief.md', 'task': 'Explain', 'after': ['two']}]})
        state = self.pilot_state()
        queue = execution.batches(self.root)
        queue['batches'][0]['unexpectedStatus'] = 'failed'
        execution.save(self.root / execution.STATE, queue)
        self.assertTrue(workflow.stale_stage_reasons(self.root, state))


if __name__ == '__main__':
    unittest.main()
