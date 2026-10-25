#!/usr/bin/env python3
"""Input-only trials expose actual work; runtime calls here are test doubles."""
import copy
import unittest

import kb_execution as kb
import test_execution as fixtures


class ReaderTrialTests(unittest.TestCase):
    setUp = fixtures.ExecutionTests.setUp
    write = fixtures.ExecutionTests.write
    batch = fixtures.ExecutionTests.batch
    state = fixtures.ExecutionTests.state
    status = fixtures.ExecutionTests.status
    verdict = fixtures.ExecutionTests.verdict
    OLD, NEW, FIXED = fixtures.ExecutionTests.OLD, fixtures.ExecutionTests.NEW, fixtures.ExecutionTests.FIXED
    SECRET_ANSWER, SECRET_REPAIR = fixtures.ExecutionTests.SECRET_ANSWER, fixtures.ExecutionTests.SECRET_REPAIR

    def plan(self, **extra):
        brief = (self.control / 'reader-brief.md').read_text()
        task = {'id': 'reader-task', 'request': brief, 'sourceQuote': brief,
                'trialInputs': [{'path': 'one.md', 'quote': '收到客户消息。'}]}
        kb.init(self.root, {'schemaVersion': 2, 'batches': [{
            'id': 'one', 'pages': ['one.md'], 'briefPath': '_kb-control/reader-brief.md',
            'task': 'Review the actual material.', 'readerTasks': [task], **extra}]})

    def trial(self, blocked=False):
        return {'tasks': [{'id': 'reader-task', 'status': 'blocked' if blocked else 'completed',
            'output': 'Only the received message can be identified.',
            'missing': 'The recipient and handoff material are absent.' if blocked else ''}]}

    def run_reading(self, blocked=False):
        self.runtime.enqueue('trial', self.trial(blocked))
        self.runtime.enqueue('reader', self.verdict())
        return kb.run_batch(self.root, 'one')

    def decision(self, resolutions=(), status='accepted'):
        return {'status': status, 'summary': 'Read the material and inspected the actual attempt.',
                'basis': [{'path': 'one.md', 'quote': '收到客户消息。'}], 'resolutions': list(resolutions)}

    def test_trial_receives_only_selected_inputs_and_full_review_can_inspect_solution(self):
        solution = 'PUBLISHED_WORKED_SOLUTION_64bb'
        self.write('one.md', self.OLD + '\n' + solution)
        self.plan()
        self.assertEqual(self.run_reading()['status'], 'awaiting_editor')
        first, second = self.runtime.calls
        self.assertEqual([first['role'], second['role']], ['trial', 'reader'])
        self.assertNotIn(solution, first['prompt'])
        self.assertIn(solution, second['prompt'])
        self.assertIn(self.trial()['tasks'][0]['output'], second['prompt'])
        for call in (first, second):
            self.assertNotIn(self.SECRET_ANSWER, call['prompt'])
            self.assertNotIn(self.SECRET_REPAIR, call['prompt'])
            self.assertNotIn('Author source context only.', call['prompt'])

    def test_reader_pass_cannot_erase_blocked_trial_or_unresolved_editor_decision(self):
        self.plan()
        self.run_reading(blocked=True)
        with self.assertRaisesRegex(ValueError, 'every actual finding'):
            kb.decide(self.root, 'one', self.decision())
        deferred = [{'id': 'trial:task:reader-task', 'action': 'deferred', 'reason': 'Need actual input.'}]
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            kb.decide(self.root, 'one', self.decision(deferred))
        self.assertEqual(kb.decide(self.root, 'one', self.decision(deferred, 'needs_work'))['status'], 'needs_work')
        self.assertTrue(kb.gate(self.root, ['one.md']))

    def test_missing_runtime_stops_before_full_review(self):
        self.plan()
        self.runtime.enqueue('trial', status='runtime_error')
        result = kb.run_batch(self.root, 'one')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual([c['role'] for c in self.runtime.calls], ['trial'])
        self.assertTrue(kb.gate(self.root, ['one.md']))

    def test_trial_input_must_be_current_published_material(self):
        brief = (self.control / 'reader-brief.md').read_text()
        for excerpt in ({'path': '_kb-control/source.md', 'quote': 'Author source context only.'},
                        {'path': 'one.md', 'quote': 'Invented customer material.'}):
            with self.subTest(excerpt=excerpt), self.assertRaises(ValueError):
                self.plan(readerTasks=[{'id': 'reader-task', 'request': brief, 'sourceQuote': brief,
                                       'trialInputs': [excerpt]}])
        self.assertFalse((self.control / 'execution.json').exists())

    def test_changed_material_and_changed_trial_request_cannot_reuse_acceptance(self):
        self.plan()
        self.run_reading()
        kb.decide(self.root, 'one', self.decision())
        paths = kb.evidence_paths(self.root, ['one.md'])
        self.assertTrue(any(p.parent.name == 'trial' and p.name == 'prompt.txt' for p in paths))
        self.write('one.md', self.NEW)
        self.assertEqual(self.status(), 'blocked')
        self.write('one.md', self.OLD)
        self.assertEqual(self.status(), 'accepted')
        attempt = self.batch()['attempts'][-1]
        prompt = self.root / attempt['trialRun'] / 'prompt.txt'
        prompt.write_text(prompt.read_text() + '\nInjected solution.')
        self.assertEqual(self.status(), 'blocked')

    def test_full_review_cannot_reuse_trial_identity(self):
        self.plan()
        self.runtime.enqueue('trial', self.trial(), identity='same-session')
        self.runtime.enqueue('reader', self.verdict(), identity='same-session')
        result = kb.run_batch(self.root, 'one')
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('distinct', result['error'])

    def test_existing_editorial_method_keeps_its_actual_acceptance(self):
        self.plan(methodVersion=1, readerTasks=[self._plain_task()])
        state = self.state()
        state['batches'][0].pop('methodVersion')
        kb.save_state(self.root, state)
        self.runtime.enqueue('reader', self.verdict())
        kb.run_batch(self.root, 'one')
        original = copy.deepcopy(self.batch())
        self.assertEqual(kb.decide(self.root, 'one', self.decision())['status'], 'accepted')
        kb.init(self.root, {'schemaVersion': 2, 'batches': [{'id': 'two', 'pages': ['two.md'],
            'briefPath': '_kb-control/reader-brief.md', 'task': 'Read a different scope.'}]})
        self.assertEqual(self.status(), 'accepted')
        self.assertEqual(self.batch()['attempts'][0]['readerRun'], original['attempts'][0]['readerRun'])

    def _plain_task(self):
        brief = (self.control / 'reader-brief.md').read_text()
        return {'id': 'reader-task', 'request': brief, 'sourceQuote': brief}

    def test_trial_output_cannot_disguise_incompletion_as_completed(self):
        self.plan()
        output = self.trial(blocked=True)
        output['tasks'][0]['status'] = 'completed'
        with self.assertRaisesRegex(ValueError, 'disagree'):
            kb.trial_result(self.batch(), output)

    def test_upgrading_old_editorial_method_retains_history_and_needs_fresh_reading(self):
        self.plan(methodVersion=1, readerTasks=[self._plain_task()])
        self.runtime.enqueue('reader', self.verdict())
        kb.run_batch(self.root, 'one')
        kb.decide(self.root, 'one', self.decision())
        original = copy.deepcopy(self.batch()['attempts'])
        kb.migrate_review(self.root, 'one', 'Investigate the actual argument with the current method.')
        self.assertEqual(self.batch()['attempts'], original)
        self.assertEqual(self.batch()['methodVersion'], 3)
        self.assertEqual(self.status(), 'blocked')
        self.runtime.enqueue('reader', self.verdict())
        self.assertEqual(kb.run_batch(self.root, 'one')['status'], 'awaiting_editor')
        self.assertEqual(kb.decide(self.root, 'one', self.decision())['status'], 'accepted')
        self.assertEqual(self.batch()['attempts'][0], original[0])


if __name__ == '__main__':
    unittest.main()
