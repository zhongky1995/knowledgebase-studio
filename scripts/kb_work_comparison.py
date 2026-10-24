#!/usr/bin/env python3
"""Compute and render a same-task workload comparison from owning page coverage."""

import argparse
import json
import math
import re
from pathlib import Path


METHODS = ("manual", "software", "ai")
HANDLERS = {"human": "人工", "software": "程序处理，人工投入", "ai": "AI处理，人工投入", "not_needed": "无需此项"}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def compute(model):
    if not isinstance(model, dict) or model.get("schemaVersion") != 1:
        raise ValueError("workComparison requires schemaVersion 1.")
    if not text(model.get("id")) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", model["id"]):
        raise ValueError("Use a stable lowercase comparison id.")
    for key in ("basis", "period", "limitations"):
        if not text(model.get(key)):
            raise ValueError(f"State {key}; a calculation does not establish observed savings.")
    if model.get("basisKind") not in {"teaching_assumption", "measured"}:
        raise ValueError("Distinguish teaching_assumption from measured inputs.")
    if model.get("basisKind") == "measured" and (not isinstance(model.get("measurementRefs"), dict) or not model["measurementRefs"]):
        raise ValueError("Measured inputs need a measurementRefs mapping from each numeric input to an existing source#claim.")
    volume = model.get("volume")
    if not number(volume) or volume <= 0:
        raise ValueError("volume must be positive; zero work cannot amortize maintenance.")
    activities = model.get("activities")
    if not isinstance(activities, list) or not activities:
        raise ValueError("List the same task's original and newly introduced activities.")
    identities = []
    for row in activities:
        if not isinstance(row, dict) or not text(row.get("id")) or not text(row.get("label")):
            raise ValueError("Each activity needs an id and concrete label.")
        if row["id"] in identities:
            raise ValueError("Duplicate activity id.")
        identities.append(row["id"])
    methods = model.get("methods")
    if not isinstance(methods, list) or len(methods) != 3 or any(not isinstance(m, dict) for m in methods):
        raise ValueError("Compare manual, software-only and AI approaches to the same task.")
    if {m.get("id") for m in methods} != set(METHODS):
        raise ValueError("Method ids must be manual, software and ai; separate ordinary software's contribution.")
    totals, allocations = {}, {}
    for method in methods:
        if not text(method.get("label")):
            raise ValueError("Each method needs a reader-facing label.")
        rows = method.get("allocations")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError("Method allocations must be records.")
        ids = [row.get("activityId") for row in rows]
        if len(ids) != len(set(ids)) or set(ids) != set(identities):
            raise ValueError("Every method must account for every activity, including work removed or added; omission is not zero.")
        if not number(method.get("fixedHumanMinutes")):
            raise ValueError("Declare non-negative fixedHumanMinutes for the same period.")
        for row in rows:
            if row.get("handler") not in HANDLERS or not number(row.get("humanMinutes")):
                raise ValueError("Each allocation needs a handler and finite non-negative humanMinutes.")
            if row["handler"] == "not_needed" and (row["humanMinutes"] != 0 or not text(row.get("reason"))):
                raise ValueError("An absent activity needs zero minutes and a reason; identify where work moved.")
            if method["id"] != "ai" and row["handler"] == "ai":
                raise ValueError("The non-AI baseline cannot contain AI work.")
        allocations[method["id"]] = {row["activityId"]: row for row in rows}
        try:
            per_task = math.fsum(row["humanMinutes"] for row in rows)
        except OverflowError as error:
            raise ValueError("Human-work totals exceed finite numeric range.") from error
        totals[method["id"]] = {"variableMinutes": per_task, "fixedMinutes": method["fixedHumanMinutes"],
                                 "perTaskMinutes": per_task + method["fixedHumanMinutes"] / volume}
        if not number(totals[method["id"]]["perTaskMinutes"]):
            raise ValueError("Human-work totals must be finite.")
    sensitivities = model.get("sensitivityVolumes", [])
    if not isinstance(sensitivities, list) or any(not number(v) or v <= 0 for v in sensitivities):
        raise ValueError("sensitivityVolumes must contain positive task counts.")
    sensitivity = [{"volume": v, "totals": {k: t["variableMinutes"] + t["fixedMinutes"] / v for k, t in totals.items()}}
                   for v in sensitivities]
    if any(not number(value) for row in sensitivity for value in row["totals"].values()):
        raise ValueError("Sensitivity totals must be finite.")
    return {"totals": totals, "allocations": allocations,
            "overallSavingMinutes": totals["manual"]["perTaskMinutes"] - totals["ai"]["perTaskMinutes"],
            "incrementalAiSavingMinutes": totals["software"]["perTaskMinutes"] - totals["ai"]["perTaskMinutes"],
            "sensitivity": sensitivity}


def display(value):
    return f"{value:.4f}".rstrip("0").rstrip(".")


def cell(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def change_text(saving):
    if abs(saving) < 1e-9:
        return "人工作量没有变化"
    return f'{"减少" if saving > 0 else "增加"} {display(abs(saving))} 分钟'


def render(model):
    result = compute(model)
    methods = {m["id"]: m for m in model["methods"]}
    start, end = markers(model)
    kind = "教学假设，非实测收益" if model["basisKind"] == "teaching_assumption" else "据所列测量计算；数据真实性另核"
    basis = cell(model["basis"]).rstrip("。.!?！？；;")
    lines = [start, f'> {kind}。比较同一任务：{basis}。以下单位均为人工作业分钟，包含核对与纠错。', "",
             "| 工作 | " + " | ".join(cell(methods[k]["label"]) for k in METHODS) + " |",
             "| --- | --- | --- | --- |"]
    for activity in model["activities"]:
        values = []
        for key in METHODS:
            row = result["allocations"][key][activity["id"]]
            values.append(f'{HANDLERS[row["handler"]]}：{display(row["humanMinutes"])}' + (f'（{cell(row["reason"])}）' if row.get("reason") else ""))
        lines.append(f'| {cell(activity["label"])} | ' + " | ".join(values) + " |")
    lines.extend(["| 每笔固定维护分摊 | " + " | ".join(display(result["totals"][k]["fixedMinutes"] / model["volume"]) for k in METHODS) + " |",
                  "| 每笔人工作量合计 | " + " | ".join(display(result["totals"][k]["perTaskMinutes"]) for k in METHODS) + " |", "",
                  f'按每{cell(model["period"])} {display(model["volume"])} 笔分摊固定维护。相对原做法，AI 方案每笔{change_text(result["overallSavingMinutes"])}；相对普通软件方案，每笔{change_text(result["incrementalAiSavingMinutes"])}。'])
    for row in result["sensitivity"]:
        lines.append(f'若同一期间只有 {display(row["volume"])} 笔，三种做法每笔分别为 ' + "、".join(display(row["totals"][k]) for k in METHODS) + " 分钟。")
    lines.extend([f'比较限制：{cell(model["limitations"])}', end])
    return "\n".join(lines)


def markers(model):
    identity = model.get("id", "")
    return f"<!-- kb-work-comparison:{identity} -->", f"<!-- /kb-work-comparison:{identity} -->"


def block_span(page_text, model):
    start, end = markers(model)
    if page_text.count(start) != 1 or page_text.count(end) != 1:
        raise ValueError("Place exactly one matching comparison start/end marker in the owning page.")
    left = page_text.index(start)
    right = page_text.index(end)
    if right <= left:
        raise ValueError("Comparison markers are out of order.")
    return left, right + len(end)


def validate_work_comparison(root, page, errors, measurements=None):
    example = page.get("workedExample") or {}
    if not isinstance(example, dict) or "workComparison" not in example:
        return
    model = example["workComparison"]
    try:
        expected = render(model)
        path = (root / page["path"]).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError("Comparison owner must be a file inside the knowledge base.")
        actual = path.read_text(encoding="utf-8")
        left, right = block_span(actual, model)
        if actual[left:right] != expected:
            errors.append({"kind": "work-comparison-stale", "path": page["path"], "detail": "The published comparison differs from its executable data. Re-render the marked block; do not manually correct only the total."})
        if model["basisKind"] == "measured" and measurements is not None:
            values = {"volume": (model["volume"], {"tasks", "笔", "count"})}
            for method in model["methods"]:
                values[f'{method["id"]}.fixedHumanMinutes'] = (method["fixedHumanMinutes"], {"minutes", "分钟"})
                for row in method["allocations"]:
                    if row["handler"] != "not_needed":
                        values[f'{method["id"]}.{row["activityId"]}.humanMinutes'] = (row["humanMinutes"], {"minutes", "分钟"})
            for key, (value, allowed_units) in values.items():
                ref = model["measurementRefs"].get(key)
                measurement = measurements.get(ref)
                if not isinstance(measurement, dict) or (measurement.get("verification") or {}).get("status") != "verified":
                    raise ValueError(f"Measured input {key} needs an existing verified source measurement: {ref}")
                if not number(measurement.get("value")) or not math.isclose(value, measurement["value"], rel_tol=1e-9, abs_tol=1e-9) or measurement.get("unit") not in allowed_units:
                    raise ValueError(f"Measured input {key} differs from its source value/unit; use aligned minute/task measurements.")
    except (ValueError, TypeError, KeyError, OSError) as error:
        errors.append({"kind": "work-comparison-invalid", "path": str(page.get("path")), "detail": str(error)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root")
    parser.add_argument("--page", required=True)
    parser.add_argument("--write", action="store_true", help="Replace only the existing marked comparison block in its owner")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    try:
        coverage = json.loads((root / "_kb-control/content-coverage.json").read_text(encoding="utf-8"))
        page = next((p for p in coverage.get("pages", []) if isinstance(p, dict) and p.get("path") == args.page), None)
        if page is None:
            raise ValueError("Select an existing covered page.")
        model = page.get("workedExample", {}).get("workComparison")
        block = render(model)
        if args.write:
            path = (root / args.page).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError("Owner must be a project file.")
            source = path.read_text(encoding="utf-8")
            left, right = block_span(source, model)
            path.write_text(source[:left] + block + source[right:], encoding="utf-8")
        print(block)
    except (ValueError, TypeError, KeyError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
