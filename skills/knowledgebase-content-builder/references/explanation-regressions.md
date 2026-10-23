# Calibrating Explanation Completeness

These are fictional editorial comparisons distilled from repeated beginner-content repairs. They test how to explain a promised observation, not whether particular keywords appear. Select the family relevant to a pilot or repair. Keep the actual product's source claims and boundaries; do not add these examples, parameters or sections to every page.

## A decision needs information and a rule

**Incomplete:** “If the cached copy is valid, reuse it; otherwise update it.” “The receiver detects missing data and retransmits.” Both repeat the promised behavior without explaining how it becomes known.

**Sufficient direction:** A copy is stored with a reuse deadline. At 9:03 the program compares the time with 9:05 and may reuse it; a change at 9:02 can therefore remain unseen. For a transfer, the receiver has positions 1–100 and 201–300, so it can report a gap beginning at 101; the arriving 101–200 fills that gap, while the same range arriving again is a duplicate. The feedback and retransmission are performed by their respective participants, not by an unnamed network.

**Challenge:** What exact value or evidence distinguishes the two branches? What happens when the original changes before the deadline, or the acknowledgment is late? Stop before teaching a cache implementation or all TCP fields unless the page promises those details.

## A trigger needs a path to execution

**Incomplete:** “Clicking runs the rules.” “The model calls the reading tool.” There is no stated association between the visible action and an executable capability.

**Sufficient direction:** The page has associated its favorite button's click with a handler. The browser invokes that code, which takes the current article ID and prepares a request. For an application-defined model tool, the model returns a registered tool name and article ID; the host matches the name, validates the request, executes the reading program and returns its actual result.

**Challenge:** If the handler was never registered or the tool name is unavailable, what starts? Where does article A enter the actual request? Stop at this bridge; do not add DOM internals or a full tool protocol tutorial.

## An association must survive the relevant change

**Incomplete:** “When the result arrives, display it.” “The exit remembers which device should receive the reply.” “Run two copies of the same server to share the load.” The missing association changes the result.

**Sufficient direction:** The request retains article A's identity. When its result arrives after the user moved to B, the page stores it under A and checks the current article before displaying. A shared exit records distinct outward connection ports for internal A and B and reverses the mapping on the reply. Two program copies need an arrangement for common records; the same code does not copy one process's new memory into the other.

**Challenge:** Change the current article, let internal port numbers coincide, or send the next query to another program copy. Which stored association still identifies the right object? Stop before surveying every possible dispatch or replication strategy.

## A first step needs an available starting point

**Incomplete:** “The device is automatically assigned an address.” “Ask DNS where the website is.” “Verify the login marker.” A newcomer cannot infer who has the first address or what the marker refers to.

**Sufficient direction:** In a specified IPv4 example, a new device asks locally for a configuration service, receives an offer, requests it and gets confirmation plus a lease record. DNS can start from an already configured resolver, whose root hints give known addresses. In a server-stored session example, login creates a hard-to-guess marker linked to an account, expiry and revocation state; later requests look up that association.

**Challenge:** With no old record, where can this participant send the first request? With an expired or revoked record, what changes? Not every page needs a cold-start lesson: use a declared prerequisite when the current promise begins after setup.

## A guarantee needs an enforcement point and a bounded scope

**Incomplete:** “Give the request an ID so retries cannot duplicate it.” “Record migration progress so a restart continues safely.” These labels do not coordinate simultaneous requests or a crash between actions.

**Sufficient direction:** A service saves the account's operation ID, input and task association under a uniqueness constraint in one transaction. A competing request uses the existing task rather than creating another. A migration reuses a user's unique default folder and updates only records whose folder is still empty at write time; a repeated batch skips already-filled records even if progress recording was interrupted.

**Challenge:** Both requests first observe “absent”; execution stops after data is committed but before progress is recorded; the remote model or payment service has already acted but its reply is lost. Explain which result the local coordination establishes and which still needs the other participant's cooperation. Do not promise end-to-end exactly-once effects from a local unique record.

## A capability label does not replace the relevant transformation

**Incomplete:** “TLS encrypts the data.” “The model generates from context.” “A private-network tool arranges connectivity.” Whether this is sufficient depends on what the page promises to explain.

**Sufficient direction:** For a page asking how a transit observer cannot directly read content, distinguish public exchange values from retained secrets and the resulting communication keys, and explain endpoint access. For a page asking why fluent text can add unsupported facts, explain the relevant text-generation process and why plausible continuation is not a fact lookup. For a remote-access page that already taught inbound NAT limits, show the two devices' outbound relay connections and how data is handed across them.

**Challenge:** Can the reader derive the stated observation without treating the capability's name as an answer? Explain the transformation needed here; leave algorithm derivations and unrelated implementation detail optional. A short glossary definition or a page that explicitly assumes a protected connection need not become a cryptography lesson.

## Use the comparisons as a review

Try an unshown case from the target domain after revising a rule. Assess missing teaching, false guarantees and unnecessary expansion separately. Include a complete concise example and a reference entry so the reviewer cannot “succeed” by requesting more detail everywhere. Save the actual verdict, rationale and repair; distinguish same-editor calibration from independent review or observed learners.

Mechanical tests verify receipt versions, exact excerpts, hashes and declared promise coverage. They cannot establish that an excerpt explains its claim. A structurally valid receipt for “the system handles it” can still fail the editorial test above; a maintained regression test should preserve that distinction rather than introducing keyword-based semantic approval.
