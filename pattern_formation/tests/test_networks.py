"""Tests for adaptive flow networks, including the tree-versus-loops result of Hu and Cai (2013)."""
import numpy as np
import pytest

from pattern_formation.networks import (
    grid_edges,
    solve_pressure,
    link_flows,
    adapt,
    count_loops,
    relax,
)

N_SIDE = 11
N = N_SIDE ** 2
CENTRE = N // 2
SINKS = [i for i in range(N) if i != CENTRE]


def test_grid_edges_count():
    n = 5
    assert len(grid_edges(n)) == 2 * n * (n - 1)


def test_flow_is_conserved_at_every_node():
    edges = grid_edges(6)
    rng = np.random.default_rng(0)
    C = rng.uniform(0.5, 2, len(edges))
    s = rng.normal(size=36)
    s -= s.mean()
    Q = link_flows(edges, C, solve_pressure(edges, C, s))
    net_out = np.zeros(36)
    np.add.at(net_out, edges[:, 0], Q)
    np.add.at(net_out, edges[:, 1], -Q)
    assert np.allclose(net_out, s)


def test_adapt_fixed_point():
    # Q^2/C = nu C^gamma  =>  C = (Q^2/nu)^(1/(gamma+1)); Q = 1 gives C = 1
    assert adapt(np.array([1.0]), np.array([1.0]), nu=1.0, gamma=0.5)[0] == pytest.approx(1.0)


def test_loop_count_of_known_graphs():
    square = np.array([[0, 1], [1, 3], [3, 2], [2, 0]])
    assert count_loops(square, np.ones(4), 4, 0.5) == 1
    assert count_loops(square[:3], np.ones(3), 4, 0.5) == 0


# --- the phenomena -----------------------------------------------------------

def test_concave_cost_gives_a_tree_convex_cost_keeps_loops():
    for gamma, expect_tree in [(0.5, True), (1.5, False)]:
        edges, C = relax(N_SIDE, CENTRE, SINKS, gamma=gamma, steps=8000)
        loops = count_loops(edges, C, N, 1e-3 * C.max())
        assert (loops == 0) == expect_tree
