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
    relax_fluctuating,
    moving_load_Q2,
    relax_moving_graph,
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


def test_adapt_is_stable_for_weak_links_with_a_big_step():
    # explicit Euler overshoots when dt * C^(gamma-1) is large; the implicit step just decays
    weak = adapt(np.array([1e-4]), np.array([0.0]), dt=1.0)[0]
    assert 1e-6 <= weak < 1e-4
    x = adapt(np.array([1.0]), np.array([1e6]), dt=1.0)[0]  # solves x^2 + x^1.5 - x = 1e6
    assert x ** 2 + x ** 1.5 - x == pytest.approx(1e6, rel=1e-6)


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


def test_moving_load_keeps_loops_even_for_concave_cost():
    edges, C = relax_fluctuating(N_SIDE, CENTRE, SINKS, gamma=0.5, steps=4000,
                                 rng=np.random.default_rng(0))
    assert count_loops(edges, C, N, 1e-3 * C.max()) > 10  # steady load gave 0


def test_relax_can_be_continued_from_C0():
    # two half-runs equal one full run (needed to take snapshots along the way)
    n, c = 5, 12
    sinks = [i for i in range(25) if i != c]
    _, whole = relax(n, c, sinks, steps=200)
    _, half = relax(n, c, sinks, steps=100)
    _, again = relax(n, c, sinks, steps=100, C0=half)
    assert np.allclose(whole, again)
    rng = np.random.default_rng(1)
    _, whole = relax_fluctuating(n, c, sinks, steps=20, rng=np.random.default_rng(1))
    _, half = relax_fluctuating(n, c, sinks, steps=10, rng=rng)
    _, again = relax_fluctuating(n, c, sinks, steps=10, rng=rng, C0=half)
    assert np.allclose(whole, again)


# --- moving load (exact average over which sink is busy) ---------------------

def test_moving_load_with_no_fluctuation_is_the_steady_load():
    edges = grid_edges(5)
    C = np.random.default_rng(0).uniform(0.5, 2, len(edges))
    sinks = np.arange(1, 25)
    s = -np.ones(25) / 24  # the moving load supplies 1 unit in total, 1/24 to each sink
    s[0] = 1.0
    steady = link_flows(edges, C, solve_pressure(edges, C, s)) ** 2
    assert np.allclose(moving_load_Q2(edges, C, 25, 0, sinks, 0.0), steady)


def test_triangle_loop_appears_at_alpha_one_over_root_three():
    # Klemm and Martens (arXiv:2407.04120): one source, two sinks, gamma = 1.  Below
    # alpha = 1/sqrt(3) the settled state is a tree; above it the third link stays open
    # with C = (alpha - 1/sqrt(3)) / 2 while the two spokes sit at 1/sqrt(3).
    edges = np.array([[0, 1], [0, 2], [1, 2]])
    sinks = np.array([1, 2])
    root3 = 1 / np.sqrt(3)
    for alpha, third in [(0.4, 1e-6), (0.9, (0.9 - root3) / 2)]:
        C = relax_moving_graph(edges, 3, 0, sinks, alpha, gamma=1.0, dt=0.2, steps=6000)
        assert C[2] == pytest.approx(third, abs=1e-4)
        if alpha > root3:
            assert C[:2] == pytest.approx([root3, root3], abs=1e-4)


def test_relax_moving_can_be_continued_from_C0():
    edges = grid_edges(4)
    sinks = np.arange(1, 16)
    whole = relax_moving_graph(edges, 16, 0, sinks, 0.7, steps=60)
    half = relax_moving_graph(edges, 16, 0, sinks, 0.7, steps=30)
    assert np.allclose(whole, relax_moving_graph(edges, 16, 0, sinks, 0.7, steps=30, C0=half))
