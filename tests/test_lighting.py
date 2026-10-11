import numpy as np
import math_vis as mv


def test_lead_mask():
    d1 = np.array([0, 0, 2, 5])
    d2 = np.array([0, 4, 4, 6])
    alpha = mv.lead_mask(d1, d2, width=2.0, mode="smooth")
    assert alpha.shape == d1.shape
    assert alpha[0] > alpha[-1]


def test_glass_lighting_changes_brightness():
    rng = np.random.default_rng(0)
    seeds = rng.uniform([0, 0], [100, 100], size=(20, 2))
    X, Y = np.meshgrid(np.arange(100) + 0.5, np.arange(100) + 0.5)
    P = np.column_stack([X.ravel(), Y.ravel()])
    from scipy.spatial import cKDTree

    d, idx = cKDTree(seeds).query(P, k=2)
    rgb = np.full((len(P), 3), 128, dtype=np.float32)
    lit = mv.apply_glass_lighting(rgb, P, seeds, d[:, 0], idx[:, 0], facet=0.5, glow=0.5)
    assert lit.shape == rgb.shape
    assert lit.std() > rgb.std()


def test_bloom_increases_brightness():
    img = np.zeros((120, 120, 3), dtype=np.float32)
    img[45:75, 45:75] = 255
    bloomed = mv.apply_bloom(img, bloom=1.0)
    assert bloomed.mean() > img.mean()


def test_streaks_change_color():
    rng = np.random.default_rng(1)
    n_cells = 5
    t_cell = rng.uniform(0, 1, n_cells)
    cell = np.repeat(np.arange(n_cells), 100)
    X = rng.uniform(0, 100, len(cell))
    Y = rng.uniform(0, 100, len(cell))
    rgb = np.full((len(cell), 3), 128, dtype=np.float32)
    palette = mv.make_cmap(["#000000", "#ffffff"])
    out = mv.apply_streaks(rgb, t_cell, cell, X, Y, n_cells, palette, rng=rng)
    assert out.shape == rgb.shape


def test_rounded_lead_adds_border():
    rng = np.random.default_rng(2)
    seeds = rng.uniform([0, 0], [80, 80], size=(10, 2))
    X, Y = np.meshgrid(np.arange(80) + 0.5, np.arange(80) + 0.5)
    P = np.column_stack([X.ravel(), Y.ravel()])
    from scipy.spatial import cKDTree

    d, _ = cKDTree(seeds).query(P, k=2)
    rgb = np.full((80 * 80, 3), 200, dtype=np.float32)
    out = mv.apply_rounded_lead(rgb, d[:, 0], d[:, 1], 80, 80, rng=rng)
    assert out.shape == (80, 80, 3)
