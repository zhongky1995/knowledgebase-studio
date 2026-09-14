# Knowledgebase Studio

**English** | [简体中文](README.zh-CN.md)

Knowledgebase Studio is a source-grounded Codex plugin for turning raw material into a traceable, teachable, testable, and release-ready Markdown knowledge base.

它不只检查“文件有没有”，而是把资料理解、知识建模、学习设计、内容生产、应用验收和发布质检串成一条可恢复的工作流，并用语义门禁阻止“报告写完但产品没做完”。

## What it does

The plugin follows an evidence-first pipeline:

```text
intake → audit → architecture → pilot → content → app → QC → release
```

- Locks the intended product posture, audience, learning pressure, source presentation, and distribution boundary before scaling.
- Audits sources and records claims, mechanisms, boundaries, conflicts, and unknowns.
- Models traceable knowledge units and page responsibilities.
- Reviews prerequisites, examples, exercises, feedback, cognitive load, and transfer evidence for learning products.
- Builds transferable judgment through mechanisms, usable decision questions, predictive analogies, and uncertainty beside the claim. Optional quantitative contracts check context, verification, and cross-source alignment in the existing content checker.
- Connects operational steps to observable outcomes and recovery, with text-only walkthroughs supported.
- Shares optional teaching activities across learning design, content, app, and QC: evidence-based feedback, layered hints, revision, changed transfer cases, and readable fallbacks.
- Checks bounded lesson updates separately while preserving any stale full-workflow verdict; structural/browser evidence is not a claim of learning efficacy.
- Decides when a visual explanation is justified, then validates the real embedded diagram or animation, its source fidelity, alternative text, and static fallback.
- Validates the actual reader-facing corpus and app deliverable, not only narrative reports.
- Fingerprints stage artifacts so changed deliverables invalidate stale downstream evidence.
- Packages an isolated local release while keeping external publication as a separate approval.

## Included skills

| Skill | Responsibility |
| --- | --- |
| `structured-knowledgebase-builder` | Orchestrates the complete resumable workflow |
| `knowledgebase-auditor` | Inventories and evaluates the source knowledge base |
| `knowledgebase-architect` | Designs the knowledge model, information architecture, and migration |
| `knowledgebase-learning-reviewer` | Reviews the learning-product layer and transfer design |
| `knowledgebase-visual-explainer` | Builds and validates source-faithful diagrams or explanatory motion when prose is insufficient |
| `knowledgebase-content-builder` | Builds faithful reader-facing content and representative pilots |
| `knowledgebase-app-builder` | Builds or validates a local Markdown knowledge app |
| `knowledgebase-qc-release` | Runs final QC and validates an isolated release package |

The repository also includes dependency-free Python tools for deterministic auditing, content checks, visual-asset validation, semantic stage gates, release checks, and durable workflow state.

## Requirements

- A Codex build with plugin marketplace support
- Python 3.10 or newer
- Git, for installation from source

The validation scripts use only the Python standard library.

## Install from source

Clone the plugin into the plugin directory used by your personal marketplace:

```bash
git clone https://github.com/zhongky1995/knowledgebase-studio.git ~/plugins/knowledgebase-studio
```

Make sure the `plugins` array in `~/.agents/plugins/marketplace.json` contains a local entry whose path is `./plugins/knowledgebase-studio`, then install it:

```bash
codex plugin add knowledgebase-studio@personal
```

If your marketplace has another name, replace `personal` with that name. Start a new Codex task after installation so the eight skills are loaded.

## Use it

Ask Codex naturally, for example:

- `完整审计并修复这个知识库，做到本地发布可用。`
- `把这些资料做成有学习坡度、案例和练习反馈的课程型知识库。`
- `从上次断点继续知识库自动流程。`
- `只完善这两课的操作步骤和可选判断练习，验证当前改动，不重建整库。`

For a complete workflow, the controller initializes durable state under the target knowledge base:

```bash
python3 scripts/kb_workflow.py init \
  --root /path/to/knowledge-base \
  --goal "Build a release-ready learning knowledge base" \
  --mode auto \
  --app auto
```

Inspect the next stage or verify current evidence:

```bash
python3 scripts/kb_workflow.py next --root /path/to/knowledge-base
python3 scripts/kb_workflow.py check --root /path/to/knowledge-base
```

Run the standalone checks when you need a narrower diagnostic:

```bash
python3 scripts/kb_audit.py /path/to/knowledge-base --strict
python3 scripts/kb_content_check.py /path/to/knowledge-base --phase content
python3 scripts/kb_visual_check.py /path/to/knowledge-base
python3 scripts/kb_learning_check.py /path/to/knowledge-base --phase content
python3 scripts/kb_stage_check.py /path/to/knowledge-base --stage qc
python3 scripts/kb_release_check.py /path/to/release-root
```

Generated workflow evidence is stored in `<knowledge-base>/_kb-control/`. Do not hand-edit `workflow.json`; use the controller commands so revisions and invalidation remain consistent.

For bounded updates, use `scripts/kb_update.py plan` and `check`; see the [scoped-update guide](skills/structured-knowledgebase-builder/references/incremental-updates.md) for required review receipts and app/release paths. New learning templates use design schema 3 and coverage schema 2; older designs remain supported. See [activity design](skills/knowledgebase-learning-reviewer/references/learning-activity-design.md) for the shared contract and validation limits.

## Design principles

1. **Sources before pages.** Understand claims and boundaries before reorganizing content.
2. **Product posture before polish.** A beautiful implementation can still teach the wrong behavior.
3. **Pilots before scale.** Validate one representative slice before rebuilding the whole corpus.
4. **Evidence before status.** A stage passes only when current artifacts and the actual deliverable pass their gates.
5. **Explanation before decoration.** Add a diagram or animation only when it makes a real relationship or change easier to understand.
6. **Local readiness before publication.** Packaging never silently authorizes an external upload.

## Development

The [evidence-to-judgment guide](skills/knowledgebase-content-builder/references/evidence-to-judgment.md) adapts selected ideas from [huashu-report](https://github.com/alchaincyf/huashu-report): reader-purpose first, evidence before prose, explanatory depth, and mechanical rules in tooling. It does not import report-only layouts, quotas, renderer code, or claims of proven learning gains.

Run the complete test suite:

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py'
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines and [SECURITY.md](SECURITY.md) for private vulnerability reporting.

## License

Released under the [MIT License](LICENSE).
