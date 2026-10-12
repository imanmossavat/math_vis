import os
import re
import subprocess

import pytest
import nbformat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')


def _git_tracked(rel_path):
    res = subprocess.run(
        ['git', 'ls-files', '--', rel_path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return bool(res.stdout.strip())


def _iter_image_refs():
    for doc in ['README.md', 'MATH.md', 'TECHNICAL.md']:
        text = (REPO_ROOT / doc).read_text()
        for m in IMAGE_RE.finditer(text):
            yield doc, m.group(1), m.group(2)

    for nb_path in sorted((REPO_ROOT / 'notebooks').glob('*.ipynb')):
        nb = nbformat.read(nb_path, as_version=4)
        rel_nb = nb_path.relative_to(REPO_ROOT)
        for cell in nb.cells:
            if cell.cell_type != 'markdown':
                continue
            for m in IMAGE_RE.finditer(cell.source):
                yield str(rel_nb), m.group(1), m.group(2)


@pytest.mark.parametrize('source,alt,href', list(_iter_image_refs()))
def test_markdown_image_is_tracked(source, alt, href):
    if href.startswith(('http://', 'https://')):
        pytest.skip('external URL')

    src_path = REPO_ROOT / source
    base = src_path.parent if src_path.is_file() else REPO_ROOT
    target = os.path.normpath(base / href)
    rel_target = os.path.relpath(target, REPO_ROOT)

    assert _git_tracked(rel_target), (
        f'{source}: image {href!r} resolves to {rel_target!r}, '
        'which is not tracked by git'
    )
