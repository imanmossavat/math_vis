import numpy as np
import math_vis as mv


def test_smooth_field_stats():
    rng = np.random.default_rng(1)
    f = mv.smooth_field((64, 64), 8, rng)
    assert f.shape == (64, 64)
    np.testing.assert_allclose(f.mean(), 0, atol=0.05)
    np.testing.assert_allclose(f.std(), 1, atol=0.05)


def test_sample_bilinear():
    f = np.arange(9).reshape(3, 3).astype(float)
    # center of the 2x2 block formed by 0,1,3,4 -> 2.0
    val = mv.sample(f, 0.5, 0.5)
    assert abs(val - 2.0) < 1e-6


def test_lloyd_reduces_variance():
    rng = np.random.default_rng(2)
    # seeds perturbed around a regular grid should drift toward grid centers
    grid = np.array([[i, j] for i in np.linspace(10, 90, 5) for j in np.linspace(10, 90, 5)])
    raw = grid + rng.normal(0, 5, grid.shape)
    relaxed = mv.lloyd_relaxation(raw.copy(), 100, 100, iters=6)
    # after relaxation the points should be closer to the original grid centers
    assert np.linalg.norm(relaxed - grid, axis=1).mean() < np.linalg.norm(raw - grid, axis=1).mean()


def test_seeds_spiral_centered():
    rng = np.random.default_rng(3)
    s = mv.seeds_spiral(200, 400, 400, rng)
    assert s.shape == (200, 2)
    assert np.hypot(s[:, 0].mean() - 200, s[:, 1].mean() - 200) < 5


def test_seeds_rose_symmetry():
    rng = np.random.default_rng(4)
    s, ids = mv.seeds_rose(8, 5, 400, 400, rng)
    # ids should repeat because of mirroring/rotation
    assert len(np.unique(ids)) < len(ids)


def test_matchings_catalan():
    # Catalan(4) = 14
    assert len(mv.matchings(list(range(8)))) == 14


def test_rotate_2d():
    pts = np.array([[1, 0], [0, 1]], dtype=float)
    rot = mv.rotate_2d(pts, np.pi / 2)
    np.testing.assert_allclose(rot, np.array([[0, 1], [-1, 0]], dtype=float), atol=1e-6)


def test_arc_points_shape():
    a = mv.arc_points(0, 0, 1, 0, 90, n=30)
    assert a.shape == (30, 2)


def test_tile_curve_matches_inline_formula():
    def old_tile_curve(i, j, n=40):
        p, q = mv.P_TILE[i], mv.P_TILE[j]
        s = min(0.55 * np.linalg.norm(p - q), 0.2)
        c1, c2 = p + s * mv.N_TILE[i], q + s * mv.N_TILE[j]
        t = np.linspace(0, 1, n)[:, None]
        return (
            (1 - t) ** 3 * p
            + 3 * (1 - t) ** 2 * t * c1
            + 3 * (1 - t) * t**2 * c2
            + t**3 * q
        )

    for text in mv.TILE_TEXT:
        for pair in text.split():
            i, j = (int(x) for x in pair.split("-"))
            np.testing.assert_allclose(mv.tile_curve(i, j), old_tile_curve(i, j))


def test_cubic_bezier_scales_with_coordinates():
    p = np.array([0.0, 0.0])
    q = np.array([1.0, 0.0])
    curve = mv.cubic_bezier(p, q, n=20, max_offset=None)
    curve_scaled = mv.cubic_bezier(1000 * p, 1000 * q, n=20, max_offset=None)
    np.testing.assert_allclose(curve_scaled, 1000 * curve)


def _brute_rng_and_gabriel(p):
    rng, gab = set(), set()
    for i in range(len(p)):
        for j in range(i + 1, len(p)):
            others = np.delete(np.arange(len(p)), [i, j])
            L = np.linalg.norm(p[i] - p[j])
            far = np.maximum(np.linalg.norm(p[others] - p[i], axis=1), np.linalg.norm(p[others] - p[j], axis=1))
            if (far >= L).all():
                rng.add((i, j))
            if (np.linalg.norm(p[others] - (p[i] + p[j]) / 2, axis=1) >= L / 2).all():
                gab.add((i, j))
    return rng, gab


def test_proximity_graphs_match_brute_force_and_nest():
    # MST ⊆ RNG ⊆ Gabriel ⊆ Delaunay; RNG and Gabriel checked against every pair
    p = np.random.default_rng(0).random((60, 2))
    g = mv.proximity_graphs(p)
    s = {k: set(map(tuple, v)) for k, v in g.items()}
    rng, gab = _brute_rng_and_gabriel(p)
    assert s["rng"] == rng and s["gabriel"] == gab
    assert s["mst"] <= s["rng"] <= s["gabriel"] <= s["delaunay"]


def test_proximity_graph_link_counts():
    # Delaunay: 3N - 3 - h links (h points on the hull, Euler).  MST: N - 1.
    # Random points: mean Gabriel degree 4 (Matula and Sokal 1980), Delaunay 6.
    from scipy.spatial import ConvexHull
    deg = {"delaunay": [], "gabriel": []}
    for seed in range(4):
        p = np.random.default_rng(seed).random((3000, 2))
        g = mv.proximity_graphs(p)
        h = len(ConvexHull(p).vertices)
        assert len(g["delaunay"]) == 3 * len(p) - 3 - h
        assert len(g["mst"]) == len(p) - 1
        inner = (np.abs(p - 0.5) < 0.4).all(axis=1)
        for k in deg:
            deg[k].append(np.bincount(g[k].ravel(), minlength=len(p))[inner].mean())
    assert abs(np.mean(deg["delaunay"]) - 6) < 0.03
    assert abs(np.mean(deg["gabriel"]) - 4) < 0.06


def test_lloyd_relaxation_pushes_gabriel_toward_delaunay():
    p = np.random.default_rng(1).random((1500, 2)) * 1000
    before = len(mv.proximity_graphs(p)["gabriel"])
    after = len(mv.proximity_graphs(mv.lloyd_relaxation(p, 1000, 1000, iters=10))["gabriel"])
    assert after > 1.25 * before
