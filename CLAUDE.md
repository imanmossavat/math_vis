# math_vis

Two packages: `math_vis/` (generative-art toolkit) and `pattern_formation/` (experiments that check numbers; see its README). `pattern_formation` may import from `math_vis`, never the reverse.

- Tests: `python -m pytest -q`
- Style: plain NumPy/SciPy, functions not classes, short functions. Repo docs short; open questions live in notebooks. Every experiment ends in a number a calculation predicted; verified claims become tests.
- Session handoffs: `docs/handoffs/`, numbered `NN_topic.md` (git-ignored). Read the highest number first when resuming. Write a new one, next number, at the end of a session.
