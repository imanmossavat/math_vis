"""Execute all demonstrator notebooks end-to-end as a smoke test."""
import os
import time
import glob
import pytest
import nbformat
import matplotlib
matplotlib.use('Agg')  # noqa: E402


NOTEBOOK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'notebooks')


def notebooks():
    return sorted(glob.glob(os.path.join(NOTEBOOK_DIR, 'demo_*.ipynb')))


@pytest.mark.parametrize('path', notebooks())
def test_notebook_runs(path):
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
    elapsed = time.time() - t0
    print(f"{os.path.basename(path)} executed in {elapsed:.1f}s")


def test_notebook_directory_nonempty():
    assert notebooks()
