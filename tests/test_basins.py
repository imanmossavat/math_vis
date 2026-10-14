"""Property tests for Newton-basin computation."""
import warnings

import numpy as np
import pytest

from math_vis.basins import (
    basin_map,
    complex_grid,
    normalize_iters,
    render_basins,
    roots_unity,
    uncertainty_exponent,
)


SHAPE = (300, 300)
EXTENT = (-2.0, 2.0, -2.0, 2.0)


def _grid(shape=SHAPE, extent=EXTENT):
    return complex_grid(extent, shape)


def test_roots_unity_are_roots():
    for n in [2, 3, 4, 5, 7]:
        roots = roots_unity(n)
        assert roots.shape == (n,)
        assert np.allclose(roots ** n, 1.0)


def test_basin_map_does_not_mutate_input():
    z0 = _grid()
    original = z0.copy()
    basin_map(z0, n=3, max_iter=20)
    assert np.array_equal(z0, original)


def test_basin_map_is_reproducible():
    z0 = _grid()
    b1, i1, f1 = basin_map(z0, n=3, max_iter=40)
    b2, i2, f2 = basin_map(z0, n=3, max_iter=40)
    assert np.array_equal(b1, b2)
    assert np.array_equal(i1, i2)
    assert np.allclose(f1, f2)


def test_render_basins_output():
    z0 = _grid((100, 100), EXTENT)
    basin, iters, _ = basin_map(z0, n=3, max_iter=40)
    img = render_basins(basin, iters)
    assert img.shape == (100, 100, 3)
    assert img.dtype == np.uint8


def test_normalize_iters_range_and_monotonicity():
    iters = np.array([0, 10, 20, 40])
    y = normalize_iters(iters, mode="log1p", max_iter=40)
    assert np.all((y >= 0) & (y <= 1))
    assert np.all(np.diff(y) >= 0)


def test_uncertainty_exponent_z2_is_near_one():
    z0 = _grid()
    basin, _, _ = basin_map(z0, n=2, max_iter=60, tol=1e-6)
    res = uncertainty_exponent(basin, box_sizes=[4, 8, 16, 32])
    assert res["alpha"] == pytest.approx(1.0, abs=0.12)


def test_higher_n_has_lower_uncertainty_exponent():
    z0 = _grid()
    alpha = []
    for n in [2, 4]:
        basin, _, _ = basin_map(z0, n=n, max_iter=60, tol=1e-6)
        res = uncertainty_exponent(basin, box_sizes=[4, 8, 16, 32])
        alpha.append(res["alpha"])
    assert alpha[1] < alpha[0]
    assert alpha[1] < 0.9


def test_float32_breaks_deep_zoom():
    """Near the origin, complex64 cannot resolve the tiny starting values and
    misclassifies some basins compared with complex128."""
    # A tiny window around the origin where three basins of z^3-1 meet.
    z0 = complex_grid((-1e-4, 1e-4, -1e-4, 1e-4), (100, 100))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        b64, _, _ = basin_map(z0, n=3, max_iter=200, tol=1e-8, dtype=np.complex128)
        b32, _, _ = basin_map(z0, n=3, max_iter=200, tol=1e-8, dtype=np.complex64)
    assert np.any(b64 != b32), "float32 and float64 produced identical basin labels"
