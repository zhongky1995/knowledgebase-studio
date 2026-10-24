# Bounded authoring and independent reader execution

Use inside pilot/content/QC or semantic updates for novice explanations, recurring reader failures, or explicitly requested independent review. Diagnosis/design do not run workers. Pure rendering updates keep the existing browser regression route. This is a work queue consumed by existing gates, not another release workflow.

## What runs

`kb_execution.py run` directly starts fresh local Codex subprocesses: an optional writer, a reader who attempts the task, then a separate counter-reader who checks that attempt against the actual text. The counter-reader sees the attempted work and gaps, not the reader's pass label. Both reader judgments must support acceptance. Runtime success alone is insufficient.

The coordinator currently supports macOS/Linux (its project lock uses POSIX file locking). The adapter uses the existing Codex authentication and CLI defaults, without copying the calling chat or loading personal provider/model configuration. It needs a modern CLI supporting ephemeral exec, ignore-user-config, JSON events and response schemas. Capability discovery checks PATH and supported macOS app bundles; `--codex-bin` explicitly selects another compatible installation. No API key setup, model pin, new sidebar chat or task-controller plugin is required. Unavailable authentication/runtime blocks the required review; do not fill an independent receipt manually.

Processes run in an empty temporary directory with tool capabilities disabled. Requests contain selected material through stdin; any tool event invalidates the result. This limits supplied context and provides inspectable execution, not a hostile-process filesystem security boundary. Local hashes are not signatures against someone able to rewrite all receipts and the program.

## Prepare a small connected batch

1. Reuse the existing audience, route and reader-job decisions. Save a short `_kb-control/reader-brief.md` quoting or locating their owning contract/user instruction. Give the reader their real starting knowledge and intended use. Do not put author answers, expected pass, repair advice or suspected defects in the brief.
   In `readerTasks`, compile concrete reader requests into `{id, request, sourceQuote}`; the quote must exist in that brief. These are tasks to perform, not expected answers or a bug list. The default task uses the brief itself, but explicit user requests must not disappear into a broad primaryQuestion. Both reader sessions must return `taskResults` for every task; `missing` blocks acceptance even when all page summaries say pass. Use the same tasks for a rejected version and its correction.
2. Select relevant source excerpts for the writer in `sourcePaths`. Those sources and the writer's task/repair history are not sent to the reader. Source selection remains an editorial responsibility; omitted source facts cannot be manufactured by the runner.
3. Adapt `assets/control-templates/execution-batches.json`. Pages must already exist (a titled Markdown seed suffices for a new draft), have `readerJob` in content coverage, and remain within the existing architecture. Group a coherent task rather than a fixed chapter count. Inputs over `maxInputChars` stop before dispatch instead of silently truncating.
4. Put the hard representative slice first; subsequent batches depend on its ID. Omitted `after` defaults to the previous batch. Explicit independent branches may use `after: []`, but overlapping ownership cannot conceal a failed prior batch.

For existing prose, set `authoringMode: review_existing`. This honestly records existing-snapshot provenance and runs the two independent reader sessions. For authoring and model-assisted repair use `rewrite`: the writer returns proposed full pages and only the coordinator applies those exact scoped pages. The mode is fixed in the batch; `--review-only` cannot bypass a required writer. Existing links and images still undergo normal content/visual checks.

```sh
python3 <plugin-root>/scripts/kb_execution.py init --root <target> --spec <batch-spec.json>
python3 <plugin-root>/scripts/kb_execution.py run --root <target> --batch pilot
python3 <plugin-root>/scripts/kb_execution.py status --root <target>
python3 <plugin-root>/scripts/kb_execution.py check --root <target> --page manuscript/01-introduction.md
```

`run` waits for its actual workers; callers should use their host's nonblocking command session and keep the user informed. It does not auto-publish or silently start later batches. Run the next declared batch only after this one is accepted; the program enforces dependencies even if the caller tries early.

## Failure and repair

A blocking reader gap returns `needs_work` and exit 1. Missing runtime evidence, interrupted jobs, unexpected tools, malformed results and stale input return a blocked result. Read the actual attempts, repair the owning text, and rerun the same batch. In rewrite mode the next writer receives prior reader/counter-reader feedback; new reader sessions receive only the resulting current reader material. Each run consumes one of the bounded attempts. Exhaustion stops dispatch. Use an explicit `replan` after materially revising the task, reader brief, sources or reader requests; a reason and a real change are required. Increasing a retry budget alone is rejected. Replanning preserves every previous attempt, invalidates the old approval, and opens a new bounded revision. It never changes ownership, authoring mode or dependencies. Do not automatically replan to evade a failure. Creating a second owner for the same failed pages is rejected.

```sh
python3 <plugin-root>/scripts/kb_execution.py replan --root <target> --batch pilot --spec <revised-fields.json> --reason "Explain what the failed attempts revealed and what has changed"
```

`revised-fields.json` contains only changed `task`, `briefPath`, `sourcePaths`, `readerTasks`, `maxAttempts` or `maxInputChars` fields. Supply the full new reader-task list if changing it. A content-only repair within the existing budget uses ordinary `run`; a new budget requires a changed work definition or source material, not deletion of run history.

An accepted batch can later have an explicit same-scope revision using `supersedes: <prior-id>`; this preserves prior history. It cannot supersede an unresolved failure. Declare the new dependencies explicitly when reworking a connected route. The gate always examines the latest owner and latest attempt, never falls back to an older pass.

The queue saves execution nonce, task/context/dependency digests, pre-edit text, exact prompts, runtime thread identities, raw events, outputs and per-batch projections. Writer, reader and counter-reader must have distinct sessions. Worker output cannot overwrite a concurrent edit. Page, prerequisite, figure, reader intent, source, task or dependency changes invalidate acceptance. A reader pass cannot be transplanted into a different batch or attempt.

## Use the result in the existing workflow

New novice pilot/content checks require accepted execution for the selected pages. QC/release also reconcile the full public Markdown inventory and declared execution pages, so shortening the coverage list cannot hide unreviewed content. `kb_update.py check` does likewise for semantic review pages, even if a mixed update was labelled rendering. Historical receipts remain readable but cannot stand in for a new independent approval. Existing explanation/visual/source/browser gates still apply; this runner does not erase those requirements or modify authored comprehension records to make them pass.

Per-batch evidence joins the existing stage/update fingerprints, including the reader packet. Adding work to a later batch does not by itself stale an unrelated accepted pilot. The full workflow checks stale dependencies before writing a stage pass.

Keep the reader brief short and stable. The task coordinator still checks cross-chapter first use, prerequisites and handoffs; a collection of locally accepted chapters cannot establish a coherent reading route. Reader and counter-reader outputs are editorial model judgments. Text-only runs cannot establish actual tool operation, graphic legibility, factual product behavior or observed learner improvement. Retain the relevant source verification, visual/browser checks and explicitly scoped final claims.
