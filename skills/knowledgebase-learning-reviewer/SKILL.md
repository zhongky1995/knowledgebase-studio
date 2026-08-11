---
name: knowledgebase-learning-reviewer
description: Design and audit the learning-product layer of a knowledge base when product posture is reader-led learning, guided learning, a practice workbench, or learning-oriented hybrid. Use to separate source-file count from learner-visible units, verify prerequisite order and terminology, define lesson-level outcomes and example contracts, estimate realistic reading load, challenge pilots, and produce `_kb-control/learning-design.json`.
---

# Knowledgebase Learning Reviewer

Prevent a technically complete content repository from being mistaken for a coherent course or learning manual.

## Architecture Review

1. Read the project contract, inventory, knowledge model, architecture decision, and migration map.
2. Separate orientation, core path, advanced path, reference, lab, workbook, and compatibility routes. Report source-file count and learner-visible unit count separately.
3. For every main-path unit define:
   - the learner's starting state and one observable learning result;
   - prerequisite units and terms already introduced;
   - new terms and relationships introduced here;
   - the likely misconception and consequential boundary;
   - whether a worked example is required;
   - transfer evidence and realistic reading time;
   - exercise policy consistent with the product posture.
4. Sequence units from prerequisites and conceptual load. Every main-path unit appears exactly once and after its dependencies.
5. Create `_kb-control/learning-design.json` from `../../assets/control-templates/learning-design.json`.

## Worked-Example Contract

A worked example is not a topic label, prompt template, or list of principles. When required, it must expose:

`realistic input → AI or human first attempt → human judgment → revised output → transfer to a second case`

Label the case real, anonymized, composite, or fictional. Do not present fictional outcomes as evidence.

## Pilot Counter-Review

After the pilot is built, review it again from the position of a representative novice. Look specifically for:

- an answer that is readable but still not learnable;
- undefined terms or dependencies introduced out of order;
- examples that omit the decision process or revised result;
- one lesson template forced onto different page jobs;
- exercises or progress language that contradict the approved pressure policy;
- navigation that names a route but does not let the reader enter it directly;
- reading-time labels that ignore tables, decisions, and practice.

Record the result in `_kb-control/pilot-verdict.json`. Do not approve scaling while posture, fidelity, usefulness, page-job distinctiveness, example depth, progression, transfer, or navigation fails.

## Gate

Pass only when the learning path is coherent independently of folder order, learner-visible units have distinct jobs, prerequisites precede use, required worked examples are concrete and locatable, practice matches the promised posture, and a representative reader can transfer at least one key model to a new case.
