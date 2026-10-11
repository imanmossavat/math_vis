import numpy as np
import math_vis as mv


def test_squash_range():
    x = np.linspace(-10, 10, 100)
    y = mv.squash(x)
    assert y.min() >= 0 and y.max() <= 1
    np.testing.assert_allclose(y[0], 0, atol=1e-3)
    np.testing.assert_allclose(y[-1], 1, atol=1e-3)


def test_make_cmap_callable():
    cmap = mv.make_cmap(["#000000", "#ffffff"])
    assert cmap(0.0)[:3] == (0.0, 0.0, 0.0)
    assert cmap(1.0)[:3] == (1.0, 1.0, 1.0)


def test_cosine_cmap_bounds():
    cmap = mv.cosine_cmap(a=(0.5, 0.5, 0.5), b=(0.5, 0.5, 0.5), c=(1, 1, 1), d=(0, 0, 0))
    rgbs = cmap(np.linspace(0, 1, 50))[:, :3]
    assert rgbs.min() >= 0 and rgbs.max() <= 1


def test_new_rng_deterministic():
    rng1 = mv.new_rng(42)
    rng2 = mv.new_rng(42)
    assert rng1.random() == rng2.random()


def test_upfield_resize():
    f = np.random.randn(10, 10)
    g = mv.upfield(f, 50, 80)
    assert g.shape == (80, 50)


def test_fig_to_img_shape():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(2, 2))
    ax.plot([0, 1], [0, 1])
    img = mv.fig_to_img(fig, dpi=50)
    assert img.ndim == 3 and img.shape[2] == 3
    assert img.dtype == np.uint8
