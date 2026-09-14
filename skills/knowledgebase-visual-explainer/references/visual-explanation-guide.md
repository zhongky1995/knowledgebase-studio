# Visual Explanation Guide

## Choose The Smallest Useful Medium

- Use prose when sequence, relationship, and comparison remain easy to hold in working memory.
- Use a table for repeated exact mappings or comparisons.
- Use a static diagram for hierarchy, ownership, layout, dependency, or a stable system relationship.
- Use animation for flow, feedback, accumulation, transformation, focus, or state change that loses meaning when frozen.

Animation is not a premium version of a diagram. It is justified only when time or change carries part of the explanation.

## Explanation Contract

Before production, state:

1. the reader's starting misconception;
2. the one relationship or change they should understand;
3. the entities and information, energy, or decision flow;
4. one to five facts the source supports;
5. the visible evidence that the explanation worked.

Choose one spatial or physical metaphor that can carry the entire explanation. A metaphor may simplify appearance but must not replace the real mechanism. Keep source terms nearby when the metaphor could be mistaken for a literal implementation.

## Storyboard

For a static visual, use one to four ordered reading beats. For animation, use this four-to-six-beat arc:

1. signal the concept and starting state;
2. expose the problem or initial relationship;
3. reveal the mechanism;
4. show the cause-and-effect change;
5. show the resulting state or boundary when needed;
6. reset only when a loop serves comprehension.

Use a small motion vocabulary: reveal, flow, split, merge, focus, accumulate, transform, return. Animate explanatory properties, not every object.

## Destination And Accessibility

Let the knowledge-base destination determine aspect ratio, dimensions, duration, and format. Do not force a universal 4:3 canvas. Check the asset at the reader's desktop and mobile widths.

For animation:

- keep a static SVG or PNG fallback;
- respect reduced-motion preferences;
- avoid rapid flashes and decorative camera movement;
- keep labels stable long enough to read;
- provide a representative poster or preview;
- test the actual embedded asset, not only the source frames.

Alternative text should name the important entities, relationship or change, and conclusion. Nearby prose may carry details that would make the alternative text unwieldy.

## Failure Modes

For quantitative visuals, also read `../../knowledgebase-content-builder/references/evidence-to-judgment.md`. Choose the encoding from the reader's comparison: magnitude, change, distribution, composition, relationship, or exact lookup. Use a qualified conclusion title when the evidence supports one; retain neutral titles for lookup/exploration. Show units, relevant basis/period, and important limitations near the figure. Distinguish actual values, forecasts, and illustrative cases.

Check negative, zero, and missing values separately; never invent a zero series for a missing group. Bar lengths normally share a zero baseline; explain deliberate truncation, and choose meaningful clearly labeled scales for line/scatter plots. Inspect near-equal decimal ticks, long labels, edge annotations, and source lines at desktop/mobile widths. Keep color semantics stable with non-color cues and the existing accessible theme. Do not impose a fixed brand-color percentage or copy a report's print dimensions onto the app.

- **Prompt-only delivery:** export and inspect the real asset.
- **Decorative motion:** add a visible flow, feedback, transformation, accumulation, or state change that explains the mechanism.
- **Icon collage:** remove secondary metaphors until one visual model remains.
- **Diagram inflation:** return to prose or a table when the image does not reduce cognitive load.
- **False certainty:** restore the source condition, boundary, or unknown.
- **Unreadable labels:** shorten copy, enlarge type, and preserve safe margins.
- **Missing fallback:** add and test a static asset before app or release approval.
