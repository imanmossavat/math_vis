#!/usr/bin/env python3
"""Regenerate assets/stained_glass_crisp_preview.png from archive-studio settings.

This script makes the generation parameters version-controlled in git, so the
preview asset can always be traced back to its source.
"""
from pathlib import Path

import numpy as np
from PIL import Image

from math_vis import (
    seeds_relaxed,
    cell_colors,
    glass_crisp,
    make_cmap,
    save_with_meta,
)

# Source parameters come from archive/stained_glass_studio.ipynb, default
# glass_crisp settings cell.
SEED = 4
RENDER_W, RENDER_H = 1300, 900
N_CELLS = 170
LLOYD_ITERS = 2
TARGET_WIDTH = 800

rng = np.random.default_rng(SEED)

JEWEL = make_cmap(
    [
        "#0b1d3a",
        "#1f4e8c",
        "#2aa5c9",
        "#58d3c0",
        "#f4e285",
        "#f59e3b",
        "#e0453a",
        "#8e2a6a",
        "#3a1d6e",
    ]
)

seeds = seeds_relaxed(N_CELLS, RENDER_W, RENDER_H, rng, iters=LLOYD_ITERS)
t_cell = cell_colors(
    seeds, RENDER_W, RENDER_H, rng, trend=0.5, smooth=20, jitter=0.07
)
img, stages = glass_crisp(
    seeds,
    t_cell,
    JEWEL,
    RENDER_W,
    RENDER_H,
    rng=rng,
    stages=True,
    warp=16,
    lead_px=1.8,
    round_px=4.0,
    streak=0.035,
    streak_light=0.10,
    crack_alpha=0.30,
    contour_alpha=0.28,
)
full_size = stages["final"]

# Resize to the web-friendly landscape size used in the README gallery.
target_height = int(round(TARGET_WIDTH * RENDER_H / RENDER_W))
preview = np.array(
    Image.fromarray(full_size).resize(
        (TARGET_WIDTH, target_height), Image.Resampling.LANCZOS
    )
)

repo_root = Path(__file__).resolve().parent.parent
out_path = repo_root / "assets" / "stained_glass_crisp_preview.png"

save_with_meta(
    preview,
    out_path,
    source_notebook="archive/stained_glass_studio.ipynb",
    generator_script="scripts/generate_stained_glass_crisp_preview.py",
    seed=SEED,
    render_width=RENDER_W,
    render_height=RENDER_H,
    n_cells=N_CELLS,
    lloyd_iters=LLOYD_ITERS,
    palette="JEWEL",
    glass_crisp_params={
        "warp": 16,
        "lead_px": 1.8,
        "round_px": 4.0,
        "streak": 0.035,
        "streak_light": 0.10,
        "crack_alpha": 0.30,
        "contour_alpha": 0.28,
    },
    finish_params={"grain": 2},
    resize={
        "width": TARGET_WIDTH,
        "height": target_height,
        "filter": "LANCZOS",
    },
)

print(f"Wrote {out_path} ({preview.shape[1]}x{preview.shape[0]})")
