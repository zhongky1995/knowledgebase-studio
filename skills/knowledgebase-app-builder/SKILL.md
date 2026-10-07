---
name: knowledgebase-app-builder
description: Build, refactor, or validate a local Markdown knowledge-base app after content architecture is stable. Use for homepage, directory, search, reader, workflow or learning maps, templates, routes, generated content, desktop/mobile behavior, and `_kb-control/app-validation.md`. Skip explicitly when no app exists or is requested.
---

# Knowledgebase App Builder

Treat the app first as information architecture, then visual styling. Read `references/local-knowledge-app-ux.md`.

For data-backed content or reusable explanatory components, read `../knowledgebase-content-builder/references/evidence-to-judgment.md`. Keep canonical evidence values separate from display logic, reuse the existing design system, and validate supported content blocks. Rebuild before inspecting actual pages. After a rendering defect, check other consumers of that component and include long tables, negative/missing values, narrow decimals, and long labels where applicable. Do not replace semantic review with mechanical checks.

When learning activities are declared, also read `../knowledgebase-learning-reviewer/references/learning-activity-design.md`. Implement the shared activity IDs, cases, feedback rules/rubric, optional hints, retry, and transfer material. Do not replace pedagogical feedback with a non-empty-field check. Label scripted results; never imply a real tool/model run.

For new or redesigned diagrams, follow `../knowledgebase-visual-explainer/references/diagram-design-system.md` and complete schema 2 visual design receipts against the actual embedded files. Inspect arrow endpoints, grouping, color-independent meaning, clipping and rendered labels; preserve desktop/mobile figure screenshots and file hashes. A legacy schema 1 pass does not establish these checks.

## Entry Decision

- If no app exists and the project contract does not require one, skip the workflow stage with `kb_workflow.py skip --stage app --reason <reason>`.
- If an app exists or is required, inspect its routes, content generation, entrypoint, design system, and build/test commands before editing.

## Procedure

1. Match navigation to the approved knowledge-base mode and product posture.
   Read `_kb-control/navigation-contract.json`; do not silently reinterpret visible direct entries as decorative cards.
2. Assign distinct responsibilities to home, directory/search, reader, tools/templates, cases/practice, and internal control pages.
3. Update route/config references after file migration.
4. Rebuild generated Markdown/search content.
5. Verify representative user paths on desktop and mobile, including the unassisted first 30 seconds, default catalog state, Reader first screen, optional-practice boundary, and return/resume behavior.
   - Record click depth and actionability for the primary path and every visible direct route entry. “One primary action” does not make secondary route cards non-clickable.
   - Useful content must be reachable in one or two clicks from an intended entry unless the contract explicitly approves a deeper path.
6. Use the project's maintained Markdown parser and shared rendering path; avoid a replacement parser built from ad hoc regular expressions. Verify the final DOM and visible text, not only source patterns. Cover Chinese text adjacent to emphasis punctuation, literal asterisks in code, nested lists/quotes, links with anchors, fenced code, image/figure nesting and tables. A global `**` search is not sufficient because code can legitimately contain it. After a shared rendering fix, inspect every affected article plus desktop/mobile representative pages.
   Run rendering-fidelity checks on representative Markdown: semantic tables, images with useful alternative text, relative `.md` links, code blocks, headings, and wide content. Confirm a search label and its default filter describe the same actual scope.
   - When `_kb-control/visual-explanations.json` exists, test every declared asset in its real page: loading, aspect behavior, label readability, alternative text, poster/static fallback, and reduced-motion behavior. Animation may not replace access to the explanation.
   - For teaching interactions, check feedback against different choices/evidence, optional hints, retry, changed transfer material, text fallback, keyboard use, and draft retention/clearing. Mobile review must preserve material → action → result → feedback reading order, not merely avoid overflow. Verify practice is skippable when promised and progress labels describe observed actions, not mastery.
7. Repeat the browser checks against any packaged static-site or single-file output; source-app success does not prove release success.
8. Write `_kb-control/app-validation.md` with commands, paths checked, views inspected, defects repaired, and remaining risks. Also write `_kb-control/app-validation.json` from the plugin template with app paths, browser status, desktop/mobile widths, checks, primary-path click depth, direct-entry destinations, visual IDs and fallback/reduced-motion results when applicable, and checks not run.

For every interactive activity, add a `learningActivities` entry with its ID, pass/fail status, actual viewport widths, behavior checks, and real evidence paths. Run `python3 <plugin-root>/scripts/kb_learning_check.py <target> --phase app`. The checker verifies declarations/evidence presence; it does not run the browser or judge feedback quality for you.

## Gate

Pass only when routes resolve, generated content is current, the primary and visible direct paths are actually actionable, Markdown and declared visuals render faithfully, animated explanations retain a tested static/reduced-motion path, search behavior matches its label, mobile order is usable, no page-level overflow or blocking console errors remain, and internal control/archive content is not exposed. If a required real-browser check cannot run, record the blocker; do not pass the app stage from static checks alone.
