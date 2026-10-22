"""Leaf venation by space colonization (Runions et al.) and shared vein drawing.

Veins grow toward scattered "auxin sources" inside a leaf outline::

    sources     placed at random, never closer than b to each other or to a vein
    association each source belongs to its nearest vein node (open venation) or to
                every node that is its relative neighbour (closed venation)
    growth      a node with sources steps D toward the mean direction of its sources
    kill        a source disappears once a vein is within d_k of it

Open venation always makes a tree.  Closed venation lets several veins reach one
source and joins them there, which makes loops.  Vein widths follow Murray's law,
r_parent^n = sum of r_child^n.

Every network here is the triple ``(xy, edges, width)``, the same shape the flow
networks in ``networks.py`` produce, so both can be measured and drawn alike.
Lengths are in units of the final leaf length (the leaf is 1 long).
"""
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.path import Path
from scipy.spatial import cKDTree

from math_vis.utils import make_cmap, fig_to_img
from pattern_formation.networks import count_loops, masked_grid


__all__ = [
    "SHAPES",
    "PALETTE",
    "leaf_outline",
    "inside",
    "grow_veins",
    "leaf_grid",
    "murray_widths",
    "vein_stats",
    "draw_veins",
    "render_veins",
]

SHAPES = ("ovate", "elliptic", "lanceolate", "round", "lobed")
PALETTE = ["#10331f", "#1f6b3a", "#6fae3f", "#d8d26a", "#fff6c2"]
BG = "#0d1411"


# --- leaf outline ------------------------------------------------------------

def leaf_outline(shape="ovate", n=120):
    """Closed polygon (M, 2) of a leaf 1 long: base at (0, 0), tip at (0, 1), y up."""
    s = np.linspace(0, 1, n)
    if shape == "elliptic":
        w = 0.24 * np.sin(np.pi * s) ** 0.9
    elif shape == "lanceolate":
        w = 0.14 * np.sin(np.pi * s ** 0.8)
    elif shape == "round":
        w = 0.40 * np.sin(np.pi * s) ** 0.6
    elif shape == "lobed":
        w = 0.30 * np.sin(np.pi * s ** 0.7) * (1 + 0.28 * np.cos(2 * np.pi * 4 * s))
    else:  # ovate: widest near the base
        w = 0.30 * np.sin(np.pi * s ** 0.7)
    right = np.stack([w, s], axis=1)
    left = np.stack([-w, s], axis=1)[::-1]
    return np.vstack([right, left[1:-1]])


def inside(poly, pts):
    """Boolean mask: which of ``pts`` (K, 2) lie inside the polygon."""
    return Path(poly).contains_points(pts)


def _area(poly):
    x, y = poly.T
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


# --- space colonization ------------------------------------------------------

def _throw_darts(poly, rng, rho, b, sources, nodes):
    """New sources by dart throwing: inside the leaf, at least b from everything."""
    lo, hi = poly.min(axis=0), poly.max(axis=0)
    m = rng.poisson(rho * _area(poly))
    pts = rng.uniform(lo, hi, size=(m, 2))
    pts = pts[inside(poly, pts)]
    for others in (nodes, sources):
        if len(pts) and len(others):
            pts = pts[cKDTree(others).query(pts)[0] > b]
    kept = []
    for p in pts:  # darts must also keep their distance from each other
        if all(np.hypot(*(p - q)) > b for q in kept):
            kept.append(p)
    return np.array(kept).reshape(-1, 2)


def _relative_neighbors(src, nodes, tree, m=12):
    """For each source, which of its m nearest nodes v are relative neighbours:
    no node u has both d(s,u) < d(s,v) and d(v,u) < d(s,v).  Returns (idx, rn, d)."""
    k = min(m, len(nodes))
    d, idx = tree.query(src, k=k)
    d, idx = d.reshape(len(src), k), idx.reshape(len(src), k)
    P = nodes[idx]
    dvu = np.linalg.norm(P[:, :, None, :] - P[:, None, :, :], axis=3)
    blocked = np.maximum(d[:, None, :], dvu) < d[:, :, None] - 1e-12
    blocked &= ~np.eye(k, dtype=bool)
    return idx, ~blocked.any(axis=2), d


def _associate(src, nodes, closed, kill):
    """Pairs (source, node, distance) of sources and the nodes that pull on them."""
    tree = cKDTree(nodes)
    if not closed:
        d, j = tree.query(src)
        return np.arange(len(src)), j, d
    idx, rn, d = _relative_neighbors(src, nodes, tree)
    i, c = np.nonzero(rn)
    return i, idx[i, c], d[i, c]


def _grow_step(xy, src, closed, kill, step):
    """Propose new nodes.  Returns (parents, positions) of the nodes to add."""
    si, ni, dist = _associate(src, xy, closed, kill)
    pull = dist > kill  # a vein already close enough stops growing toward it
    si, ni = si[pull], ni[pull]
    vec = src[si] - xy[ni]
    vec /= np.linalg.norm(vec, axis=1, keepdims=True)
    total = np.zeros_like(xy)
    np.add.at(total, ni, vec)
    norm = np.linalg.norm(total, axis=1)
    grow = np.nonzero(norm > 1e-9)[0]
    return grow, xy[grow] + step * total[grow] / norm[grow, None]


def _kill_sources(xy, src, age, closed, kill, max_age):
    """Remove reached sources.  Returns (alive mask, merges) where merges lists
    (source position, member nodes) for closed venation joins."""
    tree = cKDTree(xy)
    merges = []
    if not closed:
        alive = tree.query(src)[0] > kill
    else:
        idx, rn, d = _relative_neighbors(src, xy, tree)
        reached = (d <= kill) | ~rn  # members that are not relative neighbours don't count
        alive = ~(rn.any(axis=1) & reached.all(axis=1))
        for i in np.nonzero(~alive)[0]:
            members = idx[i][rn[i]]
            if len(members) >= 2:
                merges.append((src[i], members))
    return alive & (age < max_age), merges


def grow_veins(poly, b=0.05, kill=0.02, step=0.01, steps=200, closed=False,
               start_size=0.3, grow_steps=80, rho=3000.0, max_age=150, seed=0):
    """Grow veins inside the leaf ``poly``.

    b : birth distance, the spacing of sources.   kill : kill distance d_k.
    step : length of one vein segment.   closed : loops allowed.
    start_size : leaf scale at step 0 (1 = no growth); it grows linearly to 1
        over ``grow_steps`` steps, scaling about the base.
    rho : dart-throwing rate, darts per unit area per step.

    Returns a dict: ``xy`` (N, 2), ``edges`` (E, 2), ``parent`` (N,) (first parent,
    -1 at the root), and a history for scrubbing: ``n_nodes``, ``n_edges``,
    ``sources`` and ``size`` per step.
    """
    rng = np.random.default_rng(seed)
    xy = np.array([[0.0, 0.01]])
    parent = [-1]
    edges = []
    src = np.zeros((0, 2))
    age = np.zeros(0)
    hist = dict(n_nodes=[], n_edges=[], sources=[], size=[])
    for t in range(steps):
        size = min(1.0, start_size + (1 - start_size) * t / max(grow_steps, 1))
        leaf = poly * size
        new = _throw_darts(leaf, rng, rho, b, src, xy)
        src, age = np.vstack([src, new]), np.concatenate([age, np.zeros(len(new))])
        if len(src):
            who, pos = _grow_step(xy, src, closed, kill, step)
            ok = inside(leaf, pos)
            who, pos = who[ok], pos[ok]
            edges += [(v, len(xy) + j) for j, v in enumerate(who)]
            parent += list(who)
            xy = np.vstack([xy, pos])
            alive, merges = _kill_sources(xy, src, age, closed, kill, max_age)
            for where, members in merges:
                edges += [(m, len(xy)) for m in members]
                parent.append(members[0])
                xy = np.vstack([xy, where])
            src, age = src[alive], age[alive] + 1
        hist["n_nodes"].append(len(xy))
        hist["n_edges"].append(len(edges))
        hist["sources"].append(src.copy())
        hist["size"].append(size)
    return dict(xy=xy, edges=np.array(edges, dtype=int).reshape(-1, 2),
                parent=np.array(parent), poly=poly, **hist)


def leaf_grid(poly, rows=30):
    """The leaf as a grid graph for flow: ``rows`` nodes along its length.

    Returns (xy, edges, base): node positions in leaf units, 4-neighbour links, and
    the node nearest the leaf base (where the flow enters).
    """
    h = 1.0 / rows
    xs = np.arange(poly[:, 0].min() - h, poly[:, 0].max() + 2 * h, h)
    ys = np.arange(0.0, 1.0 + h, h) + h / 2
    X, Y = np.meshgrid(xs, ys)
    mask = inside(poly, np.stack([X.ravel(), Y.ravel()], axis=1)).reshape(X.shape)
    pix, edges = masked_grid(mask)
    xy = np.stack([xs[pix[:, 0].astype(int)], ys[pix[:, 1].astype(int)]], axis=1)
    base = int(np.argmin(np.hypot(xy[:, 0], xy[:, 1] - h)))
    return xy, edges, base


# --- widths and measurements -------------------------------------------------

def murray_widths(parent, edges, n=2.0, r_min=1.0):
    """Vein radius per link from Murray's law, r_parent^n = sum r_child^n.

    Tips get ``r_min``.  Link (a, b) takes the radius of its child b; joining links
    (a second parent) take ``r_min``.  Returns (radius per node, width per link).
    """
    N = len(parent)
    acc = np.zeros(N)
    r = np.zeros(N)
    for i in range(N - 1, -1, -1):  # children are always numbered after parents
        r[i] = r_min if acc[i] == 0 else acc[i] ** (1 / n)
        if parent[i] >= 0:
            acc[parent[i]] += r[i] ** n
    w = np.array([r[b] if parent[b] == a else r_min for a, b in edges])
    return r, w


def vein_stats(xy, edges, width, cutoff=0.0, root=None):
    """Same measuring stick for every network: links, tips, loops, total length.

    Tips are nodes with one link; the ``root`` node (where fluid enters) is not counted."""
    keep = width > cutoff
    e = edges[keep]
    deg = np.bincount(e.ravel(), minlength=len(xy))
    length = np.linalg.norm(xy[e[:, 0]] - xy[e[:, 1]], axis=1).sum() if len(e) else 0.0
    loops = count_loops(edges, width, len(xy), cutoff) if len(e) else 0
    return dict(links=int(keep.sum()), tips=int((deg == 1).sum() - (root is not None and deg[root] == 1)), loops=int(loops),
                length=float(length))


# --- drawing -----------------------------------------------------------------

def draw_veins(ax, xy, edges, width, poly=None, palette=None, bg=BG, lw=4.0,
               cutoff=0.0, power=0.8, glow=True):
    """Draw links with line width and colour set by ``width`` (links <= cutoff hidden)."""
    keep = width > cutoff
    ax.set_facecolor(bg)
    ax.set_aspect("equal")
    ax.axis("off")
    if poly is not None:
        ax.fill(*poly.T, color="#16231b", zorder=0)
        ax.plot(*np.vstack([poly, poly[:1]]).T, color="#2c4a37", lw=0.8, zorder=1)
        pad = 0.04
        ax.set_xlim(poly[:, 0].min() - pad, poly[:, 0].max() + pad)
        ax.set_ylim(poly[:, 1].min() - pad, poly[:, 1].max() + pad)
    if not keep.any():
        return
    w = width[keep] / width.max()
    segs = xy[edges[keep]]
    cmap = make_cmap(palette or PALETTE)
    colors = cmap(np.clip(w ** 0.5, 0, 1))
    order = np.argsort(w)  # thick veins on top
    segs, colors, w = segs[order], colors[order], w[order]
    if glow:
        ax.add_collection(LineCollection(segs, linewidths=lw * 2.4 * w ** power + 1.0,
                                         colors=colors, alpha=0.12, zorder=2,
                                         capstyle="round"))
    ax.add_collection(LineCollection(segs, linewidths=lw * w ** power + 0.35,
                                     colors=colors, zorder=3, capstyle="round"))
    if poly is None:
        ax.autoscale()


def render_veins(xy, edges, width, poly, size=(4.2, 5.6), dpi=200, **kw):
    """Draw one network on its own dark canvas; returns a uint8 RGB array."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=size, facecolor=kw.get("bg", BG))
    ax.set_position([0, 0, 1, 1])
    draw_veins(ax, xy, edges, width, poly, **kw)
    return fig_to_img(fig, dpi=dpi)
