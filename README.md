# Knowledgebase Studio

**English** | [简体中文](README.zh-CN.md)

Knowledgebase Studio helps design, produce and maintain coherent, source-grounded knowledge products for a defined reader and situation, with Markdown as the editable content base.

## Work at the requested scope

The controller chooses the current delivery endpoint before starting production:

| Request | Deliverable |
| --- | --- |
| Diagnose | Evidence-backed findings and priorities |
| Design the whole | Reader outcome, connected content map, routes and explicit decisions |
| Make a sample | Reviewed representative slice without automatic expansion |
| Build for local release | Validated content and the requested app/package |
| Update selected work | Scoped changes and current evidence, preserving global workflow truth |

Full production keeps the existing eight stages:

`intake → audit → architecture → pilot → content → app → QC → release`

The product may serve understanding, judgment, action or retrieval. Knowledge units have canonical ownership and may be reused across routes; page counts follow the reader's cognitive steps. New sources deepen or repair the product where useful rather than automatically expanding its scope.

Sources, learning choices, delivered content and evidence have distinct [authoring homes](skills/structured-knowledgebase-builder/references/workflow-protocol.md). Learning, activities and visuals are applied when the product needs them. The actual explanation, navigation, rendering and requested package are checked; changed inputs invalidate old evidence. Structural checks, editorial review and observed learning remain separate claims. Local readiness does not authorize external publication.

## Included skills

| Skill | Responsibility |
| --- | --- |
| `structured-knowledgebase-builder` | Chooses the requested endpoint and coordinates the existing skills |
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

- `先梳理整体知识地图和阅读路线，完成设计，暂不开发。`
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

## Beginner mental models

For zero-prerequisite explanations of how systems work, use the optional `novice_mental_model` profile: connect a complete everyday event before splitting concept pages. Mechanism examples use participants, actions, handoffs, outcomes and changed conditions; judgment/creation examples retain draft-and-revision teaching. Pilot receipts must locate actual explanatory text and distinguish editorial or simulated review from observed learners. See the [novice mental-model guide](skills/knowledgebase-content-builder/references/novice-mental-model.md). Structural checks cannot establish learning efficacy.

New novice pilot/content/QC approvals and scoped editorial updates require version 2 comprehension reviews: inventory each consequential promise, link it to a causal challenge, and pinpoint its basis in the current prose. Page receipts are bound to the complete page's SHA-256. Legacy receipts remain readable, with their promise coverage reported separately; rendering-only updates do not force unrelated content reviews. The [calibration examples](skills/knowledgebase-content-builder/references/explanation-regressions.md) help expose missing mechanisms without expanding every explanation. Validators check evidence integrity and declared coverage; editors must still judge whether the prose supports the result.

## Diagram design and examples

The [diagram design system](skills/knowledgebase-visual-explainer/references/diagram-design-system.md) covers type, spacing, semantic color, connectors, boundaries and narrow layouts. Open the [local pattern gallery](assets/visual-patterns/index.html) for four editable SVG patterns and deliberate counterexamples; rebuild with `python3 scripts/kb_visual_examples.py --output <directory>`. New/redesigned visuals use manifest schema 2 with real mobile/desktop figure captures, rendered type measurements, design observations and file hashes. The checker validates receipts, not aesthetics; legacy schema 1 remains compatible with an explicit warning.

### Tool-assisted reader review

Use [reader-task review](skills/knowledgebase-content-builder/references/reader-task-review.md) to distinguish understanding, performing, judging and retrieving. `kb_reader_probe.py prepare --root <target> --page <page>` creates answer-free current prose/prerequisite material, a later-section challenge and original/masked SVG pairs. New novice approvals reference these actual files in existing reviews; workflow and scoped-update checks bind their freshness. Copying a mechanism question and answer into a different check category is rejected. Preparation does not establish that a review was performed or that readers understood.

For numeric AI workload cases, optional `workedExample.workComparison` data generates one same-task manual/software/AI table with `kb_work_comparison.py <target> --page <page> --write`. Totals, incremental AI contribution and maintenance allocation are computed; checks reject drift in the published block. Teaching assumptions remain labeled, measured inputs bind to existing source measurements, and comparable business outcomes still require editorial judgment. Both tools use the Python standard library.
