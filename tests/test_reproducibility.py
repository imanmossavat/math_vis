"""Reproducibility and property tests for core primitives."""
import numpy as np
import pytest

from math_vis.math_tools import smooth_field
from math_vis.utils import squash
from math_vis.lighting import cell_facet_offset, apply_glass_lighting
from math_vis.rendering import (
    render_flow_field,
    render_truchet_weave,
    render_stained_glass_crisp,
    render_glass_rose,
)

RENDERERS = [
    (
        render_flow_field,
        dict(n_lines=1000, steps=100, dpi=72, smooth=12),
    ),
    (
        render_truchet_weave,
        dict(nx=8, ny=10),
    ),
    (
        render_stained_glass_crisp,
        dict(W=200, H=150, n_cells=40, lloyd_iters=1),
    ),
    (
        render_glass_rose,
        dict(size=200, n_fold=8, rings=3),
    ),
]


@pytest.mark.parametrize('func,kwargs', RENDERERS, ids=[r[0].__name__ for r in RENDERERS])
def test_renderer_same_seed_is_byte_identical(func, kwargs):
    a = func(seed=42, **kwargs)
    b = func(seed=42, **kwargs)
    assert a.dtype == np.uint8
    assert np.array_equal(a, b)


@pytest.mark.parametrize('func,kwargs', RENDERERS, ids=[r[0].__name__ for r in RENDERERS])
def test_renderer_different_seeds_differ(func, kwargs):
    a = func(seed=42, **kwargs)
    b = func(seed=43, **kwargs)
    assert not np.array_equal(a, b)


def test_smooth_field_wrap_periodicity():
    rng = np.random.default_rng(0)
    f = smooth_field((128, 128), 10, rng)
    assert f.shape == (128, 128)
    assert abs(f.mean()) < 0.05
    assert abs(f.std() - 1.0) < 0.1

    # Because gaussian_filter uses mode="wrap", opposite edges should be as
    # close to each other as adjacent rows/columns.
    row_opp = np.abs(f[0, :] - f[-1, :]).mean()
    row_adj = np.abs(f[:-1, :] - f[1:, :]).mean()
    col_opp = np.abs(f[:, 0] - f[:, -1]).mean()
    col_adj = np.abs(f[:, :-1] - f[:, 1:]).mean()

    assert row_opp <= 2 * row_adj
    assert col_opp <= 2 * col_adj


def test_squash_properties():
    x = np.linspace(-10, 10, 1000)
    y = squash(x, softness=1.5)
    assert np.all(np.diff(y) >= 0)
    assert np.all((y > 0) & (y < 1))
    assert squash(0.0, softness=1.5) == pytest.approx(0.5)


def test_cell_facet_offset_should_be_reproducible():
    # Non-zero displacement so that the randomly-chosen tilt direction matters.
    P = np.full((20, 2), 0.5, dtype=np.float32)
    seeds = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=np.float32)
    cell = np.zeros(20, dtype=int)
    rng = np.random.default_rng(0)
    f1 = cell_facet_offset(P, seeds, cell, R=1.0, rng=rng)
    rng = np.random.default_rng(0)
    f2 = cell_facet_offset(P, seeds, cell, R=1.0, rng=rng)
    assert np.allclose(f1, f2)


def test_apply_glass_lighting_should_be_reproducible():
    rgb = np.full((20, 3), 128, dtype=np.float32)
    P = np.full((20, 2), 0.5, dtype=np.float32)
    seeds = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=np.float32)
    d1 = np.ones(20, dtype=np.float32)
    cell = np.zeros(20, dtype=int)
    rng = np.random.default_rng(0)
    out1 = apply_glass_lighting(rgb, P, seeds, d1, cell, rng=rng)
    rng = np.random.default_rng(0)
    out2 = apply_glass_lighting(rgb, P, seeds, d1, cell, rng=rng)
    assert np.allclose(out1, out2)
