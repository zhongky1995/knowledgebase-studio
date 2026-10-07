---
name: structured-knowledgebase-builder
description: Orchestrate full or scoped knowledge-base work across source understanding, learning design, content, app, QC, and release. Use to build, overhaul, resume, package, update a few lessons, revise operational teaching or heuristic interactions, or jointly change content and navigation/app behavior. Supports bounded update checks without falsely renewing an old full-workflow pass.
---

# Structured Knowledgebase Builder

Run Knowledgebase Studio as a state-driven controller. Lock the intended knowledge-product experience and distribution boundary before optimizing it, then keep moving until a local release-ready deliverable passes or a defined blocker makes further safe progress impossible.

## Start Or Resume

Locate the plugin root from this `SKILL.md`. Use `../../scripts/kb_workflow.py` relative to this skill directory.

First choose scope. For a bounded update to existing lessons, examples, or learning interactions, or an explicitly requested standalone lesson sample, read `references/incremental-updates.md` and use its scoped plan/check route. Do not automatically reconcile with `--apply`, restart all stages, or initialize a new full workflow for that route. A course-wide restructure, changed audience/product posture, or requested full release still uses the full workflow below.

1. If `<target>/_kb-control/workflow.json` does not exist, initialize it:

   `python3 <plugin-root>/scripts/kb_workflow.py init --root <target> --goal <goal> --mode auto --app auto`

2. Reconcile passed stages against current contracts and artifacts before resuming:

   `python3 <plugin-root>/scripts/kb_workflow.py reconcile --root <target> --apply`

3. Read the next action and claim it:

   `python3 <plugin-root>/scripts/kb_workflow.py next --root <target> --claim`

4. Apply the stage skill named in the returned JSON.
5. Produce every required stage artifact inside `_kb-control/`.
6. Mark the stage passed:

   `python3 <plugin-root>/scripts/kb_workflow.py complete --root <target> --stage <stage> --artifact <path> ...`

7. The completion command automatically claims the next eligible stage. Continue immediately.

For full cross-stage requests, run `check` before reporting completion even when the task did not begin through this controller. A raw `workflow.json` status is not a current verdict; `check` and the semantic gate artifacts are authoritative. Scoped updates instead run `kb_update.py check` and report both the limited result and the unchanged full-workflow state.

Read `references/workflow-protocol.md` before the first automated run.

## Autonomy Contract

Treat “全自动”“直接做完”“不要停”“从头做到发布” and equivalent wording as approval to continue through all safe in-scope stages. Do not request confirmation at normal stage boundaries.

Continue through ordinary uncertainty by inspecting the repository, choosing a reversible default, and recording the assumption in the stage artifact. Do not stop for:

- naming, formatting, page length, and other choices that do not change the product posture;
- completion of an intermediate stage;
- a non-blocking warning or optional enrichment source;
- a choice that can be changed locally without invalidating the project contract;
- lack of a local app when the app stage can be skipped.

Stop only for:

- a required truth source that cannot be found or safely inferred;
- contradictory scope, audience, or source-of-truth requirements;
- destructive deletion or overwrite outside the approved reversible migration;
- required external authentication, credential, or permission;
- irreversible external publication or sending;
- the same stage failing its gate after the configured retry limit.

Product posture is not ordinary uncertainty. If the default user action, pressure level, exercise requirement, progress semantics, catalog visibility, or source presentation is unclear, write an intent mirror that states the practical consequence and obtain explicit confirmation before scaling. A reversible implementation is still a costly wrong direction when it changes what the product feels like.

## Intake Contract

Resolve every product-experience field in `project-contract.yaml` before passing intake:

- `product_posture`: `reading_manual`, `guided_learning`, `practice_workbench`, `operations_manual`, `reference_library`, or `hybrid`;
- `reader_moment` and `default_user_action`;
- `first_success`: first understanding, first retrieval, first decision, or first deliverable;
- `catalog_visibility`: progressive disclosure or direct catalog;
- `exercise_policy`, `progress_semantics`, and `pressure_policy`;
- `source_presentation`: learner-visible, contextual, or internal-only;
- `distribution_mode`: `local_entrypoint`, `single_file`, `static_site`, or `archive`;
- `audience_scope`: `internal` or `public`, plus the isolated `release_root` when packaging is requested;
- `external_publish_authorized`: default `false`; local release readiness and external publication are separate approvals;
- `license_policy`: `internal_only`, `all_rights_reserved`, or `explicit_files`; never select an open-source license on the user's behalf;
- `intent_mirror`: one plain-language sentence describing what approval makes the reader do or see;
- `anti_goals`: outcomes that would make a polished implementation wrong.

For high-impact posture choices, add a plain-language intent mirror such as: “Approving this means a new reader must complete a task before reading.” Approval must cover the consequence, not merely a screenshot.

Record a stop with `kb_workflow.py block`; never simulate progress past a blocker.

For requests to understand how a system works from zero, route architecture, pilot and content through `../knowledgebase-content-builder/references/novice-mental-model.md`. Reuse explicit audience/posture decisions from the current conversation or authorized prior context; only clarify unresolved consequential choices. “No technical vocabulary” does not mean a collection of disconnected short definitions.

## Stage Map

| Stage | Apply skill | Required output |
| --- | --- | --- |
| intake | this controller | project contract |
| audit | `knowledgebase-auditor` | inventory, source-understanding ledger, and audit report |
| architecture | `knowledgebase-architect` | knowledge model, architecture decision, and migration map |
| pilot | `knowledgebase-content-builder` | representative rewritten slice and pilot review |
| content | `knowledgebase-content-builder` | content coverage/integrity and full content build report |
| app | `knowledgebase-app-builder` | app validation, or an explicit skip |
| qc | `knowledgebase-qc-release` | QC report |
| release | `knowledgebase-qc-release` | local release-ready report and isolated package/entrypoint when requested |

For `reading_manual`, `guided_learning`, `practice_workbench`, or learning-oriented `hybrid`, apply `knowledgebase-learning-reviewer` inside architecture and pilot. Architecture cannot pass without `_kb-control/learning-design.json`; pilot cannot pass without `_kb-control/pilot-verdict.json` and its counter-review.

When `learning-design.json` marks a visual explanation as required, apply `knowledgebase-visual-explainer` inside pilot and content. The visual remains part of those stage deliverables rather than becoming a separate workflow stage. Content cannot pass until `_kb-control/visual-explanations.json` and the real embedded assets pass `kb_visual_check.py`.

## Gate And Correction Rules

For evidence-heavy learning, comparisons, or knowledge pages that must build judgment, route to `../knowledgebase-content-builder/references/evidence-to-judgment.md`. Reuse the existing source ledger and knowledge model. Keep research, editorial, presentation, and review responsibilities distinct without adding stages or requiring separate agents. This route does not turn an ordinary lesson into a research report.

- Do not mark a stage passed unless its required artifacts exist.
- Do not mark a stage passed from report existence alone. `kb_workflow.py complete` must generate and pass the corresponding `_kb-control/stage-check-<stage>.json`.
- Content, app, QC, and release passes must fingerprint the actual learner-facing corpus, app deliverable, and release root. A changed deliverable makes downstream evidence stale even when narrative reports were not edited.
- Required visual assets and their manifest are learner-facing deliverables. Editing an SVG, PNG, GIF, video, fallback, or declaration invalidates the affected content, app, and QC evidence.
- Shared learning-activity declarations, real interaction assets, and their review evidence are also fingerprinted. Required verdict dimensions must pass; `not_applicable` is allowed only for explicitly irrelevant dimensions.
- Do not scale content before the pilot gate passes.
- When the user changes scope or rejects the sample, invalidate from the earliest affected stage:

  `python3 <plugin-root>/scripts/kb_workflow.py invalidate --root <target> --from-stage <stage> --reason <reason>`

- For feedback after a pilot or release, classify it and invalidate deterministically:

  `python3 <plugin-root>/scripts/kb_workflow.py feedback --root <target> --kind <kind> --reason <reason>`

  Product posture, audience, and source-presentation feedback returns to intake; missing system relationships, navigation pressure and learning progression return to architecture; content depth, example depth, or learning-transfer rejection returns to pilot; tone-only feedback returns to content; rendering, interaction, or responsive defects return to app; validation defects return to QC.

- Keep public content separate from `_kb-control/`, archives, build caches, and release reports.
- Build public-ready material in an isolated release root. Never treat the full working repository as the share package.
- Stop at a validated local package or entrypoint unless the user separately authorizes a named external destination. Repository creation, upload, hosting, sending, and permission changes are not implied by `package_required`.
- Keep implementation and final QC logically separate even when one agent performs both sequentially.
- When another task controller is used, it may schedule work but must not create a second domain truth. `_kb-control/workflow.json` owns Knowledgebase Studio revisions; external task state must reference that revision and contract digest.

## Persistence Boundary

The local state machine prevents context loss and supports deterministic resume; it does not self-wake Codex after the host ends a task. When the runtime exposes a goal, task-controller, recurring automation, or task wakeup mechanism and the user explicitly requested persistent automation, use it to resume the same objective. Keep `_kb-control/workflow.json` as the project source of truth.

Before any turn or runtime boundary, save the current checkpoint. On the next invocation, reconcile first, then resume the recorded `in_progress`, `needs_work`, `stale`, or `blocked` stage instead of trusting an old pass.

## Communication Budget

Send progress updates only at stage start, material discovery, blocker/failure, repair decision, and stage completion. Do not narrate routine polling, repeated waiting, unchanged checks, or every controller command.

## Completion

For full-workflow work, finish only when `kb_workflow.py check` reports `status: ok`, the workflow reports complete, QC and release both passed, every required verdict dimension has current evidence, and all requested local routes/builds/packages are validated. For scoped work, finish with a passed current update check and identify exactly which pages/deliverables it covers; keep any old full-workflow staleness explicit. External upload is a separate action and may remain intentionally undone. Never turn a corpus/link/build-only or scoped pass into an “overall pass.” Report substantive outcomes, not every controller command.
