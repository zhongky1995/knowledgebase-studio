---
name: structured-knowledgebase-builder
description: Design, build, diagnose, or update a coherent knowledge product from sources. Choose the requested endpoint—diagnosis, overall design, sample, local release, or scoped update—and coordinate the existing domain skills without expanding that scope.
---

# Structured Knowledgebase Builder

Build a coherent, source-grounded knowledge product for a defined reader and situation. Success is the promised understanding, judgment, action or retrieval supported by a usable deliverable. File counts, polished pages and passed structural checks are supporting evidence, not that outcome.

## Choose The Delivery Endpoint First

Reuse the user's confirmed decisions and inspect existing project artifacts before asking questions. Record `delivery_target` in the existing project contract or design brief; do not create a second control system. This is the endpoint of the current assignment, not the product posture.

| Endpoint | Work and completion boundary |
| --- | --- |
| `diagnosis` | Inspect the relevant sources and deliver prioritized findings with evidence, uncertainty and recommended scope. Do not modify the knowledge product or initialize its workflow. |
| `design` | Use audit, architect and relevant learning review guidance. Deliver reader goals, boundaries, connected content map, routes, presentation responsibilities, source allocation and unresolved decisions sufficient for the next step. Proposed paths and untested ideas stay labeled. Do not require finished lessons, app/browser evidence, packaging decisions or a release pass. |
| `sample` | Make the explicitly requested representative slice and review its real content and presentation using the scoped route below. Do not silently scale it to a full corpus. |
| `release` | Run the full production workflow below to a validated local entrypoint/package. |
| `update` | Change and verify the selected content/app/package through the scoped route below; retain the truth of older whole-product evidence. |

A design assignment may finish with open implementation choices; that is not a blocked release. Save its decisions and next step in the existing architecture/design document. Do not initialize, advance or reset `workflow.json` for diagnosis/design, including when it already exists. When production is requested later, reuse the design and validate it through the normal stages. An absent `delivery_target` in an older contract keeps existing full-workflow behavior; current user scope always wins.

Overall design precedes a pilot in a new or restructured product. A sample tests the hardest assumptions of that design; it cannot substitute for deciding the whole. Routine updates preserve the approved whole rather than reopening it.

## Route Only The Needed Guidance

Use the stage skills below for their responsibilities. The shared artifact ownership map is in `references/workflow-protocol.md`; keep decisions at their owning location and reference them elsewhere.

For `sample` or `update`, read `references/incremental-updates.md`. Use `kb_update.py plan/check`, not a new full workflow or automatic `reconcile --apply`. Inspect the affected reader path and new-source allocation before editing. A changed audience or product posture requires design reconsideration, not a silently broadened incremental pass.

For unfamiliar-system explanations, read `../knowledgebase-content-builder/references/novice-mental-model.md` in architecture and pilot. For explanation depth and source synthesis, the content builder owns the shared editorial guidance. Learning review sets learning intent, visual explanation makes required assets, app builds the experience, and QC challenges the delivered result. Do not add a second model, extra stage or universal lesson template for a project-specific technique.

When the confirmed audience wants a zero-prerequisite system explanation, activate `explanationProfile: novice_mental_model` in a new design and carry its review into content/QC. Reuse the same reference for “话说一半” or incomplete-scene feedback during updates. Older designs may lack the profile even when their prose says “零基础”: inspect the audience and actual passages before choosing the review, and record page comprehension evidence for the selected explanation rewrite. Do not silently label legacy coverage as reviewed or force a whole-design migration for a rendering-only repair.

## Full Production Workflow

Locate the plugin root via `../../` from this skill directory. Read `references/workflow-protocol.md` before the first full run.

1. If `_kb-control/workflow.json` is absent, run `python3 <plugin-root>/scripts/kb_workflow.py init --root <target> --goal <goal> --mode auto --app auto`.
2. Reconcile existing evidence with `kb_workflow.py reconcile --root <target> --apply`, then `next --root <target> --claim`.
3. Apply the returned stage skill, produce its required artifacts, and run `complete --root <target> --stage <stage> --artifact <path> ...` only after the work is actually reviewed.
4. Continue with the automatically claimed stage. Run `check --root <target>` before reporting full completion.

| Stage | Skill | Main responsibility |
| --- | --- | --- |
| intake | this controller | Reader/product/distribution contract |
| audit | `knowledgebase-auditor` | Source understanding and current-product baseline |
| architecture | `knowledgebase-architect` | Knowledge ownership, content relationships, routes and migration |
| pilot | `knowledgebase-content-builder` | Representative slice and counter-review before scaling |
| content | `knowledgebase-content-builder` | Complete, traceable reader-facing content |
| app | `knowledgebase-app-builder` | Actual navigation/rendering/interaction, or an explicit skip |
| qc | `knowledgebase-qc-release` | Current semantic and functional evidence |
| release | `knowledgebase-qc-release` | Clean, validated local package or entrypoint |

Learning-oriented postures use `knowledgebase-learning-reviewer` in architecture and pilot. Required visuals use `knowledgebase-visual-explainer` inside pilot/content. Neither adds a stage. An optional technique does not become compulsory merely because a template contains an example of it.

## Lock Consequential Choices, Reuse Existing Authorization

For production, resolve the product-experience and distribution fields of `assets/control-templates/project-contract.yaml`: audience and reader moment, default action and first success, posture, catalog visibility, exercise/pressure/progress policies, source presentation, anti-goals, distribution and license. Explain consequential unresolved choices in plain language before scaling. Approval must cover what the reader will do or see, not just a screenshot. Do not request the same decision again when the user has already made it.

Continue ordinary reversible decisions within the requested endpoint. “Do it all” authorizes the safe in-scope stages, not a new product direction or external destination. Stop only for an indispensable missing source, contradictory scope, destructive work outside authorization, required authentication/permission, or repeated gate failure after the retry limit. Use `kb_workflow.py block` for a full-workflow blocker; diagnosis/design record the missing decision in their own deliverable.

## Evidence And Correction

Full-workflow transitions are controlled by `kb_workflow.py`, including stage checks and deliverable fingerprints. Never hand-edit workflow state or renew evidence by copying digests into old reports. Use `invalidate` from the earliest affected stage, or `feedback --kind <kind> --reason <reason>` for changed intent or rejected output. Missing system relationships return to architecture, failed explanation to pilot/content, rendering defects to app. See the protocol for state and retry semantics.

Distinguish deterministic integrity, editorial/simulated judgment, real browser checks and observed learner evidence. A source, screenshot or report must support the actual claim; none alone proves comprehension. QC remains logically separate from production even when performed sequentially by one agent.

For new novice approvals or recurring task/value/diagram failures, use the content builder's `references/reader-task-review.md`: prepare current answer-free material with `kb_reader_probe.py`, actually attempt the task, and then record the existing review. Numeric AI workload examples can use `kb_work_comparison.py` to generate and verify their same-task comparison. These tools feed existing pilot/content/QC/update gates; they do not create another workflow or replace editorial judgment.

Keep internal controls and archives out of the reader product. Package into an isolated release root when requested. A local release pass does not authorize repository creation, upload, hosting, sending or visibility changes; reuse any explicit destination authorization already given. Do not choose a license on the user's behalf.

## Completion And Continuity

Report the requested endpoint and what was actually established. Diagnosis/design finish against their scoped deliverables; samples/updates require a current scoped check and retain global status separately; a full release requires `check` status `ok`, completed workflow, current QC/release evidence and validated deliverables. Never describe a bounded or structural pass as overall quality or learning efficacy.

Save evidence and the next action before a context boundary. Resume full production by reconciling its checkpoint; resume scoped work from its saved plan and current inputs. Runtime goals or wakeups may continue an explicitly requested persistent task; the plugin state alone cannot self-wake. An external controller references this domain state, never duplicates it.
