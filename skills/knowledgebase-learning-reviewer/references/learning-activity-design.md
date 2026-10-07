# Operational and heuristic learning design

Read this when a lesson teaches an operation, troubleshooting, or a judgment that benefits from learner input. Keep ordinary explanations and lookup pages simple. Use one shared activity declaration across learning design, content, implementation, and QC.

## Choose the learning action before the control

| Learner needs to… | Useful activity | Evidence to observe |
| --- | --- | --- |
| Understand a mechanism | Predict, change one condition, compare the result, explain why | Explains the consequential relationship in a changed case |
| Judge evidence | Choose a conclusion and locate supporting material | Both conclusion and evidence fit the case |
| Perform an operation | Follow a concrete action and select the continuation for the observed result | Reaches the intended output and opens/checks it |
| Troubleshoot | Inspect a failure, choose what to check, repair, retest | Original failure disappears and relevant earlier behavior still works |
| Assess a creative result | Compare actual artifacts or regions against their intended use | Explains which difference affects the purpose |

Use text if it carries the task clearly. Diagrams, images, scripted demonstrations, and interactive components are options, not a quality ladder. No universal screenshot, recording, animation, step count, or interaction quota applies. Do not require a live AI call when a labeled teaching example meets the learning goal.

## Operational continuity

For each meaningful step, explain the prerequisite, concrete action, supplied material/request, possible observable results, check, and continuation or recovery. Keep neighboring steps connected: the previous output must supply what the next action needs.

For AI-tool lessons, distinguish common delivery branches when relevant:

- Chat text/code: copy the actual content, save in the intended format, then open it.
- Downloadable attachment: download, locate the file, open and check it.
- Workspace file: locate the real file in the chosen working directory, open and check it.

A plan, filename, selected attachment, or generated code alone does not demonstrate execution, successful reading, file existence, or a working result. Describe capability prerequisites and tool-neutral action names; use exact menus only for a verified product-specific walkthrough. Follow the user's presentation constraints; recordings are optional unless explicitly required.

## Guided inquiry with support

A useful optional pattern is context → prediction → observable consequence → evidence/explanation → revision → transfer. Select only the steps the goal needs; do not force every lesson into a quiz.

Allow a novice to see a worked example first. On later attempts, reduce support rather than hide necessary prerequisites. A hint can direct attention, supply the relevant criterion, or show a worked explanation. Keep help available by choice. Do not make repeated guessing the only path to an explanation.

Feedback should depend on the learner's actual choice and the case evidence. A correct choice with an unsupported reason is a different state from a supported judgment. Preserve the previous answer while revising and explain what changed. Rule-based feedback is appropriate only for bounded cases with authored criteria. For open answers use a rubric/reference analysis or human review; never infer understanding from non-empty text or a keyword alone.

Transfer changes a consequential condition or surface context. Declare whether the expected conclusion should change or remain stable, and why. Repeating the same answer is legitimate when the underlying rule remains applicable; relabeling the same input is not a new test of transfer.

## Worked examples and provenance

When a judgment/revision worked example is required, locate input, first attempt, human judgment, revision action, revised output, and transfer material. Concept explanations may instead use `mechanism_trace` from `../../knowledgebase-content-builder/references/novice-mental-model.md`; do not invent an attempt/revision exercise for them. These requirements follow the learning promise, including elective cases/labs; they are not limited to core-course pages. Check that the artifacts and explanatory text agree. Location checks only establish presence, not instructional quality.

Label real, anonymized, composite, and fictional materials. Scripted outputs must be identified as teaching examples. Distinguish observable tool results, illustrative runtime traces, source-backed mechanisms, and analogies. Fictional cases may be authored for teaching; do not invent real user observations, model runs, or learning outcomes.

## Shared declaration

Choose `assets/control-templates/learning-activities-text.json` for a minimal text operation, or `assets/control-templates/learning-activities.json` for an interactive judgment starter. Save the chosen/combined items as `_kb-control/learning-activities.json`. Adapt IDs, sources, lesson task type, steps, and page locations to the real task; these are incomplete starter declarations, not deliverable pages or passed reviews. Keep only activities needed by the task. Each item owns one `unitId` and its canonical `pagePath`.

- `kind`: concept, judgment, operation, troubleshooting, or creation.
- `mode`: text or interactive. Text walkthroughs do not require a frontend component.
- `learningGoal`, `misconception`, `provenance`, `sourceRefs`, `provenanceLocation`.
- `steps` for operations/troubleshooting: `precondition`, `action`, `input`, `possibleResults` (each has `result` and `nextAction`), `check`, `recovery`, `location` in the page. Other activity kinds may omit steps.
- `cases`: ID, guided/transfer role, material/task/feedback/evidence locations, and `expectedOutcome`. Transfer cases name their guided `comparedWith`, `changedCondition`, `expectedChange` (different/same), and `transferRationale`.
- For `interactive` mode only, `interaction` records actual `assetPaths`, page `entryLocation`, `feedbackMode` (rule-based/rubric/human-review), `resultMode` (scripted/live), optional hints with levels and page locations, `fallbackLocation`, `skipAllowed`, and `draftPolicyLocation`. Scripted results also require `simulationLabelLocation`.
- `review`: status, method (editor-review/simulated-walkthrough/learner-study), evidence paths, learnerStudyStatus (not_run/completed); completed studies additionally need learnerStudyEvidencePaths.

Locations are literal text anchors in the canonical page. The readable fallback can contain case materials, answers, and hint text in optional disclosure sections. Code/component files are not substitutes for that learner-accessible explanation. During review verify the actual component and fallback agree.

Schema version 3 of `learning-design.json` adds `learningTaskType` and `activityIds` per lesson. An empty list is valid where no activity is needed; an operation or troubleshooting lesson needs at least a text walkthrough. Include elective lessons that promise a worked example or activity. Add the IDs to page coverage and the representative pilot verdict.

Schema 1/2 designs remain supported. Upgrade touched lessons/designs when adopting activities; a narrow update does not require remaking every historical lesson. Missing historical global evidence remains stale and is reported separately from the new update.

## Page and learning states

Design learner states (not attempted, tentative judgment, feedback received, revised, attempted transfer) alongside UI states. Record observed facts such as viewed-example, used-hint, revised-answer, or independent-transfer-attempt. Click count, time spent, a single correct choice, and an opened answer do not establish mastery.

Reader-led practice remains optional. Keep the full explanation accessible, allow retry and leaving the activity, and state whether drafts survive refresh/return. Mobile layout follows material → action → result → feedback without forcing the learner to scroll sideways between necessary evidence. Support keyboard/touch, visible focus, labeled feedback, and text alternatives.

## Review and validation

Content: `python3 <plugin-root>/scripts/kb_learning_check.py <target>`.

App/QC: run the same command with `--phase app` or `--phase qc`. For each interactive ID, `app-validation.json.learningActivities` must record pass status, actual desktop/mobile viewport widths, evidence paths, and checked behaviors: feedback, retry, transfer, fallback, keyboard, mobile-reading. Check help and draft behavior as appropriate in the underlying browser report.

Pilot can select `--id`; incremental review can select `--page`. The machine checker validates structure, files, locators, case declarations, and review evidence. The editor must still assess causal coherence, meaningful feedback, and whether changed material really tests transfer. Real learner observations are a separate evidence class. A local release may be ready while learner study remains not_run; report the limited claim honestly.

## Design basis

The [IES practice guide](https://ies.ed.gov/ncee/wwc/PracticeGuide/1) recommends interleaving worked examples and exercises, connecting concrete/abstract representations, and asking explanatory questions. The patterns above are an application to knowledge-base learning pages, not evidence that this particular course has achieved learning gains.
