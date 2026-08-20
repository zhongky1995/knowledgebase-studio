---
name: knowledgebase-app-builder
description: Build, refactor, or validate a local Markdown knowledge-base app after content architecture is stable. Use for homepage, directory, search, reader, workflow or learning maps, templates, routes, generated content, desktop/mobile behavior, and `_kb-control/app-validation.md`. Skip explicitly when no app exists or is requested.
---

# Knowledgebase App Builder

Treat the app first as information architecture, then visual styling. Read `references/local-knowledge-app-ux.md`.

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
6. Run rendering-fidelity checks on representative Markdown: semantic tables, images with useful alternative text, relative `.md` links, code blocks, headings, and wide content. Confirm a search label and its default filter describe the same actual scope.
   - When `_kb-control/visual-explanations.json` exists, test every declared asset in its real page: loading, aspect behavior, label readability, alternative text, poster/static fallback, and reduced-motion behavior. Animation may not replace access to the explanation.
7. Repeat the browser checks against any packaged static-site or single-file output; source-app success does not prove release success.
8. Write `_kb-control/app-validation.md` with commands, paths checked, views inspected, defects repaired, and remaining risks. Also write `_kb-control/app-validation.json` from the plugin template with app paths, browser status, desktop/mobile widths, checks, primary-path click depth, direct-entry destinations, visual IDs and fallback/reduced-motion results when applicable, and checks not run.

## Gate

Pass only when routes resolve, generated content is current, the primary and visible direct paths are actually actionable, Markdown and declared visuals render faithfully, animated explanations retain a tested static/reduced-motion path, search behavior matches its label, mobile order is usable, no page-level overflow or blocking console errors remain, and internal control/archive content is not exposed. If a required real-browser check cannot run, record the blocker; do not pass the app stage from static checks alone.
