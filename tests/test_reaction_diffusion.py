"""Tests for Gray-Scott reaction-diffusion, including the phenomena the notebook shows."""
import numpy as np
import pytest

from math_vis.reaction_diffusion import (
    laplacian,
    initial_state,
    gray_scott,
    param_map,
    dominant_wavelength,
    render_rd,
    render_reaction_diffusion,
)

CORAL = dict(f=0.0545, k=0.062)


def _run(shape=(64, 64), steps=3000, seed=0, **kw):
    params = {**CORAL, **kw}
    return gray_scott(shape, steps=steps, rng=np.random.default_rng(seed),
                      init="noise", **params)


def test_laplacian_conserves_mass_and_kills_constants():
    X = np.random.default_rng(0).normal(size=(32, 40))
    assert abs(laplacian(X).sum()) < 1e-9
    assert np.allclose(laplacian(np.full((8, 8), 3.0)), 0)


def test_trivial_state_is_fixed():
    A, B = gray_scott((32, 32), steps=200, state=(np.ones((32, 32)), np.zeros((32, 32))))
    assert np.allclose(A, 1) and np.allclose(B, 0)


def test_reproducible_and_bounded():
    _, B1 = _run(steps=500)
    _, B2 = _run(steps=500)
    assert np.array_equal(B1, B2)
    assert B1.min() >= 0 and B1.max() <= 1


def test_does_not_mutate_state():
    A0, B0 = initial_state((32, 32), np.random.default_rng(1))
    A_copy, B_copy = A0.copy(), B0.copy()
    gray_scott((32, 32), steps=10, state=(A0, B0))
    assert np.array_equal(A0, A_copy) and np.array_equal(B0, B_copy)


def test_unstable_timestep_rejected():
    with pytest.raises(ValueError):
        gray_scott((8, 8), dA=1.0, dt=1.5, steps=1)


def test_extreme_rules_stay_finite():
    f, k = param_map((48, 48), f_range=(0.0, 0.1), k_range=(0.03, 0.07))
    _, B = gray_scott((48, 48), f=f, k=k, steps=300, rng=np.random.default_rng(0))
    assert np.isfinite(B).all()


def test_snapshots():
    _, _, frames = _run(steps=100, snapshot_every=25)
    assert len(frames) == 4


def test_dominant_wavelength_of_stripes():
    x = np.arange(128)
    stripes = np.sin(2 * np.pi * x / 16)[None, :] * np.ones((128, 1))
    assert dominant_wavelength(stripes) == pytest.approx(16, rel=0.05)


# --- the phenomena -----------------------------------------------------------

def test_equal_diffusion_makes_no_pattern():
    _, B_equal = _run(dA=1.0, dB=1.0)
    _, B_turing = _run(dA=1.0, dB=0.5)
    assert B_equal.std() < 1e-3
    assert B_turing.std() > 0.05


def test_pattern_size_scales_with_sqrt_of_diffusion():
    _, B1 = _run(shape=(96, 96), steps=8000, dA=1.0, dB=0.5)
    _, B4 = _run(shape=(96, 96), steps=8000, dA=0.25, dB=0.125)
    ratio = dominant_wavelength(B1) / dominant_wavelength(B4)
    assert 1.6 < ratio < 2.4  # sqrt(4) = 2


def test_renderers():
    _, B = _run(steps=200)
    img = render_rd(B)
    assert img.shape == (64, 64, 3) and img.dtype == np.uint8
    out = render_reaction_diffusion(seed=1, size=48, steps=200)
    assert out.shape == (48, 48, 3) and out.dtype == np.uint8
