# pattern_formation

Experiments where each result is checked against a number a calculation predicted
(unlike `math_vis`, which makes images).

- `reaction_diffusion.py` — Gray-Scott simulation, spacing measurement, rendering.
- `tests/` — verified phenomena (e.g. equal diffusion gives no pattern; spacing scales with sqrt(D)).

Rule: `pattern_formation` may import from `math_vis`; nothing in `math_vis` imports from `pattern_formation`.
