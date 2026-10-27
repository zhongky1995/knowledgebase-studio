# Independent reading and accountable editorial decisions

Arrange a review for a current doubt, significant consequence or explicit request. A novice label, previous complaint or unrelated queue is not itself a review requirement. The main editor owns the content and final disposition; a reviewer can challenge the question and chapter value as well as missing steps.

## Current batch specification (schema 2)

Reuse the existing reader brief and select the complete prose unit needed for the current question, following the argument across necessary adjacent chapters. The brief contains actual starting knowledge and intended use, not expected answers, a suspected-defect list or a pass request. Use `readerTasks` for concrete explanatory, comparative or operational work, with exact supporting `sourceQuote` text from the brief. Ordinary batches retain the brief fallback; new batches with `intentSources` require explicit tasks so the fallback cannot silently replace the work. The program does not judge whether a task is intellectually useful or the chosen scope is sufficient.

For delegated writing, put the current claim, chapter responsibility, accepted choices and unresolved editorial questions in the writer `task` or an existing design file selected through `sourcePaths`. These authoring choices stay private to the writer. When developing or substantially revising the content core, also carry the user's relevant original questions and thoughts through `intentSources` below, so both writer and reader can distinguish them from the editor's interpretation. A design merely read by the coordinator is not automatically present in a worker's context. Keep the brief focused on the actual reader need; changing it also requires updating requests grounded in it. Old source quotes cannot silently stand for new intent.

Start from `assets/control-templates/execution-batches.json`. Existing prose is reviewed in place by default (`authoringMode: review_existing`). Use `rewrite` only when intentionally delegating a bounded writing task; the coordinator preserves preimages and checks concurrent edits before applying its exact output. The main author retains continuity and personally inspects the result.

Schema 2 defaults to one independent reader and no implicit serial dependencies. Declare `after` only for real prerequisites. `counterReview: true` requests another perspective when the question warrants it; it does not demand consensus. Inputs are bounded without truncation. No per-page self-review or coverage contract is needed for a manuscript-only review; existing jobs/prerequisites are reused when present.

```sh
python3 <plugin-root>/scripts/kb_execution.py init --root <target> --spec <batch-spec.json>
python3 <plugin-root>/scripts/kb_execution.py run --root <target> --batch <id>
```

The runner uses the authenticated modern local Codex CLI in fresh tool-free sessions. It preserves actual requests, response schemas, identities, events and results. A runtime error, missing evidence or stale material cannot be hand-filled into success. No new sidebar chat, API key setup, model pin or task-controller plugin is needed. This is bounded process execution, not a hostile-process filesystem security boundary.

## Keep the original question available

When developing a core argument or examining whether a rewrite still answers the user's problem, select relevant original excerpts from existing input records in the same schema 2 batch:

```json
{
  "intentSources": [{"path": "sources/original-question.md", "quote": "The exact original question or thought being developed."}],
  "readerTasks": [{
    "id": "explain-change",
    "request": "Using the selected complete explanation, compare how the two arrangements could change the outcome, and what happens when a relevant condition changes. Distinguish text, inference and extra assumptions.",
    "sourceQuote": "The exact reader need from the existing brief that makes this comparison relevant."
  }]
}
```

Use one contiguous excerpt per source file, containing the relevant qualifications and context. Do not label an author-written summary as the user's original words. Selected excerpts go to both writer and reader; the rest of the source file, author rationale and repair history do not. The input is a question or proposition to examine, not a proved fact, mandatory conclusion or expected answer. A sound article may qualify or reject it while still addressing the problem. Ordinary reference edits need no separate original-intent review.

The existing reader run adds `intentReview`: what the manuscript actually answers, how its reasoning and allocation of attention respond to that original problem within the assigned scope, and any consequential mismatch. Its `basis` must quote both a supplied original excerpt and selected manuscript text. Those original inputs cannot stand in for missing published evidence in page reviews or reader-task answers. Its findings use the existing editor decision and failure handling, without another reviewer or approval stage.

The program checks exact excerpts, binds source files and selected scope to the attempt, and preserves them in evidence. A substantive `replan` can revise the selection but cannot silently drop it with an empty list. It cannot authenticate a local file as user-authored or establish that the editor selected the complete problem; inspect provenance and selection in the current task. Claims of fidelity apply only to the selected excerpts and supplied prose.

## An actual structure question

For whole-product arrangement or a cross-chapter progression question, add `readingPath` to the existing schema 2 batch using method 3. It is the actual ordered list of reader-facing Markdown paths, not filesystem alphabetical order or the author's rationale. `pages` selects the full texts needed to test the question and must be within that route. For example:

```json
{
  "id": "opening",
  "pages": ["start.md", "opportunity.md", "mechanism.md"],
  "readingPath": ["start.md", "opportunity.md", "mechanism.md", "application.md", "reference.md"],
  "briefPath": "_kb-control/reader-brief.md",
  "task": "Read the opening and its transition in this learning route.",
  "authoringMode": "review_existing"
}
```

The runner supplies real headings in that order plus the selected full texts, and snapshots the architect's `structure-method.md` along with the shared editorial method. Full texts follow the route order; legacy prerequisite declarations do not silently inject later answers into this reading. Author rationale remains writer-only. The reader returns `structureReview` with its actual reading, evidence and findings in addition to page verdicts. Missing overall work cannot be replaced by page passes; its findings use the same unique IDs and editor dispositions. Quote checks permit the full texts actually supplied and only the displayed headings from other route pages. Results name `structureScope`, including which pages were outline-only, rather than implying a full-book read.

The route order and relevant contents are bound to the execution; changes require a current review. A substantive `replan` may change the order but cannot turn a declared structure review off by supplying an empty route. In `rewrite` mode, the writer receives the same actual route and the main editor's current choices, and may write only the assigned pages. Reorganizing other chapters is an explicit editorial task, not an automatic side effect. The declared route is selected by the editor; the runner cannot prove it matches an external site's navigation or that the selected full texts are sufficient. Inspect both in the current task.

Use this when structure is actually in question. A normal page revision needs no route or separate structure result. For a design-only assignment without prose, evaluate the proposed design as a design and state the uncertainty; do not manufacture manuscript files or claim its teaching sequence has been validated.

## Inspect reasoning and actual work

New schema 2 batches use method 3. The runner reads and sends the content builder's shared `editorial-method.md` as actual text; writers also receive `editorial-examples.md`. Every attempt saves the exact method files in `method.json`, binds their digest to the actual prompts and includes the snapshot in its evidence. Updating the plugin does not rewrite an earlier attempt's method or approval. Missing or changed snapshots cannot pass. The bounded input budget includes these resources and still rejects oversized work without truncation.

The reader first does the requested work in `taskResults.answer`, using `basis` for text evidence and distinguishing stated facts, valid inference and extra assumptions in the answer. It then forms page and overall judgments from that work and the whole argument's purpose, development and emphasis. Task success alone is not article value; finding related phrases is not an explanation. At a stuck point, check the rest of the supplied unit and distinguish a content gap from a scope omission, a reader error or a justified unknown. Exploratory reasoning need not have a mature success case. The existing fields carry this work; there is no extra scorecard or review phase. The reader cannot certify external source truth or see private authoring choices and repair answers.

A rewrite retry receives actual prior review results and the most recent editor decision, including the editor's own findings and declined suggestions. The current task takes precedence when the assignment has changed; rejected review suggestions are not outstanding requirements. Independent readers never receive this decision. Keep current intent and unresolved questions in the existing authoring task/design when handing work to another conversation or capability.

When a worked answer could conceal missing material, add optional `trialInputs` to the relevant existing reader task. Select exact `{path, quote}` excerpts containing **all available task instructions and raw input**, omitting the worked solution and author verdict. Paths must belong to the assigned reader-facing pages; private sources cannot silently supply the reader's missing facts. For example:

```json
{
  "id": "choose",
  "request": "Choose an option from the supplied quotes and explain your calculation.",
  "sourceQuote": "I need to compare these offers.",
  "trialInputs": [{"path": "comparison.md", "quote": "The exact published instructions and quote data."}]
}
```

This is a diagnostic option for the particular task, not an automatic extra reader for every page. The program first runs a fresh session with only the selected inputs and request, saves its actual output or blocked point, then passes that work to the independent full-text reader. It excludes the article, authoring task, sources, prior review and worked answer from this first prompt unless the editor mistakenly selected them as input. It verifies excerpt provenance, prompt/run identity and current material; it cannot decide whether the selected excerpts are complete or leak a solution. Inspect the selection and compare with the full page. Do not call a selection omission a manuscript defect.

The first session can read, reason and calculate text; it uses explicitly supplied teaching assumptions for a simulation without demanding real customer records. It cannot operate external tools. A real software operation still needs the relevant authorized tool run and evidence. A successful model output also does not establish human comprehension or a sound chapter argument. Failed runtime evidence stops the declared work. A completed trial with missing material remains visible to the editor as `trial:task:<id>`, even if the full-text reader says pass; unresolved consequential findings cannot complete the scope. Refresh excerpts if edited prose changes their raw inputs.

## Read and decide

A completed schema 2 review returns `awaiting_editor` (exit 1 until accepted), even when the reader says pass. Inspect the actual answers, their evidence and the current complete prose unit against the original problem. Trace a suspected gap to the relationship the reader could not explain; check adjacent material before editing. Neither the reader's label nor the editor's disagreement establishes correctness. Preserve sound content and justified uncertainty, and repair the owning relationship or scope rather than adding every suggestion. Do not rerun just to change a label.

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

Unversioned/schema 1 specifications retain their legacy writer/reader/counter-reader consensus semantics. Existing editorial batches without `methodVersion` retain method 1; explicit method 1/2 batches retain their exact old prompts. New schema 2 batches record `methodVersion: 3`. Updating the plugin does not reinterpret old receipts. To move an existing legacy or method-1/2 batch to the current method:

```sh
python3 <plugin-root>/scripts/kb_execution.py migrate --root <target> --batch <id> --reason "Explain why this current scope needs editorial disposition"
```

Migration preserves old attempts, scope, authoring mode and dependencies, creates a new revision and requires a fresh review followed by an editor decision. It grants no pass, including when the old batch failed. Old whole-workflow claims remain separate. `status` and `check` expose current acceptance; model review is editorial evidence, not observed learner effectiveness.
