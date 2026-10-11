# math_vis

[![tests](https://github.com/imanmossavat/math_vis/actions/workflows/tests.yml/badge.svg)](https://github.com/imanmossavat/math_vis/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-live-blue?logo=githubpages)](https://imanmossavat.github.io/math_vis/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)

> Can visual beauty spark mathematical curiosity?

This project explores mathematical ideas by turning them into things we can
generate, see, and experiment with. Using Python, we investigate how simple
rules, randomness, geometry, and transformations produce complex visual
patterns.

The project is a work in progress. It is also an invitation to explore, learn,
experiment, and contribute. You are welcome to use the existing notebooks,
adapt them, or create your own to investigate mathematical ideas that interest
you.

## Inspiration

The initial idea for this project came from seeing Kenny Vaden's art work on LinkedIn.
If you enjoy these experiments, you should check them out on [LinkedIn](https://www.linkedin.com/search/results/people/?keywords=Kenny%20Vaden).

---

## What's inside?

The repository contains experiments with topics including:

- **Random fields and convolution** — generating noise and exploring how
  Gaussian smoothing creates spatial structure.
- **Voronoi diagrams and tessellations** — partitioning space, exploring
  geometric patterns, and experimenting with Lloyd relaxation.
- **Random walks and stochastic processes** — investigating how repeated random
  movements, drift, and other rules shape patterns.
- **Flow fields and particle trajectories** — exploring how vector fields guide
  movement.
- **Truchet tiles** — creating intricate patterns from simple tile
  arrangements.
- **Symmetry and transformations** — experimenting with rotations, reflections,
  and radial designs.
- **Generative landscapes and stained glass** — combining mathematical processes
  into more elaborate visual compositions.

---

## Installation

```bash
git clone git@github.com:imanmossavat/math_vis.git
cd math_vis
pip install numpy matplotlib scipy pillow ipython nbformat pytest
```

---

## Quick start

```python
import math_vis as mv

img = mv.render_flow_field(seed=11)
img = mv.render_glass_rose(seed=9)
```

Each `render_*` function returns a `uint8` RGB NumPy array. Pass it to
`mv.finish(...)` to add grain, vignette, save, and display.

---

## Notebooks

The `notebooks/` directory contains multi-panel demonstrators:

- `demo_lighting_and_sampling.ipynb` — raw noise → smooth fields → palettes →
  lighting → finishing.
- `demo_flow_field.ipynb` — smooth field → angles → particle integration →
  final render.
- `demo_truchet.ipynb` — tile library → orientation/color fields → woven
  ribbons.
- `demo_stained_glass_crisp.ipynb` — Voronoi cells → colors → streaks →
  rounded lead lines.
- `demo_glass_rose.ipynb` — symmetric seed layout → rose color recipe →
  glass lighting → circular crop.

---

## Tests

```bash
python3 -m pytest -q
```

---

## License

This project is released under the MIT License — see [LICENSE](LICENSE).

---

## Contribute

Ideas, bug reports, and new visual experiments are all welcome. Open an issue
or a pull request on GitHub.
