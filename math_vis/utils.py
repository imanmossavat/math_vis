"""Low-level utilities: palettes, RNG, image helpers."""
import io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image


def make_cmap(hex_colors, N=512):
    """Turn a short list of hex colors into a smooth 0..1 colormap."""
    return LinearSegmentedColormap.from_list("pal", hex_colors, N=N)


def cosine_cmap(a, b, c, d, n=256):
    """Cosine palette: color(t) = a + b*cos(2*pi*(c*t + d)) per RGB channel.

    Parameters
    ----------
    a, b, c, d : sequence of 3 floats
        One value per RGB channel.
    n : int
        Number of samples in the lookup table.

    Returns
    -------
    matplotlib.colors.LinearSegmentedColormap
    """
    t = np.linspace(0, 1, n)[:, None]
    rgb = np.clip(
        np.array(a, dtype=float)
        + np.array(b, dtype=float)
        * np.cos(
            2 * np.pi
            * (np.array(c, dtype=float) * t + np.array(d, dtype=float))
        ),
        0,
        1,
    )
    return LinearSegmentedColormap.from_list("cos", rgb, N=512)


def squash(f, softness=1.5):
    """Map an unbounded scalar field to the range [0, 1] with a soft tanh."""
    return 0.5 + 0.5 * np.tanh(f / softness)


def new_rng(seed=None):
    """Return a NumPy Generator, printing the seed for reproducibility."""
    if seed is None:
        seed = int(np.random.SeedSequence().entropy % 1_000_000)
    print("seed:", seed)
    return np.random.default_rng(seed)


def upfield(f, W, H):
    """Stretch a small scalar field to full image size using bilinear resize."""
    return np.asarray(
        Image.fromarray(f.astype(np.float32), mode="F").resize((W, H), Image.BILINEAR)
    )


def fig_to_img(fig, dpi=300):
    """Render a matplotlib figure to a uint8 RGB array and close it."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return np.asarray(Image.open(buf).convert("RGB"))
