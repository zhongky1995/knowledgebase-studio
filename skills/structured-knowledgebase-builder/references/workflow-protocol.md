# Knowledgebase Studio Workflow Protocol

## Artifact Ownership

Keep one authoring home per decision. Other artifacts describe its implementation or evidence, not another independent specification.

| Existing artifact | Owns | Consumers |
| --- | --- | --- |
| Project contract / design brief | Requested endpoint, reader outcome, product posture and boundaries | Every stage |
| Source understanding | Claims, basis, uncertainty; what new material contributes or does not warrant importing | Knowledge model and editorial review |
| Knowledge model | Unit identity, core reader change, necessary dependencies, mechanism and canonical owner | Learning design, routes and page coverage |
| Learning design | Starting state, teaching choices, route composition, examples and unit-level time estimate | Content, visuals and app |
| Content coverage | Actual page responsibility, preserved meanings and locations in delivered content | QC; a page may contain multiple units |
| Activity / visual manifests | Shared behavior or asset contract when needed | Content, app and QC refer to the same IDs |
| Navigation contract | Entrypoints, destinations and reachability | App implementation and browser checks |
| Stage/update receipts | Checks actually performed against particular inputs | Completion claims |

In learning design, omitted `learningResult` inherits the unit's `readerChange`; omitted `prerequisiteUnitIds` inherits its `dependencies`. Explicit values remain supported for an actual teaching distinction. Do not restate either merely to satisfy a template. Page-level outcomes and total reading time can differ from unit-level ones; they are not aliases. Existing contracts remain readable without migration. Plain-language reports interpret the records and explain decisions instead of transcribing every field.

## Control Model

This protocol governs full production only. Diagnosis/design finish at their requested endpoint without starting this state machine; samples/updates use the scoped protocol. Use `_kb-control/workflow.json` as the durable workflow checkpoint. The controller script owns state transitions; do not hand-edit the JSON.

Stages move through:

`pending → in_progress → pass`

Exceptional states are `needs_work`, `stale`, `blocked`, and `skipped`. Only the optional app stage may be skipped by default. `stale` means a stage once passed but its contract, dependency artifacts, or validated deliverable changed afterward.

## Automatic Loop

1. Reconcile fingerprints and freshness; invalidate from the earliest stale stage.
2. Claim the next action.
3. Read the stage contract and relevant evidence.
4. Perform the work.
5. Run the stage-specific checks.
6. Write the required control artifacts.
7. Complete the stage with `pass` or `needs-work`. Completion generates `_kb-control/stage-check-<stage>.json`; a report-only stage cannot pass.
8. Continue with the automatically claimed next stage.

Do not turn a stage checkpoint into a user approval gate unless the project contract explicitly requires one.

An unresolved product posture is not a normal checkpoint. Before scaling, require explicit intent confirmation when a choice changes the default action, exercise pressure, progress truth, catalog exposure, or learner-facing evidence presentation.

An unresolved distribution boundary is also not a normal implementation detail. Lock the share form, audience scope, release root, external-publication authorization, and license policy before building a package. “Generate a webpage” authorizes a local static deliverable; it does not authorize creating a repository, uploading, hosting, changing visibility, or sending the result.

## Blocker Policy

Allowed blocker kinds:

- `missing-source`
- `scope-conflict`
- `destructive-approval`
- `external-auth`
- `external-publish`
- `repeated-failure`

For a blocker, record what was attempted, why assumptions are unsafe, the smallest user decision or permission needed, and the exact stage that will resume.

## Retry Policy

A failed validation returns the stage to `needs_work`. Repair the stage using the error evidence. After the configured maximum attempts, record a `repeated-failure` blocker instead of looping indefinitely.

## Runtime Integration

Prefer these persistence layers in descending order when available and authorized:

1. a runtime goal or task controller that automatically continues the objective;
2. a recurring task wakeup or monitor that reopens the same task;
3. the current Codex task continuing stage by stage;
4. manual invocation of “继续知识库自动流程”, which resumes from local state.

The plugin must remain correct under the fourth option; higher layers improve liveness, not correctness.

## Revision Integrity

- Every passed stage records the project-contract digest and its artifact digests.
- A changed contract invalidates intake and all downstream stages unless the change is control-only metadata.
- A changed stage artifact invalidates that stage and every dependent stage.
- QC and release cannot remain passed when content, app validation, architecture, or the contract is newer than their evidence.
- Pilot, content, app, QC, and release record fingerprints for their actual learner-facing pages, app paths, and release root. Editing only the deliverable, without editing a report, still makes the relevant stage stale.
- New novice editorial approvals also reference tool-prepared reader material inside the existing comprehension review. Pilot/content/QC and scoped-update fingerprints include those packets and actual material files. This derivative material is not another verdict or source of content truth; use the content builder's `reader-task-review.md` for preparation, review and limits.
- New novice pilot/content/QC/release transitions and semantic updates also consume real author/reader/counter-reader execution via `independent-execution.md`. Per-batch evidence binds actual worker requests, identities, results and dependencies. An accepted prior batch does not authorize continuation after its input changes; missing or failed reader tasks stop the gate. These jobs live inside the existing stages and do not create a parallel release state machine.
- `check` reports stale evidence; `reconcile --apply` records the invalidation and resumes from the earliest affected stage.
- External task controllers may reference Knowledgebase Studio state but may not replace its contract, revision, or QC truth.

## Non-Goals

- Do not claim that a Skill or plugin manifest can create an infinite autonomous loop by itself.
- Do not bypass user permissions, sandbox rules, credential gates, or destructive-action safeguards.
- Do not use repeated commentary or empty checkpoints as evidence of progress.
- Do not mark release complete merely because the content files exist.
- Do not call corpus integrity, links, builds, or browser rendering an overall product pass. Learning transfer and content quality are separate QC dimensions.
- Do not choose a content or code license by analogy with another project.
- Do not let an external host become the first place where links, images, search, or responsive layout are tested.
