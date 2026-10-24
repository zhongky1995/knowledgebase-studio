# Knowledgebase Studio

**English** | [简体中文](README.zh-CN.md)

Design, write and maintain useful, source-grounded knowledge products, with a responsible author/editor owning the connected reading experience.

## Work at the requested scope

Diagnose, design, make a sample, write the requested product or update selected work. Reuse confirmed direction and authorization. Architecture, teaching, prose, diagrams and interface can inform each other while making the product. A sample resolves an actual uncertainty; it is not a universal gate or a new approval requirement.

Ordinary production uses the existing scoped planner/checker, not a mandatory eight-stage sequence. It works from actual manuscript, existing intent/sources and one current editorial decision. Separate model, learning, coverage, migration and per-page self-review records are not required for an ordinary manuscript. Complex products can retain structured records where they help.

Independent reading is selected for a current doubt, impact or explicit requirement. New batch specifications use one reader by default, optional further review and an accountable editor decision. The editor can question or decline suggestions without rewriting until two models agree. Findings can lead to deletion, merging, moving or replacement as well as additions. Actual runtime evidence and unresolved consequential findings remain visible.

## Included capabilities

Eight skills cover coordination, source/corpus audit, content architecture, writing, learning review, explanatory visuals, local apps and delivery. Use the capability needed for the current question; loading a skill does not require the whole production sequence.

The Python tools retain source/measurement alignment, arithmetic, local links, declared assets, actual runtime records, current-version evidence and release hygiene. These checks do not certify useful prose or observed learner outcomes. Local readiness never authorizes external publication.

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

Ask naturally, for example:

- `先判断这几章为什么读不下去，暂不改稿。`
- `按已经确定的方向继续写，发现结构问题就结合正文调整。`
- `只检查这两章的例子是否支撑观点，必要时独立审读。`

For ordinary work, after candidate files exist:

```bash
python3 scripts/kb_update.py plan --root /path/to/knowledge-base \
  --path manuscript/chapter.md --page manuscript/chapter.md \
  --context _kb-control/reader-brief.md --context sources/relevant.md \
  --output _kb-control/updates/current/plan.json
python3 scripts/kb_update.py record --root /path/to/knowledge-base \
  --plan _kb-control/updates/current/plan.json --kind editor-review \
  --summary "Actual editorial reading judgment" \
  --output _kb-control/updates/current/plan.json
python3 scripts/kb_update.py check --root /path/to/knowledge-base \
  --plan _kb-control/updates/current/plan.json
```

The planner creates schema 3. Perform its actual checks before recording the current editorial summary/evidence. The [scoped guide](skills/structured-knowledgebase-builder/references/incremental-updates.md) explains input binding, shared assets and local delivery. Current independent execution supplies its own editor decision without another report.

Use [independent execution](skills/structured-knowledgebase-builder/references/independent-execution.md) when warranted. `kb_execution.py init/run/decide/check` uses the authenticated modern Codex CLI, captures real sessions and binds the editor decision to current material. An unrelated queue, novice tag or resolved historical feedback does not require a new reader. Explicit pending review and true failed dependencies still block completion.

## Existing projects

Existing eight-stage state, schema 1/2 scoped plans and old execution batches retain their original contracts. The [legacy protocol](skills/structured-knowledgebase-builder/references/workflow-protocol.md) explains continuing them. A new scoped check does not reset or promote a historical whole-product verdict. `kb_execution.py migrate` explicitly changes an old review batch to editorial decisions, preserves attempts and requires fresh evidence; it does not grant a pass.

## Specialized tools

- [Explanation diagnosis](skills/knowledgebase-content-builder/references/novice-mental-model.md) and [calibration examples](skills/knowledgebase-content-builder/references/explanation-regressions.md) help inspect causal continuity without turning every page into a tutorial.
- [Reader-task review](skills/knowledgebase-content-builder/references/reader-task-review.md) prepares current prose and available figures; preparation itself does not prove reading.
- `kb_work_comparison.py` computes declared same-task workload comparisons, retaining teaching/measurement provenance and limits.
- [Visual design](skills/knowledgebase-visual-explainer/references/diagram-design-system.md) and the [pattern gallery](assets/visual-patterns/index.html) support actual explanatory assets; declared visual and interaction checks remain current and scoped.
- `kb_release_check.py` checks requested local packages, including private-file exclusions and local references. Browser checks inspect actual apps, not every plain manuscript.

## Development

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py'
```

Tests exercise integrity and orchestration, not reader value. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). The [evidence-to-judgment guide](skills/knowledgebase-content-builder/references/evidence-to-judgment.md) adapts selected ideas from [huashu-report](https://github.com/alchaincyf/huashu-report), without importing its layouts, quotas or renderer.

## License

[MIT License](LICENSE).
