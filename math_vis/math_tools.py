"""Mathematical primitives: fields, sampling, geometry, seed layouts."""
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.spatial import cKDTree


def smooth_field(shape, sigma, rng=None):
    """Create a smooth random scalar field with mean 0 and std 1.

    Parameters
    ----------
    shape : tuple(int, int)
        (rows, cols) of the field.
    sigma : float
        Blur radius in grid cells. Larger = broader features.
    rng : np.random.Generator, optional
        If None, a new default generator is used.

    Returns
    -------
    np.ndarray
        2-D array of floats.
    """
    rng = rng or np.random.default_rng()
    noise = rng.normal(size=shape)
    if sigma > 0:
        blurred = gaussian_filter(noise, sigma, mode="wrap")
    else:
        blurred = noise
    return (blurred - blurred.mean()) / (blurred.std() + 1e-12)


def sample(field, row, col):
    """Bilinear lookup of ``field`` at fractional (row, col) positions.

    Parameters can be scalars or arrays of the same shape. Coordinates are
    wrapped at the edges.
    """
    row = np.asarray(row)
    col = np.asarray(col)
    scalar = row.ndim == 0
    if scalar:
        row = row[None]
        col = col[None]
    coords = np.stack([row, col])
    out = map_coordinates(field, coords, order=1, mode="wrap")
    return out.item() if scalar else out


def lloyd_relaxation(seeds, W, H, rng=None, iters=3):
    """Move seeds toward the centroid of their Voronoi cells.

    Operates on a coarse grid for speed.
    """
    rng = rng or np.random.default_rng()
    seeds = np.asarray(seeds, dtype=float).copy()
    n = len(seeds)
    step = max(4, W // 250)
    gx, gy = np.meshgrid(
        np.arange(0, W, step) + step / 2, np.arange(0, H, step) + step / 2
    )
    grid = np.column_stack([gx.ravel(), gy.ravel()])
    for _ in range(iters):
        _, own = cKDTree(seeds).query(grid)
        cnt = np.bincount(own, minlength=n)
        cx = np.bincount(own, weights=grid[:, 0], minlength=n)
        cy = np.bincount(own, weights=grid[:, 1], minlength=n)
        ok = cnt > 0
        seeds[ok] = np.column_stack([cx[ok] / cnt[ok], cy[ok] / cnt[ok]])
    return seeds


def seeds_relaxed(n, W, H, rng=None, iters=3):
    """Random seeds followed by Lloyd relaxation."""
    rng = rng or np.random.default_rng()
    s = rng.uniform([0, 0], [W, H], size=(n, 2))
    return lloyd_relaxation(s, W, H, rng=rng, iters=iters)


def seeds_spiral(n, W, H, rng=None, jitter=0.12):
    """Sunflower / golden-angle spiral layout with optional jitter."""
    rng = rng or np.random.default_rng()
    i = np.arange(1, n + 1)
    R = 0.53 * np.hypot(W, H)
    r = R * np.sqrt(i / n)
    th = i * np.pi * (3 - np.sqrt(5))  # golden angle
    s = np.column_stack([W / 2 + r * np.cos(th), H / 2 + r * np.sin(th)])
    spacing = R * np.sqrt(np.pi / n)
    return s + rng.normal(0, jitter * spacing, s.shape)


def seeds_rose(n_fold, rings, W, H, rng=None, radius=0.46):
    """Rose-window seed layout: one half-sector rotated and mirrored.

    Returns
    -------
    seeds : (N, 2) array
    ids : (N,) array
        The id of the original seed each copy came from, so colors can be
        kept symmetric.
    """
    rng = rng or np.random.default_rng()
    R = radius * min(W, H)
    pts, ids, cid = [(0.0, 0.0)], [0], 1
    for k in range(1, rings + 1):
        r_k = R * k / rings
        for _ in range(max(1, k)):
            th = rng.uniform(0.12, 0.88) * np.pi / n_fold
            rr = r_k * (1 + rng.normal(0, 0.03))
            pts.append((rr * np.cos(th), rr * np.sin(th)))
            ids.append(cid)
            cid += 1
    pts, ids = np.array(pts), np.array(ids)
    out, oid = [], []
    for k in range(n_fold):
        a = 2 * np.pi * k / n_fold
        c, s_ = np.cos(a), np.sin(a)
        for sign in (1, -1):
            q = pts * [1, sign]
            out.append(
                np.column_stack(
                    [c * q[:, 0] - s_ * q[:, 1], s_ * q[:, 0] + c * q[:, 1]]
                )
            )
            oid.append(ids)
    out, oid = np.vstack(out), np.concatenate(oid)
    _, keep = np.unique(np.round(out, 3), axis=0, return_index=True)
    return out[keep] + [W / 2, H / 2], oid[keep]


# ---------- Geometry helpers ----------


def arc_points(cx, cy, r, deg0, deg1, n=24):
    """Points along a circular arc from ``deg0`` to ``deg1`` (in degrees)."""
    a = np.radians(np.linspace(deg0, deg1, n))
    return np.column_stack([cx + r * np.cos(a), cy + r * np.sin(a)])


def rotate_2d(pts, angle, centre=None):
    """Rotate 2-D points around ``centre`` (defaults to origin)."""
    pts = np.asarray(pts, dtype=float)
    if centre is not None:
        pts = pts - centre
    c, s = np.cos(angle), np.sin(angle)
    R = np.array([[c, -s], [s, c]])
    rotated = pts @ R.T
    if centre is not None:
        rotated = rotated + centre
    return rotated


def cubic_bezier(p, q, n=40, strength=0.55, normal_p=None, normal_q=None,
                 max_offset=0.2):
    """Cubic Bezier from ``p`` to ``q`` leaving along inward normals.

    max_offset : float, optional
        Upper limit on the control-point distance, in the same units as
        ``p`` and ``q``. ``None`` disables the cap. The default ``0.2`` is
        appropriate for unit-square tile coordinates.
    """
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)
    if normal_p is None:
        normal_p = (q - p) / (np.linalg.norm(q - p) + 1e-12)
    if normal_q is None:
        normal_q = (p - q) / (np.linalg.norm(p - q) + 1e-12)
    s = strength * np.linalg.norm(p - q)
    if max_offset is not None:
        s = min(s, max_offset)
    c1 = p + s * normal_p
    c2 = q + s * normal_q
    t = np.linspace(0, 1, n)[:, None]
    return (
        (1 - t) ** 3 * p
        + 3 * (1 - t) ** 2 * t * c1
        + 3 * (1 - t) * t**2 * c2
        + t**3 * q
    )


def matchings(idx):
    """All non-crossing pairings of a circularly ordered list (Catalan)."""
    if not idx:
        return [[]]
    out, first = [], idx[0]
    for k in range(1, len(idx), 2):
        for left in matchings(idx[1:k]):
            for right in matchings(idx[k + 1 :]):
                out.append([(first, idx[k])] + left + right)
    return out
