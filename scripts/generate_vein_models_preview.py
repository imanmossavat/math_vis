"""Regenerate assets/vein_models_preview.png: both vein recipes on the same leaf.

Left: space colonization (closed venation, b=0.04, kill=0.01, seed 0, 200 steps).
Right: adaptive flow on a leaf mesh under a moving load (gamma=0.5, alpha=0.6, 28 rows, 800 steps).
Same palette and drawing; grain from math_vis.finish.  Run from the repo root.
"""
import numpy as np
from PIL import Image

from math_vis import finish
from pattern_formation.networks import relax_moving_graph
from pattern_formation.venation import (
    grow_veins, leaf_mesh, leaf_outline, murray_widths, render_veins,
)

OUT = "assets/vein_models_preview.png"


def main():
    poly = leaf_outline("ovate")
    g = grow_veins(poly, b=0.04, kill=0.01, closed=True, steps=200, seed=0)
    _, wd = murray_widths(g["parent"], g["edges"])
    left = render_veins(g["xy"], g["edges"], wd, poly, size=(4.2, 5.6), dpi=170, lw=5.0)

    xy, edges, base = leaf_mesh(poly, 28)
    N = len(xy)
    length = np.linalg.norm(xy[edges[:, 0]] - xy[edges[:, 1]], axis=1)
    sinks = np.array([i for i in range(N) if i != base])
    C = relax_moving_graph(edges, N, base, sinks, 0.6, gamma=0.5, dt=0.5, steps=800, length=length)
    right = render_veins(xy, edges, C ** 0.25, poly, size=(4.2, 5.6), dpi=170, lw=5.0, power=3.0,
                         cutoff=(1e-4 * C.max()) ** 0.25)
    img = finish(np.hstack([left, right]), grain=2.0, display=False)
    Image.fromarray(np.asarray(img).astype(np.uint8)).resize((960, 640), Image.LANCZOS).save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
