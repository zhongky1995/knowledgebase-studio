"""Shared editorial resources sent as actual text, with replayable snapshots."""
import hashlib
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
METHOD_FILES = tuple('skills/knowledgebase-content-builder/references/' + name for name in
                     ('editorial-method.md', 'editorial-examples.md'))
STRUCTURE_METHOD = 'skills/knowledgebase-architect/references/structure-method.md'


def text_digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def current_method(*, structure=False):
    files = []
    for path in (*METHOD_FILES, *((STRUCTURE_METHOD,) if structure else ())):
        content = (PLUGIN_ROOT / path).read_text(encoding='utf-8')
        files.append({'path': path, 'content': content, 'sha256': text_digest(content)})
    return validate_method({'schemaVersion': 1, 'files': files})


def validate_method(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get('schemaVersion') != 1:
        raise ValueError('Missing editorial method snapshot.')
    rows = snapshot.get('files')
    if (not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows)
            or [r.get('path') for r in rows] not in [list(METHOD_FILES), [*METHOD_FILES, STRUCTURE_METHOD]]):
        raise ValueError('Editorial snapshot must contain the shared method and examples.')
    for row in rows:
        content = row.get('content')
        if not isinstance(content, str) or not content.strip() or row.get('sha256') != text_digest(content):
            raise ValueError('Editorial method text differs from its captured digest.')
    return snapshot


def render_method(snapshot, role):
    rows = validate_method(snapshot)['files']
    # Examples support author selection; an independent reader gets only the
    # common method, never author choices or the expected repair.
    if role == 'reader':
        rows = [r for r in rows if r['path'] != METHOD_FILES[1]]
    elif role != 'writer':
        raise ValueError('Unknown editorial role.')
    return '\n\n'.join(f'共用方法 {row["path"]}\n{row["content"]}' for row in rows)
