"""Actual structural review scope and failure behavior, using a runtime double."""
import copy
import unittest

import kb_execution as kb
import kb_structure as structure
import test_execution as fixtures


class StructureReadingTests(unittest.TestCase):
    setUp = fixtures.ExecutionTests.setUp
    write = fixtures.ExecutionTests.write
    state = fixtures.ExecutionTests.state
    batch = fixtures.ExecutionTests.batch
    status = fixtures.ExecutionTests.status
    verdict = fixtures.ExecutionTests.verdict
    OLD, NEW, FIXED = fixtures.ExecutionTests.OLD, fixtures.ExecutionTests.NEW, fixtures.ExecutionTests.FIXED
    SECRET_ANSWER, SECRET_REPAIR = fixtures.ExecutionTests.SECRET_ANSWER, fixtures.ExecutionTests.SECRET_REPAIR

    def plan(self, **extra):
        self.write('prior.md', '# 后续主题\n\n## 实际小节\n未提供的正文秘密_913。\n')
        return kb.init(self.root, {'schemaVersion': 2, 'batches': [{'id': 'one', 'pages': ['one.md', 'two.md'],
            'readingPath': ['two.md', 'prior.md', 'one.md'], 'briefPath': '_kb-control/reader-brief.md',
            'task': 'AUTHOR_INTENT_531', 'sourcePaths': ['_kb-control/source.md'], **extra}]})

    def output(self, blocking=False):
        value = self.verdict()
        value['pages'].append(self.verdict('two.md')['pages'][0])
        value['structureReview'] = {'status': 'needs_work' if blocking else 'pass',
            'attempt': '跨章检验实际阅读顺序；只据提供全文判断，后续页只看到标题。',
            'basis': [{'path': 'prior.md', 'quote': '# 后续主题'}, {'path': 'two.md', 'quote': '收到客户消息'}],
            'gaps': [{'id': 'route-gap', 'detail': 'STRUCTURE_REPAIR_627', 'blocking': True,
                      'cause': 'structure', 'proposal': 'move'}] if blocking else []}
        return value

    def review(self, output=None):
        self.runtime.enqueue('reader', self.output() if output is None else output)
        return kb.run_batch(self.root, 'one')

    def decision(self, **extra):
        return {'status': 'accepted', 'summary': 'Read the actual route and selected texts.',
                'basis': [{'path': 'two.md', 'quote': '收到客户消息'}], 'resolutions': [], **extra}

    def test_route_and_full_text_order_are_real_and_author_material_stays_private(self):
        self.plan()
        kb.save(self.control / 'knowledge-model.json', {'units': [
            {'id': 'first', 'canonicalOwner': 'one.md', 'dependencies': ['later']},
            {'id': 'later', 'canonicalOwner': 'prior.md', 'dependencies': []}]})
        self.coverage['pages'][0]['knowledgeUnitIds'] = ['first']
        kb.save(self.control / 'content-coverage.json', self.coverage)
        result = self.review()
        self.assertEqual(result['status'], 'awaiting_editor')
        self.assertEqual(result['structureScope']['fullTextPages'], ['two.md', 'one.md'])
        self.assertEqual(result['structureScope']['outlineOnlyPages'], ['prior.md'])
        prompt = self.runtime.calls[-1]['prompt']
        self.assertLess(prompt.index('## 完整正文：two.md'), prompt.index('## 完整正文：one.md'))
        self.assertIn('# 后续主题', prompt)
        for hidden in ('未提供的正文秘密_913', 'AUTHOR_INTENT_531', 'Author source context only.', self.SECRET_ANSWER):
            self.assertNotIn(hidden, prompt)
        snapshot = kb.captured_method(self.root, self.batch(), self.batch()['attempts'][-1])
        self.assertEqual(len(snapshot['files']), 3)
        self.assertIn(snapshot['files'][-1]['content'], prompt)

    def test_page_passes_cannot_hide_unresolved_structure_or_release_dependents(self):
        self.plan()
        kb.init(self.root, {'schemaVersion': 2, 'batches': [{'id': 'later', 'pages': ['prior.md'],
            'briefPath': '_kb-control/reader-brief.md', 'task': 'Continue after the route is settled.', 'after': ['one']}]})
        self.assertEqual(self.review(self.output(True))['status'], 'awaiting_editor')
        resolution = [{'id': 'reader:route-gap', 'action': 'deferred', 'reason': 'The structure remains unresolved.'}]
        with self.assertRaisesRegex(ValueError, 'Unresolved consequential'):
            kb.decide(self.root, 'one', self.decision(resolutions=resolution))
        kb.decide(self.root, 'one', self.decision(status='needs_work', resolutions=resolution))
        with self.assertRaisesRegex(ValueError, 'dependency one'):
            kb.run_batch(self.root, 'later')
        self.assertTrue(kb.gate(self.root, ['one.md']))
        self.assertEqual(len(self.runtime.calls), 1)

    def test_missing_whole_route_work_cannot_be_replaced_by_page_passes(self):
        self.plan()
        output = self.output(); del output['structureReview']
        result = self.review(output)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('overall structureReview', result['error'])

    def test_citation_cannot_claim_to_have_read_outline_only_body(self):
        self.plan()
        output = self.output()
        output['structureReview']['basis'] = [{'path': 'prior.md', 'quote': '未提供的正文秘密_913'}]
        result = self.review(output)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('absent', result['error'])

    def test_route_material_change_invalidates_the_accepted_reading(self):
        self.plan(); self.review()
        kb.decide(self.root, 'one', self.decision())
        self.assertEqual(self.status(), 'accepted')
        self.write('prior.md', '# 后续主题\n\n正文已变。\n')
        self.assertEqual(self.status(), 'blocked')
        self.assertIn(self.root/'prior.md', kb.evidence_paths(self.root, ['one.md']))

    def test_replanning_order_preserves_history_and_cannot_drop_structure(self):
        self.plan(); self.review()
        kb.decide(self.root, 'one', self.decision())
        old = copy.deepcopy(self.batch()['attempts'])
        with self.assertRaises(ValueError):
            kb.replan(self.root, 'one', {'readingPath': []}, 'Do not bypass the declared reading.')
        kb.replan(self.root, 'one', {'readingPath': ['one.md', 'two.md', 'prior.md']}, 'Test a substantive reordered route.')
        self.assertEqual(self.batch()['attempts'], old)
        self.assertEqual(self.status(), 'blocked')
        result = self.review()
        self.assertEqual(result['structureScope']['fullTextPages'], ['one.md', 'two.md'])

    def test_rewrite_replays_preimages_and_gets_structure_feedback(self):
        self.plan(authoringMode='rewrite')
        for number in range(2):
            content = self.NEW if number == 0 else self.FIXED
            self.runtime.enqueue('writer', {'pages': [{'path': p, 'content': content} for p in ['one.md', 'two.md']]})
            self.runtime.enqueue('reader', self.output(number == 0))
            self.assertEqual(kb.run_batch(self.root, 'one')['status'], 'awaiting_editor')
            if number == 0:
                kb.decide(self.root, 'one', self.decision(status='needs_work', summary='EDITOR_MOVE_719', resolutions=[
                    {'id': 'reader:route-gap', 'action': 'deferred', 'reason': 'Change this transition.'}]))
        writer, reader = self.runtime.calls[-2:]
        for marker in ('EDITOR_MOVE_719', 'STRUCTURE_REPAIR_627'):
            self.assertIn(marker, writer['prompt']); self.assertNotIn(marker, reader['prompt'])
        self.assertEqual(kb.decide(self.root, 'one', self.decision())['status'], 'accepted')

    def test_private_duplicate_and_incomplete_routes_are_rejected(self):
        for route in [[], ['one.md'], ['one.md', 'one.md'], ['one.md', '_kb-control/source.md'], ['one.md', 'prior.md']]:
            with self.subTest(route=route), self.assertRaises(ValueError):
                self.plan(readingPath=route)
        with self.assertRaisesRegex(ValueError, 'method'):
            self.plan(methodVersion=2)

    def test_heading_outline_excludes_frontmatter_and_code_not_body(self):
        value = '---\n# private metadata\n---\n# 第一章\n\n```md\n# code title\n```\n\n第二节\n------\n正文\n\n## 真正小节\n'
        self.assertEqual(structure.headings(value), '# 第一章\n第二节\n------\n## 真正小节')


if __name__ == '__main__':
    unittest.main()
