"""High-level renderers and the glass rendering pipeline."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from scipy.ndimage import distance_transform_edt, label
from scipy.spatial import cKDTree

from .utils import make_cmap, upfield, fig_to_img, squash, new_rng
from .math_tools import (
    smooth_field,
    sample,
    seeds_relaxed,
    seeds_rose,
    cubic_bezier,
)
from .lighting import (
    apply_lead_lines,
    apply_texture,
    apply_bloom,
    apply_streaks,
    apply_cracks,
    apply_rounded_lead,
)
from .finishing import finish


# ---------- Color recipes ----------


def cell_colors(seeds, W, H, rng=None, trend=0.4, smooth=18, jitter=0.06):
    """Per-cell palette parameter: diagonal trend + smooth field + jitter."""
    rng = rng or np.random.default_rng()
    gh, gw = 140, 112
    fld = smooth_field((gh, gw), smooth * 0.8, rng)
    noise = sample(fld, seeds[:, 1] * gh / H, seeds[:, 0] * gw / W)
    diag = np.clip((seeds[:, 0] / W + seeds[:, 1] / H) / 2, 0, 1)
    return np.clip(
        trend * diag + (1 - trend) * squash(noise) + rng.normal(0, jitter, len(seeds)),
        0,
        1,
    )


# ---------- Glass renderers ----------


def glass(
    seeds,
    t_cell,
    palette,
    W,
    H,
    *,
    rng=None,
    stretch=1.0,
    warp=0.0,
    warp_sigma=80,
    wave_amp=0.0,
    wave_len=500,
    irid=0.0,
    facet=0.35,
    glow=0.35,
    cell_var=0.08,
    lead_px=4.0,
    lead_var=0.5,
    bevel=0.35,
    lead_color=(14, 11, 18),
    texture=0.05,
    bloom=0.25,
    stages=False,
):
    """Soft, glowing, gem-like stained glass renderer."""
    rng = rng or np.random.default_rng()
    n = len(seeds)
    snap = {}
    X, Y = np.meshgrid(
        np.arange(W, dtype=np.float32) + 0.5, np.arange(H, dtype=np.float32) + 0.5
    )

    if warp > 0:
        gh, gw = max(8, H // 8), max(8, W // 8)
        X = X + warp * upfield(smooth_field((gh, gw), warp_sigma / 8, rng), W, H)
        Y = Y + warp * upfield(smooth_field((gh, gw), warp_sigma / 8, rng), W, H)
    if wave_amp > 0:
        Y = Y + wave_amp * np.sin(2 * np.pi * X / wave_len + rng.uniform(0, 6.28))

    S = seeds * [1, stretch]
    P = np.column_stack([X.ravel(), (Y * stretch).ravel()])
    dist, idx = cKDTree(S).query(P, k=2)
    d1, d2, cell = dist[:, 0], dist[:, 1], idx[:, 0]

    # local geometry
    cnt = np.maximum(np.bincount(cell, minlength=n), 1)
    Rc = 2 * np.bincount(cell, weights=d1, minlength=n) / cnt
    R = np.maximum(Rc[cell], 1.0)
    u_ang = rng.uniform(0, 2 * np.pi, n)
    U = np.column_stack([np.cos(u_ang), np.sin(u_ang)])[cell]
    f = np.einsum("ij,ij->i", P - S[cell], U) / R

    # color
    t_pix = np.clip(t_cell[cell] + irid * f, 0, 1)
    rgb = palette(t_pix)[:, :3].astype(np.float32) * 255
    if stages:
        snap["flat"] = rgb.reshape(H, W, 3).astype(np.uint8)

    # lighting
    light = (
        1
        + facet * f
        + glow * (0.45 - np.clip(d1 / R, 0, 1))
        + cell_var * rng.uniform(-1, 1, n)[cell]
    )
    rgb *= light[:, None]
    if stages:
        snap["lit"] = np.clip(rgb, 0, 255).reshape(H, W, 3).astype(np.uint8)

    # lead
    rgb = apply_lead_lines(
        rgb,
        d1,
        d2,
        W,
        H,
        lead_px=lead_px,
        lead_var=lead_var,
        lead_color=lead_color,
        bevel=bevel,
        rng=rng,
    )
    if stages:
        snap["leaded"] = np.clip(rgb, 0, 255).reshape(H, W, 3).astype(np.uint8)

    # texture
    if texture > 0:
        e = (d2 - d1) / 2.0
        wfield = upfield(
            smooth_field((max(4, H // 16), max(4, W // 16)), 5, rng), W, H
        ).ravel()
        w = lead_px * np.clip(1 + lead_var * wfield, 0.35, None)
        alpha = 1 - np.clip(e / w, 0, 1) ** 2 * (3 - 2 * np.clip(e / w, 0, 1))
        rgb = apply_texture(rgb, alpha, W, H, rng=rng, texture=texture)
    img = np.clip(rgb, 0, 255).reshape(H, W, 3)
    if stages:
        snap["textured"] = img.astype(np.uint8)

    if bloom > 0:
        img = apply_bloom(img, bloom=bloom)
    snap["final"] = img.astype(np.uint8)
    return (img.astype(np.float32), snap) if stages else img.astype(np.float32)


def glass_crisp(
    seeds,
    t_cell,
    palette,
    W,
    H,
    *,
    rng=None,
    warp=16,
    warp_sigma=80,
    stretch=1.0,
    wave_amp=0.0,
    wave_len=500,
    streak=0.035,
    streak_light=0.10,
    tilt=0.06,
    crack_n=2.5,
    crack_alpha=0.30,
    contour_k=2.5,
    contour_alpha=0.28,
    crack_px=0.9,
    lead_px=1.8,
    lead_var=0.25,
    round_px=4.0,
    lead_color=(10, 7, 6),
    stages=False,
):
    """Crisp leaded-glass renderer with streaks and hairline cracks."""
    rng = rng or np.random.default_rng()
    n = len(seeds)
    snap = {}
    X0, Y0 = np.meshgrid(
        np.arange(W, dtype=np.float32) + 0.5, np.arange(H, dtype=np.float32) + 0.5
    )
    X, Y = X0.copy(), Y0.copy()

    if warp > 0:
        gh, gw = max(8, H // 8), max(8, W // 8)
        X = X + warp * upfield(smooth_field((gh, gw), warp_sigma / 8, rng), W, H)
        Y = Y + warp * upfield(smooth_field((gh, gw), warp_sigma / 8, rng), W, H)
    if wave_amp > 0:
        Y = Y + wave_amp * np.sin(2 * np.pi * X / wave_len + rng.uniform(0, 6.28))

    S = seeds * [1, stretch]
    P = np.column_stack([X.ravel(), (Y * stretch).ravel()])
    dist, idx = cKDTree(S).query(P, k=2)
    d1, d2, cell = dist[:, 0], dist[:, 1], idx[:, 0]

    # flat color
    rgb = palette(t_cell[cell])[:, :3].astype(np.float32) * 255
    if stages:
        snap["flat"] = rgb.reshape(H, W, 3).astype(np.uint8)

    # streaks + weak tilt
    rgb = apply_streaks(
        rgb,
        t_cell,
        cell,
        X0.ravel(),
        Y0.ravel(),
        n,
        palette,
        rng=rng,
        streak=streak,
        streak_light=streak_light,
        tilt=tilt,
        d1=d1,
        seeds=S,
    )
    if stages:
        snap["streaks"] = np.clip(rgb, 0, 255).reshape(H, W, 3).astype(np.uint8)

    # cracks
    rgb = apply_cracks(
        rgb,
        P,
        cell,
        W,
        H,
        n,
        rng=rng,
        crack_n=crack_n,
        crack_alpha=crack_alpha,
        contour_k=contour_k,
        contour_alpha=contour_alpha,
        crack_px=crack_px,
    )
    if stages:
        snap["cracks"] = np.clip(rgb, 0, 255).reshape(H, W, 3).astype(np.uint8)

    # rounded lead
    rgb = apply_rounded_lead(
        rgb,
        d1,
        d2,
        W,
        H,
        rng=rng,
        lead_px=lead_px,
        lead_var=lead_var,
        round_px=round_px,
        lead_color=lead_color,
    )
    if stages:
        snap["leaded"] = np.clip(rgb, 0, 255).astype(np.uint8)
    snap["final"] = np.clip(rgb, 0, 255).astype(np.uint8)
    return (rgb.astype(np.float32), snap) if stages else rgb.astype(np.float32)


def line_distance(segs, half_width, W, H, levels=12):
    """Distance (px) from every pixel to the surface of thick segments; < 0 inside a line.

    ``segs`` (E, 2, 2) in pixel coordinates (x, y), ``half_width`` (E,) in pixels.
    Widths are rounded to ``levels`` values and one distance transform is done per value.
    """
    half_width = np.broadcast_to(np.asarray(half_width, float), len(segs))
    edges = np.linspace(half_width.min(), half_width.max(), levels + 1)
    level = np.clip(np.searchsorted(edges, half_width) - 1, 0, levels - 1)
    out = np.full((H, W), np.inf, dtype=np.float32)
    for k in np.unique(level):
        sk = segs[level == k]
        n = np.maximum(2, np.ceil(2 * np.linalg.norm(sk[:, 1] - sk[:, 0], axis=1)).astype(int))
        t = np.concatenate([np.linspace(0, 1, m) for m in n])
        a, b = np.repeat(sk[:, 0], n, axis=0), np.repeat(sk[:, 1], n, axis=0)
        x, y = (a + t[:, None] * (b - a)).T
        ok = (x >= 0) & (x < W) & (y >= 0) & (y < H)
        centre = np.ones((H, W), bool)
        centre[y[ok].astype(int), x[ok].astype(int)] = False
        hw = half_width[level == k].mean()
        out = np.minimum(out, distance_transform_edt(centre) - hw)
    return out


def glass_lines(
    segs,
    half_width,
    palette,
    W,
    H,
    *,
    inside=None,
    rng=None,
    trend=0.4,
    smooth=18,
    jitter=0.06,
    facet=0.35,
    glow=0.35,
    cell_var=0.08,
    lead_px=1.5,
    lead_var=0.35,
    bevel=0.35,
    lead_color=(14, 11, 18),
    texture=0.05,
    bloom=0.25,
    min_pane=10,
    stages=False,
):
    """Stained glass whose lead is a given set of thick lines (veins, cracks, roads).

    The panes are the faces the lines enclose (inside the boolean ``inside`` mask).
    Lighting follows :func:`glass`, with the distance to the lead in place of the
    distance to a seed.  Panes under ``min_pane`` pixels (slivers where lines meet) are
    filled with lead.  Returns the image, or (image, stages) with ``stages=True``;
    ``stages["panes"]`` is the number of panes.
    """
    rng = rng or np.random.default_rng()
    snap = {}
    inside = np.ones((H, W), bool) if inside is None else inside
    d = line_distance(segs, half_width, W, H)
    cell, n = label(inside & (d > 0))
    small = np.bincount(cell.ravel(), minlength=n + 1) < min_pane
    small[0] = False
    d[small[cell]] = -1.0
    cell, n = label(inside & (d > 0))
    pane = cell.ravel() > 0
    cell = np.maximum(cell.ravel() - 1, 0)
    snap["panes"] = n

    # per-pane geometry
    X, Y = np.meshgrid(np.arange(W, dtype=np.float32) + 0.5, np.arange(H, dtype=np.float32) + 0.5)
    P = np.column_stack([X.ravel(), Y.ravel()])
    w = pane.astype(float)
    cnt = np.maximum(np.bincount(cell, weights=w, minlength=n), 1)
    cen = np.column_stack([np.bincount(cell, weights=w * P[:, i], minlength=n) for i in (0, 1)]) / cnt[:, None]
    R = np.sqrt(cnt / np.pi)[cell]
    dist = np.maximum(d.ravel(), 0)
    dmax = np.ones(n)
    np.maximum.at(dmax, cell[pane], dist[pane])

    # color
    t_cell = cell_colors(cen, W, H, rng, trend=trend, smooth=smooth, jitter=jitter)
    rgb = palette(t_cell[cell])[:, :3].astype(np.float32) * 255
    lead = np.array(lead_color, dtype=np.float32)
    rgb[~pane] = lead
    if stages:
        snap["flat"] = rgb.reshape(H, W, 3).astype(np.uint8)

    # lighting: tilt, thicker glass glows in the middle of a pane, pane-to-pane variation
    ang = rng.uniform(0, 2 * np.pi, n)
    f = np.einsum("ij,ij->i", P - cen[cell], np.column_stack([np.cos(ang), np.sin(ang)])[cell]) / R
    f = np.clip(f, -1, 1)  # long thin panes would otherwise tilt far out of range
    light = 1 + facet * f + glow * (dist / dmax[cell] - 0.55) + cell_var * rng.uniform(-1, 1, n)[cell]
    rgb[pane] *= light[pane, None]
    if stages:
        snap["lit"] = np.clip(rgb, 0, 255).reshape(H, W, 3).astype(np.uint8)

    # lead: the lines themselves, softened over lead_px, and everything outside ``inside``
    zero = np.zeros_like(dist)
    e2 = np.where(inside.ravel(), 2 * dist, 0)
    rgb = apply_lead_lines(rgb, zero, e2, W, H, lead_px=lead_px, lead_var=lead_var,
                           lead_color=lead_color, bevel=bevel, rng=rng)
    if stages:
        snap["leaded"] = np.clip(rgb, 0, 255).reshape(H, W, 3).astype(np.uint8)

    if texture > 0:
        alpha = 1 - np.clip(e2 / 2 / lead_px, 0, 1)
        rgb = apply_texture(rgb, alpha, W, H, rng=rng, texture=texture)
    img = np.clip(rgb, 0, 255).reshape(H, W, 3)
    if bloom > 0:
        img = apply_bloom(img, bloom=bloom)
    snap["final"] = img.astype(np.uint8)
    return (img.astype(np.float32), snap) if stages else img.astype(np.float32)


# ---------- Truchet tile library ----------

TILE_TEXT = [
    "0-1 2-3 4-5 6-7",
    "0-1 2-3 4-7 5-6",
    "0-1 2-5 3-4 6-7",
    "0-1 2-7 3-4 5-6",
    "0-1 2-7 3-6 4-5",
    "0-3 1-2 4-5 6-7",
    "0-3 1-2 4-7 5-6",
    "0-5 1-2 3-4 6-7",
    "0-5 1-4 2-3 6-7",
    "0-7 1-2 3-4 5-6",
    "0-7 1-2 3-6 4-5",
    "0-7 1-4 2-3 5-6",
    "0-7 1-6 2-3 4-5",
    "0-7 1-6 2-5 3-4",
]

A = 0.3
P_TILE = np.array(
    [[A, 0], [1 - A, 0], [1, A], [1, 1 - A], [1 - A, 1], [A, 1], [0, 1 - A], [0, A]]
)
N_TILE = np.array(
    [[0, 1], [0, 1], [-1, 0], [-1, 0], [0, -1], [0, -1], [1, 0], [1, 0]]
)


def parse_tile(text):
    """Convert '0-1 2-3 ...' to list of point-index pairs."""
    return [tuple(map(int, pair.split("-"))) for pair in text.split()]


def rotate_tile(tile, r):
    """Rotate a tile pairing by r quarter-turns."""
    return [((i + 2 * r) % 8, (j + 2 * r) % 8) for i, j in tile]


def tile_curve(i, j, n=40):
    """Smooth cubic Bezier curve connecting two edge points of a tile."""
    return cubic_bezier(
        P_TILE[i], P_TILE[j], n=n,
        normal_p=N_TILE[i], normal_q=N_TILE[j],
    )


# ---------- High-level renderers ----------


def render_flow_field(
    seed=11,
    bg="#14161f",
    n_lines=7000,
    steps=260,
    step=0.0035,
    smooth=22,
    twist=0.9,
    palette=None,
    width_range=(0.3, 1.4),
    alpha_range=(0.15, 0.5),
    trend=0.28,
    jitter=0.05,
    grain=3.0,
    vignette=0.25,
    dpi=300,
):
    """Render a flow-field line image and return a uint8 RGB array."""
    rng = np.random.default_rng(seed)
    palette = palette or make_cmap(
        ["#1d3557", "#3a6ea5", "#5bc0be", "#f4e3b1", "#f2a65a", "#d1495b"]
    )

    GW, GH = 256, 320
    field = smooth_field((GH, GW), smooth, rng)
    angle = field * np.pi * twist

    def at(f, pts):
        return sample(f, pts[:, 1] * GW, pts[:, 0] * GW)

    side = int(np.sqrt(n_lines))
    gx, gy = np.meshgrid(
        np.linspace(-0.05, 1.05, side),
        np.linspace(-0.05, 1.30, n_lines // side),
    )
    pts = np.column_stack([gx.ravel(), gy.ravel()])
    pts = pts + rng.normal(0, 0.006, pts.shape)
    n = len(pts)

    paths = np.empty((n, steps, 2))
    paths[:, 0] = pts
    for i in range(1, steps):
        a = at(angle, pts)
        pts = pts + step * np.column_stack([np.cos(a), np.sin(a)])
        paths[:, i] = pts

    start_value = at(field, paths[:, 0])
    t = 0.5 + trend * start_value + rng.normal(0, jitter, n)
    colors = palette(np.clip(t, 0, 1))
    colors[:, 3] = rng.uniform(*alpha_range, n)
    widths = rng.uniform(*width_range, n)

    fig = plt.figure(figsize=(8, 10), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    fig.patch.set_facecolor(bg)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.25)
    ax.axis("off")
    ax.add_collection(
        LineCollection(paths, colors=colors, linewidths=widths, capstyle="round")
    )
    return fig_to_img(fig)


def render_truchet_weave(
    seed=None,
    nx=16,
    ny=20,
    tile_ids=(9,),
    rotations=(0, 1),
    n_strands=3,
    band=0.055,
    strand_shift=0.09,
    orient_smooth=1.2,
    color_smooth=3.0,
    jitter=0.04,
    palette=None,
    bg="#f1e9d2",
    grain=3.0,
):
    """Render a multi-strand Truchet weave."""
    rng = new_rng(seed)
    palette = palette or make_cmap(
        ["#d9674a", "#e8a56b", "#e6d28f", "#9db08c", "#5f8a86", "#2c3a35"]
    )

    tiles = [parse_tile(TILE_TEXT[k]) for k in tile_ids]

    orient_field = smooth_field((ny, nx), orient_smooth, rng)
    color_field = smooth_field((ny, nx), color_smooth, rng)
    pick_field = smooth_field((ny, nx), orient_smooth * 2, rng)

    def to_index(field, n):
        if n == 1:
            return np.zeros(field.shape, dtype=int)
        cuts = np.quantile(field, np.linspace(0, 1, n + 1)[1:-1])
        return np.digitize(field, cuts)

    rot_idx = to_index(orient_field, len(rotations))
    tile_idx = to_index(pick_field, len(tiles))
    offsets = np.linspace(-1, 1, n_strands) if n_strands > 1 else np.array([0.0])

    segments, colors = [], []
    for j in range(ny):
        for i in range(nx):
            tile = rotate_tile(tiles[tile_idx[j, i]], rotations[rot_idx[j, i]])
            for a, b in tile:
                base = tile_curve(a, b) + [i, j]
                t = squash(color_field[j, i]) + rng.normal(0, jitter)
                for off in offsets:
                    # offset curve perpendicular to its tangent
                    tang = np.gradient(base, axis=0)
                    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
                    seg = base + off * band * (n_strands - 1) / 2 * np.column_stack(
                        [-tang[:, 1], tang[:, 0]]
                    )
                    segments.append(seg)
                    colors.append(
                        palette(np.clip(t + off * strand_shift, 0, 1))
                    )

    strand_w = band * (8 * 72 / nx) * 0.9
    fig = plt.figure(figsize=(8, 10), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    fig.patch.set_facecolor(bg)
    ax.set_xlim(0, nx)
    ax.set_ylim(0, ny)
    ax.axis("off")
    ax.add_collection(
        LineCollection(segments, colors=colors, linewidths=strand_w, capstyle="butt")
    )
    return finish(fig_to_img(fig), grain=grain, display=False)


def render_stained_glass_crisp(
    seed=None,
    W=1300,
    H=900,
    n_cells=170,
    lloyd_iters=2,
    palette=None,
    warp=16,
    lead_px=1.8,
    round_px=4.0,
    streak=0.035,
    streak_light=0.10,
    crack_alpha=0.30,
    contour_alpha=0.28,
    trend=0.5,
    smooth=20,
    jitter=0.07,
    grain=2.0,
    stages=False,
):
    """Render a crisp stained-glass example (the "crisp" style)."""
    rng = new_rng(seed)
    palette = palette or make_cmap(
        ["#0b1d3a", "#1f4e8c", "#2aa5c9", "#58d3c0", "#f4e285",
         "#f59e3b", "#e0453a", "#8e2a6a", "#3a1d6e"]
    )
    seeds = seeds_relaxed(n_cells, W, H, rng, iters=lloyd_iters)
    t_cell = cell_colors(seeds, W, H, rng, trend=trend, smooth=smooth, jitter=jitter)
    out = glass_crisp(
        seeds,
        t_cell,
        palette,
        W,
        H,
        rng=rng,
        warp=warp,
        lead_px=lead_px,
        round_px=round_px,
        streak=streak,
        streak_light=streak_light,
        crack_alpha=crack_alpha,
        contour_alpha=contour_alpha,
        stages=stages,
    )
    if stages:
        img, snap = out
        return img, snap
    return finish(out, grain=grain, display=False)


def render_glass_rose(
    seed=None,
    size=1300,
    n_fold=12,
    rings=7,
    palette=None,
    facet=0.4,
    glow=0.35,
    lead_px=5.5,
    lead_var=0.3,
    grain=3.0,
    stages=False,
):
    """Render a rose-window stained-glass example."""
    rng = new_rng(seed)
    palette = palette or make_cmap(
        ["#0b1d3a", "#1f4e8c", "#2aa5c9", "#58d3c0", "#f4e285",
         "#f59e3b", "#e0453a", "#8e2a6a", "#3a1d6e"]
    )
    W = H = size
    seeds, ids = seeds_rose(n_fold, rings, W, H, rng)
    r = np.hypot(seeds[:, 0] - W / 2, seeds[:, 1] - H / 2) / (0.46 * W)
    th = np.arctan2(seeds[:, 1] - H / 2, seeds[:, 0] - W / 2)
    jitter = rng.normal(0, 0.05, ids.max() + 1)[ids]
    t_cell = np.clip(
        0.55 * r
        + 0.22 * np.cos(n_fold * th)
        + 0.10 * np.cos(2 * n_fold * th)
        + jitter
        + 0.1,
        0,
        1,
    )
    img = glass(
        seeds,
        t_cell,
        palette,
        W,
        H,
        rng=rng,
        facet=facet,
        glow=glow,
        lead_px=lead_px,
        lead_var=lead_var,
    )
    # crop to circle
    yy, xx = np.mgrid[0:W, 0:W]
    mask = np.clip((0.47 * W - np.hypot(xx - W / 2, yy - H / 2)) / 3, 0, 1)[..., None]
    img = img * mask + np.array([14, 11, 18]) * (1 - mask)
    if stages:
        return img, {"final": img.astype(np.uint8)}
    return finish(img, grain=grain, display=False)
