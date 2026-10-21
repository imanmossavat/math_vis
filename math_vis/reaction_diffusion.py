"""Gray-Scott reaction-diffusion: simulation, measurement, and rendering.

Two chemicals live on a periodic grid. ``A`` is fed in, ``B`` eats ``A`` to
make more ``B`` and slowly dies. Both diffuse, ``A`` faster than ``B``::

    A' = A + (dA * lap(A) - A*B*B + f*(1 - A)) * dt
    B' = B + (dB * lap(B) + A*B*B - (k + f)*B) * dt

Defaults follow Karl Sims' tutorial (https://karlsims.com/rd.html).
``f``, ``k``, ``dA`` and ``dB`` may be scalars or arrays of the grid shape, so
the rules can change across the image.

Like ``basins``, this module may import from ``math_vis`` but nothing in the
package depends on it.
"""
import numpy as np
from matplotlib.colors import LightSource

from .math_tools import smooth_field
from .utils import make_cmap, new_rng
from .finishing import finish


__all__ = [
    "laplacian",
    "initial_state",
    "gray_scott",
    "param_map",
    "radial_spectrum",
    "dominant_wavelength",
    "render_rd",
    "render_reaction_diffusion",
]


DEFAULT_PALETTE = ["#0b1d3a", "#1f4e8c", "#2aa5c9", "#58d3c0", "#f4e285",
                   "#f59e3b", "#e0453a", "#8e2a6a", "#3a1d6e"]


def laplacian(X):
    """9-point Laplacian with periodic edges (centre -1, sides 0.2, corners 0.05)."""
    up, down = np.roll(X, 1, 0), np.roll(X, -1, 0)
    side = up + down + np.roll(X, 1, 1) + np.roll(X, -1, 1)
    corner = (np.roll(up, 1, 1) + np.roll(up, -1, 1)
              + np.roll(down, 1, 1) + np.roll(down, -1, 1))
    return 0.2 * side + 0.05 * corner - X


def initial_state(shape, rng=None, kind="spots", n=12, radius=4, noise=0.0):
    """Starting fields: ``A = 1`` everywhere, ``B`` seeded where chosen.

    kind : "spots" (n random squares), "center" (one square), or "noise"
        ("noise" puts small uniform B everywhere).
    """
    rng = rng or np.random.default_rng()
    H, W = shape
    A = np.ones(shape)
    B = np.zeros(shape)
    if kind == "noise":
        B = rng.uniform(0, 0.25, shape)
    else:
        centres = ([(H // 2, W // 2)] if kind == "center"
                   else zip(rng.integers(0, H, n), rng.integers(0, W, n)))
        for r, c in centres:
            rows = np.arange(r - radius, r + radius) % H
            cols = np.arange(c - radius, c + radius) % W
            B[np.ix_(rows, cols)] = 1.0
    if noise > 0:
        B = np.clip(B + rng.uniform(-noise, noise, shape), 0, 1)
    return A, B


def gray_scott(shape=(256, 256), f=0.055, k=0.062, dA=1.0, dB=0.5,
               steps=5000, dt=1.0, rng=None, init="spots", state=None,
               snapshot_every=None):
    """Run the Gray-Scott model.

    Parameters
    ----------
    shape : (H, W)
    f, k, dA, dB : float or (H, W) array
        Feed rate, kill rate and diffusion rates.  Explicit Euler is only
        stable for ``max(dA, dB) * dt < 1.25``.
    steps : int
    init : str
        ``kind`` passed to :func:`initial_state` when ``state`` is None.
    state : (A, B), optional
        Continue from an existing state (not modified in place).
    snapshot_every : int, optional
        If given, also return a list of ``B`` copies taken every so many steps.

    Returns
    -------
    A, B : np.ndarray  (and ``frames`` if ``snapshot_every`` is set)
    """
    if np.max(np.maximum(dA, dB)) * dt >= 1.25:
        raise ValueError("unstable: need max(dA, dB) * dt < 1.25")
    rng = rng or np.random.default_rng()
    if state is None:
        A, B = initial_state(shape, rng, kind=init)
    else:
        A, B = state
    # float32 halves the cost and is plenty for pattern formation
    A, B = (np.array(x, dtype=np.float32) for x in (A, B))
    f, k, dA, dB, dt = (np.asarray(x, dtype=np.float32) for x in (f, k, dA, dB, dt))
    frames = []
    for i in range(steps):
        ABB = A * B * B
        A, B = (A + (dA * laplacian(A) - ABB + f * (1 - A)) * dt,
                B + (dB * laplacian(B) + ABB - (k + f) * B) * dt)
        # Concentrations stay in [0, 1]; clamping stops Euler overshoot in
        # extreme corners of rule space and is a no-op elsewhere.
        np.clip(A, 0, 1, out=A)
        np.clip(B, 0, 1, out=B)
        if snapshot_every and (i + 1) % snapshot_every == 0:
            frames.append(B.copy())
    return (A, B, frames) if snapshot_every else (A, B)


def param_map(shape, f_range=(0.01, 0.10), k_range=(0.045, 0.07)):
    """Feed varies bottom-to-top, kill left-to-right: a map of the rule space."""
    H, W = shape
    f = np.linspace(*f_range, H)[::-1, None] * np.ones((1, W))
    k = np.linspace(*k_range, W)[None, :] * np.ones((H, 1))
    return f, k


def radial_spectrum(field):
    """Radially averaged power spectrum.

    Returns
    -------
    freq : cycles per pixel, power : mean power in each ring (DC removed).
    """
    field = np.asarray(field, dtype=float)
    H, W = field.shape
    P = np.abs(np.fft.fft2(field - field.mean())) ** 2
    fy = np.fft.fftfreq(H)[:, None]
    fx = np.fft.fftfreq(W)[None, :]
    n = min(H, W)
    ring = np.rint(np.hypot(fy, fx) * n).astype(int).ravel()  # ring width 1/n
    power = np.bincount(ring, P.ravel())
    count = np.bincount(ring)
    rings = np.arange(1, n // 2 + 1)  # skip DC, stop at Nyquist
    return rings / n, power[rings] / np.maximum(count[rings], 1)


def dominant_wavelength(field):
    """Typical pattern spacing in pixels (power-weighted mean frequency)."""
    freq, power = radial_spectrum(field)
    if power.sum() == 0:
        return np.nan
    return 1.0 / (np.sum(freq * power) / np.sum(power))


def render_rd(B, palette=None, emboss=4.0, light=(315, 45), blend=0.55):
    """Color ``B`` with a palette and light it as if it were a height map.

    emboss : height scale for the relief (0 = flat colors).
    Returns a uint8 RGB array.
    """
    B = np.asarray(B, dtype=float)
    lo, hi = np.percentile(B, [1, 99])
    t = np.clip((B - lo) / (hi - lo + 1e-12), 0, 1)
    cmap = make_cmap(palette or DEFAULT_PALETTE)
    rgb = cmap(t)[..., :3]
    if emboss > 0:
        ls = LightSource(azdeg=light[0], altdeg=light[1])
        rgb = ls.shade_rgb(rgb, t, vert_exag=emboss, blend_mode="soft",
                           fraction=blend)
    return (np.clip(rgb, 0, 1) * 255).astype(np.uint8)


def render_reaction_diffusion(seed=None, size=384, steps=8000,
                              f_range=(0.018, 0.050), k=0.062,
                              smooth=40, palette=None, emboss=4.0, grain=2.0):
    """Gray-Scott with feed rate drifting smoothly across the canvas.

    Different regions obey different rules, so spots, stripes and mazes
    blend into each other. Returns a finished uint8 RGB array.
    """
    rng = new_rng(seed)
    shape = (size, size)
    g = smooth_field(shape, smooth, rng)
    g = (g - g.min()) / (g.max() - g.min())
    f = f_range[0] + (f_range[1] - f_range[0]) * g
    _, B = gray_scott(shape, f=f, k=k, steps=steps, rng=rng, init="spots")
    img = render_rd(B, palette=palette, emboss=emboss)
    return finish(img, grain=grain, display=False)
