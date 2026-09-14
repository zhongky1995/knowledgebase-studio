---
name: knowledgebase-learning-reviewer
description: Design and audit the learning-product layer of a knowledge base. Use for prerequisite order, terminology, lesson outcomes, operational walkthroughs, worked examples, heuristic learning, evidence-based feedback, optional hints, transfer cases, and visual-explanation contracts; produce learning-design.json and shared learning-activities.json contracts without equating interaction completion with mastery.
---

# Knowledgebase Learning Reviewer

Prevent a technically complete content repository from being mistaken for a coherent course or learning manual.

For evidence-based explanations or transferable judgment, read `../knowledgebase-content-builder/references/evidence-to-judgment.md`. Review whether the learner can ask useful questions of the next claim, not just repeat today's answer. Test analogies by a new inference and their failure boundary; allow prediction and revision without forcing errors, hiding necessary help, or requiring a toolkit chapter.

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
5. Create `_kb-control/learning-design.json` from `../../assets/control-templates/learning-design.json`. Use schema version 3: declare a learning task type, explicit visual decision, and activity IDs (empty when unnecessary). Include elective cases/labs that promise an example or activity, not only the core path. Existing schema 1/2 designs remain compatible.

## Operational And Interactive Learning

Read `references/learning-activity-design.md` when designing or reviewing operations, troubleshooting, or teaching interactions. Choose the learning action before a widget. A text walkthrough is sufficient when it connects concrete actions to observable results, checks, and continuation/recovery.

For teaching interactions, share `_kb-control/learning-activities.json` with content, app, and QC. Define the learning goal, misconception, evidence-dependent feedback, optional support, changed transfer material, and a readable fallback. Context → prediction → consequence → explanation → revision → transfer is an optional pattern, not a universal lesson template. Allow novices a worked demonstration before independent attempts. Reader-led practice must remain skippable.

Do not count a filled field, click, or correct guess as understanding. Distinguish editor review, simulated walkthrough, and real learner studies in the review evidence; never invent learner observations.

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
- examples that omit the first attempt, decision process, revision action, or revised result;
- operations that jump from a request to success without observable results and recovery;
- interactions that give generic feedback, repeat identical transfer material, hide necessary help, or require practice before reading;
- visuals that decorate the page, flatten source boundaries, or stop at an unrendered prompt;
- one lesson template forced onto different page jobs;
- exercises or progress language that contradict the approved pressure policy;
- navigation that names a route but does not let the reader enter it directly;
- reading-time labels that ignore tables, decisions, and practice.

Record the result in `_kb-control/pilot-verdict.json`. Do not approve scaling while posture, fidelity, usefulness, page-job distinctiveness, example depth, progression, transfer, or navigation fails.

## Gate

Pass only when the learning path is coherent independently of folder order, learner-visible units have distinct jobs, prerequisites precede use, required worked examples are concrete and locatable, every lesson has a justified visual decision, and practice matches the promised posture. Review at least one changed case against its evidence and rubric; only claim observed learner transfer when a real learner study supports it.
