import numpy as np
import math_vis as mv


def test_render_flow_field():
    img = mv.render_flow_field(
        seed=1,
        n_lines=200,
        steps=40,
        smooth=8,
        dpi=50,
    )
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.dtype == np.uint8


def test_render_truchet_weave():
    img = mv.render_truchet_weave(
        seed=1,
        nx=8,
        ny=10,
        n_strands=2,
    )
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.dtype == np.uint8


def test_render_stained_glass_crisp():
    img = mv.render_stained_glass_crisp(
        seed=1,
        W=120,
        H=100,
        n_cells=15,
        lloyd_iters=1,
    )
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.dtype == np.uint8


def test_render_glass_rose():
    img = mv.render_glass_rose(
        seed=1,
        size=120,
        n_fold=6,
        rings=3,
    )
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.dtype == np.uint8

def test_render_stained_glass_crisp_stages():
    img, stages = mv.render_stained_glass_crisp(
        seed=1,
        W=120,
        H=100,
        n_cells=15,
        lloyd_iters=1,
        stages=True,
    )
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.dtype == np.float32
    assert isinstance(stages, dict)
    assert "flat" in stages and "final" in stages

def test_glass_stages():
    rng = np.random.default_rng(1)
    seeds = mv.seeds_relaxed(20, 80, 80, rng, iters=1)
    t = mv.cell_colors(seeds, 80, 80, rng)
    img, stages = mv.glass(seeds, t, mv.make_cmap(["#000", "#fff"]), 80, 80, rng=rng, stages=True)
    assert "flat" in stages and "final" in stages
    assert stages["final"].shape == (80, 80, 3)


def test_glass_crisp_stages():
    rng = np.random.default_rng(1)
    seeds = mv.seeds_relaxed(20, 80, 80, rng, iters=1)
    t = mv.cell_colors(seeds, 80, 80, rng)
    img, stages = mv.glass_crisp(seeds, t, mv.make_cmap(["#000", "#fff"]), 80, 80, rng=rng, stages=True)
    assert "flat" in stages and "final" in stages


def test_glass_lines_panes_are_the_faces_of_the_lines():
    # k lines across and k down, edge to edge, cut the image into (k + 1)^2 panes
    k, W = 3, 120
    xs = np.arange(1, k + 1) * W / (k + 1)
    segs = np.array([[[x, 0], [x, W]] for x in xs] + [[[0, y], [W, y]] for y in xs], float)
    img, stages = mv.glass_lines(segs, 2.0, mv.make_cmap(["#000", "#fff"]), W, W, stages=True)
    assert stages["panes"] == (k + 1) ** 2
    assert img.shape == (W, W, 3)
