---
name: knowledgebase-qc-release
description: Validate and release a completed knowledge base. Use for semantic and deterministic QC, representative learning/task scenarios, readability sampling, evidence and source checks, link/route/build verification, package cleanliness, `_kb-control/qc-report.md`, `_kb-control/release-report.md`, and final share packages.
---

# Knowledgebase QC And Release

Keep QC logically separate from implementation. Read `references/qc-checklist.md`.

For declared teaching activities, read `../knowledgebase-learning-reviewer/references/learning-activity-design.md` and run `python3 <plugin-root>/scripts/kb_learning_check.py <target> --phase qc`. Review operational continuity, case provenance, evidence-dependent feedback, optional support, changed transfer material, and the component/fallback agreement. Record `learningActivities` as a separate verdict dimension when activities exist.

## QC Stage

1. Run `kb_audit.py` in strict mode after resolving intentionally allowed patterns through configuration.
2. Inspect representative pages of every major page type.
3. Test the primary reading, learning transfer, work task, or lookup scenario using only published material, according to the product posture.
4. Check intent invariants, first-screen orientation, pressure policy, catalog visibility, exercise/progress boundaries, evidence labels, source presentation/freshness, internal defaults, terminology, canonical links, navigation, and app/build behavior.
   - If visual explanations are required or declared, run `kb_visual_check.py`, inspect the actual embedded assets, and verify learning job, misconception correction, source fidelity, readability, alternative text, and animated fallback/reduced-motion behavior as a separate QC dimension.
5. Reconcile the migration map and public file tree.
6. Write `_kb-control/qc-report.md` with pass/fail evidence and required repairs.
7. Write `_kb-control/qc-verdict.json` from the plugin template. Report corpus integrity, product architecture, content quality, evidence, learning transfer when applicable, and app experience when applicable as separate dimensions with evidence. `checksNotRun` and critical issues must be empty for a pass.

Required dimensions cannot pass as `not_applicable`. Distinguish required checks from optional learner studies: an editor review or simulated walkthrough can support local readiness, while `learnerStudyStatus: not_run` must remain explicit and cannot support claims of learning gains. If the user requires learner testing, it becomes a required check and cannot be waived by this distinction.

Return failed items to the earliest affected stage. Do not repair silently and claim independent review; record what changed and rerun QC.

## Release Stage

1. Confirm QC passed for the current workflow revision.
2. Read the distribution contract: `distribution_mode`, `audience_scope`, `release_root`, `external_publish_authorized`, and `license_policy`.
3. Build the requested local package or identify the validated local entrypoint. For `static_site`, `single_file`, or `archive`, use an isolated release root rather than copying the working repository wholesale.
4. Exclude `_kb-control`, `_task-control`, `_meta`, archives, internal planning, caches, test traces, secret-like files, local absolute paths, and irrelevant repositories.
5. Copy `../../assets/control-templates/knowledgebase-release.json` into the internal control area, adjust it to the approved contract, and run:

   `python3 <plugin-root>/scripts/kb_release_check.py <release-root> --config <release-config> --output <release-check-report>`

   Keep marker-scan exclusions exact and file-specific. A validator may contain forbidden strings as test patterns; learner content, runtime files, and whole directories must not receive blanket exclusions.

6. Verify the package in a real browser after packaging. At minimum cover the entrypoint, first reading path, Markdown tables, images, relative article links, search scope, optional-practice state, desktop/mobile overflow, and console errors.
7. If the audience is public, require an explicit `all_rights_reserved` or `explicit_files` license decision. Do not infer CC, MIT, or another license from the content type.
8. Write `_kb-control/release-report.md` with scope, changes, validation, package/entrypoint, audience, license decision, external-publication status, remaining risks, and maintenance triggers.
9. Write `_kb-control/release-verdict.json`. `kb_workflow.py complete` will rerun the release package checker, write `_kb-control/release-check.json`, require real-browser evidence for the final entrypoint, and fingerprint the release root.

Release readiness ends at the validated local package or entrypoint by default. Do not create a repository, push code, enable hosting, upload files, send the package, or change external visibility without separate explicit authorization for that named destination.

## Gate

QC passes only with evidence bound to the current contract and learner-facing deliverable fingerprints. A link/build-only pass is not a content-quality, learning-transfer, or visual-explanation pass. Required visuals must be real, embedded, source-faithful, accessible assets. Release passes only when the local package or entrypoint is usable and clean, not merely when source files or a Markdown report exist. A successful external upload cannot substitute for local release checks. Any newer contract, architecture, content, app, visual, or validation artifact makes QC and release stale.
