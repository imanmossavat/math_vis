"""Tests for leaf venation (space colonization) and flow networks on a leaf."""
import numpy as np
import pytest

from pattern_formation.networks import (
    count_loops, link_flows, solve_pressure, relax_graph, masked_grid,
)
from pattern_formation.venation import (
    SHAPES, leaf_outline, inside, grow_veins, leaf_grid, murray_widths, vein_stats,
)

POLY = leaf_outline("ovate")


def _loops(g):
    _, w = murray_widths(g["parent"], g["edges"])
    return vein_stats(g["xy"], g["edges"], w, 0.5)["loops"]


def test_leaf_outline_contains_its_axis_not_its_surroundings():
    for shape in SHAPES:
        poly = leaf_outline(shape)
        assert inside(poly, np.array([[0.0, 0.5]]))[0]
        assert not inside(poly, np.array([[0.9, 0.5], [0.0, 1.2], [0.0, -0.2]])).any()


def test_masked_grid_keeps_the_largest_piece():
    mask = np.zeros((3, 6), dtype=bool)
    mask[:, :3] = True          # 3x3 block: 9 nodes, 12 links
    mask[1, 5] = True           # an isolated pixel is dropped
    xy, edges = masked_grid(mask)
    assert len(xy) == 9 and len(edges) == 12


def test_open_venation_is_a_tree_closed_has_loops():
    open_ = grow_veins(POLY, b=0.06, kill=0.02, closed=False, steps=150)
    closed = grow_veins(POLY, b=0.06, kill=0.01, closed=True, steps=150)
    assert _loops(open_) == 0
    assert _loops(closed) > 10


@pytest.mark.parametrize("n", [2.0, 3.0])
def test_murray_law_root_radius_is_tips_to_the_one_over_n(n):
    g = grow_veins(POLY, b=0.06, kill=0.02, closed=False, steps=150)
    parent = g["parent"]
    tips = (np.bincount(parent[parent >= 0], minlength=len(parent)) == 0).sum()
    r, _ = murray_widths(parent, g["edges"], n=n)
    assert r[0] == pytest.approx(tips ** (1 / n))


def test_flow_widths_follow_conductance_flow_power_law():
    # settled link: Q^2/C = C^gamma  =>  C = Q^(2/(gamma+1)); gamma = 1/2 gives r^3 ~ Q
    # (Murray's law with n = 3) when radius r = C^(1/4)
    xy, edges, base = leaf_grid(POLY, 16)
    N = len(xy)
    s = -np.ones(N)
    s[base] = N - 1
    for gamma in (0.5, 0.75):
        C = relax_graph(edges, s, gamma=gamma, steps=3000)
        Q = np.abs(link_flows(edges, C, solve_pressure(edges, C, s)))
        k = C > 1e-2 * C.max()
        slope = np.polyfit(np.log(Q[k]), np.log(C[k]), 1)[0]
        assert slope == pytest.approx(2 / (gamma + 1), abs=0.03)
        assert count_loops(edges, C, N, 1e-3 * C.max()) == 0
