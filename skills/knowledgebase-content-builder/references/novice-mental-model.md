# Explain an unfamiliar system

Use when the reader lacks the vocabulary and experience needed to follow a system. Keep the requested breadth, free reading and optional practice. This is an editorial method inside the current product, not a new course mode.

## Begin with something worth understanding

Use the reader's question to choose the core explanation. What observation should become understandable, or what tempting mistake should the reader be able to avoid? Develop the judgment with [evidence-to-judgment.md](evidence-to-judgment.md) when the page needs an argument. A taxonomy of components gives places to store explanations; it does not supply the explanation of the whole.

Follow one recognizable event before splitting it among pages. Keep the actual objects and participants in view across the handoffs. A page boundary should continue the event: “地址帮助消息到达那台电脑，但同一台电脑可以运行多个接收消息的程序。接下来要确定这次消息交给哪一个。” A link to “ports” adds navigation; this connection supplies the reason to keep reading.

## Walk the case before writing its result

Establish the situation the reader actually has: the tool, available input and relevant prior setup. Follow what each participant receives and changes until you can account for the result. If your own sketch reaches “the system handles it,” resolve that step before polishing prose. Give the next participant enough information to continue; an unexplained token, interface or transaction name cannot do that work.

For an AI example, a chat application receiving pasted text and a business application retrieving company records have different starting conditions. Show which is being used, how the material reaches it and where professional confirmation still occurs. An instruction to “update the record” leaves a real gap if the example has introduced only a chat box. Label invented facts as teaching assumptions.

Keep the claim proportional to this trace. A saved request identifier alone does not establish duplicate prevention: the reader needs the relevant coordinated check and change. If the topic includes crash recovery, explain the needed recovery information and its limits. Supporting implementation detail belongs in optional depth when it does not affect the promised observation.

Now change one condition that could alter the result. Derive the consequence through the same objects and decisions. This can expose a missing premise and establish a stopping point: stop expanding when the reader can derive the promised observation and relevant changed-condition result. Use [explanation-regressions.md](explanation-regressions.md) for a recurring incomplete mechanism; its cases are calibration, not a domain checklist.

## Make the reasoning readable

Read the paragraphs in order and restore omitted objects, actions or causal connections. Define a term when the reader needs the distinction; the glossary cannot carry the paragraph's teaching.

“网络负责路径可达，软件负责业务判断” compresses away the event. A connected explanation is: “浏览器把查看订单的请求交给网络。网络把请求送到网站后，网站还要核对你登录的是哪个账号，才能决定返回哪些订单。”

Likewise, “状态负责持久化，前端反馈不等于后端成功” gives labels. Show the actual change: “你点了收藏，星星先亮起来。网页还要把收藏请求发给网站，网站再把这条记录保存下来。如果请求没有送到，星星虽然亮了，重新打开时收藏仍可能消失。” A figure can show the lit star alongside the unchanged saved record and the incomplete handoff. Boxes containing the abstract sentences add little.

Use the same attention for titles, captions and tooltips. Familiar language should make the professional mechanism easier to inspect. Preserve consequential comparisons and conditions; remove repeated setup, summaries and material unrelated to the core explanation.

## Review the available material

Reconstruct the explanation and a relevant changed-condition result using the actual prose. For a worked operation, try producing the result from the given instructions and raw input. Keep the earliest missing information visible. The optional input-only trial in [reader-task-review.md](reader-task-review.md) helps expose cases where seeing a worked answer would hide this gap. Inspect the model's actual work and distinguish its errors from missing teaching material.

Record consequential choices and remaining uncertainty in the existing editorial decision. A novice label does not by itself require another sample, agent or page certificate.

For legacy staged contracts, conceptual examples can use `exampleContract.pattern: mechanism_trace` with `kind`, `input`, `participants`, `trace`, `output`, `boundary`, `transfer` and corresponding coverage locations. Judgment/creation examples retain the compatible `judgment_revision` pattern. These are existing contract formats, not instructions to create them for ordinary prose. Read [legacy comprehension receipts](legacy-comprehension-records.md) only when renewing that old claim.
