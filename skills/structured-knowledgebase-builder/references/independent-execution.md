# Independent reading and accountable editorial decisions

Arrange a review for a current doubt, significant consequence or explicit request. A novice label, previous complaint or unrelated queue is not itself a review requirement. The main editor owns the content and final disposition; a reviewer can challenge the question and chapter value as well as missing steps.

## Current batch specification (schema 2)

Reuse the existing reader brief and select a connected reading scope. The brief contains the reader's actual starting knowledge and intended use, not expected answers, a suspected-defect list or a pass request. `readerTasks` can identify concrete requests with exact supporting `sourceQuote` text from that brief; omission uses the brief itself. Source selection and full-product completeness remain editorial responsibilities.

Start from `assets/control-templates/execution-batches.json`. Existing prose is reviewed in place by default (`authoringMode: review_existing`). Use `rewrite` only when intentionally delegating a bounded writing task; the coordinator preserves preimages and checks concurrent edits before applying its exact output. The main author retains continuity and personally inspects the result.

Schema 2 defaults to one independent reader and no implicit serial dependencies. Declare `after` only for real prerequisites. `counterReview: true` requests another perspective when the question warrants it; it does not demand consensus. Inputs are bounded without truncation. No per-page self-review or coverage contract is needed for a manuscript-only review; existing jobs/prerequisites are reused when present.

```sh
python3 <plugin-root>/scripts/kb_execution.py init --root <target> --spec <batch-spec.json>
python3 <plugin-root>/scripts/kb_execution.py run --root <target> --batch <id>
```

The runner uses the authenticated modern local Codex CLI in fresh tool-free sessions. It preserves actual requests, response schemas, identities, events and results. A runtime error, missing evidence or stale material cannot be hand-filled into success. No new sidebar chat, API key setup, model pin or task-controller plugin is needed. This is bounded process execution, not a hostile-process filesystem security boundary.

## Read and decide

A completed schema 2 review returns `awaiting_editor` (exit 1 until accepted), even when the reader says pass. Read the current manuscript and actual findings. Decide what the text needs, rather than adding every suggested paragraph. Do not rerun just to change a reader's label.

Record the editor decision with `kb_execution.py decide --root <target> --batch <id> --spec <decision.json>`. It lives in the existing execution record; the input JSON can be temporary. It contains:

- `status`: `accepted` or `needs_work`;
- `summary`: the responsible editor's actual reading/use judgment;
- `basis`: current `{path, quote}` evidence for that judgment;
- `resolutions`: each finding once, with `id`, `action` (`addressed`, `declined`, `deferred`) and `reason`. IDs are `reader:<gap-id>` or `auditor:<gap-id>`; a missing reader task is `<role>:task:<task-id>`. A consequential finding that is addressed/declined also needs current `basis`. An unresolved consequential finding cannot be accepted.

This binds a decision to the actual attempt and manuscript. It cannot prove that a human read the text or that an editor's reasoning is good. Original model judgments remain unchanged even when the editor disagrees. If the editor finds a substantive gap, repair the owning content by addition, deletion, restructuring or replacement as appropriate. Changed relevant content makes the old review stale; review the changed scope again when it is still required. An unresolved explicit requirement cannot be quietly removed.

The updater consumes accepted current editorial execution directly; do not copy it into `comprehensionReview`, a second editor report and a stage narrative. Keep conclusions at the inspected scope.

## Failure, changes and dependencies

A required batch must finish and receive an editor decision before its scope or true dependents can complete. Unrelated branches can continue. The latest attempt governs; a later failure never falls back to an old pass. Relevant page, figure, source, task, prerequisite or reader-intent changes invalidate acceptance. Control-only bookkeeping and unrelated work do not.

Attempts are bounded. Exhaustion stops dispatch. `replan --spec <changed-fields.json> --reason <reason>` requires a substantive task/source/brief/request change and retains prior attempts; increasing the budget alone is rejected. Replanning is not an automatic retry loop or a way to override user intent. Escalate or narrow a still-unresolved question rather than seeking indefinite model agreement.

## Compatibility

Unversioned/schema 1 batch specifications and existing batches retain their legacy writer/reader/counter-reader consensus semantics. The runner does not silently reinterpret their receipts. To change an existing batch to editorial decisions:

```sh
python3 <plugin-root>/scripts/kb_execution.py migrate --root <target> --batch <id> --reason "Explain why this current scope needs editorial disposition"
```

Migration preserves old attempts, scope, authoring mode and dependencies, creates a new revision and requires a fresh review followed by an editor decision. It grants no pass, including when the old batch failed. Old whole-workflow claims remain separate. `status` and `check` expose current acceptance; model review is editorial evidence, not observed learner effectiveness.
