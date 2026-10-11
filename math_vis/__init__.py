"""Generative-art toolkit for math-driven visuals.

Import commonly used pieces with:

    from math_vis import make_cmap, render_flow_field, finish
"""
from .utils import make_cmap, cosine_cmap, squash, new_rng, upfield, fig_to_img
from .math_tools import (
    smooth_field,
    sample,
    seeds_relaxed,
    seeds_spiral,
    seeds_rose,
    lloyd_relaxation,
    arc_points,
    rotate_2d,
    cubic_bezier,
    matchings,
)
from .lighting import (
    apply_glass_lighting,
    apply_lead_lines,
    apply_texture,
    apply_bloom,
    apply_streaks,
    apply_cracks,
    apply_rounded_lead,
    lead_mask,
    bevel_rim,
)
from .finishing import finish
from .rendering import (
    cell_colors,
    glass,
    glass_crisp,
    render_flow_field,
    render_truchet_weave,
    render_stained_glass_crisp,
    render_glass_rose,
    TILE_TEXT,
    parse_tile,
    rotate_tile,
    tile_curve,
    P_TILE,
    N_TILE,
)

__all__ = [
    # utils
    "make_cmap",
    "cosine_cmap",
    "squash",
    "new_rng",
    "upfield",
    "fig_to_img",
    # math
    "smooth_field",
    "sample",
    "seeds_relaxed",
    "seeds_spiral",
    "seeds_rose",
    "lloyd_relaxation",
    "arc_points",
    "rotate_2d",
    "cubic_bezier",
    "matchings",
    # lighting
    "apply_glass_lighting",
    "apply_lead_lines",
    "apply_texture",
    "apply_bloom",
    "apply_streaks",
    "apply_cracks",
    "apply_rounded_lead",
    "lead_mask",
    "bevel_rim",
    # finishing
    "finish",
    # rendering
    "cell_colors",
    "glass",
    "glass_crisp",
    "render_flow_field",
    "render_truchet_weave",
    "render_stained_glass_crisp",
    "render_glass_rose",
    "TILE_TEXT",
    "parse_tile",
    "rotate_tile",
    "tile_curve",
    "P_TILE",
    "N_TILE",
]
