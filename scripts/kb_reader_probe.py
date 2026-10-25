#!/usr/bin/env python3
"""Prepare answer-free reader-review material. Integrity is not comprehension."""

import argparse
import hashlib
import html
import json
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


JOBS = {
    "understand": "沿同一个具体事件解释参与者收到什么、依据什么行动、怎样产生结果。再改变一个会影响结果的条件，从正文推导差异。",
    "perform": "只用正文和已列出的前提完成一次本页任务，交出完成后的实际样例。逐步指出材料、动作、决定和核对依据；遇到缺项就记录卡点，不替正文补步骤。",
    "judge": "用本页给定的同一组材料作出选择，列出支持选择的依据。改变一项决定性条件后重新判断；若声称 AI 带来价值，区分人工、普通软件和 AI 的贡献及新增负担。",
    "retrieve": "提出一次本页应能回答的具体查用问题，给出可直接使用的答案及适用条件，指出准确位置。缺少必要定义、单位或范围就记录缺口。",
}
PROBE_DIR = Path("_kb-control/reader-probes")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_object(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def file_inside(root, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("An explicit project file path is required.")
    candidate = (root / value).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise ValueError(f"File must exist inside the project: {value}")
    return candidate


def unit_context(row, units):
    identities = row.get("knowledgeUnitIds", [])
    if not isinstance(identities, list) or any(not isinstance(v, str) for v in identities):
        raise ValueError("knowledgeUnitIds must be a list of unit IDs.")
    pending, seen, context = list(identities), set(), []
    while pending:
        identity = pending.pop()
        if identity in seen:
            continue
        seen.add(identity)
        unit = units.get(identity, {})
        dependencies = unit.get("dependencies", [])
        if not isinstance(dependencies, list) or any(not isinstance(v, str) for v in dependencies):
            raise ValueError("Knowledge dependencies must be unit IDs.")
        context.append({"id": identity, "canonicalOwner": unit.get("canonicalOwner"), "dependencies": sorted(dependencies)})
        pending.extend(dependencies)
    return {"knowledgeUnitIds": sorted(identities), "units": sorted(context, key=lambda v: v["id"])}


def contract_context(root):
    """Capture reader-facing intent, not update bookkeeping that would widen scope."""
    path = root / "_kb-control/project-contract.yaml"
    if not path.is_file():
        return {}
    fields = {"audiences", "reader_moment", "product_posture", "first_success", "exercise_policy"}
    context, active = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if match:
            active = match[1] if match[1] in fields else None
            if active:
                context[active] = [match[2].strip()]
        elif active and line[:1].isspace():
            context[active].append(line.strip())
        else:
            active = None
    return context


def late_section(text):
    """Select a later section mechanically; the reviewer still judges significance."""
    lines = text.splitlines()
    headings, fenced = [], False
    for index, line in enumerate(lines):
        if re.match(r"^\s*(```|~~~)", line):
            fenced = not fenced
        if not fenced and re.match(r"^#{2,6}\s+\S", line):
            headings.append(index)
    if headings:
        # Do not let a strong opening certify an unexamined later section.
        selected = headings[(len(headings) * 2) // 3]
        end = next((i for i in headings if i > selected), len(lines))
        return {"line": selected + 1, "text": "\n".join(lines[selected:end]).strip()}
    start = len(lines) // 2
    return {"line": start + 1, "text": "\n".join(lines[start:]).strip()}


def sanitized_svg(data, *, mask=False):
    """Keep geometry, remove active content; masking does not identify outlined glyphs."""
    tree = ET.fromstring(data)
    if tree.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("Not an SVG document")
    removed = {"script", "foreignObject"} | ({"text", "tspan", "textPath"} if mask else set())
    for parent in list(tree.iter()):
        for child in list(parent):
            tag = child.tag.rsplit("}", 1)[-1] if isinstance(child.tag, str) else ""
            if tag in removed:
                parent.remove(child)
    for node in tree.iter():
        for key, value in list(node.attrib.items()):
            local = key.rsplit("}", 1)[-1].lower()
            if local.startswith("on") or (local in {"href", "src"} and not value.startswith("#")):
                del node.attrib[key]
            elif local == "style" and unsafe_css(value):
                del node.attrib[key]
        if node.tag.rsplit("}", 1)[-1] == "style" and node.text:
            if unsafe_css(node.text):
                node.text = ""
    return ET.tostring(tree, encoding="utf-8", xml_declaration=True)


def unsafe_css(value):
    urls = re.findall(r"url\(\s*([^)]*)\)", value, re.I)
    return "@import" in value.lower() or any(not url.strip().strip("\"'").startswith("#") for url in urls)


def prepare(root, pages, *, job=None, default_job=None, include_prerequisites=True):
    root = Path(root).resolve()
    if job is not None and job not in JOBS:
        raise ValueError("Choose understand, perform, judge or retrieve.")
    if default_job is not None and default_job not in JOBS:
        raise ValueError('Unknown default reader job.')
    if not pages:
        raise ValueError("Select the actual reader-facing pages.")
    control = root / "_kb-control"
    coverage = read_object(control / "content-coverage.json") if (control / "content-coverage.json").is_file() else {}
    by_path = {p.get("path"): p for p in coverage.get("pages", []) if isinstance(p, dict)}
    visuals = read_object(control / "visual-explanations.json") if (control / "visual-explanations.json").is_file() else {}
    model = read_object(control / "knowledge-model.json") if (control / "knowledge-model.json").is_file() else {}
    units = {u.get("id"): u for u in model.get("units", []) if isinstance(u, dict)}
    records, inputs, warnings, figures = [], {}, [], []
    texts = {}

    def include(path):
        relative = str(path.relative_to(root))
        inputs[relative] = sha(path.read_bytes())
        return relative

    for value in dict.fromkeys(pages):
        page = file_inside(root, value)
        if page.suffix.lower() not in {".md", ".markdown"}:
            raise ValueError("Reader probes currently support final Markdown, not an HTML source dump.")
        relative = include(page)
        text = page.read_text(encoding="utf-8")
        row = by_path.get(relative, {})
        selected_job = job or row.get("readerJob") or default_job
        if selected_job not in JOBS:
            raise ValueError(f"State this page's readerJob in coverage or pass --job: {relative}")
        if job and row.get("readerJob") and job != row["readerJob"]:
            raise ValueError("Update the owning readerJob before reviewing a different promise.")
        model_context = unit_context(row, units)
        prereqs, pending, seen = [], list(row.get("knowledgeUnitIds", [])) if include_prerequisites else [], set()
        while pending:
            identity = pending.pop()
            if identity in seen:
                continue
            seen.add(identity)
            unit = units.get(identity, {})
            pending.extend(unit.get("dependencies", []))
            if identity not in row.get("knowledgeUnitIds", []):
                owner = unit.get("canonicalOwner")
                if owner and owner != relative:
                    prerequisite = file_inside(root, owner)
                    owner = include(prerequisite)
                    if owner not in prereqs:
                        prereqs.append(owner)
                        texts[owner] = prerequisite.read_text(encoding="utf-8")
        texts[relative] = text
        records.append({"path": relative, "job": selected_job, "title": next((l.lstrip("# ") for l in text.splitlines() if l.startswith("# ")), page.stem),
                        "declaredJob": row.get("readerJob"),
                        "primaryQuestion": row.get("primaryQuestion"), "readerChange": row.get("readerChange"),
                        "modelContext": model_context, "lateSection": late_section(text), "prerequisitePaths": prereqs})
        assets = []
        for item in visuals.get("items", []):
            if isinstance(item, dict) and item.get("pagePath") == relative:
                assets.extend(item.get(field) for field in ("assetPath", "fallbackPath") if item.get(field))
                hashes = (item.get("designReview") or {}).get("assetSha256", {})
                if isinstance(hashes, dict):
                    assets.extend(hashes)
        # Markdown-only samples need no manifest to inspect their actual figures.
        assets.extend(str((page.parent / m).relative_to(root)) for m in
                      re.findall(r"!\[[^\]]*\]\(<?([^\s)>]+)>?(?:\s+[^)]*)?\)", text)
                      if not re.match(r"[a-z]+:|^/|^#", m, re.I))
        for asset in dict.fromkeys(value for value in assets if value):
            try:
                candidate = file_inside(root, asset)
                include(candidate)
                if candidate.suffix.lower() in {".svg", ".png", ".jpg", ".jpeg", ".webp"}:
                    figures.append({"pagePath": relative, "path": str(candidate.relative_to(root))})
                else:
                    warnings.append(f"Inspect unsupported media in the delivered app: {asset}")
            except ValueError as error:
                raise ValueError(f"Cannot prepare the declared local figure: {asset}: {error}") from error

    parent = (root / PROBE_DIR).resolve()
    if not parent.is_relative_to(root):
        raise ValueError("Reader-probe directory must stay inside the project.")
    parent.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix="probe-", dir=parent))
    try:
        cards = []
        for index, figure in enumerate(figures):
            asset = file_inside(root, figure["path"])
            original = f"figure-{index + 1}{asset.suffix.lower()}"
            note = ""
            if asset.suffix.lower() == ".svg":
                if any(node.tag.rsplit("}", 1)[-1] == "foreignObject" for node in ET.fromstring(asset.read_bytes()).iter()):
                    note = "安全预览移除了 foreignObject 内容；本图须在最终应用中核对原始显示，不能以此预览判定解释效果。"
                    warnings.append(f'{figure["path"]}: {note}')
                (output / original).write_bytes(sanitized_svg(asset.read_bytes()))
                masked = f"figure-{index + 1}-masked.svg"
                (output / masked).write_bytes(sanitized_svg(asset.read_bytes(), mask=True))
                figure["maskedPath"] = masked
                masked_html = f'<img src="{masked}" alt="去字后的关系与变化"><details><summary>放大查看去字版</summary><div class="native"><img src="{masked}" alt="放大的去字版"></div></details>'
            else:
                shutil.copyfile(asset, output / original)
                masked_html = "<p>此格式未自动去字，请在原图中实际检查视觉关系。</p>"
            figure["originalPath"] = original
            cards.append(f'<section><h2>{html.escape(figure["path"])}</h2><p>{html.escape(note)}</p><div class="pair"><figure><figcaption>原图</figcaption><img src="{original}" alt="原图"><details><summary>放大查看原图</summary><div class="native"><img src="{original}" alt="放大的原图"></div></details></figure><figure><figcaption>去字版</figcaption>{masked_html}</figure></div></section>')
        sheet = '<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>图解关系复核</title><style>body{font:16px sans-serif;max-width:1500px;margin:24px auto;padding:0 16px;color:#183c35}.pair{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px}figure{margin:0;min-width:0}img{width:100%;height:auto}.native{max-width:100%;overflow:auto}.native img{width:auto;min-width:720px;max-width:none}summary{cursor:pointer;padding:12px 0}section{margin-bottom:48px}h2{overflow-wrap:anywhere}@media(max-width:700px){.pair{grid-template-columns:minmax(0,1fr)}}</style><h1>图解关系复核</h1><p>去字后能看出哪些对象、对应、传递、数量差或状态变化？恢复文字后是否准确？宽图可展开后横向查看。去字失败或变空白是审读线索，不自动判定图片不合格。转曲文字和位图中的文字不会自动消失。</p>' + "\n".join(cards) + '</html>'
        (output / "figures.html").write_text(sheet, encoding="utf-8")
        reader = ["# 读者任务复核", "\n材料来自当前读者正文，不含作者的审核问题、答案或通过结论。若审读者已看过制作上下文，不得声称独立盲测。\n"]
        for record in records:
            reader.extend([f'## {record["title"]}', f'正文：{record["path"]}', f'本页承诺：{record["primaryQuestion"] or record["title"]}',
                           JOBS[record["job"]], "先交出你的解释、选择或完成样例，并列出正文无法支持的部分；然后才对照作者承诺与审核答案。",
                           f'必须另外挑战后部片段（第 {record["lateSection"]["line"]} 行起）：\n\n{record["lateSection"]["text"]}',
                           "若有图：打开 figures.html，分别检查原图与去字版。判断需要的关系是否由空间、映射、分支、前后状态或比例承担，而非仅由长文字承担。"])
        for path, text in texts.items():
            reader.extend([f"## 完整正文：{path}", "\n".join(f"{i:04d} | {line}" for i, line in enumerate(text.splitlines(), 1))])
        (output / "reader.md").write_text("\n\n".join(reader) + "\n", encoding="utf-8")
        packet = {"schemaVersion": 1, "kind": "reader-probe", "pages": records, "inputDigests": inputs,
                  "contractContext": contract_context(root),
                  "figures": figures, "warnings": warnings,
                  "materialDigests": {str(p.relative_to(output)): sha(p.read_bytes()) for p in sorted(output.iterdir())},
                  "limitation": "Prepared editorial material only. No review has been performed and no learning effectiveness is established."}
        packet_path = output / "packet.json"
        packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"status": "prepared", "validationKind": "review-material-preparation", "readiness": "not_assessed",
                "readerProbe": {"packetPath": str(packet_path.relative_to(root)), "packetSha256": sha(packet_path.read_bytes())},
                "readerPath": str((output / "reader.md").relative_to(root)), "figureSheetPath": str((output / "figures.html").relative_to(root)), "warnings": warnings}
    except Exception:
        shutil.rmtree(output)
        raise


def validate_probe(root, reference, pages, errors, *, required=False):
    """Validate current review material, never infer that it was read or understood."""
    def fail(kind, detail):
        errors.append({"kind": kind, "path": "readerProbe", "detail": detail})

    root = Path(root).resolve()
    if reference is None and not required:
        return
    if not isinstance(reference, dict):
        fail("reader-probe-required", "Prepare current answer-free material with kb_reader_probe.py; recording a pass is a separate editorial task.")
        return
    try:
        path = file_inside(root, reference.get("packetPath"))
        if not path.is_relative_to((root / PROBE_DIR).resolve()):
            raise ValueError("Use the tool's internal reader-probes directory.")
        if reference.get("packetSha256") != sha(path.read_bytes()):
            fail("reader-probe-changed", "The prepared packet was changed; regenerate instead of renewing its hash.")
        packet = read_object(path)
        if packet.get("schemaVersion") != 1 or packet.get("kind") != "reader-probe":
            raise ValueError("Unknown reader-probe format.")
        records = packet.get("pages")
        if not isinstance(records, list) or not records or any(not isinstance(p, dict) or p.get("job") not in JOBS for p in records):
            raise ValueError("A prepared packet needs explicit page jobs.")
        paths = {record.get("path") for record in records}
        if not set(pages).issubset(paths):
            fail("reader-probe-coverage", "The prepared material does not include all pages being approved.")
        inputs = packet.get("inputDigests")
        if not isinstance(inputs, dict) or not paths.issubset(inputs):
            raise ValueError("Prepared material must fingerprint every reviewed page.")
        for value, digest in inputs.items():
            candidate = file_inside(root, value)
            if sha(candidate.read_bytes()) != digest:
                fail("reader-probe-stale", f"Published input changed: {value}")
        materials = packet.get("materialDigests")
        if not isinstance(materials, dict) or not {"reader.md", "figures.html"}.issubset(materials):
            raise ValueError("The actual reader material and figure sheet are required.")
        for value, digest in materials.items():
            candidate = file_inside(path.parent, value)
            if sha(candidate.read_bytes()) != digest:
                fail("reader-probe-material-changed", f"Prepared review material changed: {value}")
        coverage_path = root / "_kb-control/content-coverage.json"
        model_path = root / "_kb-control/knowledge-model.json"
        model = read_object(model_path) if model_path.is_file() else {}
        units = {u.get("id"): u for u in model.get("units", []) if isinstance(u, dict)}
        if packet.get("contractContext") != contract_context(root):
            fail("reader-probe-job-changed", "Audience, product posture or first-success intent changed.")
        coverage = read_object(coverage_path) if coverage_path.is_file() else {}
        rows = {p.get("path"): p for p in coverage.get("pages", []) if isinstance(p, dict)}
        for record in records:
            current = rows.get(record["path"], {})
            if current.get("readerJob") != record.get("declaredJob"):
                fail("reader-probe-job-changed", f'Reader job changed: {record["path"]}')
            for field in ("primaryQuestion", "readerChange"):
                if current.get(field) != record.get(field):
                    fail("reader-probe-job-changed", f'{field} changed: {record["path"]}')
            if record.get("modelContext") != unit_context(current, units):
                fail("reader-probe-prerequisites-changed", f'Relevant knowledge owners or prerequisites changed: {record["path"]}')
    except (OSError, ValueError, TypeError, ET.ParseError) as error:
        fail("reader-probe-invalid", str(error))


def reader_probe_paths(root, page_paths=None, *, pilot=False):
    """Expose prepared materials to existing workflow/update fingerprints."""
    control = root / "_kb-control"
    try:
        document = read_object(control / ("pilot-verdict.json" if pilot else "content-coverage.json")) if (control / ("pilot-verdict.json" if pilot else "content-coverage.json")).is_file() else {}
    except (OSError, ValueError):
        return []
    rows = [document] if pilot else [p for p in document.get("pages", []) if isinstance(p, dict) and (page_paths is None or p.get("path") in page_paths)]
    paths = set()
    for row in rows:
        review = row.get("comprehensionReview")
        reference = review.get("readerProbe") if isinstance(review, dict) else None
        if not isinstance(reference, dict) or not isinstance(reference.get("packetPath"), str):
            continue
        path = (root / reference["packetPath"]).resolve()
        if not path.is_relative_to(root.resolve()):
            continue
        paths.add(path)
        if not path.is_file():
            continue
        try:
            packet = read_object(path)
            for base, values in ((root, packet.get("inputDigests", {})), (path.parent, packet.get("materialDigests", {}))):
                if not isinstance(values, dict):
                    continue
                for value in values:
                    candidate = (base / value).resolve()
                    if candidate.is_relative_to(root.resolve()):
                        paths.add(candidate)
        except (OSError, ValueError, TypeError):
            continue  # Validators report malformed packets; fingerprints still bind the packet itself.
    return sorted(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "check"])
    parser.add_argument("--root", required=True)
    parser.add_argument("--page", action="append", default=[])
    parser.add_argument("--job", choices=JOBS)
    parser.add_argument("--packet")
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    try:
        if args.command == "prepare":
            result = prepare(root, args.page, job=args.job)
        else:
            path = file_inside(root, args.packet)
            errors = []
            validate_probe(root, {"packetPath": str(path.relative_to(root)), "packetSha256": sha(path.read_bytes())}, args.page, errors, required=True)
            result = {"status": "fail" if errors else "pass", "validationKind": "review-material-integrity", "readiness": "not_assessed", "errors": errors}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(result["status"] == "fail")
    except (OSError, ValueError, TypeError, ET.ParseError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
