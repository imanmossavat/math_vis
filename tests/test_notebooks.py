"""Execute all demonstrator notebooks end-to-end as a smoke test."""
import os
import subprocess
import time
import glob

import pytest
import nbformat
import matplotlib
matplotlib.use('Agg')  # noqa: E402
import matplotlib.pyplot as plt


NOTEBOOK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notebooks')
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))


def notebooks():
    return sorted(glob.glob(os.path.join(NOTEBOOK_DIR, 'demo_*.ipynb')))


@pytest.mark.parametrize('path', notebooks())
def test_notebook_runs(path, monkeypatch, tmp_path):
    # Run each notebook in an isolated temp directory so that any files it
    # creates (e.g. saved PNGs) do not pollute the repository root.
    monkeypatch.chdir(tmp_path)
    with open(path) as f:
        nb = nbformat.read(f, as_version=4)
    ns = {}
    t0 = time.time()
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == 'code':
            # Skip IPython magic lines (e.g. %matplotlib inline) when exec-ing outside a kernel
            src = '\n'.join(line for line in cell.source.splitlines() if not line.lstrip().startswith('%'))
            if not src.strip():
                continue
            try:
                exec(src, ns)
            except Exception as e:
                raise AssertionError(f"Error in {os.path.basename(path)} cell {i}: {e}") from e
    plt.close('all')
    elapsed = time.time() - t0
    print(f"{os.path.basename(path)} executed in {elapsed:.1f}s")


def test_repo_has_no_new_pngs():
    """Notebook tests must not leave generated PNGs in the repository."""
    res = subprocess.run(
        ['git', 'status', '--ignored'],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    ignored_pngs = [
        line.strip()
        for line in res.stdout.splitlines()
        if line.strip().endswith('.png') and not line.strip().startswith('assets/')
    ]
    assert not ignored_pngs, f'ignored PNGs appeared in the repo: {ignored_pngs}'


def test_notebook_directory_nonempty():
    assert notebooks()
