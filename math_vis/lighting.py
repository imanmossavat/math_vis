"""Lighting, material, and glass-effect helpers."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt
from scipy.spatial import cKDTree

from .math_tools import smooth_field as _smooth_field
from .utils import upfield


def cell_facet_offset(P, seeds, cell, R):
    """Project pixel-seed displacement onto a random per-cell tilt direction.

    Returns ``f`` in about [-1, 1] for use with ``facet`` lighting.
    """
    n_cells = len(seeds)
    ang = np.random.default_rng().uniform(0, 2 * np.pi, n_cells)
    U = np.column_stack([np.cos(ang), np.sin(ang)])[cell]
    f = np.einsum("ij,ij->i", P - seeds[cell], U) / np.maximum(R, 1.0)
    return f


def lead_mask(d1, d2, width, mode="smooth"):
    """Compute an alpha mask for lead lines between Voronoi cells.

    Parameters
    ----------
    d1, d2 : (N,) arrays
        Distance from each pixel to its nearest and second-nearest seed.
    width : (N,) array or scalar
        Desired lead width in pixels.
    mode : "smooth" | "step"

    Returns
    -------
    alpha : (N,) array in [0, 1]
        1 = on the lead, 0 = inside the cell.
    """
    e = (d2 - d1) / 2.0
    u = np.clip(e / width, 0, 1)
    if mode == "smooth":
        alpha = 1 - u * u * (3 - 2 * u)
    else:
        alpha = (e < width).astype(float)
    return alpha


def bevel_rim(e, width, bevel=0.35):
    """Return a bright rim just inside the lead lines."""
    rim = np.clip(1 - (e - width) / (3 * width), 0, 1) ** 2 * (e > width)
    return bevel * rim


def apply_glass_lighting(
    rgb,
    P,
    seeds,
    d1,
    cell,
    facet=0.35,
    glow=0.35,
    cell_var=0.08,
):
    """Apply gem-like lighting to a flat color image (flattened pixels)."""
    n_cells = len(seeds)
    cnt = np.maximum(np.bincount(cell, minlength=n_cells), 1)
    Rc = 2 * np.bincount(cell, weights=d1, minlength=n_cells) / cnt
    R = np.maximum(Rc[cell], 1.0)
    f = cell_facet_offset(P, seeds, cell, R)
    rng = np.random.default_rng()
    light = (
        1
        + facet * f
        + glow * (0.45 - np.clip(d1 / R, 0, 1))
        + cell_var * rng.uniform(-1, 1, n_cells)[cell]
    )
    return rgb * light[:, None]


def apply_lead_lines(
    rgb,
    d1,
    d2,
    W,
    H,
    lead_px=4.0,
    lead_var=0.5,
    lead_color=(14, 11, 18),
    bevel=0.35,
    rng=None,
):
    """Blend in soft lead lines and a bright rim. Operates on flattened pixels."""
    rng = rng or np.random.default_rng()
    e = (d2 - d1) / 2.0
    wfield = upfield(_smooth_field((max(4, H // 16), max(4, W // 16)), 5, rng), W, H).ravel()
    w = lead_px * np.clip(1 + lead_var * wfield, 0.35, None)
    alpha = lead_mask(d1, d2, w, mode="smooth")
    rim = bevel_rim(e, w, bevel)
    rgb = rgb * (1 + rim[:, None]) + 40 * rim[:, None]
    lead = np.array(lead_color, dtype=np.float32)
    return rgb * (1 - alpha[:, None]) + lead * alpha[:, None]


def apply_texture(rgb, alpha, W, H, rng=None, texture=0.05):
    """Add slow brightness ripples ("hammered glass") on non-lead areas."""
    rng = rng or np.random.default_rng()
    rip = upfield(
        _smooth_field((max(8, H // 4), max(8, W // 4)), 3, rng), W, H
    ).ravel()
    return rgb * (1 + texture * rip * (1 - alpha))[:, None]


def _resize_rgb(arr, W, H):
    """Bilinear resize of an (H, W, 3) float image to (H, W)."""
    return np.stack(
        [
            np.asarray(
                Image.fromarray(arr[..., c].astype(np.float32), mode="F").resize(
                    (W, H), Image.BILINEAR
                )
            )
            for c in range(3)
        ],
        axis=-1,
    )


def apply_bloom(img, bloom=0.25):
    """Make bright areas bleed light into their surroundings."""
    img = np.asarray(img, dtype=np.float32)
    H, W = img.shape[:2]
    sw, sh = max(1, W // 4), max(1, H // 4)
    small = _resize_rgb(img, sw, sh)
    lum = small.mean(axis=-1, keepdims=True)
    glowimg = gaussian_filter(small * (lum > 150), sigma=(8, 8, 0))
    glowup = _resize_rgb(glowimg, W, H)
    return np.clip(img + bloom * glowup, 0, 255)


def apply_streaks(
    rgb,
    t_cell,
    cell,
    X0,
    Y0,
    n_cells,
    palette,
    rng=None,
    streak=0.035,
    streak_light=0.10,
    tilt=0.06,
    d1=None,
    seeds=None,
):
    """Apply soft parallel bands and a weak lens tilt inside each cell."""
    rng = rng or np.random.default_rng()
    th = rng.uniform(0, np.pi, n_cells)
    v = X0 * np.cos(th)[cell] + Y0 * np.sin(th)[cell]
    waves, amps = (140.0, 66.0, 31.0), (1.0, 0.6, 0.35)
    s = np.zeros(len(v), dtype=np.float32)
    for lam, amp in zip(waves, amps):
        s += amp * np.sin(
            2 * np.pi * v / lam + rng.uniform(0, 6.28, n_cells)[cell]
        )
    s /= sum(amps)
    rgb = palette(np.clip(t_cell[cell] + streak * s, 0, 1))[:, :3].astype(np.float32) * 255
    la = streak_light * np.clip(s, 0, 1) ** 2
    rgb = rgb * (1 - la[:, None]) + 255 * la[:, None]

    if d1 is not None and seeds is not None:
        cnt = np.maximum(np.bincount(cell, minlength=n_cells), 1)
        Rc = 2 * np.bincount(cell, weights=d1, minlength=n_cells) / cnt
        ang = rng.uniform(0, 2 * np.pi, n_cells)
        f = (
            (np.column_stack([X0, Y0]) - seeds[cell])
            * np.column_stack([np.cos(ang), np.sin(ang)])[cell]
        ).sum(1) / np.maximum(Rc[cell], 1)
        rgb *= (1 + tilt * f)[:, None]
    return rgb


def apply_cracks(
    rgb,
    P,
    cell,
    W,
    H,
    n_cells,
    rng=None,
    crack_n=2.5,
    crack_alpha=0.30,
    contour_k=2.5,
    contour_alpha=0.28,
    crack_px=0.9,
):
    """Add two kinds of hairline cracks inside cells."""
    rng = rng or np.random.default_rng()

    def hair(e_px, alpha):
        return np.clip(crack_px - e_px + 0.5, 0, 1) * alpha

    # finer Voronoi network
    seeds2 = rng.uniform([0, 0], [W, H], size=(int(crack_n * n_cells), 2))
    dd, _ = cKDTree(seeds2).query(P, k=2)
    a1 = hair((dd[:, 1] - dd[:, 0]) / 2.0, crack_alpha)

    # contour lines of a smooth field
    g = upfield(_smooth_field((max(8, H // 8), max(8, W // 8)), 7, rng), W, H) * contour_k
    gy, gx = np.gradient(g)
    phase = g.ravel() + rng.uniform(0, 1, n_cells)[cell]
    dpx = np.abs(phase - np.round(phase)) / (np.hypot(gx, gy).ravel() + 1e-4)
    a2 = hair(dpx, contour_alpha)

    a = np.maximum(a1, a2)
    dark = (rng.random(n_cells) < 0.7)[cell]
    shade = np.where(dark[:, None], rgb * 0.45, rgb + (255 - rgb) * 0.65)
    return rgb * (1 - a[:, None]) + shade * a[:, None]


def apply_rounded_lead(
    rgb,
    d1,
    d2,
    W,
    H,
    rng=None,
    lead_px=1.8,
    lead_var=0.25,
    round_px=4.0,
    lead_color=(10, 7, 6),
):
    """Crisp lead lines with rounded corners using Euclidean distance transform."""
    rng = rng or np.random.default_rng()
    H, W = int(H), int(W)
    e = ((d2 - d1) / 2.0).reshape(H, W)
    wf = upfield(_smooth_field((max(4, H // 16), max(4, W // 16)), 5, rng), W, H)
    w = lead_px * np.clip(1 + lead_var * wf, 0.5, None)
    core = e > (w + round_px)
    dist_core = distance_transform_edt(~core)
    inside = np.clip(round_px - dist_core + 0.5, 0, 1)[..., None]
    rgb = rgb.reshape(H, W, 3) * inside + np.array(lead_color, dtype=np.float32) * (1 - inside)
    return rgb
