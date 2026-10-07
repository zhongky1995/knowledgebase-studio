"""Optional novice explanation contracts; receipts are not proof of learning."""

EXAMPLE_FIELDS = {
    "judgment_revision": ("input", "firstAttempt", "judgment", "revision", "output", "transfer"),
    "mechanism_trace": ("input", "participants", "trace", "output", "boundary", "transfer"),
}
COMPREHENSION_CHECKS = {
    "causalContinuity", "concreteLanguage", "scenarioApplication", "conceptBoundaries",
}


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


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


def validate_comprehension(root, design, verdict, errors):
    if design.get("explanationProfile") != "novice_mental_model":
        return
    review = verdict.get("comprehensionReview")
    if not isinstance(review, dict):
        issue(errors, "comprehension-review", "pilot-verdict", "The novice profile requires locatable comprehension evidence.")
        return
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
    for dimension in sorted(COMPREHENSION_CHECKS - found):
        issue(errors, "comprehension-missing-dimension", "pilot-verdict", dimension)
    for path in sorted(representative - covered):
        issue(errors, "comprehension-page-coverage", path, "Each pilot page needs a locatable comprehension check.")
