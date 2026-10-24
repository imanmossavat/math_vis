"""Regenerate assets/vein_glass_preview.png: vein networks drawn as leaded glass.

Left: space colonization (closed venation, b=0.04, kill=0.01, seed 0, 200 steps), jewel palette.
Right: adaptive flow on a leaf mesh under a moving load (gamma=0.5, alpha=0.6, 28 rows, 800 steps),
backlit-leaf palette.  Lighting is the glass rose's.  Run from the repo root.
"""
import numpy as np
from PIL import Image

from math_vis import finish
from pattern_formation.networks import relax_moving_graph
from pattern_formation.venation import (
    grow_veins, leaf_mesh, leaf_outline, murray_widths, render_vein_glass,
)

OUT = "assets/vein_glass_preview.png"
ROSE_LIGHT = dict(facet=0.45, glow=0.4, lead_var=0.35, bevel=0.35, texture=0.04, bloom=0.2)
BACKLIT = ["#1d2a0c", "#4f6b14", "#93b52a", "#d6e36a", "#fff7c8"]


def main():
    poly = leaf_outline("ovate")
    g = grow_veins(poly, b=0.04, kill=0.01, closed=True, steps=200, seed=0)
    _, wd = murray_widths(g["parent"], g["edges"])
    left = render_vein_glass(g["xy"], g["edges"], wd, poly, height=900, cutoff=0.5, **ROSE_LIGHT)

    xy, edges, base = leaf_mesh(poly, 28)
    N = len(xy)
    length = np.linalg.norm(xy[edges[:, 0]] - xy[edges[:, 1]], axis=1)
    sinks = np.array([i for i in range(N) if i != base])
    C = relax_moving_graph(edges, N, base, sinks, 0.6, gamma=0.5, dt=0.5, steps=800, length=length)
    right = render_vein_glass(xy, edges, C ** 0.25, poly, height=900, cutoff=(1e-4 * C.max()) ** 0.25,
                              power=3.0, palette=BACKLIT, lead_color=(20, 26, 12), **ROSE_LIGHT)
    img = finish(np.hstack([left, right]), grain=2.0, display=False)
    Image.fromarray(np.asarray(img).astype(np.uint8)).resize((800, 635), Image.LANCZOS).save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
