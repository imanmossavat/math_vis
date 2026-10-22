# Gallery assets

Committed preview images used by the README and notebooks.
Each asset should be reproducible from a version-controlled generator.

## Current assets

| asset | dimensions | generator | source / parameters |
|-------|------------|-----------|---------------------|
| `bezier_tiles_preview.png` | 960 × 1280 | `notebooks/demo_bezier_tiles.ipynb` | Final cell output: `SEED=7`, `K=3`, `NX=12`, `NY=16`, `MAX_OFFSET=0.3`, 3 strands, extracted from the executed notebook. |
| `bezier_tiles_field_preview.png` | 1158 × 1090 | `notebooks/demo_bezier_tiles.ipynb` | Cell 20 output: gradient-rank and smooth-field rank panels, `K=3`, `MAX_OFFSET=0.3`, extracted from the executed notebook. |
| `stained_glass_crisp_preview.png` | 800 × 554 | [`scripts/generate_stained_glass_crisp_preview.py`](../scripts/generate_stained_glass_crisp_preview.py) | `archive/stained_glass_studio.ipynb` default `glass_crisp` cell: seed=4, render 1300×900, `n_cells=170`, `lloyd_iters=2`, JEWEL palette, `warp=16`, `lead_px=1.8`, `round_px=4.0`, then resized to 800 px wide with LANCZOS. |
| `vein_models_preview.png` | 960 × 640 | [`scripts/generate_vein_models_preview.py`](../scripts/generate_vein_models_preview.py) | Left: closed space-colonization venation, `b=0.04`, `kill=0.01`, seed 0, 200 steps. Right: adaptive flow, moving load, `gamma=0.5`, `k=8`, 28 rows, 1500 steps, seed 0. Both on the ovate leaf. |

## Verifying / regenerating

Run the generator script from the repository root:

```bash
python scripts/generate_stained_glass_crisp_preview.py
```

Then inspect the embedded metadata:

```python
from math_vis import load_meta
print(load_meta("assets/stained_glass_crisp_preview.png"))
```
