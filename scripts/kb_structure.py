"""An actual ordered reading path, separate from author rationale and full-text scope."""
import json
import re

from kb_reader_probe import file_inside


def validate_reading_path(root, batch):
    if 'readingPath' not in batch:
        return
    paths = batch['readingPath']
    if (not isinstance(paths, list) or len(paths) < 2
            or any(not isinstance(p, str) for p in paths)
            or len(set(paths)) != len(paths)):
        raise ValueError('readingPath needs an ordered list of at least two distinct reader-facing pages.')
    if batch.get('reviewMode') != 'editorial' or batch.get('methodVersion', 1) < 3:
        raise ValueError('Structure reading requires the shared editorial method (3 or later).')
    if not set(batch['pages']).issubset(paths):
        raise ValueError('Every selected full-text page must occur in readingPath.')
    resolved = []
    for value in paths:
        path = file_inside(root, value)
        if path.suffix != '.md' or path.relative_to(root).parts[0] == '_kb-control':
            raise ValueError('readingPath must use reader-facing Markdown, not private control or design files.')
        resolved.append(path)
    if len(set(resolved)) != len(resolved):
        raise ValueError('readingPath cannot repeat a page through path aliases.')


def headings(text):
    """Extract visible heading source lines, not a renderer or semantic summary."""
    lines, result, fence = text.splitlines(), [], None
    frontmatter = bool(lines and lines[0].strip() == '---')
    for index, line in enumerate(lines):
        if frontmatter:
            if index and line.strip() in {'---', '...'}:
                frontmatter = False
            continue
        mark = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if mark and mark[1][0] == fence[0] and len(mark[1]) >= len(fence) and not mark[2].strip():
                fence = None
            continue
        if mark:
            fence = mark[1]
            continue
        if re.match(r'^ {0,3}#{1,6}(?:\s|$)', line):
            result.append(line)
        elif index and re.fullmatch(r' {0,3}(?:=+|-+)\s*', line) and lines[index - 1].strip():
            result.append(lines[index - 1] + '\n' + line)
    return '\n'.join(result)


def outline(root, batch, page_contents=None):
    validate_reading_path(root, batch)
    return [{'path': p, 'headings': headings(page_contents[p] if page_contents is not None and p in page_contents
                                          else file_inside(root, p).read_text(encoding='utf-8'))}
            for p in batch.get('readingPath', [])]


def context(root, batch, page_contents=None):
    if 'readingPath' not in batch:
        return ''
    return ('\n\n实际阅读顺序与标题（按列表顺序；仅供编排判断，不代表读过未提供的正文）：\n'
            + json.dumps(outline(root, batch, page_contents), ensure_ascii=False)
            + '\n完整正文范围：' + json.dumps(fulltext_order(batch), ensure_ascii=False)
            + '\n未给全文的章节只能据标题定位，不能据此认定其论证完整、缺失或重复；需要时提出读取范围。')


def coverage(batch):
    if 'readingPath' not in batch:
        return {}
    return {'structureScope': {'kind': 'ordered-outline-and-selected-fulltext',
            'readingPath': batch['readingPath'], 'fullTextPages': fulltext_order(batch),
            'outlineOnlyPages': [p for p in batch['readingPath'] if p not in batch['pages']]}}


def fulltext_order(batch):
    return [p for p in batch['readingPath'] if p in batch['pages']] if 'readingPath' in batch else batch['pages']
