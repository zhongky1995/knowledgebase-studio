# Legacy comprehension receipt contracts

Read only when renewing an existing staged/schema 1–2 update claim. Ordinary schema 3 work does not create these per-page certificates.

## Pilot And Review Evidence

Set `explanationProfile: novice_mental_model` in `learning-design.json` and use the fragments in `../../../assets/control-templates/novice-mental-model.json`. Other designs may omit the profile. It adds no stage and requires no user quiz.

The design's `scenarioSpine` records the overall reader question, entry path, steps (`unitId`, `trigger`, `actor`, `action`, `result`, `handoff`), and `everydayQuestions` mapped to existing unit IDs. Explain the terminal result in the last handoff rather than inventing another participant. Review handoff continuity semantically; nonempty fields alone cannot establish it.

The following receipt procedure is for renewing legacy staged/schema 1–2 update evidence. Ordinary schema 3 work uses the current scoped editorial decision and any specifically required independent run; it does not add these per-page certificates. A sample is needed only for an actual unresolved editorial question.

Choose a pilot that crosses a page boundary and includes the hardest distinction, concrete scenario and required visual, rather than selecting only easy definitions. Add `comprehensionReview` to `pilot-verdict.json`, with `reviewType` (`editorial`, `simulated`, or `learner_observed`) and checks for:

- `causalContinuity`: can the reader follow the same event across participants and pages without supplying missing steps?
- `concreteLanguage`: can a novice identify the objects and actions without already knowing the conclusion?
- `scenarioApplication`: can they explain an everyday observation and predict a changed condition?
- `conceptBoundaries`: can they distinguish neighboring concepts and explain which part changes?

Each check contains `status`, `question`, `expectedExplanation`, `path`, an exact `excerpt` from that pilot page, and `rationale`. Explain how the excerpt supports the expected explanation, not merely that the page was reviewed. Use multiple checks when the pilot spans multiple pages; every representative page needs locatable evidence. `learner_observed` additionally needs real `observationEvidencePaths`; otherwise label the review editorial or simulated. The gate checks completeness and excerpt presence, not whether people learned.

For newly written or semantically revised novice reviews, use `comprehensionReview.schemaVersion: 2` from the same template. Its `promises` enumerate the consequential promises actually found on the page (`id`, `path`, exact `claim` from the prose). Each check names its `promiseIds` and pinpoints a `basisExcerpt` inside its longer exact `excerpt`: the part that supplies the decisive information, comparison or changed-condition reasoning. Every promise needs a passed `causalContinuity` challenge; scenario and boundary checks may cover the same promise. A single coherent trace may support related promises, but a generic question with a whole-page excerpt does not establish several independent mechanisms. Read the complete page to discover omitted promises; the validator can check declared coverage, not whether the author declared everything.

Before recording a new approval, use `reader-task-review.md` and `kb_reader_probe.py` to prepare the final page, available prerequisites, later passage and actual figures without the author's answers. Attempt the reader's job first, then write the existing review and attach the returned `readerProbe`. A repeated question and answer cannot establish a different check by changing its category; the checker now rejects that specific shortcut. The tool's current-material result is not an editorial or learning pass.

For visuals, ask what relationship remains visible if most text labels are hidden. Inspect actual size on mobile. If only text boxes remain, redesign around objects, movement, grouping or before/after state. Retain concise labels where they carry meaning; this is a test of explanatory value, not a ban on flowcharts.

## Carry Review Into The Delivered Pages

A pilot approves a way of explaining; it does not approve pages written later. For a novice content build or an explanation rewrite, read every main-path/case page within the claimed editorial scope and reuse `comprehensionReview` in that page's existing `content-coverage.json` entry. Use the `pageComprehensionReview` fragment in the existing novice template. Keep checks proportional to the page's promises: at least a `causalContinuity` challenge about its decisive mechanism and a `scenarioApplication` challenge about a changed condition. Add checks for other consequential claims that remain separate; one easy opening example cannot certify a harder section later in the article.

For each check, write the reader's concrete question, then reconstruct the answer **using only the published passage and established prerequisites**. Copy enough exact text into `excerpt` to support the reasoning. The `expectedExplanation` or `rationale` must not secretly add a missing step; restore that step to the article first. A heading or a sentence naming the principle is not support for how it works. Record unresolved gaps as `unresolvedGaps`; a required gap prevents editorial readiness. Bind the review to the final page bytes with `contentSha256`, computed after editing. Changing unquoted text still makes the review stale; reread before recording a new digest.

Review in two directions: follow the explanation forward from its starting state, then work backward from each promised result and identify the published step that makes it possible. Read later substantive sections and inspect the basis excerpt rather than accepting the reviewer's expected answer as evidence. For restart or repeatability promises, challenge interruption between the check and the write; for time or sharing promises, change the active object or participant. A clean normal trace is necessary but does not alone establish the advertised guarantee.

Use `reviewType: editorial` or `simulated` unless real reader evidence exists. These are internal review questions, not mandatory learner exercises. During QC, challenge the weakest passage and a later substantive section of the delivered pages, and check connected transitions. Do not infer success from the author's review labels. The checker verifies receipts, excerpts and digests, not whether their reasoning is adequate.

Legacy coverage without page receipts remains structurally readable; the content checker reports missing novice receipts separately. A structural `status: pass` with incomplete comprehension evidence is not editorial readiness. Full novice content/QC gates require current receipts on main-path/case pages; scoped updates require them only within `reviewPages`. Add receipts for the pages being authored or semantically revised; a rendering-only repair does not require backfilling an unrelated corpus. Preserve global review scope separately from the selected update.

Schema 1 receipts remain readable and digest-checked as historical evidence, with promise coverage reported separately as legacy. New novice pilot/content/QC approvals and main-path/case pages in a scoped editorial update require version 2; unrelated regression pages and rendering-only work do not require that migration. Do not upgrade receipts by adding version numbers, copying old answers or changing hashes. On a new explanation review, actually inventory the current promises and reread their supporting passages. A newer gate does not rewrite or retroactively renew a historical verdict.

Word count, page count, asset count and successful builds do not prove comprehension. Report editorial review, rendering verification and observed learner evidence separately. If feedback shows a missing system chain, return to architecture; unexplained mechanisms or abstract writing return to pilot/content according to their scope. Do not treat every “看不懂” as cosmetic tone feedback.
