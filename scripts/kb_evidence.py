"""Optional quantitative contracts; checks declarations, not scientific truth."""

import math


def issue(items, kind, label, detail):
    items.append({"kind": kind, "path": str(label), "detail": detail})


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return (isinstance(value, int) and not isinstance(value, bool)) or (isinstance(value, float) and math.isfinite(value))


def check_measurement(value, errors, warnings, label):
    if not isinstance(value, dict):
        issue(errors, "measurement-shape", label, "measurement must be an object; omit it for non-quantitative claims.")
        return
    for key in ("unit", "basis", "population", "period", "analysisLevel"):
        if not text(value.get(key)):
            issue(errors, "measurement-context", label, f"Missing {key}.")
    if not number(value.get("value")):
        issue(errors, "measurement-value", label, "Use a finite numeric value, including a real zero or negative value; missing is not zero.")
    kinds = {"proportion", "relative-change", "percentage-point-change", "count", "continuous"}
    if not text(value.get("measureKind")) or value["measureKind"] not in kinds:
        issue(errors, "measurement-kind", label, "Declare proportion, relative-change, percentage-point-change, count, or continuous.")
    if value.get("measureKind") == "proportion":
        maximum = {"%": 100, "fraction": 1}.get(value.get("unit")) if text(value.get("unit")) else None
        if maximum is None or (number(value.get("value")) and not 0 <= value["value"] <= maximum):
            issue(errors, "measurement-proportion", label, "A proportion uses % (0–100) or fraction (0–1); growth is a relative-change, not a proportion.")
    if value.get("measureKind") == "count" and number(value.get("value")) and (value["value"] < 0 or value["value"] % 1):
        issue(errors, "measurement-count", label, "A raw count is a non-negative integer; use continuous for estimates or weighted values.")
    sample = value.get("sampleSize")
    if not isinstance(sample, dict):
        issue(errors, "measurement-sample", label, "Declare sampleSize status: known, not_reported, or not_applicable.")
    elif sample.get("status") == "known":
        n = sample.get("value")
        if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
            issue(errors, "measurement-sample", label, "A known sample size is a positive integer for this result, not the whole report.")
    elif text(sample.get("status")) and sample["status"] in {"not_reported", "not_applicable"}:
        if not text(sample.get("reason")):
            issue(errors, "measurement-sample", label, "Explain missing/inapplicable sample size; do not invent N for census counts or prices.")
        if "value" in sample:
            issue(errors, "measurement-sample", label, "Unknown/inapplicable sample size must not carry a numeric value.")
    else:
        issue(errors, "measurement-sample", label, "Unsupported sampleSize status.")
    if not text(value.get("citationMode")) or value["citationMode"] not in {"direct", "secondary"}:
        issue(errors, "measurement-citation", label, "Distinguish a directly inspected source from a secondary citation.")
    if value.get("citationMode") == "secondary" and not text(value.get("originalSource")):
        issue(errors, "measurement-citation", label, "Identify the reported original source, or explicitly say it is unidentified.")
    review = value.get("verification")
    if not isinstance(review, dict) or not text(review.get("status")) or review["status"] not in {"verified", "unverified"}:
        issue(errors, "measurement-verification", label, "Declare verification status; confidence is not a verification record.")
    elif review["status"] == "verified":
        for key in ("reviewer", "locator", "basis"):
            if not text(review.get(key)):
                issue(errors, "measurement-verification", label, f"A verified value needs {key} from the actual review.")
    else:
        if not text(review.get("reason")):
            issue(errors, "measurement-verification", label, "Explain what remains unverified.")
        issue(warnings, "measurement-unverified", label, "Do not present this value as a verified empirical finding.")


def check_comparisons(unit, measurements, errors, label):
    comparisons = unit.get("comparisons", [])
    if not isinstance(comparisons, list):
        issue(errors, "comparison-shape", label, "comparisons must be a list.")
        return
    for index, comparison in enumerate(comparisons):
        where = f"{label}.comparisons[{index}]"
        if not isinstance(comparison, dict):
            issue(errors, "comparison-shape", where, "Expected a comparison object.")
            continue
        refs = comparison.get("claimRefs")
        if not isinstance(refs, list) or any(not text(ref) for ref in refs) or len(set(refs)) < 2:
            issue(errors, "comparison-refs", where, "Compare at least two distinct source#claim references.")
            continue
        values = []
        for ref in refs:
            if ref not in (unit.get("sourceRefs") or []) or not isinstance(measurements.get(ref), dict):
                issue(errors, "comparison-refs", where, f"No declared measurement in this unit's sourceRefs: {ref}")
            else:
                values.append(measurements[ref])
        for key in ("conclusion", "remainingLimitations"):
            if not text(comparison.get(key)):
                issue(errors, "comparison-context", where, f"Missing {key}.")
        notes = comparison.get("alignmentNotes", {})
        if not isinstance(notes, dict):
            issue(errors, "comparison-context", where, "alignmentNotes must be an object.")
            notes = {}
        for field in ("unit", "measureKind", "basis", "population", "period", "analysisLevel"):
            declared = [item.get(field) for item in values]
            if declared and any(item != declared[0] for item in declared[1:]) and not text(notes.get(field)):
                issue(errors, "comparison-alignment", where, f"Explain the difference in {field}; alignment notes do not by themselves establish comparability.")
