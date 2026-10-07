# Novice Mental Models

Use this route when readers want to understand how a system works without already knowing its vocabulary. This is an explanation profile within the existing product posture, not a new course mode. Preserve free reading, optional practice, and the requested breadth. Do not apply it to an expert reference merely because the topic is technical.

## Build The Whole Before Splitting Pages

Begin with the user's everyday questions and one recognizable end-to-end event. Map the actual objects, actions, information or state changes, handoffs, and visible result. For each handoff explain what the next participant receives and why it can continue. Then allocate canonical pages around this map. A taxonomy or a row of linked definitions is not an explanation of the whole.

Keep both a continuous reading route and direct entries from everyday questions. A focused page should briefly locate its subject in the whole process, explain its part, and show where the result goes next. Links offer further depth; they must not replace the connecting sentence needed to understand the current page.

Do not interpret “no jargon or parameters” as permission to omit mechanisms the reader encounters. Introduce only the details needed to explain their observations. For a networking example, a reader who sees an address, a port, a subdomain and a URL parameter needs to understand their different jobs in one visit, even if they never memorize those names. Expand coverage when a real question reveals a missing relationship, not to hit a page or word count.

## Explain A Real Sequence

For a conceptual worked example use `exampleContract.pattern: mechanism_trace`:

`familiar situation → concrete participants and actions → intermediate handoffs → visible result → changed condition and its consequence`

The contract fields are `kind`, `input`, `participants`, `trace`, `output`, `boundary`, and `transfer`. Coverage records use `pattern: mechanism_trace` and corresponding `inputLocation`, `participantsLocation`, `traceLocation`, `outputLocation`, `boundaryLocation`, `transferLocation`. Use real objects in the domain before an analogy. A parcel metaphor may support a network explanation, but must return to what a browser sends and what a website receives, including where the metaphor stops working.

For judgment or creation examples, keep `pattern: judgment_revision` (the compatible default): input, first attempt, judgment, revision, output, transfer. Do not invent an AI draft and revision merely to satisfy the conceptual example gate. Operational teaching still requires actions, observable results, checks and recovery in the existing activity contract.

## Sentence-Level Comprehension

Read paragraphs aloud in sequence. Identify who acts, what they act on, what changes, and how the next sentence follows. If a novice has to translate an abstraction before understanding the sentence, restore the omitted action. Define necessary terms at first use, then use them consistently; the glossary cannot do the paragraph's teaching.

- Weak: “网络负责路径可达，软件负责业务判断。”
- Clearer: “浏览器把查看订单的请求交给网络。网络把请求送到网站后，网站还要核对你登录的是哪个账号，才能决定返回哪些订单。”

Do not merely replace “路径可达” with another metaphor such as “打通入口”. Preserve factual boundaries while naming the objects. Apply this pass to headings, cards, captions, labels and glossary entries as well as body text. Shorter is useful only after the causal explanation is complete.

## Pilot And Review Evidence

Set `explanationProfile: novice_mental_model` in `learning-design.json` and use the fragments in `../../../assets/control-templates/novice-mental-model.json`. Other designs may omit the profile. It adds no stage and requires no user quiz.

The design's `scenarioSpine` records the overall reader question, entry path, steps (`unitId`, `trigger`, `actor`, `action`, `result`, `handoff`), and `everydayQuestions` mapped to existing unit IDs. Explain the terminal result in the last handoff rather than inventing another participant. Review handoff continuity semantically; nonempty fields alone cannot establish it.

Choose a pilot that crosses a page boundary and includes the hardest distinction, concrete scenario and required visual, rather than selecting only easy definitions. Add `comprehensionReview` to `pilot-verdict.json`, with `reviewType` (`editorial`, `simulated`, or `learner_observed`) and checks for:

- `causalContinuity`: can the reader follow the same event across participants and pages without supplying missing steps?
- `concreteLanguage`: can a novice identify the objects and actions without already knowing the conclusion?
- `scenarioApplication`: can they explain an everyday observation and predict a changed condition?
- `conceptBoundaries`: can they distinguish neighboring concepts and explain which part changes?

Each check contains `status`, `question`, `expectedExplanation`, `path`, an exact `excerpt` from that pilot page, and `rationale`. Explain how the excerpt supports the expected explanation, not merely that the page was reviewed. Use multiple checks when the pilot spans multiple pages; every representative page needs locatable evidence. `learner_observed` additionally needs real `observationEvidencePaths`; otherwise label the review editorial or simulated. The gate checks completeness and excerpt presence, not whether people learned.

For visuals, ask what relationship remains visible if most text labels are hidden. Inspect actual size on mobile. If only text boxes remain, redesign around objects, movement, grouping or before/after state. Retain concise labels where they carry meaning; this is a test of explanatory value, not a ban on flowcharts.

Carry the accepted conventions through the corpus and sample the weakest transitions during final content review. Word count, page count, asset count, successful builds and self-authored pass labels do not prove comprehension. Report editorial review, rendering verification and observed learner evidence separately. If feedback shows a missing system chain, return to architecture; unexplained mechanisms or abstract writing return to pilot/content according to their scope. Do not treat every “看不懂” as cosmetic tone feedback.
