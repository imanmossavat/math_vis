# Contributing

By **Iman Mossavat**, Fontys ICT.

Thank you for being interested in the project. Contributions — new visual
experiments, bug reports, better explanations, or small fixes — are welcome.

## Setup

You need Python 3.12 or newer.

```bash
git clone https://github.com/imanmossavat/math_vis.git
cd math_vis
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m pytest -q
```

`pip install -e ".[dev]"` installs the package in editable mode (`-e .`) plus
the test and notebook development dependencies.

## How the tests work

`python -m pytest -q` runs the full suite:

* **Unit tests** for `utils`, `math_tools`, `lighting`, `rendering`, `finishing`,
  and `io`.
* **Reproducibility tests** check that each `render_*` function returns
  byte-identical output for the same seed.
* **`test_docs_links.py`** checks that every image referenced from
  `README.md`, `conceptualGuide.md`, `recipes.md`, and the notebooks points to a file
  tracked by git.
* **`test_notebooks.py`** executes every `notebooks/demo_*.ipynb` end-to-end as
  a smoke test and makes sure the run did not leave untracked PNGs in the
  repository root.

## Conventions taken from the repo

* Put parameters at the top of a notebook, right after the imports.
* Add a markdown explanation before each code cell.
* End each section with a short prediction question for the reader.
* Name demonstrator notebooks `demo_*.ipynb`.
* Reference images only from `assets/`, and keep them tracked by git.
* Pass an `rng` or an explicit seed to helpers; do not create unseeded NumPy
  generators. If you want a printed seed, use `rng = mv.new_rng(seed)`.
* When you commit a generated asset, prefer to add a generator script under
  `scripts/` and record the mapping in `assets/README.md` so the image can be
  reproduced.

## Adding a new piece

A typical path from idea to merge:

1. **Explore in a notebook.** Start with `notebooks/demo_<name>.ipynb`, reuse
   `smooth_field`, `sample`, `make_cmap`, `finish`, and the other primitives,
   and keep parameters at the top.
2. **Extract reusable helpers.** Move field recipes, geometry builders, or
   lighting steps into the appropriate `math_vis/` module.
3. **Add a `render_*` function.** High-level renderers take a seed and return a
   `uint8` RGB array; they usually end by calling `finish(...)`.
4. **Add tests.** At minimum add a reproducibility test and a smoke test in
   `tests/test_rendering.py` or a new `tests/test_<name>.py`. Update
   `tests/test_reproducibility.py` if you add another renderer.
5. **Document it.** Add a gallery preview to `assets/`, a generator script if
   applicable, an entry in `assets/README.md`, a row in the README "Start here"
   table, and any notes needed by `conceptualGuide.md` or `recipes.md`.

## Reporting issues

A good issue includes:

* Your operating system and Python version.
* The exact command or notebook cell that failed.
* The seed, if the problem is reproducibility-related.
* What you expected and what actually happened.
* A minimal code snippet that shows the problem, if possible.

Open an issue or pull request on GitHub when you are ready.
