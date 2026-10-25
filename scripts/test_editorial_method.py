"""Dispatch and feedback behavior, not semantic writing-quality assertions."""
import copy
import unittest
from unittest.mock import patch

import kb_execution as kb
import kb_editorial as methods
import kb_update as update
import test_execution as fixtures


class SharedMethodTests(unittest.TestCase):
    setUp = fixtures.ExecutionTests.setUp
    write = fixtures.ExecutionTests.write
    state = fixtures.ExecutionTests.state
    batch = fixtures.ExecutionTests.batch
    status = fixtures.ExecutionTests.status
    verdict = fixtures.ExecutionTests.verdict
    OLD, NEW, FIXED = fixtures.ExecutionTests.OLD, fixtures.ExecutionTests.NEW, fixtures.ExecutionTests.FIXED
    SECRET_ANSWER, SECRET_REPAIR = fixtures.ExecutionTests.SECRET_ANSWER, fixtures.ExecutionTests.SECRET_REPAIR

    def plan(self, **extra):
        kb.init(self.root, {'schemaVersion': 2, 'batches': [{'id': 'one', 'pages': ['one.md'],
            'briefPath': '_kb-control/reader-brief.md', 'task': 'Write for the current reader.', **extra}]})

    def review(self):
        self.runtime.enqueue('reader', self.verdict())
        return kb.run_batch(self.root, 'one')

    def decision(self, **extra):
        return {'status': 'accepted', 'summary': 'Current editorial choice.',
                'basis': [{'path': 'one.md', 'quote': '收到客户消息'}], 'resolutions': [], **extra}

    def test_dispatch_sends_exact_shared_method_and_writer_examples(self):
        self.plan(authoringMode='rewrite', counterReview=True)
        self.runtime.enqueue('writer', {'pages': [{'path': 'one.md', 'content': self.NEW}]})
        self.runtime.enqueue('reader', self.verdict())
        self.runtime.enqueue('auditor', self.verdict())
        self.assertEqual(kb.run_batch(self.root, 'one')['status'], 'awaiting_editor')
        snapshot = kb.captured_method(self.root, self.batch(), self.batch()['attempts'][-1])
        self.assertEqual(snapshot, methods.current_method())
        writer, reader, auditor = self.runtime.calls
        for row in snapshot['files']:
            self.assertIn(row['content'], writer['prompt'])
        self.assertIn(snapshot['files'][0]['content'], reader['prompt'])
        self.assertIn(snapshot['files'][0]['content'], auditor['prompt'])
        self.assertNotIn(snapshot['files'][1]['content'], reader['prompt'])
        self.assertEqual(kb.decide(self.root, 'one', self.decision())['status'], 'accepted')
        self.assertTrue(any(p.name == 'method.json' for p in kb.evidence_paths(self.root)))

    def test_retry_carries_editor_disposition_and_own_findings_only_to_writer(self):
        self.plan(authoringMode='rewrite')
        output = self.verdict()
        output['pages'][0].update(status='needs_work', gaps=[{'id': 'add', 'detail': 'REVIEWER_ADD_147',
            'blocking': True, 'cause': 'mechanism', 'proposal': 'add'}])
        self.runtime.enqueue('writer', {'pages': [{'path': 'one.md', 'content': self.NEW}]})
        self.runtime.enqueue('reader', output)
        kb.run_batch(self.root, 'one')
        decision = self.decision(status='needs_work', summary='EDITOR_REPLACE_571: change the premise; keep the comparison.',
            resolutions=[{'id': 'reader:add', 'action': 'declined', 'reason': 'EDITOR_DECLINE_319: not relevant to this reader.',
                          'basis': [{'path': 'one.md', 'quote': '收到客户消息'}]}])
        kb.decide(self.root, 'one', decision)
        self.runtime.enqueue('writer', {'pages': [{'path': 'one.md', 'content': self.FIXED}]})
        self.runtime.enqueue('reader', self.verdict())
        self.assertEqual(kb.run_batch(self.root, 'one')['status'], 'awaiting_editor')
        writer, reader = self.runtime.calls[-2:]
        for marker in ('EDITOR_REPLACE_571', 'EDITOR_DECLINE_319', 'REVIEWER_ADD_147'):
            self.assertIn(marker, writer['prompt'])
            self.assertNotIn(marker, reader['prompt'])
        self.assertIn('"action": "declined"', writer['prompt'])

    def test_method_upgrade_does_not_reinterpret_captured_runs(self):
        self.plan()
        self.review()
        kb.decide(self.root, 'one', self.decision())
        newer = copy.deepcopy(methods.current_method())
        newer['files'][0]['content'] += '\nUPDATED_METHOD_915\n'
        newer['files'][0]['sha256'] = methods.text_digest(newer['files'][0]['content'])
        with patch.object(kb, 'current_method', return_value=newer):
            self.assertEqual(self.status(), 'accepted')
            self.review()
        self.assertIn('UPDATED_METHOD_915', self.runtime.calls[-1]['prompt'])
        self.assertNotIn('UPDATED_METHOD_915', self.runtime.calls[0]['prompt'])

    def test_changed_or_missing_method_snapshot_blocks_acceptance(self):
        self.plan()
        self.review()
        kb.decide(self.root, 'one', self.decision())
        p = self.root / self.batch()['attempts'][-1]['methodSnapshot']['path']
        original = p.read_bytes()
        p.write_text('{}')
        self.assertEqual(self.status(), 'blocked')
        p.write_bytes(original)
        self.assertEqual(self.status(), 'accepted')
        p.unlink()
        self.assertEqual(self.status(), 'blocked')

    def test_unavailable_shared_method_stops_before_dispatch(self):
        self.plan(authoringMode='rewrite')
        with patch.object(kb, 'current_method', side_effect=ValueError('Missing editorial method')):
            with self.assertRaisesRegex(ValueError, 'Missing editorial'):
                kb.run_batch(self.root, 'one')
        self.assertEqual(self.runtime.calls, [])
        self.assertEqual(self.batch()['attempts'], [])
        self.assertEqual((self.root / 'one.md').read_text(), self.OLD)

    def test_malformed_snapshot_is_rejected_without_role_dispatch(self):
        snapshot = copy.deepcopy(methods.current_method())
        snapshot['files'].insert(1, None)
        with self.assertRaisesRegex(ValueError, 'shared method and examples'):
            methods.render_method(snapshot, 'reader')

    def test_method_two_remains_usable_and_migration_requires_fresh_review(self):
        self.plan(methodVersion=2)
        with patch.object(kb, 'current_method', side_effect=AssertionError('Old method must not load new guide')):
            self.review()
            kb.decide(self.root, 'one', self.decision())
            self.assertEqual(self.status(), 'accepted')
        old = copy.deepcopy(self.batch()['attempts'])
        kb.migrate_review(self.root, 'one', 'Use the shared method for a current editorial question.')
        self.assertEqual(self.batch()['attempts'], old)
        self.assertEqual(self.batch()['methodVersion'], 3)
        self.assertEqual(self.status(), 'blocked')
        self.assertEqual(self.review()['status'], 'awaiting_editor')
        self.assertEqual(kb.decide(self.root, 'one', self.decision())['status'], 'accepted')

    def test_scoped_result_separates_editor_report_from_learning_evidence(self):
        plan = update.plan_update(self.root, ['one.md'])
        plan = update.record_check(self.root, plan, 'editor-review', 'Read this current handoff.')
        result = update.check_update(self.root, plan)
        self.assertEqual(result['status'], 'pass')
        self.assertEqual(result['editorialEvidence']['editorReportedPages'], ['one.md'])
        self.assertEqual(result['editorialEvidence']['independentReviewPages'], [])
        self.assertEqual(result['editorialEvidence']['observedLearning'], 'not-assessed')


if __name__ == '__main__':
    unittest.main()
