---
name: knowledgebase-content-builder
description: Build or rewrite reader-facing knowledge-base content after architecture is locked. Use for pilot slices and full production across learning, operations, reference, or hybrid modes; minimum sufficient explanation; readability and cognitive load; SOPs, decisions, metrics, templates, examples, cases, practice, feedback, and content-build reporting.
---

# Knowledgebase Content Builder

Produce useful reader-facing content with the least necessary reading. Do not reopen approved architecture unless evidence makes it unworkable.

Read `references/readability-density.md` for every rewrite. Also read `references/learning-mode.md` or `references/operations-mode.md` for the selected mode. For learning, obey the contract's product posture; do not treat “learning” as permission to require tasks or artifacts.

For operational lessons or teaching interactions, also read `../knowledgebase-learning-reviewer/references/learning-activity-design.md`. Maintain the shared `_kb-control/learning-activities.json`; do not invent a second interaction specification. Preserve prerequisite → action/input → observable result → check → continuation/recovery even while shortening prose. Screen recordings are not mandatory.

## Pilot Stage

1. Build the representative slice selected by architecture.
2. Include every page type needed to expose risk, not merely the easiest article.
3. Trace the pilot from source claim → knowledge unit → page section. Compare essential points before and after rewriting; record preserved, intentionally changed, and unresolved meanings.
4. Validate first-screen value, explanation budget, terminology, default action, pressure level, catalog exposure, task/ability output when applicable, navigation context, evidence treatment, and whether the page has a genuinely distinct reader job.
   - When the pilot lesson requires a visual explanation, apply `knowledgebase-visual-explainer`, embed the real asset and fallback, and record its ID in the pilot verdict. Do not approve a prompt-only or decorative result.
5. Write `_kb-control/pilot-review.md` with artifacts, source/knowledge-unit trace, fidelity comparison, decisions, checks, defects, repairs, and whether the sample is safe to scale.
6. Write `_kb-control/pilot-verdict.json` from the plugin template. Run a separate counter-review that actively looks for abstract examples, terminology jumps, repeated legacy bodies, page-role confusion, exercise pressure, and inability to transfer. Do not scale while any required dimension fails.

Do not scale a sample that still contains repeated setup, unclear canonical ownership, a page template forced onto every article, a customized opening pasted above a shared legacy body, or a default interaction that contradicts the intended product posture.

## Content Stage

1. Apply the accepted pilot conventions across the migration map.
2. Rewrite high-value main-path pages first.
3. Create `_kb-control/content-coverage.json` from `assets/control-templates/content-coverage.json`. Give every target page a primary question, reader change, owned knowledge units, essential preserved meanings, fidelity locations, distinctive value, and evidence status.
4. Add only missing mechanisms, decisions, examples, tools, practice, evidence, and exceptions.
   - When `learning-design.json` requires a worked example, show locatable input, first attempt, human judgment, revision action, revised output, and transfer material. Apply the promise to case/lab pages too. A template or principle list is not a worked example.
   - Record example and practice locations plus realistic reading time in `content-coverage.json`.
   - Record activity IDs in page coverage and the representative pilot verdict. Supply actual case material, evidence-based feedback, optional hints, and a readable fallback for interactions. Label scripted outcomes and fictional cases; keep first attempt and revised result distinguishable.
   - Apply `knowledgebase-visual-explainer` for every required visual contract. Record IDs per page in `content-coverage.json` and maintain `_kb-control/visual-explanations.json`. Use no visual when the learning contract marks it unnecessary.
5. Update cross-links and indexes as canonical pages move.
6. Archive superseded material recoverably after replacements and routes exist.
7. Run:

   `python3 <plugin-root>/scripts/kb_content_check.py <target> --output <target>/_kb-control/content-integrity.json`

   When visual explanations are required or the manifest exists, also run:

   `python3 <plugin-root>/scripts/kb_visual_check.py <target> --output <target>/_kb-control/visual-check.json`

8. Rerun `kb_audit.py` and inspect `near-duplicate-page`, `repeated-outline-pattern`, and shared-block warnings. Similar structure is allowed only when the reader job genuinely requires it; a common template is not evidence of consistency.
9. Write `_kb-control/content-build-report.md` with files added/rewritten/merged/archived, knowledge-unit coverage, meanings preserved/changed/unresolved, gaps filled, assumptions, validation, and unresolved source risks.

When activities are declared, run `python3 <plugin-root>/scripts/kb_learning_check.py <target>`. Record actual editorial/simulated review evidence; passing a structural checker does not validate learning efficacy. For a bounded lesson update, use the controller's `references/incremental-updates.md` instead of asserting a fresh full-corpus pass.

## Universal Rules

- One page answers one primary question, decision, or task.
- Put a useful answer, model, action, or output in the opening section.
- Give each important concept or rule one canonical home.
- Use minimum sufficient explanation, not encyclopedic completeness.
- Define terms before use and control simultaneous new relationships.
- Attach practice and feedback to key abilities, not every article.
- Use diagrams or animation only when they reduce the cognitive load of a real relationship or change. A prompt, storyboard, renderer source, or decorative motion is not a learner-facing asset.
- Separate facts, inferences, internal defaults, and hypotheses.
- Keep learner-facing source presentation separate from internal traceability. “Do not show sources to learners” never means deleting the evidence ledger.
- Preserve the source's meaning, not its wording. A rewrite may compress language but must retain consequential mechanism, conditions, boundary, and uncertainty.
- Synthesize disagreements explicitly. Do not flatten multiple sources into a false consensus.
- Never fabricate cases, metrics, source behavior, or outcomes.
- Label every case as real, anonymized, composite, or fictional. Fictional cases may teach a mechanism but cannot be presented as outcome evidence.

## Gate

Pass the pilot only after the representative slice survives comprehension, fidelity, usefulness, posture, and any required visual-explanation review. Pass content only when the migration map is accounted for, every knowledge unit has a canonical owner, every target page has traceable coverage and distinctive value, every required visual is an actual embedded and validated asset, public navigation points to canonical content, near-duplicate risks are resolved, and the build report identifies remaining evidence gaps.
