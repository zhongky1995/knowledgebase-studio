# Scoped production and updates

Use the existing `kb_update.py` planner/checker for ordinary manuscript production, samples, maintenance and requested local delivery. This is an extension of the incremental route, not a new workflow state machine. It never initializes, advances or resets `workflow.json`.

## Current route (plan schema 3)

Work from the actual manuscript, the existing reader brief/design and relevant sources. Maintain source provenance and uncertainty where they belong. Ordinary prose needs no separate knowledge model, learning design, coverage inventory, migration map or page self-review. Existing structured records remain available for complex products and declared assets.

After the candidate files exist, select the changed inputs and reading scope:

```sh
python3 <plugin-root>/scripts/kb_update.py plan --root <target> \
  --path manuscript/chapter.md --page manuscript/chapter.md \
  --context _kb-control/reader-brief.md --context sources/relevant.md \
  --output _kb-control/updates/current/plan.json
```

Repeat `--path`/`--page`/`--context` as needed. An existing project contract or `_kb-control/reader-brief.md` can supply intent without a second brief. Relevant supporting sources must be included as context; the program cannot discover evidence omitted by the editor. Do not track the whole project root. Declare app outputs with `--delivery-path` and requested packages with `--release-path`.

The planner separates changed editorial pages from rendering regression pages. Changed prose or declared explanatory assets still carry semantic consequences even if a shared renderer changes at the same time. It projects existing structured contracts onto the relevant content and prerequisites; unrelated contract rows and unrelated review queues do not stale this work.

Perform the required checks on those current inputs, then record the actual observation in the same plan:

```sh
python3 <plugin-root>/scripts/kb_update.py record --root <target> \
  --plan _kb-control/updates/current/plan.json --kind editor-review \
  --summary "Describe the actual reading/use judgment and consequential dispositions." \
  --output _kb-control/updates/current/plan.json
```

The program binds the observation to current scope and input/contract fingerprints; no hand-copied hashes or separate editor report is needed. Use `--status needs_work` for unresolved work. Browser/release checks additionally name actual files with `--evidence`. Recording an observation does not perform the check: stale plans are rejected, and an authored summary cannot stand in for a declared independent run.

If current independent review is required, declare the selected batch using `independent-execution.md`. An editorial batch stores the main editor's decision with the actual run, so the updater does not demand another editor receipt for those same pages. Pending, failed or stale declared execution still blocks the scoped check. A beginner label or an old feedback event alone does not require new independent runs.

```sh
python3 <plugin-root>/scripts/kb_update.py check --root <target> \
  --plan _kb-control/updates/current/plan.json \
  --output _kb-control/updates/current/check.json
```

The checker recomputes required checks and affected inputs. Changed relevant evidence requires rereading/rechecking; deleting a required check from the plan does not bypass it. Local links and declared calculations/assets remain checked. Its result names `validationKind: scoped-integrity-and-review-records`; `editorialEvidence` separates editor-reported and independent-review scopes, and explicitly leaves content quality, source truth and observed learning outside automatic certification. The page lists describe evidence requirements, not approvals. A current unresolved editorial question stays in the existing intent/decision even if file and record checks pass.

## Existing projects

Plans with schema 1/2 retain their legacy coverage, comprehension and evidence contracts; use `--schema-version 2` to continue that route. Do not relabel old receipts as schema 3. A newly generated schema 3 plan is an explicit scoped editorial check, not an upgrade of prior whole-product evidence. Old per-page self-reviews stay historical; they are not silently refreshed.

Existing execution batches keep their original consensus rule until explicitly migrated with `kb_execution.py migrate --batch <id> --reason <reason>`. Migration preserves attempts and scope, invalidates the prior acceptance and requires a fresh run plus a current editor decision. It cannot turn an unresolved old failure into completion.

The result remains `selected-update-only`, even if all current manuscript pages were selected. Report the actual inspected deliverables and `globalWorkflow` separately. A stale old global pass is not an instruction to rebuild unrelated work, nor permission to claim the whole workflow passed. Local readiness does not authorize external publication.
