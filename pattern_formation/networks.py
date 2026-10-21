"""Adaptive flow networks on a grid (Hu and Cai, PRL 111, 138701, 2013).

Pixels are nodes, neighbouring pixels are joined by links, and each link has a
conductance ``C``.  Fluid enters at sources and leaves at sinks::

    L(C) p = s            pressure from sources/sinks  (L = weighted graph Laplacian)
    Q = C * (p_i - p_j)   flow along each link
    dC/dt = Q^2/C - nu * C**gamma

Busy links widen, idle links shrink.  The exponent ``gamma`` sets the cost of
wide links: below 1 the network settles into a tree, above 1 it keeps loops.
"""
import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import spsolve
from matplotlib.collections import LineCollection


__all__ = [
    "grid_edges",
    "solve_pressure",
    "link_flows",
    "adapt",
    "count_loops",
    "relax",
    "relax_fluctuating",
    "draw_network",
]


def grid_edges(n):
    """Links of an n x n grid as an (E, 2) array of node numbers (node = row*n + col)."""
    ids = np.arange(n * n).reshape(n, n)
    right = np.stack([ids[:, :-1].ravel(), ids[:, 1:].ravel()], axis=1)
    down = np.stack([ids[:-1, :].ravel(), ids[1:, :].ravel()], axis=1)
    return np.vstack([right, down])


def solve_pressure(edges, C, s):
    """Solve L(C) p = s, with node 0 held at pressure 0.  ``s`` must sum to zero."""
    N = len(s)
    i, j = edges.T
    W = sp.coo_matrix((C, (i, j)), shape=(N, N))
    W = W + W.T
    L = sp.diags(np.asarray(W.sum(axis=1)).ravel()) - W
    L = L.tocsr()[1:, 1:]
    p = np.zeros(N)
    p[1:] = spsolve(L.tocsc(), s[1:])
    return p


def link_flows(edges, C, p):
    """Flow along each link: conductance times pressure drop."""
    return C * (p[edges[:, 0]] - p[edges[:, 1]])


def adapt(C, Q2, nu=1.0, gamma=0.5, dt=0.1, floor=1e-6):
    """One explicit step of dC/dt = Q^2/C - nu C^gamma.  ``Q2`` is Q squared (or its average)."""
    C = C + dt * (Q2 / C - nu * C ** gamma)
    return np.maximum(C, floor)


def count_loops(edges, C, N, cutoff):
    """Independent loops among links with C > cutoff: links - nodes + components."""
    keep = edges[C > cutoff]
    graph = sp.coo_matrix((np.ones(len(keep)), (keep[:, 0], keep[:, 1])), shape=(N, N))
    n_components, _ = connected_components(graph, directed=False)
    return len(keep) - N + n_components


def relax(n, source, sinks, nu=1.0, gamma=0.5, dt=0.1, steps=2000, C0=None):
    """Adapt a grid network under a steady load until it settles.

    source : node number where fluid enters.
    sinks : node numbers that drain, sharing the inflow equally.
    Returns (edges, C).
    """
    N = n * n
    edges = grid_edges(n)
    s = np.zeros(N)
    s[sinks] = -1.0
    s[source] += len(sinks)
    C = np.ones(len(edges)) if C0 is None else C0.copy()
    for _ in range(steps):
        p = solve_pressure(edges, C, s)
        C = adapt(C, link_flows(edges, C, p) ** 2, nu, gamma, dt)
    return edges, C


def relax_fluctuating(n, source, sink_pool, k=5, draws=3, nu=1.0, gamma=0.5,
                      dt=0.1, steps=2000, rng=None, C0=None):
    """Like :func:`relax`, but the load moves: each step averages Q^2 over ``draws``
    random choices of ``k`` active sinks from ``sink_pool`` (each drains 1 unit).
    """
    rng = rng or np.random.default_rng()
    N = n * n
    edges = grid_edges(n)
    C = np.ones(len(edges)) if C0 is None else C0.copy()
    for _ in range(steps):
        Q2 = np.zeros(len(edges))
        for _ in range(draws):
            s = np.zeros(N)
            s[rng.choice(sink_pool, k, replace=False)] = -1.0
            s[source] += k
            Q2 += link_flows(edges, C, solve_pressure(edges, C, s)) ** 2
        C = adapt(C, Q2 / draws, nu, gamma, dt)
    return edges, C


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
