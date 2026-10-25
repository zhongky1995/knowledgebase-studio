# Architecture Modes

## Learning Postures

Learning is not one product posture. Select one before defining the main path.

### Reader-led manual

Use when the primary job is to understand a durable internal standard with low pressure:

`reader question → useful model → necessary mechanism → example/contrast → boundary → optional reflection`

The default action is reading. Exercises, saved artifacts, and completion indicators remain optional and cannot block navigation. Use progressive disclosure for large catalogs.

### Guided learning

Use when prerequisite understanding blocks a target capability and the learner expects course guidance:

`familiar problem → minimum concepts/mechanism → guided judgment → realistic output → feedback → transfer`

Do not turn supporting facts into lessons or repeat the learning chain on every page.

### Practice-led workbench

Use when the user explicitly wants to learn by producing and revising artifacts:

`real task → attempt → feedback → mechanism → revision → evidence → transfer`

Make the task commitment, expected time, and progress semantics explicit. Never infer this posture merely because the audience is a beginner or because checkable practice is possible.

## Operations

Use when repeatable execution is the main job:

`task map → inputs → workflow → decisions → outputs/templates → quality gates → exceptions/handoffs`

Allow experienced users to enter at their current stage.

## Reference

Use when fast retrieval is the main job:

`taxonomy/index → concise canonical entries → aliases/search → related rules/examples → source/freshness`

Avoid narrative transitions between entries.

## Hybrid

Use for onboarding that leads into independent work:

- a short start path;
- a task/stage operating path;
- a canonical reference library;
- tools, examples, and cases;
- optional deeper learning.

The start path must not duplicate the entire repository.

## Selection Tests

- If success is understanding a model without required production, favor reader-led learning.
- If success is explaining and applying a model with guided checks, favor guided learning.
- If success is producing and revising an artifact as the main experience, favor a practice-led workbench.
- If success is producing an accepted deliverable, favor operations.
- If success is finding a known rule quickly, favor reference.
- If all three matter at different moments, use hybrid with separate entry paths.

## Low-Value Architecture Signals

- every page repeats background, objectives, case setup, recap, and outlook;
- the answer appears after long chapter narration;
- headings describe the writing process rather than reader questions;
- procedures omit inputs, decisions, outputs, quality, or exceptions;
- templates are described but unusable;
- metrics lack calculation and interpretation;
- concepts, rules, and examples have multiple competing homes.

Repair allocation before polishing prose.

## Product-Posture Checks

When shaping a reading or application path, resolve the relevant product choices in the existing design:

- what the user sees and does in the first 30 seconds;
- whether any output is required before reading or retrieval;
- whether the full catalog is visible by default;
- what progress means and what it must never imply;
- how evidence and sources appear to learners;
- which polished outcome would still violate the user's intent.

When counts matter, distinguish learner-visible continuous units from sources, references, labs and compatibility routes. A filesystem count is never a course-size claim. Reuse the existing navigation design for an app; a complex or legacy staged app may need `navigation-contract.json` to preserve direct-entry destinations and click depth. A simple reading preview does not. One visually dominant action does not require other visible routes to be inert.
