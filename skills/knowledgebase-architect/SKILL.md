---
name: knowledgebase-architect
description: Design the target information architecture and migration plan for a knowledge base after audit. Use to select learning/operations/reference/hybrid mode, define capability or task paths, assign canonical homes, separate main-path/reference/tool/case material, decide merges/splits/archives, and produce `_kb-control/architecture-decision.md` plus `_kb-control/migration-map.yaml`.
---

# Knowledgebase Architect

Turn audit evidence into a target architecture. Do not rewrite the full corpus in this stage.

Read `references/architecture-modes.md`.

## Procedure

1. Read the project contract, inventory, audit report, and canonical sources.
2. Choose primary and secondary modes plus an explicit product posture from the reader's actual moment and desired default action.
3. Define:
   - main entry and shortest useful path;
   - capability, task, stage, or taxonomy structure;
   - public sections and internal-only areas;
   - canonical home for each important concept, rule, metric, tool, and case;
   - page types and expected outputs;
   - navigation and app consequences.
   - default visible scope, pressure policy, exercise role, progress truth, and source presentation;
   - an intent mirror describing the practical consequence of the chosen posture;
   - when an app exists, a machine-readable `_kb-control/navigation-contract.json` defining the primary path, every intended visible direct entry, destination, and maximum click depth;
4. Convert understood source claims into `_kb-control/knowledge-model.json` using `assets/control-templates/knowledge-model.json`. Each knowledge unit must own one reader question, core answer, reader change, necessary mechanism, boundary, source reference, prerequisites, role, and canonical page.
5. Define progression from dependencies and reader difficulty, not from the old folder order or a desire for visually balanced modules.
   - For any learning posture, apply `knowledgebase-learning-reviewer` and create `_kb-control/learning-design.json` from the plugin template.
   - In schema version 3, identify each lesson's learning task type and activity IDs. Operations/troubleshooting need a text walkthrough or appropriate interaction. Include elective cases/labs with promised examples; do not impose interactions on reference pages.
   - Every main-path knowledge unit must appear exactly once in a progression, after its prerequisites.
   - Count learner-visible units separately from source files, compatibility routes, wrappers, references, labs, and workbooks.
   - For every main-path lesson, record whether a visual explanation is required. Require one only when a mechanism, relationship, flow, hierarchy, comparison, or state change is materially harder to understand in prose or a table. Declare its ID, reason, static/animated preference, misconception, and success evidence before production.
6. Map every old public file to a target action and path.
7. Identify a representative pilot slice that tests the hardest architecture, source-synthesis, progression, and writing assumptions.

## Required Artifacts

`architecture-decision.md` must state mode, product posture, users/tasks, reader moment, default action, first success, main path, target tree, canonical allocation rules, knowledge progression, pressure/progress/source policies, anti-goals, app impact, pilot scope, evidence gaps, and acceptance checks.

`knowledge-model.json` must trace every important unit to understood source claims or an explicitly labeled internal standard. It must record mechanisms and boundaries, not only topic labels. One unit has one canonical owner even when it is referenced from many pages.

`migration-map.yaml` must map each old path to an action, target path, canonical owner, dependencies, and preservation status. Do not delete superseded material before the replacement and route changes are validated.

For learning products, `learning-design.json` must define route roles, learner-visible unit count, lesson starting state, one learning result, prerequisite units, new terms, likely misconception, worked-example requirement, visual-explanation decision, transfer evidence, and realistic reading time.

## Gate

Pass only when the pilot can be built without inventing page ownership, claims, mechanisms, prerequisites, or boundaries, and when the chosen posture does not contradict the contract's default action or anti-goals. Do not create pages solely to make every module visually symmetrical.
