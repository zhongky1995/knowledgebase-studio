---
name: knowledgebase-auditor
description: Audit an existing knowledge base before restructuring. Use for repository inventory, public/internal/archive separation, source-of-truth comprehension, page-type classification, content-volume and readability metrics, semantic near-duplication and process-narration detection, broken links/routes, evidence gaps, and creation of `_kb-control/content-inventory.json`, `_kb-control/source-understanding.json`, and `_kb-control/audit-report.md`.
---

# Knowledgebase Auditor

Produce an evidence-backed baseline without rewriting public content.

For empirical numbers or cross-source comparisons, read `../knowledgebase-content-builder/references/evidence-to-judgment.md`. Add optional measurement context and actual verification records to the existing source ledger before drafting around those values. Distinguish original evidence from retellings, analysis levels, subgroup denominators, and unknown sample sizes. Do not require a quantitative contract for a non-quantitative claim.

## Procedure

1. Read root entry files, `AGENTS.md`, navigation, app routes, build scripts, archives summaries, planning/control files, and nearby truth sources.
2. Separate public, internal, generated, archived, packaged, and unknown files. When path conventions are ambiguous, create `.knowledgebase-audit.json` with explicit `publicRoots`, `archiveRoots`, `internalRoots`, and `generatedRoots` before measuring the corpus. Start from `assets/control-templates/knowledgebase-audit.json` at the plugin root when useful.
3. Run:

   `python3 <plugin-root>/scripts/kb_audit.py <target> --output <target>/_kb-control/audit-metrics.json`

   This is a deterministic corpus-integrity result, not a course-quality or overall-product verdict.

4. Build `_kb-control/source-understanding.json` from `assets/control-templates/source-understanding.json`. For every canonical or materially relied-on source, record in your own words:
   - the problem and position of the source;
   - core claims and their locatable basis;
   - the mechanism or causal relationship behind the claim;
   - conditions, boundaries, conflicts, and unknowns;
   - confidence and whether the source is primary, secondary, existing corpus, or an internal standard.
5. Classify each public document by page type and primary reader job.
6. Identify:
   - duplicated or fragmented canonical knowledge;
   - long setup, process narration, generic importance, and low-value recap;
   - missing inputs, decisions, outputs, evidence, examples, practice, tools, or exceptions;
   - unsupported claims and stale-source risks;
   - navigation, route, build, and package defects.
   - product-posture drift: default task versus reading, exercise pressure, progress meaning, catalog exposure, source presentation, and control metadata visible to readers.
   - semantic near-duplicates: customized openings or headings attached to a substantially shared body;
   - conflicting claims, unsupported abstractions, lost mechanisms, and boundaries that the current corpus hides.
7. Write `_kb-control/content-inventory.json`, `_kb-control/source-understanding.json`, and `_kb-control/audit-report.md`.

Use `assets/control-templates/content-inventory.json`. Inventory must contain one record per public document; an empty object or title-only list cannot pass. For learner-facing corpora, configure `learnerForbiddenMarkers` and review advertised reading-time warnings rather than allowing control metadata or implausible time labels through.

Do not summarize from titles, snippets, prior assistant messages, or repository names when the selected source is available. Read the complete relevant source before modeling it. If access is partial, mark the unknown instead of inferring an architecture from the name.

## Inventory Fields

For each relevant file record path, visibility, section, page type, primary job, canonical status, source status, represented claims/knowledge units, readability issues, usefulness gaps, link/route status, recommended action, and confidence.

Recommended actions are `keep`, `rewrite`, `merge`, `split`, `move-reference`, `archive`, and `investigate`.

## Audit Report

Lead with conclusions. Separate deterministic integrity, product architecture, content usefulness, learning transfer, app experience, and release hygiene. Include corpus metrics, architecture diagnosis, product-posture risks, content allocation problems, readability/density findings, evidence gaps, app/build findings, high-priority repairs, and uncertainties. Do not write “整体通过” unless later QC has passed every required dimension.

Do not equate short content with good content or long content with bad content. Judge whether each section changes understanding, decision, execution, or retrieval.

## Gate

Pass only when the public corpus is identified, important sources are understood rather than merely listed, claims/mechanisms/boundaries are traceable, content allocation and product-posture risks are visible, and architecture can proceed without rediscovering the repository. Do not treat path-prefix guessing as a sufficient public-scope decision when archives or share packages use ordinary names.
