---
name: knowledgebase-learning-reviewer
description: Design and audit the learning-product layer of a knowledge base when product posture is reader-led learning, guided learning, a practice workbench, or learning-oriented hybrid. Use to separate source-file count from learner-visible units, verify prerequisite order and terminology, define lesson outcomes, worked examples and visual-explanation contracts, estimate realistic reading load, challenge pilots, and produce `_kb-control/learning-design.json`.
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
   - whether a visual explanation is required, and why prose or a table is insufficient;
   - transfer evidence and realistic reading time;
   - exercise policy consistent with the product posture.
4. Sequence units from prerequisites and conceptual load. Every main-path unit appears exactly once and after its dependencies.
5. Create `_kb-control/learning-design.json` from `../../assets/control-templates/learning-design.json`. Use schema version 2 and give every main-path lesson an explicit visual-explanation decision.

## Visual-Explanation Contract

Do not request a diagram merely to vary the page. Require one when relationship, flow, hierarchy, comparison, feedback, or state change is difficult to hold in prose. Prefer static for stable spatial structure and animation only when time or change carries part of the mechanism.

When required, define a stable visual ID, the cognitive reason, preferred mode, likely misconception, and observable success evidence. The content stage must apply `knowledgebase-visual-explainer` and deliver the real embedded asset; a prompt or storyboard cannot satisfy the contract.

## Worked-Example Contract

A worked example is not a topic label, prompt template, or list of principles. When required, it must expose:

`realistic input → AI or human first attempt → human judgment → revised output → transfer to a second case`

Label the case real, anonymized, composite, or fictional. Do not present fictional outcomes as evidence.

## Pilot Counter-Review

After the pilot is built, review it again from the position of a representative novice. Look specifically for:

- an answer that is readable but still not learnable;
- undefined terms or dependencies introduced out of order;
- examples that omit the decision process or revised result;
- visuals that decorate the page, flatten source boundaries, or stop at an unrendered prompt;
- one lesson template forced onto different page jobs;
- exercises or progress language that contradict the approved pressure policy;
- navigation that names a route but does not let the reader enter it directly;
- reading-time labels that ignore tables, decisions, and practice.

Record the result in `_kb-control/pilot-verdict.json`. Do not approve scaling while posture, fidelity, usefulness, page-job distinctiveness, example depth, progression, transfer, or navigation fails.

## Gate

Pass only when the learning path is coherent independently of folder order, learner-visible units have distinct jobs, prerequisites precede use, required worked examples are concrete and locatable, every lesson has a justified visual decision, practice matches the promised posture, and a representative reader can transfer at least one key model to a new case.
