"""Optional novice explanation contracts; receipts are not proof of learning."""

import hashlib
import unicodedata

from kb_reader_probe import validate_probe

EXAMPLE_FIELDS = {
    "judgment_revision": ("input", "firstAttempt", "judgment", "revision", "output", "transfer"),
    "mechanism_trace": ("input", "participants", "trace", "output", "boundary", "transfer"),
}
COMPREHENSION_CHECKS = {
    "causalContinuity", "concreteLanguage", "scenarioApplication", "conceptBoundaries",
}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def review_signature(value):
    """Catch copying with cosmetic punctuation/spacing changes, not semantic similarity."""
    normalized = unicodedata.normalize("NFKC", value) if isinstance(value, str) else ""
    # Keep decimals, operators and slashes: 1.5, 15 and 1/5 are different evidence.
    punctuation = set('，,。!?;:！？；：“”‘’、"')
    return "".join(c.casefold() for c in normalized if not c.isspace() and c not in punctuation)


def review_shortcuts(review, errors, warnings=None):
    checks = review.get("checks", []) if isinstance(review, dict) else []
    if not isinstance(checks, list):
        return
    signatures, rationales = {}, {}
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            continue
        question, answer = review_signature(check.get("question")), review_signature(check.get("expectedExplanation"))
        if question and answer and isinstance(check.get("path"), str):
            key = (check["path"], question, answer)
            signatures.setdefault(key, []).append((index, check.get("dimension")))
        rationale = review_signature(check.get("rationale"))
        if rationale:
            rationales.setdefault(rationale, []).append(index)
    for entries in signatures.values():
        dimensions = {dimension for _, dimension in entries if isinstance(dimension, str)}
        if {"causalContinuity", "scenarioApplication"}.issubset(dimensions):
            issue(errors, "comprehension-relabeled-check", "comprehensionReview.checks",
                  f"Checks {[i for i, _ in entries]} reuse the same question and answer for mechanism and changed-condition review. Actually test the changed input and resulting difference; relabeling is not another test.")
    if warnings is not None:
        for indices in rationales.values():
            if len(indices) >= 3:
                issue(warnings, "comprehension-repeated-rationale", "comprehensionReview.checks",
                      f"Checks {indices} share one rationale. Inspect whether each conclusion has specific support; varied wording alone is not a repair.")


def issue(errors, kind, path, detail):
    errors.append({"kind": kind, "path": str(path), "detail": detail})


def example_fields(example, errors, label, *, modern=True):
    pattern = example.get("pattern", "judgment_revision")
    if not isinstance(pattern, str) or pattern not in EXAMPLE_FIELDS:
        issue(errors, "example-pattern", label, f"Unknown example pattern: {pattern}")
        return ()
    fields = EXAMPLE_FIELDS[pattern]
    if pattern == "judgment_revision" and not modern:
        fields = tuple(f for f in fields if f not in {"firstAttempt", "revision"})
    return fields


def local_file(root, value, errors, label):
    if not nonempty(value):
        issue(errors, "explanation-path", label, "A project file path is required.")
        return None
    candidate = (root / value).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        issue(errors, "explanation-path", label, "File must exist inside the project.")
        return None
    return candidate


def require_promise_review(review, errors, label, *, root=None, pages=()):
    """New editorial approvals need v2; reading historical receipts remains compatible."""
    if isinstance(review, dict) and review.get("schemaVersion", 1) != 2:
        issue(errors, "comprehension-promises-required", label,
              "A new novice explanation approval needs a version 2 promise inventory, causal checks and basis excerpts. Reread the current prose; do not relabel an old receipt.")
    if root is not None and isinstance(review, dict):
        validate_probe(root, review.get("readerProbe"), pages, errors, required=True)


def validate_explanation_design(root, design, units, errors):
    profile = design.get("explanationProfile")
    if profile is None:
        return
    if profile != "novice_mental_model":
        issue(errors, "explanation-profile", "learning-design", f"Unknown profile: {profile}")
        return
    spine = design.get("scenarioSpine")
    if not isinstance(spine, dict):
        issue(errors, "scenario-spine", "learning-design", "The novice profile requires a scenarioSpine.")
        return
    if not nonempty(spine.get("readerQuestion")):
        issue(errors, "scenario-question", "scenarioSpine", "State the whole-process reader question.")
    local_file(root, spine.get("entryPath"), errors, "scenarioSpine.entryPath")
    steps = spine.get("steps")
    if not isinstance(steps, list) or not steps:
        issue(errors, "scenario-steps", "scenarioSpine", "Record concrete steps and their handoffs.")
        steps = []
    for index, step in enumerate(steps):
        label = f"scenarioSpine.steps[{index}]"
        if not isinstance(step, dict):
            issue(errors, "scenario-step", label, "Each step must be an object.")
            continue
        if not isinstance(step.get("unitId"), str) or step.get("unitId") not in units:
            issue(errors, "scenario-unit", label, "Use an existing knowledge unit.")
        for field in ("trigger", "actor", "action", "result", "handoff"):
            if not nonempty(step.get(field)):
                issue(errors, "scenario-step", label, f"Missing {field}.")
    questions = spine.get("everydayQuestions")
    if not isinstance(questions, list) or not questions:
        issue(errors, "scenario-everyday-questions", "scenarioSpine", "Map everyday questions to existing units.")
        questions = []
    for index, item in enumerate(questions):
        label = f"scenarioSpine.everydayQuestions[{index}]"
        if not isinstance(item, dict) or not nonempty(item.get("question")):
            issue(errors, "scenario-everyday-question", label, "A concrete reader question is required.")
            continue
        ids = item.get("unitIds")
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) or i not in units for i in ids):
            issue(errors, "scenario-unit", label, "Map the question to existing knowledge units.")


def validate_comprehension(root, design, verdict, errors, *, required_dimensions=None, warnings=None, strict_shortcuts=True):
    if design.get("explanationProfile") != "novice_mental_model":
        return
    review = verdict.get("comprehensionReview")
    if not isinstance(review, dict):
        issue(errors, "comprehension-review", "pilot-verdict", "The novice profile requires locatable comprehension evidence.")
        return
    review_shortcuts(review, errors if strict_shortcuts else (warnings if warnings is not None else []), warnings)
    validate_probe(root, review.get("readerProbe"), verdict.get("representativePaths") or [], errors)
    version = review.get("schemaVersion", 1)
    if type(version) is not int or version not in {1, 2}:
        issue(errors, "comprehension-version", "comprehensionReview", "Supported receipt versions are 1 (legacy) and 2 (promise coverage).")
    review_type = review.get("reviewType")
    if review_type not in {"editorial", "simulated", "learner_observed"}:
        issue(errors, "comprehension-review-type", "pilot-verdict", "Distinguish editorial/simulated review from observed learners.")
    if review_type == "learner_observed":
        paths = review.get("observationEvidencePaths")
        if not isinstance(paths, list) or not paths:
            issue(errors, "comprehension-observation", "pilot-verdict", "Observed learner claims require actual evidence files.")
        else:
            for path in paths:
                local_file(root, path, errors, "observationEvidencePaths")
    checks = review.get("checks")
    if not isinstance(checks, list):
        checks = []
    found, covered = set(), set()
    representative = set(verdict.get("representativePaths") or [])
    promises = {}
    promise_paths = set()
    if version == 2:
        declared = review.get("promises")
        if not isinstance(declared, list) or not declared:
            issue(errors, "comprehension-promises", "comprehensionReview", "Inventory the consequential explanation promises on the reviewed pages.")
            declared = []
        for index, promise in enumerate(declared):
            label = f"comprehensionReview.promises[{index}]"
            if not isinstance(promise, dict) or not nonempty(promise.get("id")):
                issue(errors, "comprehension-promise", label, "Each promise needs an ID, reviewed path and exact claim.")
                continue
            identity = promise["id"]
            if identity in promises:
                issue(errors, "comprehension-promise-duplicate", label, identity)
                continue
            promises[identity] = promise
            path = promise.get("path")
            if not isinstance(path, str) or path not in representative:
                issue(errors, "comprehension-promise-path", label, "Use the page whose promise is being reviewed.")
            candidate = local_file(root, path, errors, label)
            claim = promise.get("claim")
            if not nonempty(claim):
                issue(errors, "comprehension-promise-claim", label, "Quote the actual promised observation or guarantee.")
            elif candidate and claim not in candidate.read_text(encoding="utf-8", errors="replace"):
                issue(errors, "comprehension-promise-claim", label, "The claim is absent from the current page.")
            elif isinstance(path, str) and path in representative:
                promise_paths.add(path)
        for path in sorted(representative - promise_paths):
            issue(errors, "comprehension-promise-page", path, "Each reviewed page needs its own promise inventory.")
    causally_reviewed = set()
    for index, check in enumerate(checks):
        label = f"comprehensionReview.checks[{index}]"
        if not isinstance(check, dict):
            issue(errors, "comprehension-check", label, "Each check must be an object.")
            continue
        dimension = check.get("dimension")
        if not isinstance(dimension, str) or dimension not in COMPREHENSION_CHECKS:
            issue(errors, "comprehension-dimension", label, "Unknown comprehension dimension.")
        else:
            found.add(dimension)
        if check.get("status") != "pass":
            issue(errors, "comprehension-not-passed", label, "Repair the comprehension gap before scaling.")
        for field in ("question", "expectedExplanation", "excerpt", "rationale"):
            if not nonempty(check.get(field)):
                issue(errors, "comprehension-field", label, f"Missing {field}.")
        value = check.get("path")
        if not isinstance(value, str) or value not in representative:
            issue(errors, "comprehension-pilot-path", label, "Review an actual representative pilot page.")
        candidate = local_file(root, value, errors, label)
        excerpt = check.get("excerpt")
        if candidate and nonempty(excerpt):
            if excerpt not in candidate.read_text(encoding="utf-8", errors="replace"):
                issue(errors, "comprehension-excerpt", label, "Excerpt is absent from the current pilot page.")
            else:
                covered.add(value)
        if version == 2:
            basis = check.get("basisExcerpt")
            if not nonempty(basis) or not nonempty(excerpt) or basis not in excerpt:
                issue(errors, "comprehension-basis-excerpt", label,
                      "Pinpoint the decisive published basis inside this check's exact excerpt; explanatory text only in the answer is not evidence.")
            ids = check.get("promiseIds")
            if not isinstance(ids, list) or not ids or any(not nonempty(i) for i in ids):
                issue(errors, "comprehension-promise-reference", label, "Reference the promises this question actually challenges.")
                ids = []
            for identity in ids:
                promise = promises.get(identity)
                if promise is None:
                    issue(errors, "comprehension-promise-reference", label, f"Unknown promise: {identity}")
                elif promise.get("path") != value:
                    issue(errors, "comprehension-promise-reference", label, "A check cannot establish another page's promise.")
                elif check.get("status") == "pass" and dimension == "causalContinuity":
                    causally_reviewed.add(identity)
    required = COMPREHENSION_CHECKS if required_dimensions is None else required_dimensions
    for dimension in sorted(required - found):
        issue(errors, "comprehension-missing-dimension", "pilot-verdict", dimension)
    for path in sorted(representative - covered):
        issue(errors, "comprehension-page-coverage", path, "Each pilot page needs a locatable comprehension check.")
    if version == 2:
        for identity in sorted(set(promises) - causally_reviewed):
            issue(errors, "comprehension-promise-unreviewed", identity,
                  "Each declared promise needs a passed causal challenge; a changed-condition question alone cannot replace its mechanism.")


def validate_page_comprehension(root, page, errors, warnings=None, *, strict_shortcuts=True):
    """Validate a declared page receipt, without deciding semantic adequacy."""
    review = page.get("comprehensionReview")
    value = page.get("path")
    if not isinstance(review, dict):
        issue(errors, "page-comprehension-review", value, "A page comprehension receipt must be an object.")
        return
    candidate = local_file(root, value, errors, "comprehensionReview.path")
    if candidate:
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if review.get("contentSha256") != digest:
            issue(errors, "page-comprehension-stale", value,
                  "Review the current complete page before recording its SHA-256; unchanged excerpts alone are insufficient.")
    gaps = review.get("unresolvedGaps")
    if not isinstance(gaps, list):
        issue(errors, "page-comprehension-gaps", value, "Record unresolvedGaps explicitly, using [] only after review.")
    elif gaps:
        issue(errors, "page-comprehension-unresolved", value, "Resolve the recorded explanation gaps before claiming readiness.")
    receipt_errors = []
    validate_comprehension(
        root, {"explanationProfile": "novice_mental_model"},
        {"representativePaths": [value], "comprehensionReview": review}, receipt_errors,
        required_dimensions={"causalContinuity", "scenarioApplication"},
        warnings=warnings,
        strict_shortcuts=strict_shortcuts,
    )
    for error in receipt_errors:
        # Reuse the pilot check format while keeping diagnostics page-specific.
        error["path"] = f"{value}: {error['path']}"
        error["detail"] = error["detail"].replace("pilot", "reviewed")
        errors.append(error)
