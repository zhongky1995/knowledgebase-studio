# Scoped lesson and interaction updates

Use for a bounded change to existing lessons, examples, operations, or teaching interactions. A different audience/product posture, course-wide redesign, or full-release request uses the full workflow. This route records current evidence for selected work; it never resets or promotes `_kb-control/workflow.json`.

An explicitly requested standalone lesson sample can also use this limited route without initializing a full-course workflow. First lock the sample's audience/posture and establish only the baseline the checks need: project contract, understood source/claim ledger, knowledge model, learning design, and page coverage; add the activity manifest only when needed. Label authored teaching assumptions as internal standards rather than pretending they came from research. Leave global workflow status uninitialized and report a sample-only claim. For audit scans, use `.knowledgebase-audit.json` to declare public roots and internal/raw-material directories; an underscore-prefixed directory is not automatically excluded. File counts do not establish learner-visible unit counts.

## Scope and implementation

1. Inspect the project contract and existing source, knowledge-model, learning-design, coverage, navigation, activity, and app contracts. Respect existing product posture. If the user asks only for diagnosis, report findings without implementing this workflow.
2. Identify changed pages and shared dependencies. Use the learning reviewer for teaching decisions, content builder for examples/operations, and app builder for actual interactions. Read the shared `learning-activity-design.md` reference under the learning-reviewer skill when applicable.
3. Update source/claim understanding, unit ownership, examples, activity IDs, and page coverage as needed. Keep old schema 1/2 designs supported; when adopting schema 3, fill its required fields consistently across the design. This metadata migration does not require rewriting unrelated lesson bodies.
4. Build the actual requested deliverables, including generated content, search/navigation, assets, and any separately requested local release. Inspect source-to-app-to-package consistency. Do not publish externally without authorization for the destination.

## Bind checks to this update

After the files/build outputs to be checked exist, create a plan with every changed input. Repeat `--path` for additional files or scoped directories. Declare generated app/delivery directories explicitly if `app-validation.json.appPaths` does not already name them; use `--release-path` for a requested packaged output. Never pass the whole knowledge-base root as a tracked directory.

```sh
python3 <plugin-root>/scripts/kb_update.py plan --root <target> \
  --path lessons/example.md --page lessons/example.md \
  --delivery-path app/dist \
  --output _kb-control/updates/<update-id>/plan.json
```

Omit `--delivery-path` for text-only work without an app. The planner includes declared activity assets, prerequisites, and control contracts, infers page references, and expands shared app or structural-contract changes to coverage pages. For lesson-level metadata edits, give explicit `--page` values; without them, changed control files conservatively include all coverage pages. A declared activity asset maps to its owning page rather than automatically treating it as shared app code. Review scope yourself: arbitrary build/runtime dependencies cannot always be inferred. Add `--page` for other affected learner pages and record missing baseline contracts instead of fabricating a pass.

The plan contains input fingerprints and required checks. Run the actual editorial review and, when required, architecture review, browser tests, and release checks on those exact inputs. Record evidence under `_kb-control/updates/<update-id>/` outside tracked deliverable directories. Each entry in `checks` has:

- `kind`: one of the plan's required checks;
- `status`: `pass` only after performing the check;
- `inputDigests`: the exact plan fingerprints that the check actually inspected;
- `evidencePaths`: non-empty report/trace paths inside the knowledge base.

Do not copy fingerprints into an old report to relabel it as current. Evidence must describe the affected pages, checks actually run, observed results, defects/rechecks, and limitations. Browser evidence must include real interaction checks when applicable. The updater validates receipt binding and file existence; it does not itself run a browser or prove a report's claims.

```sh
python3 <plugin-root>/scripts/kb_update.py check --root <target> \
  --plan _kb-control/updates/<update-id>/plan.json \
  --output _kb-control/updates/<update-id>/check.json
```

Changed source, contracts, assets, or delivery files invalidate the plan. Rebuild affected outputs, create a fresh plan, and rerun the affected checks. Do not edit away `requiredChecks` to skip checks: the checker re-derives them from the current scope.

## Completion boundary

The result is explicitly `selected-update-only`. Report the affected lessons/deliverables, current checks, any learner study not run, and `globalWorkflow` separately. A historical global pass may remain stale; explain that without turning the bounded update into an unsolicited whole-course rebuild. A scoped pass is not a global quality certificate or external publication approval.

Save the plan, evidence, and check result before a context/turn boundary. Resume by checking the same inputs and scope, not by trusting the previous prose summary.
