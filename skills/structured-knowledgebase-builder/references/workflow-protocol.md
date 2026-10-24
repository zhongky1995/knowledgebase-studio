# Existing staged workflow and compatibility

Ordinary production and maintenance use `incremental-updates.md`. This protocol is for continuing an existing eight-stage project or an explicitly requested staged production process. It is not the default for every manuscript and should not be recreated as four mandatory stages.

## Existing state and artifacts

`_kb-control/workflow.json` remains owned by `kb_workflow.py`. Existing project contracts, source ledgers, knowledge models, learning designs, coverage and navigation contracts remain readable. Keep their decisions in their original home; do not copy them into a parallel planning system. Required activity and visual manifests describe actual assets/behavior and are shared by their consumers.

Legacy stages are `intake → audit → architecture → pilot → content → app → qc → release`. App is optional; the other stage contracts remain supported rather than automatically marked skipped under the new method. A passed legacy stage still needs its declared artifacts, semantic checks and current deliverable evidence. Reports need substantive observations, not a minimum character count.

Continue a deliberately selected staged run with:

```sh
python3 <plugin-root>/scripts/kb_workflow.py next --root <target> --claim
python3 <plugin-root>/scripts/kb_workflow.py complete --root <target> --stage <stage> --artifact <actual-path>
python3 <plugin-root>/scripts/kb_workflow.py check --root <target>
```

For a new explicitly staged assignment, `init --root <target> --goal <goal> --mode auto --app auto` creates the existing state. Consult `assets/control-templates/` only for the contracts that this selected route needs. Learning result/prerequisites can inherit their knowledge unit values where supported; don't restate them for appearance.

## Scope and changes

A scoped schema 3 plan can be used beside an old workflow. It does not change, promote or renew the whole-product verdict. If the global verdict is stale, report that truth without automatically rebuilding everything. Do not run `reconcile --apply` for an ordinary local edit; it deliberately invalidates downstream legacy stages.

When actually renewing the full workflow, `check` detects changed contracts, dependency artifacts and deliverables. `reconcile --apply` records invalidation and resumes the legacy sequence; `feedback`/`invalidate` revise it explicitly. Never change hashes in old evidence to fabricate a fresh check.

Legacy novice stage contracts retain their [page-comprehension requirements](../../knowledgebase-content-builder/references/legacy-comprehension-records.md) and real independent execution; new scoped work does not inherit them merely from the novice label. Historical feedback triggers no permanent global reader requirement once its owning stage is resolved. Existing execution batches can be explicitly migrated using `independent-execution.md`; migration does not turn an old failure into a pass.

## Boundaries

Reuse confirmed user choices and authorization. Stage completion is not a new user approval. Only unresolved consequential choices, missing indispensable information or permissions require clarification. Local readiness does not authorize an external destination or rights choice.

Failures and stale evidence remain visible. A failed required check cannot be relabeled completed; repeated attempts remain bounded. Program checks establish execution and integrity facts, not overall usefulness or observed learning. A responsible editor must read and judge the delivered product even when all legacy stages pass.
