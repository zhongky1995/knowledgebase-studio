"""Original-question provenance, reader isolation and existing editorial gates."""
import copy
import unittest

import kb_execution as kb
import test_execution as fixtures


class IntentReadingTests(unittest.TestCase):
    setUp = fixtures.ExecutionTests.setUp
    write = fixtures.ExecutionTests.write
    state = fixtures.ExecutionTests.state
    batch = fixtures.ExecutionTests.batch
    status = fixtures.ExecutionTests.status
    verdict = fixtures.ExecutionTests.verdict
    OLD, NEW, FIXED = fixtures.ExecutionTests.OLD, fixtures.ExecutionTests.NEW, fixtures.ExecutionTests.FIXED
    SECRET_ANSWER, SECRET_REPAIR = fixtures.ExecutionTests.SECRET_ANSWER, fixtures.ExecutionTests.SECRET_REPAIR
    ORIGINAL = '团队怎样从交接中学到可复用的判断，而不只是把消息转走？'
    RAW = '_kb-control/original.md'

    def plan(self, **extra):
        self.write(self.RAW, self.ORIGINAL + '\n未选原文_PRIVATE_891\n另一个问题。')
        return kb.init(self.root, {'schemaVersion': 2, 'batches': [{'id': 'one', 'pages': ['one.md'],
            'briefPath': '_kb-control/reader-brief.md', 'task': 'AUTHOR_PLAN_249',
            'sourcePaths': ['_kb-control/source.md'],
            'readerTasks': [{'id': 'reader-task', 'request': '依据正文说明一项客户消息怎样完成交接，哪些情况仍不确定。',
                             'sourceQuote': '能够完成一次交接'}],
            'intentSources': [{'path': self.RAW, 'quote': self.ORIGINAL}], **extra}]})

    def output(self, blocking=False):
        value = self.verdict()
        value['intentReview'] = {'status': 'needs_work' if blocking else 'pass',
            'attempt': '对照原问题辨认正文实际论证的内容，并判断当前范围的回应。',
            'basis': [{'path': self.RAW, 'quote': self.ORIGINAL}, {'path': 'one.md', 'quote': '收到客户消息'}],
            'gaps': [{'id': 'core-gap', 'detail': 'INTENT_REPAIR_627', 'blocking': True,
                      'cause': 'question', 'proposal': 'replace'}] if blocking else []}
        return value

    def review(self, output=None):
        self.runtime.enqueue('reader', self.output() if output is None else output)
        return kb.run_batch(self.root, 'one')

    def decision(self, **extra):
        return {'status': 'accepted', 'summary': 'Read the actual manuscript against the selected original question.',
                'basis': [{'path': 'one.md', 'quote': '收到客户消息'}], 'resolutions': [], **extra}

    def test_selected_original_reaches_both_roles_without_private_reader_context(self):
        self.plan(authoringMode='rewrite')
        self.runtime.enqueue('writer', {'pages': [{'path': 'one.md', 'content': self.NEW}]})
        result = self.review()
        self.assertEqual(result['status'], 'awaiting_editor')
        self.assertEqual(result['intentScope']['sourcePaths'], [self.RAW])
        writer, reader = self.runtime.calls
        for call in (writer, reader):
            self.assertIn(self.ORIGINAL, call['prompt'])
            self.assertNotIn('未选原文_PRIVATE_891', call['prompt'])
        for hidden in ('AUTHOR_PLAN_249', 'Author source context only.', self.SECRET_ANSWER, self.SECRET_REPAIR):
            self.assertNotIn(hidden, reader['prompt'])
        self.assertIn('Author source context only.', writer['prompt'])
        self.assertIn('intentReview', reader['schema']['required'])
        self.assertNotIn('intentReview', kb.EDITORIAL_SCHEMA['required'])

    def test_page_passes_do_not_replace_original_question_review(self):
        self.plan()
        result = self.review(self.verdict())
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('overall intentReview', result['error'])

    def test_new_intent_reading_cannot_silently_use_a_broad_brief_as_work(self):
        self.write(self.RAW, self.ORIGINAL)
        with self.assertRaisesRegex(ValueError, 'explicit readerTasks'):
            kb.init(self.root, {'schemaVersion': 2, 'batches': [{'id': 'one', 'pages': ['one.md'],
                'briefPath': '_kb-control/reader-brief.md', 'task': 'Read the core.',
                'intentSources': [{'path': self.RAW, 'quote': self.ORIGINAL}]}]})
        self.assertFalse(self.runtime.calls)
        self.assertFalse((self.control/'execution.json').exists())

    def test_existing_intent_reading_keeps_its_captured_task_and_method(self):
        self.plan(); self.review()
        kb.decide(self.root, 'one', self.decision())
        before = copy.deepcopy(self.batch())
        with unittest.mock.patch.object(kb, 'current_method', side_effect=AssertionError('Do not load the new method for old evidence.')):
            self.assertEqual(self.status(), 'accepted')
        self.assertEqual(self.batch(), before)

    def test_citations_must_compare_original_and_actual_prose(self):
        for basis in [[{'path': self.RAW, 'quote': self.ORIGINAL}],
                      [{'path': 'one.md', 'quote': '收到客户消息'}]]:
            with self.subTest(basis=basis):
                self.plan()
                output = self.output(); output['intentReview']['basis'] = basis
                result = self.review(output)
                self.assertEqual(result['status'], 'blocked')
                self.assertIn('must compare', result['error'])
                # Reuse this filesystem for the next independent invalid-input case.
                for path in [self.control/'execution.json', self.control/'execution-batches/one.json']:
                    path.unlink()

    def test_unselected_original_cannot_be_claimed_as_seen(self):
        self.plan()
        output = self.output(); output['intentReview']['basis'][0]['quote'] = '未选原文_PRIVATE_891'
        result = self.review(output)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('absent', result['error'])

    def test_original_input_cannot_fill_missing_published_task_answer(self):
        self.plan()
        output = self.output(); output['taskResults'][0]['basis'] = [{'path': self.RAW, 'quote': self.ORIGINAL}]
        result = self.review(output)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('task basis', result['error'])

    def test_unresolved_core_gap_blocks_acceptance_and_real_dependents(self):
        self.plan()
        kb.init(self.root, {'schemaVersion': 2, 'batches': [{'id': 'later', 'pages': ['two.md'],
            'briefPath': '_kb-control/reader-brief.md', 'task': 'Continue this settled argument.', 'after': ['one']}]})
        self.assertEqual(self.review(self.output(True))['status'], 'awaiting_editor')
        resolutions = [{'id': 'reader:core-gap', 'action': 'deferred', 'reason': 'The core still needs development.'}]
        with self.assertRaisesRegex(ValueError, 'Unresolved consequential'):
            kb.decide(self.root, 'one', self.decision(resolutions=resolutions))
        kb.decide(self.root, 'one', self.decision(status='needs_work', resolutions=resolutions))
        with self.assertRaisesRegex(ValueError, 'dependency one'):
            kb.run_batch(self.root, 'later')
        self.assertTrue(kb.gate(self.root, ['one.md']))
        self.assertEqual(len(self.runtime.calls), 1)

    def test_original_source_change_invalidates_accepted_reading(self):
        self.plan(); self.review()
        kb.decide(self.root, 'one', self.decision())
        self.assertEqual(self.status(), 'accepted')
        self.assertIn(self.root/self.RAW, kb.evidence_paths(self.root, ['one.md']))
        # Even a change outside the selected excerpt changes the bound source.
        self.write(self.RAW, self.ORIGINAL + '\nchanged context')
        self.assertEqual(self.status(), 'blocked')

    def test_replan_preserves_history_and_cannot_disable_original_reading(self):
        self.plan(); self.review()
        kb.decide(self.root, 'one', self.decision())
        old = copy.deepcopy(self.batch()['attempts'])
        with self.assertRaises(ValueError):
            kb.replan(self.root, 'one', {'intentSources': []}, 'Do not bypass the assigned question.')
        kb.replan(self.root, 'one', {'intentSources': [{'path': self.RAW, 'quote': '另一个问题。'}]}, 'The user changed the problem.')
        self.assertEqual(self.batch()['attempts'], old)
        self.assertEqual(self.status(), 'blocked')
        output = self.output(); output['intentReview']['basis'][0]['quote'] = '另一个问题。'
        self.assertEqual(self.review(output)['status'], 'awaiting_editor')

    def test_structure_and_original_question_both_need_actual_results(self):
        self.plan(readingPath=['one.md', 'two.md'])
        output = self.output()
        result = self.review(output)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('overall structureReview', result['error'])
        output['structureReview'] = {'status': 'pass', 'attempt': '读过所选全文和后续标题。',
            'basis': [{'path': 'one.md', 'quote': '收到客户消息'}], 'gaps': []}
        result = self.review(output)
        self.assertEqual(result['status'], 'awaiting_editor')
        self.assertEqual(result['structureScope']['outlineOnlyPages'], ['two.md'])
        self.assertIn('intentScope', result)

    def test_retry_receives_actual_core_feedback_but_fresh_reader_does_not(self):
        self.plan(authoringMode='rewrite')
        for number in range(2):
            self.runtime.enqueue('writer', {'pages': [{'path': 'one.md', 'content': self.NEW if number == 0 else self.FIXED}]})
            self.assertEqual(self.review(self.output(number == 0))['status'], 'awaiting_editor')
            if number == 0:
                kb.decide(self.root, 'one', self.decision(status='needs_work', summary='EDITOR_CORE_719', resolutions=[
                    {'id': 'reader:core-gap', 'action': 'deferred', 'reason': 'Develop the original question.'}]))
        writer, reader = self.runtime.calls[-2:]
        for marker in ('EDITOR_CORE_719', 'INTENT_REPAIR_627'):
            self.assertIn(marker, writer['prompt']); self.assertNotIn(marker, reader['prompt'])
        self.assertEqual(kb.decide(self.root, 'one', self.decision())['status'], 'accepted')

    def test_counter_reader_receives_observed_intent_work_without_prior_label(self):
        self.plan(counterReview=True)
        self.runtime.enqueue('reader', self.output(True))
        self.runtime.enqueue('auditor', self.output())
        self.assertEqual(kb.run_batch(self.root, 'one')['status'], 'awaiting_editor')
        prompt = self.runtime.calls[-1]['prompt']
        self.assertIn('INTENT_REPAIR_627', prompt)
        self.assertNotIn('"status": "needs_work"', prompt)

    def test_invalid_selection_is_rejected_before_dispatch(self):
        for sources in [[], [{'path': self.RAW, 'quote': 'absent'}],
                        [{'path': self.RAW, 'quote': self.ORIGINAL}, {'path': '_kb-control/./original.md', 'quote': self.ORIGINAL}],
                        [{'path': './one.md', 'quote': '收到客户消息'}]]:
            with self.subTest(sources=sources), self.assertRaises(ValueError):
                self.plan(intentSources=sources)
        with self.assertRaisesRegex(ValueError, 'method'):
            self.plan(methodVersion=2)
        self.assertFalse(self.runtime.calls)

    def test_original_source_cannot_leak_as_a_legacy_prerequisite(self):
        self.write('prior.md', self.ORIGINAL + '\n未选原文_PRIVATE_891')
        self.plan(intentSources=[{'path': './prior.md', 'quote': self.ORIGINAL}])
        kb.save(self.control / 'knowledge-model.json', {'units': [
            {'id': 'first', 'canonicalOwner': 'one.md', 'dependencies': ['later']},
            {'id': 'later', 'canonicalOwner': 'prior.md', 'dependencies': []}]})
        self.coverage['pages'][0]['knowledgeUnitIds'] = ['first']
        kb.save(self.control / 'content-coverage.json', self.coverage)
        result = kb.run_batch(self.root, 'one')
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('distinct', result['error'])
        self.assertFalse(self.runtime.calls)


if __name__ == '__main__':
    unittest.main()
