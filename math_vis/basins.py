"""Basins of attraction for Newton's method on z^n - 1.

This module is intentionally one-directional: it may import from the rest of
``math_vis``, but no other module depends on it.
"""
import numpy as np
from matplotlib import colormaps as _mpl_colormaps

from .utils import make_cmap


__all__ = [
    "roots_unity",
    "complex_grid",
    "basin_map",
    "fast_lyapunov_indicator",
    "uncertainty_exponent",
    "basin_entropy",
    "normalize_iters",
    "render_basins",
    "render_fli",
]


# A small, distinct palette.  Red is deliberately first because the user likes
# red-forward Newton fractals.
DEFAULT_PALETTE = [
    "#e41a1c",  # red
    "#377eb8",  # blue
    "#4daf4a",  # green
    "#984ea3",  # purple
    "#ff7f00",  # orange
    "#ffff33",  # yellow
    "#a65628",  # brown
    "#f781bf",  # pink
]


def roots_unity(n):
    """Return the ``n`` complex roots of ``z**n - 1``.

    Parameters
    ----------
    n : int
        Degree of the polynomial.

    Returns
    -------
    np.ndarray
        1-D complex array of length ``n``.
    """
    n = int(n)
    if n < 1:
        raise ValueError("n must be a positive integer")
    return np.exp(2j * np.pi * np.arange(n) / n)


def complex_grid(extent, shape):
    """Build a 2-D complex sampling grid.

    Parameters
    ----------
    extent : tuple(float, float, float, float)
        ``(xmin, xmax, ymin, ymax)`` in the complex plane.
    shape : tuple(int, int)
        ``(height, width)`` of the desired grid.

    Returns
    -------
    np.ndarray
        2-D complex array with shape ``(height, width)``.
    """
    xmin, xmax, ymin, ymax = extent
    height, width = shape
    x = np.linspace(xmin, xmax, width)
    y = np.linspace(ymin, ymax, height)
    xx, yy = np.meshgrid(x, y)
    return xx + 1j * yy


def _newton_step(z, n):
    """One Newton step for ``z**n - 1``.

    The derivative is protected against ``z == 0`` so the iteration stays
    well-defined everywhere.
    """
    zn = z ** n
    d = n * z ** (n - 1)
    # Replace zero derivatives by a tiny real number.  This only matters at the
    # origin and a few pathological lattice points; the perturbation kicks the
    # iterate back into play.
    d = np.where(np.abs(d) < 1e-30, 1e-30 + 0j, d)
    return z - (zn - 1.0) / d


def _newton_derivative(z, n):
    """Magnitude of the Newton-map derivative for ``z**n - 1``.

    ``N(z) = z - f(z)/f'(z)`` with ``f(z) = z**n - 1``.  A short derivation
    gives ``N'(z) = (n-1)*(z**n - 1) / (n*z**n)``.
    """
    zn = z ** n
    num = (n - 1) * (zn - 1.0)
    den = n * zn
    den = np.where(np.abs(den) < 1e-30, 1e-30 + 0j, den)
    return np.abs(num / den)


def basin_map(z0, n, max_iter=80, tol=1e-6, dtype=np.complex128):
    """Compute basins, settling times, and FLI for Newton on ``z**n - 1``.

    Parameters
    ----------
    z0 : np.ndarray
        2-D array of complex starting points.
    n : int
        Degree of the polynomial.
    max_iter : int
        Maximum number of Newton iterations.
    tol : float
        Distance to a root that counts as convergence.
    dtype : {np.complex64, np.complex128}
        Precision of the iteration.  Use ``np.complex64`` to demonstrate
        precision loss on deep zooms.

    Returns
    -------
    basin : np.ndarray
        Integer array with the index of the root each point converged to, or
        ``-1`` for points that did not converge within ``max_iter``.
    iters : np.ndarray
        Integer array with the number of iterations to convergence.  Points
        that did not converge are set to ``max_iter``.
    fli : np.ndarray
        Fast Lyapunov indicator map (base-10 logarithm of ``1 + sum |N'|^2``).
    """
    n = int(n)
    z0 = np.asarray(z0)
    if z0.ndim != 2:
        raise ValueError("z0 must be a 2-D array")

    roots = roots_unity(n)
    z = np.array(z0, dtype=dtype, copy=True)

    basin = np.full(z0.shape, -1, dtype=np.int32)
    iters = np.full(z0.shape, max_iter, dtype=np.int32)
    fli_sum = np.zeros(z0.shape, dtype=np.float64)

    active = np.ones(z0.shape, dtype=bool)

    for k in range(max_iter):
        if not np.any(active):
            break

        z_active = z[active]
        z_new = _newton_step(z_active, n)
        z[active] = z_new

        # Accumulate squared derivative magnitudes for the FLI.
        fli_sum[active] += _newton_derivative(z_active, n) ** 2

        # Find nearest root and check convergence.
        dists = np.abs(z_new[:, None] - roots[None, :])
        nearest = np.argmin(dists, axis=1)
        converged = np.min(dists, axis=1) < tol

        idx = np.argwhere(active)
        new_conv = idx[converged]
        basin[tuple(new_conv.T)] = nearest[converged]
        iters[tuple(new_conv.T)] = k + 1
        active[tuple(new_conv.T)] = False

    # Assign any still-active points to their nearest root for coloring.
    remaining = np.argwhere(active)
    if remaining.size:
        dists = np.abs(z[remaining[:, 0], remaining[:, 1]][:, None] - roots[None, :])
        basin[tuple(remaining.T)] = np.argmin(dists, axis=1)

    fli = np.log10(1.0 + fli_sum)
    return basin, iters, fli


def fast_lyapunov_indicator(z0, n, max_iter=80, dtype=np.complex128):
    """Convenience wrapper that returns only the FLI map from :func:`basin_map`."""
    _, _, fli = basin_map(z0, n, max_iter=max_iter, tol=1e-6, dtype=dtype)
    return fli


def uncertainty_exponent(basin, box_sizes=None):
    """Estimate the uncertainty exponent ``alpha`` from a basin map.

    For each box size ``b`` we tile the image into non-overlapping ``b x b``
    blocks and measure ``P_both(b)``, the fraction of blocks that contain more
    than one basin label.  If the basin boundary is fractal with box-counting
    dimension ``D`` in a 2-D plane, ``P_both ~ b**alpha`` with ``alpha = 2 - D``.
    A straight boundary has ``D = 1`` and therefore ``alpha = 1``.

    Parameters
    ----------
    basin : np.ndarray
        Integer basin-label array.
    box_sizes : sequence of int, optional
        Box sizes to use.  Defaults to ``[4, 8, 16, 32, 64]``.

    Returns
    -------
    dict
        ``{"alpha": float, "box_sizes": array, "p_both": array,
        "log_b": array, "log_p": array, "intercept": float}``.
        ``alpha`` is ``nan`` if a fit cannot be computed.
    """
    basin = np.asarray(basin)
    if basin.ndim != 2:
        raise ValueError("basin must be 2-D")

    H, W = basin.shape
    if box_sizes is None:
        box_sizes = [4, 8, 16, 32, 64]
    box_sizes = np.array([b for b in box_sizes if b <= min(H, W)])
    if box_sizes.size < 2:
        return {"alpha": np.nan, "box_sizes": box_sizes, "p_both": np.array([])}

    p_both = []
    for b in box_sizes:
        h = H - H % b
        w = W - W % b
        # Reshape to (n_rows, box, n_cols, box) and then collapse the two box axes.
        view = basin[:h, :w].reshape(h // b, b, w // b, b)
        view = view.transpose(0, 2, 1, 3).reshape(h // b, w // b, b * b)
        # A block is "mixed" if not every cell equals the first cell.
        mixed = np.any(view[:, :, 0:1] != view, axis=2)
        p_both.append(mixed.mean())
    p_both = np.asarray(p_both)

    # Fit log(P_both) vs log(box_size).  Only use the unsaturated middle of the
    # curve, because at very small b noise dominates and at very large b every
    # block is mixed.
    valid = (p_both > 0) & (p_both < 1)
    if valid.sum() < 2:
        return {
            "alpha": np.nan,
            "box_sizes": box_sizes,
            "p_both": p_both,
        }

    log_b = np.log(box_sizes[valid])
    log_p = np.log(p_both[valid])
    alpha, intercept = np.polyfit(log_b, log_p, 1)

    return {
        "alpha": float(alpha),
        "intercept": float(intercept),
        "box_sizes": box_sizes,
        "p_both": p_both,
        "log_b": log_b,
        "log_p": log_p,
    }


def basin_entropy(basin, box_sizes=None):
    """Average Shannon entropy of basin labels inside non-overlapping boxes.

    Parameters
    ----------
    basin : np.ndarray
        Integer basin-label array.
    box_sizes : sequence of int, optional
        Box sizes to scan.  Defaults to ``[4, 8, 16, 32]``.

    Returns
    -------
    box_sizes : np.ndarray
        The box sizes that were actually used.
    entropies : np.ndarray
        Average Shannon entropy per block for each box size.
    """
    basin = np.asarray(basin)
    H, W = basin.shape
    if box_sizes is None:
        box_sizes = [4, 8, 16, 32]
    box_sizes = [b for b in box_sizes if b <= min(H, W)]

    entropies = []
    for b in box_sizes:
        h = H - H % b
        w = W - W % b
        view = basin[:h, :w].reshape(h // b, b, w // b, b)
        view = view.transpose(0, 2, 1, 3).reshape(h // b, w // b, b * b)
        total = 0.0
        n_blocks = view.shape[0] * view.shape[1]
        for block in view.reshape(n_blocks, b * b):
            labels, counts = np.unique(block, return_counts=True)
            p = counts / counts.sum()
            total -= np.sum(p * np.log(p))
        entropies.append(total / n_blocks)

    return np.array(box_sizes), np.array(entropies)


def normalize_iters(iters, mode="log1p", gamma=1.0, max_iter=None):
    """Map iteration counts to ``[0, 1]`` for brightness mapping.

    Settling times have heavy tails, so several normalisations are offered.

    Parameters
    ----------
    iters : np.ndarray
        Integer iteration counts.
    mode : {"linear", "sqrt", "log1p"}
        Normalisation function.
    gamma : float
        Final gamma curve.  ``gamma < 1`` brightens the dark tail.
    max_iter : int, optional
        Maximum to normalise against; defaults to ``iters.max()``.
    """
    iters = np.asarray(iters, dtype=np.float64)
    if max_iter is None:
        max_iter = int(iters.max())
    if max_iter <= 0:
        return np.zeros_like(iters)

    t = iters / max_iter
    if mode == "linear":
        y = t
    elif mode == "sqrt":
        y = np.sqrt(t)
    elif mode == "log1p":
        y = np.log1p(iters) / np.log1p(max_iter)
    else:
        raise ValueError(f"Unknown normalisation mode: {mode!r}")

    if gamma != 1.0:
        y = y ** gamma
    return np.clip(y, 0.0, 1.0)


def render_basins(
    basin,
    iters,
    palette=None,
    hue_shift=0.0,
    norm="log1p",
    gamma=1.0,
    bright="fast",
    bg=(0, 0, 0),
):
    """Render a basin map as a uint8 RGB image.

    Hue comes from the attractor (basin label).  Brightness comes from the
    settling time: by default fast-converging points are bright and slow,
    tangled boundary regions are darker.

    Parameters
    ----------
    basin : np.ndarray
        Integer basin-label array (``-1`` for unconverged).
    iters : np.ndarray
        Integer iteration counts.
    palette : list of str, optional
        List of matplotlib-compatible colors, one per root (cycled if too short).
    hue_shift : float
        Global hue rotation in ``[0, 1]``.
    norm : {"linear", "sqrt", "log1p"}
        Settling-time normalisation.
    gamma : float
        Gamma curve applied after normalisation.
    bright : {"fast", "slow"}
        Whether fast or slow points are bright.
    bg : sequence of float
        RGB background color for unconverged points.

    Returns
    -------
    np.ndarray
        ``uint8`` RGB image.
    """
    basin = np.asarray(basin)
    iters = np.asarray(iters)
    if basin.shape != iters.shape:
        raise ValueError("basin and iters must have the same shape")

    n_roots = int(basin.max()) + 1 if basin.max() >= 0 else 0
    if n_roots == 0:
        return np.zeros((*basin.shape, 3), dtype=np.uint8)

    v = normalize_iters(iters, mode=norm, gamma=gamma)
    if bright == "fast":
        value = 1.0 - v
    elif bright == "slow":
        value = v
    else:
        raise ValueError("bright must be 'fast' or 'slow'")

    if palette is None:
        palette = DEFAULT_PALETTE
    cmap = make_cmap(palette)

    # Map root index to a palette coordinate, with optional rotation.
    t = ((basin % n_roots) / n_roots + hue_shift) % 1.0
    rgb = cmap(t)[:, :, :3]
    rgb = rgb * value[:, :, None]

    unconverged = basin < 0
    rgb = rgb.copy()
    rgb[unconverged] = np.asarray(bg, dtype=float)

    return (np.clip(rgb, 0.0, 1.0) * 255).astype(np.uint8)


def render_fli(fli, cmap="magma", lo=1, hi=99):
    """Render an FLI map as a uint8 RGB edge image.

    Parameters
    ----------
    fli : np.ndarray
        Fast Lyapunov indicator array.
    cmap : str
        Matplotlib colormap name.
    lo, hi : float
        Percentiles used for contrast stretching.

    Returns
    -------
    np.ndarray
        ``uint8`` RGB image.
    """
    fli = np.asarray(fli)
    cmap = _mpl_colormaps.get_cmap(cmap)
    vmin = np.percentile(fli, lo)
    vmax = np.percentile(fli, hi)
    t = np.clip((fli - vmin) / (vmax - vmin + 1e-12), 0.0, 1.0)
    rgb = cmap(t)[:, :, :3]
    return (np.clip(rgb, 0.0, 1.0) * 255).astype(np.uint8)
