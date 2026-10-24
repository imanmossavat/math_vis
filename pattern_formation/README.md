# pattern_formation

Experiments where each result is checked against a number a calculation predicted
(unlike `math_vis`, which makes images).

- `reaction_diffusion.py` — Gray-Scott simulation, spacing measurement, rendering.
- `networks.py` — adaptive flow networks (Hu-Cai type): pressure solve (optional link lengths), implicit conductance adaptation, steady and exactly averaged moving load (Klemm-Martens alpha), loop counting, drawing.
- `venation.py` — leaf venation by space colonization (open/closed), Murray widths, leaf outlines, leaf meshes (`leaf_mesh`: jittered Delaunay; `leaf_grid`: square) and vein drawing shared with `networks.py`.
- `tests/` — verified phenomena (e.g. equal diffusion gives no pattern; spacing scales with sqrt(D)).

Rule: `pattern_formation` may import from `math_vis`; nothing in `math_vis` imports from `pattern_formation`.

Sources for the models are listed at the end of `notebooks/demo_vein_models.ipynb`.
