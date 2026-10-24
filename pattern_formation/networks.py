"""Adaptive flow networks on a grid (Hu and Cai, PRL 111, 138701, 2013).

Pixels are nodes, neighbouring pixels are joined by links, and each link has a
conductance ``C``.  Fluid enters at sources and leaves at sinks::

    L(C) p = s            pressure from sources/sinks  (L = weighted graph Laplacian)
    Q = C * (p_i - p_j)   flow along each link (divided by its length if links differ)
    dC/dt = Q^2/C - nu * C**gamma

Busy links widen, idle links shrink.  The exponent ``gamma`` sets the cost of
wide links: below 1 the network settles into a tree, above 1 it keeps loops.

The update is gradient descent on E = sum (Q^2/C + nu C^gamma / gamma) / 2 with mobility
f(C) = C (Klemm and Martens, arXiv:2407.04120, eq. 5, write the general family
dC/dt = -f(C) dE/dC).  Every f gives the same settled state, C = (Q^2/nu)^(1/(gamma+1)).
"""
import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spsolve, splu
from matplotlib.collections import LineCollection


__all__ = [
    "grid_edges",
    "solve_pressure",
    "link_flows",
    "adapt",
    "count_loops",
    "relax",
    "relax_fluctuating",
    "relax_graph",
    "relax_fluctuating_graph",
    "moving_load_Q2",
    "relax_moving_graph",
    "masked_grid",
    "largest_piece",
    "draw_network",
]


def grid_edges(n):
    """Links of an n x n grid as an (E, 2) array of node numbers (node = row*n + col)."""
    ids = np.arange(n * n).reshape(n, n)
    right = np.stack([ids[:, :-1].ravel(), ids[:, 1:].ravel()], axis=1)
    down = np.stack([ids[:-1, :].ravel(), ids[1:, :].ravel()], axis=1)
    return np.vstack([right, down])


def _laplacian(edges, C, N):
    """Weighted graph Laplacian of the network (N x N, sparse)."""
    i, j = edges.T
    W = sp.coo_matrix((C, (i, j)), shape=(N, N))
    W = W + W.T
    return (sp.diags(np.asarray(W.sum(axis=1)).ravel()) - W).tocsr()


def _per_length(C, length):
    """Link conductance for flow: C, or C / length when links have different lengths."""
    return C if length is None else C / length


def solve_pressure(edges, C, s, length=None):
    """Solve L(C) p = s, with node 0 held at pressure 0.  ``s`` must sum to zero.

    ``length`` (one per link, default all 1) makes the flow in a link C * drop / length."""
    N = len(s)
    L = _laplacian(edges, _per_length(C, length), N)[1:, 1:]
    p = np.zeros(N)
    p[1:] = spsolve(L.tocsc(), s[1:])
    return p


def link_flows(edges, C, p, length=None):
    """Flow along each link: conductance times pressure drop (over its length)."""
    return _per_length(C, length) * (p[edges[:, 0]] - p[edges[:, 1]])


def adapt(C, Q2, nu=1.0, gamma=0.5, dt=0.1, floor=1e-6):
    """One implicit step of dC/dt = Q^2/C - nu C^gamma.  ``Q2`` is Q squared (or its average).

    The explicit step is unstable for weak links (its rate is about C^(gamma-1)), so each
    link solves x^2 + dt nu x^(gamma+1) - C x - dt Q2 = 0 for the new C by Newton's method.
    The left side is convex, so starting right of the root the iteration falls onto it.
    """
    x = 0.5 * (C + np.sqrt(C * C + 4 * dt * Q2))  # root without the upkeep term: f(x) >= 0
    for _ in range(8):
        f = x * x + dt * nu * x ** (gamma + 1) - C * x - dt * Q2
        x = x - f / (2 * x + dt * nu * (gamma + 1) * x ** gamma - C)
    return np.maximum(x, floor)


def count_loops(edges, C, N, cutoff):
    """Independent loops among links with C > cutoff: links - nodes + components."""
    keep = edges[C > cutoff]
    graph = sp.coo_matrix((np.ones(len(keep)), (keep[:, 0], keep[:, 1])), shape=(N, N))
    n_components, _ = connected_components(graph, directed=False)
    return len(keep) - N + n_components


def relax_graph(edges, s, nu=1.0, gamma=0.5, dt=0.1, steps=2000, C0=None, length=None):
    """Adapt any connected graph under the steady load ``s`` (sums to zero).  Returns C."""
    C = np.ones(len(edges)) if C0 is None else C0.copy()
    for _ in range(steps):
        p = solve_pressure(edges, C, s, length)
        C = adapt(C, link_flows(edges, C, p, length) ** 2, nu, gamma, dt)
    return C


def relax(n, source, sinks, nu=1.0, gamma=0.5, dt=0.1, steps=2000, C0=None):
    """Adapt an n x n grid network under a steady load until it settles.

    source : node number where fluid enters.
    sinks : node numbers that drain, sharing the inflow equally.
    Returns (edges, C).
    """
    s = np.zeros(n * n)
    s[sinks] = -1.0
    s[source] += len(sinks)
    edges = grid_edges(n)
    return edges, relax_graph(edges, s, nu, gamma, dt, steps, C0)


def relax_fluctuating_graph(edges, N, source, sink_pool, k=5, draws=3, nu=1.0,
                            gamma=0.5, dt=0.1, steps=2000, rng=None, C0=None):
    """Moving load on any graph: each step averages Q^2 over ``draws`` random
    choices of ``k`` active sinks from ``sink_pool`` (each drains 1 unit).  Returns C.
    """
    rng = rng or np.random.default_rng()
    C = np.ones(len(edges)) if C0 is None else C0.copy()
    for _ in range(steps):
        Q2 = np.zeros(len(edges))
        for _ in range(draws):
            s = np.zeros(N)
            s[rng.choice(sink_pool, k, replace=False)] = -1.0
            s[source] += k
            Q2 += link_flows(edges, C, solve_pressure(edges, C, s)) ** 2
        C = adapt(C, Q2 / draws, nu, gamma, dt)
    return C


def relax_fluctuating(n, source, sink_pool, k=5, draws=3, nu=1.0, gamma=0.5,
                      dt=0.1, steps=2000, rng=None, C0=None):
    """Like :func:`relax`, but the load moves (see :func:`relax_fluctuating_graph`)."""
    edges = grid_edges(n)
    C = relax_fluctuating_graph(edges, n * n, source, sink_pool, k, draws, nu,
                                gamma, dt, steps, rng, C0)
    return edges, C


def moving_load_Q2(edges, C, N, source, sinks, alpha, length=None):
    """Mean of Q^2 over a moving load, averaged exactly over which sink is busy.

    The source supplies 1 unit.  Every sink drains (1 - alpha)/m, and one sink, chosen
    uniformly from the m ``sinks``, drains alpha more (Klemm and Martens, arXiv:2407.04120).
    alpha = 0 is the steady uniform load, alpha = 1 a single sink open at a time.
    """
    m = len(sinks)
    S = np.zeros((N, m))
    S[sinks, :] = -(1 - alpha) / m
    S[sinks, np.arange(m)] -= alpha
    S[source, :] += 1.0
    g = _per_length(C, length)
    p = np.zeros((N, m))
    p[1:] = splu(_laplacian(edges, g, N)[1:, 1:].tocsc()).solve(S[1:])
    Q = g[:, None] * (p[edges[:, 0]] - p[edges[:, 1]])
    return (Q ** 2).mean(axis=1)


def relax_moving_graph(edges, N, source, sinks, alpha, nu=1.0, gamma=0.5, dt=0.1,
                       steps=2000, C0=None, length=None):
    """Adapt a graph under the moving load of :func:`moving_load_Q2`.  Returns C."""
    C = np.ones(len(edges)) if C0 is None else C0.copy()
    for _ in range(steps):
        C = adapt(C, moving_load_Q2(edges, C, N, source, sinks, alpha, length), nu, gamma, dt)
    return C


def masked_grid(mask):
    """Grid graph on the True pixels of ``mask[iy, ix]`` (largest connected piece only).

    Returns (xy, edges): pixel coordinates (x, y) of each node, and 4-neighbour links
    numbered 0..N-1, ready for :func:`relax_graph`.
    """
    ids = -np.ones(mask.shape, dtype=int)
    ids[mask] = np.arange(mask.sum())
    pairs = []
    for a, b in [(ids[:, :-1], ids[:, 1:]), (ids[:-1, :], ids[1:, :])]:
        ok = (a >= 0) & (b >= 0)
        pairs.append(np.stack([a[ok], b[ok]], axis=1))
    edges = np.vstack(pairs)
    iy, ix = np.nonzero(mask)
    xy = np.stack([ix, iy], axis=1).astype(float)
    return largest_piece(xy, edges)


def largest_piece(xy, edges):
    """Keep only the biggest connected piece of a graph; nodes are renumbered 0..N-1."""
    N = len(xy)
    graph = sp.coo_matrix((np.ones(len(edges)), (edges[:, 0], edges[:, 1])), shape=(N, N))
    _, label = connected_components(graph, directed=False)
    keep = label == np.bincount(label).argmax()
    new_id = -np.ones(N, dtype=int)
    new_id[keep] = np.arange(keep.sum())
    edges = new_id[edges[keep[edges[:, 0]]]]
    return xy[keep], edges


def draw_network(ax, n, edges, C, cutoff=0.0, width=4.0, color="k"):
    """Draw links with line width proportional to C (links at or below ``cutoff`` hidden)."""
    xy = np.stack([np.arange(n * n) % n, -(np.arange(n * n) // n)], axis=1)
    keep = C > cutoff
    segs = xy[edges[keep]]
    ax.add_collection(LineCollection(segs, linewidths=width * C[keep] / C.max(), colors=color))
    ax.set_xlim(-1, n)
    ax.set_ylim(-n, 1)
    ax.set_aspect("equal")
    ax.axis("off")
