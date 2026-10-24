# Review the reader's actual task

Use to investigate a current difficulty following a case, making a judgment, acting or understanding a figure. Read the whole selected passage and its role before treating the problem as a missing step. This is an optional diagnostic aid, not an automatic novice approval procedure.

## Choose the promise before the prose

Use the existing reader purpose or choose `--job` from `understand`, `perform`, `judge` or `retrieve`. Decide from the title, promised takeaway and actual reader situation, rather than calling every handbook chapter a conceptual explanation.

| Job | Evidence the reader needs |
| --- | --- |
| understand | One connected event, the information/rule enabling its decisive change, and a changed-condition prediction. |
| perform | A completed example reached from explicit inputs through decisions, checks and handoff; enough to try the task without inventing missing instructions. |
| judge | Material supporting a choice, the comparison or alternative, and a condition that changes the decision. |
| retrieve | A directly usable answer with the definitions, scope and units needed to interpret it. |

Free reading and optional practice concern what learners must submit. They do not remove a worked demonstration from a chapter promising a method. Conversely, an explanatory page does not automatically need an action checklist.

## Prepare the actual material with the tool

After the final prose, calculations and figures exist, run:

```sh
python3 <plugin-root>/scripts/kb_reader_probe.py prepare --root <target> --page manuscript/page.md
```

The tool uses `readerJob` in coverage; `--job perform` is an explicit override for a sample or older project. It produces a numbered copy of the complete page, available prerequisite pages, a mechanically selected later section, job-specific review instructions, and original/masked local SVG pairs in `figures.html`. It excludes the author's promise inventory and review answers. It does not invoke another model, run a learner experiment or establish that the material was read.

Prepare individual pages separately for maintenance; a connected pilot slice may use repeated `--page`. Any changed input invalidates a packet containing it. The whole-packet invalidation is conservative; it does not renew unrelated pages.

Read the complete material and inspect relevant figures. Try the reader's task using only what the passage actually supplies. A changed condition can expose a missing premise, but first decide whether the question or example itself belongs in this chapter. Record the finding and editorial treatment in the current scoped decision or execution result. Do not supply missing steps only in an expected answer.

When reading a solution would let the reviewer fill missing steps, use the executor's optional input-only trial described in `../../structured-knowledgebase-builder/references/independent-execution.md`. Select all published instructions and raw input for the actual task; keep the worked solution out of that first run. Inspect its concrete artifact or first blocked point, then compare against the complete page. Judge the argument separately with `evidence-to-judgment.md`: an executable example can still support an uninteresting or overstated conclusion.

Legacy staged/schema 1–2 updates can retain their [comprehension receipt procedure](legacy-comprehension-records.md). Current schema 3 work does not copy a completed independent result into another page certificate.

`kb_reader_probe.py check --root <target> --packet <packetPath> --page manuscript/page.md` checks material integrity. Its `readiness: not_assessed` is deliberate. A current packet plus completed fields still cannot establish good reasoning. If the reviewer already saw authoring context, label the review editorial/simulated; the packet does not make that person independent.

When an independent review is currently needed, use `../../structured-knowledgebase-builder/references/independent-execution.md`. The current executor prepares material, runs an independent reader and records the main editor’s disposition. A further reviewer is optional for a remaining question. Legacy batch semantics are preserved until explicitly migrated.

## Optional diagnostic example: an operational failure

Weak version: “明确负责人和权限，安排经验维护时间，把团队贡献计入评价。” These may be sound principles, but a manager cannot inspect a completed arrangement or see why a specific decision was made.

More useful teaching example, explicitly fictional:

> 周二试用后，销售每天多送来十份需求草稿，生产负责人却说自己比以前更忙：半数没有交货地址，他得逐份退回。负责人陈敏先拿其中两份逐项对照，发现缺项在交接前没有被拦住。她让销售在同一需求记录里补齐地址，把“客户期望周五”保留为待确认；只有数量、规格、地址齐备的记录才交生产。陈敏可以决定退回缺项件和调整受理顺序；会影响已承诺交期的加急，由经理决定，生产不能自行承担。

Completed arrangement visible in the same example:

| Situation | Who acts | Delivered state / check |
| --- | --- | --- |
| Address missing | Sales asks the customer and updates the original record | Remains pending; no production commitment. |
| Requirements complete | Production checks capacity and records an available date | Sales obtains customer acceptance before confirming. |
| Requested expedition conflicts with an accepted order | Manager decides the priority and cost | Decision returns to the same record; both teams can use it. |

Then change the input: the address is complete, but the customer requests an earlier date. A reader should reach the manager's decision branch, not simply repeat “明确权责”. The example establishes only this arrangement, not universal staffing or incentives. Deeper incentive questions need their own relevant evidence and example.

Use narrative where it helps: someone has a task, encounters an obstacle, sees evidence, makes a choice and gets a result. Anonymization and not showing original project details do not require stripping out events. Do not force a cast, three acts or a single story across all pages.

## Separate AI's contribution from software and organization

An order with concrete quantities and prices is not sufficient evidence of AI value. Shared records, fetching an old order and deterministic pricing can be ordinary software. Explain which reading, comparison, extraction or drafting work AI changes, which old human actions actually stop, and which checks, corrections and maintenance are introduced. A cheaper draft may leave total work unchanged or increase it. Service expansion may matter more than time savings; use the business outcome appropriate to that claim.

When the case makes a numeric workload comparison, use the optional `workedExample.workComparison` fragment from `assets/control-templates/work-comparison.json` in existing content coverage. Keep one same-task activity inventory across manual, software-only and AI methods. Every method accounts for every activity; an omitted row is not zero effort. `fixedHumanMinutes` is maintenance in the declared period; `volume` gives its per-task allocation. Do not invent times to satisfy this contract. Qualitative examples can stay qualitative.

Put one marker pair at the intended place in the owning page, using the model's ID:

```html
<!-- kb-work-comparison:order-preparation -->
<!-- /kb-work-comparison:order-preparation -->
```

Then generate only that block:

```sh
python3 <plugin-root>/scripts/kb_work_comparison.py <target> --page manuscript/page.md --write
```

The script computes totals, software-relative AI increment and optional volume sensitivity. The content, pilot, QC and update checks reject drift between this data and the published block. Keep the model as the canonical data; do not hand-edit generated totals. Generate before preparing the reader packet or computing page-review hashes.

`teaching_assumption` is visibly labeled, never an observed benefit. For `measured`, `measurementRefs` maps `volume`, `<method>.fixedHumanMinutes` and each non-absent `<method>.<activity>.humanMinutes` to verified measurements in the existing source ledger, with matching values and minute/task units. This checks declared numeric alignment, not whether the measurement is true or the task comparison is fair. The editor must still inspect comparable inputs, retained results, accounting period and exclusions such as setup, training, fees and natural waiting. Platform costs cannot be silently added to human minutes.

## Inspect what the graphic contributes

Open the generated figure sheet as review material. For SVGs the program removes text elements while preserving geometry; inspect original and masked versions together. Look for objects, mapping, movement, grouping, a condition branch, a before/after state or a quantity difference. Then restore labels and check fidelity. Labels converted to paths and raster text cannot be removed automatically. A meaningful process or chart can require labels; this is diagnostic, not an automatic rejection test.

If a figure only repeats paragraphs in boxes, use a table/prose or redesign the actual relation. The source figure sheet is not the delivered app; retain real desktop/mobile inspection in the existing visual/app review. Do not require a diagram on every page or replace explanatory relationships with decorative icons.

## Learn from a specific rejected output

When feedback contradicts a previous pass, record the concrete reader failure and reproduce it with the current passage before editing. A good failure question asks for an output or prediction that the old version cannot support. First diagnose whether the question, structure, example, mechanism or expression is wrong; then choose an appropriate treatment and inspect materially affected content. Do not automatically add detail to every page. If a shared editorial choice failed, reconsider that choice and its affected uses before repeating it. Use existing workflow feedback/invalidation or the scoped update path; do not renew hashes to preserve an obsolete claim or add routine user approvals.

Keep structural integrity, arithmetic, editorial task review, actual UI behavior and observed learner outcomes separate in the final report. The tools make evidence inspectable and catch specific shortcuts; they cannot certify comprehension, narrative quality, visual effectiveness or real business returns.
