# From evidence to transferable judgment

Use for evidence-heavy explanations, conceptual lessons, research-backed comparisons, or learning pages whose reader must make a judgment. This extends existing source, unit, activity, and coverage contracts; it does not add a workflow stage or require a report format.

## Start from the reader's use

Before drafting, state what this page helps the reader decide, understand, perform, or retrieve, and the one idea they should be able to restate. Use the existing primary question and reader-change fields rather than adding a parallel brief.

| Page job | Useful opening | Useful takeaway |
| --- | --- | --- |
| Understand a mechanism | A concrete situation or consequential question | A model with an explicit boundary |
| Judge a claim | A claim plus material that can support or weaken it | Questions to ask of the next claim |
| Perform/recover | Prerequisites and the intended observable result | Connected steps, checks, and recovery |
| Retrieve a fact | Direct answer, scope, and stable navigation | A precise value, definition, or canonical reference |

A scene is useful when it provides a cognitive foothold; it is not mandatory for every page. Preserve directories, instructions, summaries, and task steps when they help the reader. Remove production diaries, not learner operations or evidence-relevant methodology. Do not impose three acts, a fixed chapter count, or report page quotas on a knowledge base.

## Explain, then expose the boundary

Source collection is the starting point. For an explanatory page, connect observations to a mechanism and explain how that changes a decision. For uncertain causal claims, distinguish candidate explanations, what each predicts, what the evidence can discriminate, and what remains unresolved. Do not invent competing hypotheses for a settled definition or pretend observational evidence identifies a cause.

When comparing sources, explain whether the new evidence supports, qualifies, conflicts with, or addresses a different question from earlier work. Distinguish task, person/job, organization, and population-level findings (or the domain's appropriate levels). Multiple retellings of the same study are not independent replication. Lack of a relevant external baseline is a limitation, not permission to fabricate one or delay an unrelated task indefinitely.

Place consequential uncertainty next to the claim it limits, in readable text. Source links may follow the approved source-presentation policy; hiding bibliography detail must not hide uncertainty, denominators, simulated status, or conditions that change a learner's decision. Put detailed methods in adjacent optional disclosure when helpful, and keep a readable/printable fallback.

End with the usable consequence, not a repeated introduction: a decision question, worked contrast, retrieval aid, stopping rule, or next step. A toolkit can be a few lines inside the page; no mandatory extra chapter or submission is needed.

## Let learners inspect their reasoning

An optional prediction gives the learner something to revise. Keep the initial answer visible, reveal the evidence, and distinguish a supported conclusion from a lucky guess. Offer an example before independent work when prior knowledge is missing. Never force an incorrect answer, manufacture a surprise, humiliate the learner, or block reading to create suspense.

For a conceptual analogy, name the mapping, use it to predict something not yet stated, then show where that inference stops being valid. A metaphor that cannot support a useful inference is decoration. Do not equate a metaphor with a literal implementation.

A fictional numeric exercise can ask: a rate changes from 20% to 30%; what changed? Reveal both +10 percentage points and +50% relative to the initial rate, then change the initial rate or denominator. Preserve exact numbers alongside the intuitive explanation. Use the existing learning-activity contract for any interactive implementation; provide optional hints, source material, and text feedback. This is a teaching pattern, not evidence that a specific lesson improves retention.

## Quantitative evidence without a second ledger

For important empirical numbers introduced or revised in the task, add `measurement` to the owning `source-understanding.json` core claim. Use `assets/control-templates/source-understanding-quantitative.json` as an optional starter; merge records into the existing source ledger. Omit measurement for non-quantitative claims. Existing contracts without it remain supported; the checker does not discover every number in prose automatically.

Each measurement records:

- `value`: finite numeric value, with real zero, negative, and missing kept distinct;
- `measureKind`: proportion, relative-change, percentage-point-change, count, or continuous;
- `unit`, `basis` (what is counted/divided/measured), `population`, `period`, `analysisLevel`;
- `sampleSize`: status known with a positive integer `value`, or not_reported/not_applicable with a `reason` and no value;
- `citationMode`: direct or secondary; secondary also identifies `originalSource` as reported, explicitly saying if unidentified;
- `verification`: verified with actual `reviewer`, source `locator`, and review `basis`; or unverified with a `reason`.

The denominator in `basis` and the sample size are not interchangeable. A subgroup result needs its subgroup basis; a price, census count, or deterministic calculation does not acquire a fabricated N. Unknown N may be reported with a visible limitation if the intended use remains defensible. Verification means checking the quotation/value against the inspected source, not proving the study true or establishing causality. A verified secondary quotation is still secondary; a checked fictional exercise is still fictional.

For quantitative comparisons, add optional `comparisons` to the relevant knowledge unit:

```json
{
  "claimRefs": ["source.example#claim.before", "source.example#claim.after"],
  "conclusion": "What the comparison can actually support.",
  "alignmentNotes": {"period": "Different periods are the intended before/after contrast; other material conditions must be checked."},
  "remainingLimitations": "What this comparison cannot establish."
}
```

Each claimRef must also appear in the unit's sourceRefs and resolve to a measurement. Explain differences in `unit`, `measureKind`, `basis`, `population`, `period`, and `analysisLevel` using same-named alignmentNotes. The checker flags declared differences without explanations; it cannot decide whether prose notes genuinely make two measures comparable. Don't silence a mismatch with an empty justification or rewrite historical metadata to make it look aligned.

Run the existing `kb_content_check.py`: it checks these extensions during audit, architecture, and content, including scoped updates. A page using unverified declared measurements cannot label its overall evidence verified. Verify or remove unsupported factual uses; if explicitly teaching uncertainty, keep the correct evidence status and local explanation. Never bulk-flip verification flags to clear a gate.

## Put invariants in the right place

When good examples are supplied, inspect the actual approved pages/artifacts and identify the reader problems their structure solves. Record the sample scope and counterexamples before deriving local conventions. A small or domain-biased sample is calibration material, not a universal quantitative standard; match the existing project's purpose and design system before importing a new style.

- Keep source values/definitions in one canonical data layer; generate repeated numbers, labels, and citations from it where the app supports this. Do not introduce a framework just to achieve separation.
- Reuse the existing renderer/components for presentation. Declare supported content blocks; test new blocks and diagnose unsupported ones instead of silently dropping or printing raw syntax.
- Automate measurable invariants (reference resolution, numeric types, missing-vs-zero handling, known schema fields, stale inputs). Keep judgments such as causal plausibility, useful analogy, and novice comprehension in editorial review.
- Treat length/density variation as diagnostic, not a quota to pad or trim against. Test extreme content and repaired component families, not just the easiest page.
- After a change, regenerate the actual app/package before inspecting it. A successful build or unchanged route count cannot prove the displayed content is current.

## Provenance and limits of this adaptation

Inspired by [alchaincyf/huashu-report](https://github.com/alchaincyf/huashu-report/tree/8d7f4ea5bfc55776b1ef6e9b12de6d3690f4f1e1), inspected 2026-09-14, particularly its research-depth, popular-explanation, chart-pattern, and production-pipeline references. This plugin uses an independently written adaptation of those ideas, not copied renderer/chart code, styles, report templates, or institutional samples. The repository's reported institutional baseline and claims about learning effects have not been independently reproduced here. They are not universal knowledge-base standards.

Do not inherit report-only prohibitions on usage instructions, numeric page/margin/color ratios, mandatory story arcs or errors, blanket zero-baseline rules for every chart, or the claim that passing layout checks proves learning effectiveness.
