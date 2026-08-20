---
name: knowledgebase-visual-explainer
description: Design, build, embed, and validate explanatory visual assets for knowledge-base pages when a mechanism, relationship, flow, hierarchy, comparison, or state change is materially harder to understand in prose. Use for diagrams, SVG/PNG explainers, looping GIF/MP4/WebM assets, visual metaphors, storyboards, static fallbacks, alternative text, reduced-motion behavior, and `_kb-control/visual-explanations.json`. Do not use merely to decorate pages.
---

# Knowledgebase Visual Explainer

Turn one difficult relationship or change into one faithful visual explanation. Read `references/visual-explanation-guide.md` before choosing a medium.

## Entry Decision

Use the visual contract in `_kb-control/learning-design.json`. If `required` is false, do not add an asset merely for visual variety. If it is true, keep the declared learning job, misconception, preferred mode, and success evidence.

Prefer a static SVG or PNG when spatial arrangement can carry the explanation. Use animation only when time, flow, feedback, accumulation, transformation, or before/after state is part of the mechanism.

## Procedure

1. Distill one sentence stating what the reader should understand after viewing.
2. Identify the entities, relationship or change, one consequential misconception, and one to five source-grounded facts.
3. Select one dominant visual metaphor. Do not assemble a collage of icons.
4. Design one to four reading beats for a static visual, or four to six beats for animation. Give every beat one explanatory job.
5. Produce the actual asset. A prompt, storyboard, or renderer source without the exported file is not a deliverable.
6. Embed the asset in its canonical page and add alternative text that explains the mechanism rather than repeating the title.
7. For animation, provide an SVG or PNG fallback and test reduced-motion behavior. Require a seamless loop only when repetition improves understanding.
8. Create or update `_kb-control/visual-explanations.json` from `../../assets/control-templates/visual-explanations.json`.
9. Validate the manifest and files:

   `python3 <plugin-root>/scripts/kb_visual_check.py <target> --output <target>/_kb-control/visual-check.json`

## Evidence Rules

- Trace every essential visual fact to a source claim or explicitly labeled internal standard.
- Preserve mechanisms, conditions, and boundaries; visual simplicity cannot turn a qualified claim into a universal one.
- Treat generated illustrative scenery as illustrative, not evidence.
- Keep visual labels short, but carry necessary nuance in adjacent text or alternative text.

## Gate

Pass only when the real asset exists, is embedded, remains legible, performs one clear learning job, corrects the declared misconception, and passes source-fidelity review. Animation must show a meaningful mechanism-bearing state change and have a tested static fallback. Do not count decorative motion, a prompt, or an unrendered storyboard as completion.
