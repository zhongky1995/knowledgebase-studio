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

## Close The Explanation, Not Just The Sequence

A scene followed by a correct conclusion can still leave the mechanism unexplained. For each consequential claim, ask the next question a reader without the vocabulary would ask: “How does it know?”, “What does it actually receive or change?”, or “Why does that produce this result?” Answer the question needed to explain the page's observation. Words such as “detect”, “recover”, “synchronize”, “route” and “validate” can conceal the very work the page promises to teach.

Before drafting, identify the page's substantive explanation promises from its title, main answer and later sections. A promise is an observation or guarantee the reader expects to be able to explain, not every sentence or term. For each, sketch the actual participant, information available at that moment, rule or association used, decisive change, and resulting handoff. Reuse the knowledge unit's mechanism and boundary; keep this working sketch in existing editorial notes rather than adding another planning artifact. If the sketch says only “the system handles it”, resolve that gap before polishing prose. A clear opening cannot stand in for a harder promise later on the page.

Use the following questions only where the promised behavior depends on them:

| Hidden work | What generation and review must expose | Typical observations |
| --- | --- | --- |
| Trigger to execution | What was registered or connected beforehand; who receives the event or action request; which actual program runs with what input | Clicking a button; a model requesting a tool |
| Basis for a decision | Which stored value, position, version, time, credential or rule is consulted; what comparison leads to each result | Cache expiry; missing data; authorization; choosing a route |
| First use and lifecycle | Where the first usable address, configuration or association comes from; who creates it; when it is updated, revoked or expired if that changes the outcome | Automatic addresses; DNS's starting point; login sessions |
| Identity through time and sharing | What associates a late reply or shared resource with the original object; where that association is kept and consulted | Article A finishes after switching to B; devices share an IP; replicas share data |
| Enforcement of a guarantee | The place that coordinates the check and change; what simultaneous requests or interruption do to the saved result | Duplicate prevention; migration restart; conditional updates |
| Boundary between participants | What this layer establishes and what the next must still do; which data is actually handed over | Backend supplies model input; transport versus order/payment; encrypted transit versus endpoint access |

Do not turn this into six compulsory subsections or teach every supporting subsystem. A concise concrete trace is often sufficient. A linked prerequisite may supply depth only if it really establishes the needed information; the current paragraph still needs the connecting sentence. For encryption or model generation, explain the relevant input, transformation and limitation without requiring a cryptography or training course. Use sources for real implementation claims; label invented traces and numbers as teaching assumptions.

Start with the normal case: establish the relevant starting state and assumptions, follow the same concrete objects through the decisive intermediate changes, and reach the visible result. Explain what information or rule enables a consequential decision. Then change a condition and derive the different outcome from those same steps. State the reusable principle after the reader has enough evidence to understand it, and demonstrate its use in another situation when transfer is promised. “案例—解释—原理—应用” describes this reasoning, not four compulsory headings or four disconnected blocks.

- **A guarantee needs a basis.** “两次修改放进事务，要么都提交，要么都不留下” gives a guarantee. For a novice asking how partial changes are avoided, establish the starting records, distinguish pending changes from the committed result, and explain what commit or cancellation does. If the page also promises crash recovery, explain the recovery information at the needed level and qualify the implementation. A database's internal algorithms belong in optional depth unless the reader's question depends on them.
- **A handoff needs an identified recipient and an observable end.** “电脑能在家中打印，外网断了也能打印” skips setup, destination and completion. State that the local printer is already added/discoverable, explain how the computer sends a prepared task to that printer, and distinguish receipt from actually printing. Derive the external-line failure comparison only after showing which steps need it. This does not require a configuration tutorial or a catalogue of printer protocols.
- **An application needs reasoning.** “下单时也要注意一致性” names another domain. A useful transfer identifies the limited stock, the competing requests, the check/change that must be coordinated and what the losing request sees. Do not add a second unexplained technical solution just to end with an application.

Stop expanding when the reader can derive the promised observation and changed-condition result from the page plus its explicitly introduced prerequisites. Do not recursively explain every component, require a word quota, or turn a brief reference entry into a lesson. Put normal operation before a catalogue of exceptions; keep the boundary that changes the result beside the claim it qualifies. Revise the existing body around the completed reasoning instead of appending a new scene above an unchanged summary.

Before release, reconstruct the answer using the prose alone, then change the condition that tests the claimed mechanism: simultaneous requests, a reply arriving late, no existing configuration, an expired association, or an external participant that did not confirm. Choose the relevant change, not all five. If the answer needs an unintroduced mapping or rule, repair the owning passage and check analogous explanations within scope. A token, task ID, transaction or encryption label does not do the work by being named. Use [explanation-regressions.md](explanation-regressions.md) to calibrate a new pilot or recurring incomplete-explanation repair; its cases illustrate depth and stopping points, not a domain checklist to paste into every product.

## Calibrate Against A Complete Slice

These are editorial comparisons, not compulsory lesson formats. Reuse the reasoning move when it serves the reader; do not copy the surface wording.

**A summary becomes a mechanism.** “状态负责持久化，前端反馈不等于后端成功” names conclusions the novice cannot yet explain. A connected version is: “你点了收藏，星星先亮起来。网页还要把收藏请求发给网站，网站再把这条记录保存下来。如果请求没有送到，星星虽然亮了，重新打开时收藏仍可能消失。” It exposes an action, intermediate handoff and condition; the term can follow. A diagram can show the star beside the saved-record state before/after, with the uncompleted handoff visible. Repeating the two abstract sentences inside boxes adds no explanation.

**A page boundary keeps the event alive.** Ending with “下一节讲端口” leaves a topic jump. Instead connect the event: “地址帮助消息到达那台电脑，但同一台电脑可以运行多个接收消息的程序。接下来要确定这次消息交给哪一个。” The next page continues that request, distinguishes the receiving program from a webpage, and shows what changing the port changes. The link adds navigation; the bridge provides comprehension.

**A new source improves the existing explanation.** A long model-training article may suggest a small, explicitly fictional calculation: input 2, weight 1, output 2, target 8, squared error 36; changing weight to 2 gives output 4 and error 16. Show how each number follows, then explain that real training has many parameters and an update rule. Absorb useful intermediate reasoning into the owning concept; deeper training detail can remain optional reference. Do not import the article's length, whole taxonomy or numerical examples as empirical evidence.

Use a sample verdict to record which editorial choices are safe to scale and which assumptions remain untested. Existing pilot evidence carries these decisions; no additional style contract is needed. Review the reader's complete path, not isolated prose and images independently.

## Pilot And Review Evidence

Set `explanationProfile: novice_mental_model` in `learning-design.json` and use the fragments in `../../../assets/control-templates/novice-mental-model.json`. Other designs may omit the profile. It adds no stage and requires no user quiz.

The design's `scenarioSpine` records the overall reader question, entry path, steps (`unitId`, `trigger`, `actor`, `action`, `result`, `handoff`), and `everydayQuestions` mapped to existing unit IDs. Explain the terminal result in the last handoff rather than inventing another participant. Review handoff continuity semantically; nonempty fields alone cannot establish it.

Choose a pilot that crosses a page boundary and includes the hardest distinction, concrete scenario and required visual, rather than selecting only easy definitions. Add `comprehensionReview` to `pilot-verdict.json`, with `reviewType` (`editorial`, `simulated`, or `learner_observed`) and checks for:

- `causalContinuity`: can the reader follow the same event across participants and pages without supplying missing steps?
- `concreteLanguage`: can a novice identify the objects and actions without already knowing the conclusion?
- `scenarioApplication`: can they explain an everyday observation and predict a changed condition?
- `conceptBoundaries`: can they distinguish neighboring concepts and explain which part changes?

Each check contains `status`, `question`, `expectedExplanation`, `path`, an exact `excerpt` from that pilot page, and `rationale`. Explain how the excerpt supports the expected explanation, not merely that the page was reviewed. Use multiple checks when the pilot spans multiple pages; every representative page needs locatable evidence. `learner_observed` additionally needs real `observationEvidencePaths`; otherwise label the review editorial or simulated. The gate checks completeness and excerpt presence, not whether people learned.

For newly written or semantically revised novice reviews, use `comprehensionReview.schemaVersion: 2` from the same template. Its `promises` enumerate the consequential promises actually found on the page (`id`, `path`, exact `claim` from the prose). Each check names its `promiseIds` and pinpoints a `basisExcerpt` inside its longer exact `excerpt`: the part that supplies the decisive information, comparison or changed-condition reasoning. Every promise needs a passed `causalContinuity` challenge; scenario and boundary checks may cover the same promise. A single coherent trace may support related promises, but a generic question with a whole-page excerpt does not establish several independent mechanisms. Read the complete page to discover omitted promises; the validator can check declared coverage, not whether the author declared everything.

For visuals, ask what relationship remains visible if most text labels are hidden. Inspect actual size on mobile. If only text boxes remain, redesign around objects, movement, grouping or before/after state. Retain concise labels where they carry meaning; this is a test of explanatory value, not a ban on flowcharts.

## Carry Review Into The Delivered Pages

A pilot approves a way of explaining; it does not approve pages written later. For a novice content build or an explanation rewrite, read every main-path/case page within the claimed editorial scope and reuse `comprehensionReview` in that page's existing `content-coverage.json` entry. Use the `pageComprehensionReview` fragment in the existing novice template. Keep checks proportional to the page's promises: at least a `causalContinuity` challenge about its decisive mechanism and a `scenarioApplication` challenge about a changed condition. Add checks for other consequential claims that remain separate; one easy opening example cannot certify a harder section later in the article.

For each check, write the reader's concrete question, then reconstruct the answer **using only the published passage and established prerequisites**. Copy enough exact text into `excerpt` to support the reasoning. The `expectedExplanation` or `rationale` must not secretly add a missing step; restore that step to the article first. A heading or a sentence naming the principle is not support for how it works. Record unresolved gaps as `unresolvedGaps`; a required gap prevents editorial readiness. Bind the review to the final page bytes with `contentSha256`, computed after editing. Changing unquoted text still makes the review stale; reread before recording a new digest.

Review in two directions: follow the explanation forward from its starting state, then work backward from each promised result and identify the published step that makes it possible. Read later substantive sections and inspect the basis excerpt rather than accepting the reviewer's expected answer as evidence. For restart or repeatability promises, challenge interruption between the check and the write; for time or sharing promises, change the active object or participant. A clean normal trace is necessary but does not alone establish the advertised guarantee.

Use `reviewType: editorial` or `simulated` unless real reader evidence exists. These are internal review questions, not mandatory learner exercises. During QC, challenge the weakest passage and a later substantive section of the delivered pages, and check connected transitions. Do not infer success from the author's review labels. The checker verifies receipts, excerpts and digests, not whether their reasoning is adequate.

Legacy coverage without page receipts remains structurally readable; the content checker reports missing novice receipts separately. A structural `status: pass` with incomplete comprehension evidence is not editorial readiness. Full novice content/QC gates require current receipts on main-path/case pages; scoped updates require them only within `reviewPages`. Add receipts for the pages being authored or semantically revised; a rendering-only repair does not require backfilling an unrelated corpus. Preserve global review scope separately from the selected update.

Schema 1 receipts remain readable and digest-checked as historical evidence, with promise coverage reported separately as legacy. New novice pilot/content/QC approvals and main-path/case pages in a scoped editorial update require version 2; unrelated regression pages and rendering-only work do not require that migration. Do not upgrade receipts by adding version numbers, copying old answers or changing hashes. On a new explanation review, actually inventory the current promises and reread their supporting passages. A newer gate does not rewrite or retroactively renew a historical verdict.

Word count, page count, asset count and successful builds do not prove comprehension. Report editorial review, rendering verification and observed learner evidence separately. If feedback shows a missing system chain, return to architecture; unexplained mechanisms or abstract writing return to pilot/content according to their scope. Do not treat every “看不懂” as cosmetic tone feedback.
