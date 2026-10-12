# Technical Notes

By **Iman Mossavat**, Fontys ICT.

This document contains implementation recipes, function-specific notes, and detailed mathematical descriptions for the `math_vis` package. It is aimed at readers who want to understand *how* the code produces the images.

For a gentler, concept-first introduction to the mathematics, see **[MATH.md](MATH.md)**.

---

## 1. Random scalar fields


Many pieces start with a grid of independent random numbers and blur them so that
neighbouring values become similar.

```
noise  ~ N(0, 1)   on an (H, W) grid
blur   = gaussian_filter(noise, sigma, mode='wrap')
field  = (blur - mean(blur)) / std(blur)
```

* `sigma` controls feature size: small = grainy, large = smooth gradients.
* `mode='wrap'` makes the field tileable.
* Normalising to mean 0 and std 1 keeps parameters comparable across sizes.

### Bilinear sampling (`sample`)

`map_coordinates` looks up the field at fractional row/column positions with
linear interpolation. This lets us read the field at any continuous `(x, y)`
coordinate, e.g. for integrating a flow field.

---

## 2. Palettes and color mapping

### Hex palette (`make_cmap`)

A list of hex colors is turned into a continuous 1-D lookup table `palette(t)`
with `t ∈ [0, 1]`.

### Cosine palette (`cosine_cmap`)

For iridescent colors we use Inigo Quilez’s cosine palette:

```
color(t) = a + b * cos(2π * (c*t + d))
```

with different `(a, b, c, d)` triples for the R, G, B channels.

### Squashing (`squash`)

Raw field values are roughly `-3 … +3`. The tanh squash maps them smoothly to
`[0, 1]` without hard clipping:

```
squash(f) = 0.5 + 0.5 * tanh(f / softness)
```

---

## 3. Voronoi cells and Lloyd relaxation

### Seeds → cells

Given seed points `s_i`, every pixel belongs to the nearest seed:

```
cell(p) = argmin_i  |p - s_i|
```

This partitions the canvas into Voronoi cells.

### Lloyd relaxation

Each seed is moved to the centroid of its cell. Repeating this makes cells
regular and evenly spaced.

```
s_i <- mean{ p | cell(p) = i }
```

In practice we approximate the centroid on a coarse grid for speed.

---

## 4. Flow field

1. Build a smooth scalar field `f(x, y)`.
2. Turn it into an angle field: `θ(x, y) = π * twist * f(x, y)`.
3. Seed many points on a regular grid with tiny jitter.
4. Integrate each point forward with Euler steps:

```
p_{t+1} = p_t + step * (cos θ(p_t), sin θ(p_t))
```

5. Color each line by the field value at its start: `t = 0.5 + trend * f(p_0)`.
6. Vary transparency and width randomly.

---

## 5. Truchet weave

### Tile library

A tile is a set of connection points on each edge. Pairing the points with
non-crossing curves gives valid tiles. For 8 points around a square, the number
of valid pairings is the Catalan number `C_4 = 14`.

```
matchings([0..7])  -> 14 pairings
```

### Orientation and color fields

Two independent smooth fields drive the piece:

* `orient_field` selects the rotation of each tile.
* `color_field` selects the palette value of each tile.

Multiple parallel strands are drawn per curve, shifted slightly along the
palette to create ribbon-like depth.

---

## 6. Stained glass (crisp)

### Cell colors

Each cell receives a palette value:

```
t_i = trend   * diagonal_i
    + (1-trend) * squash(field(s_i))
    + N(0, jitter)
```

where `diagonal_i = (x_i/W + y_i/H) / 2`. The whole expression is clipped to [0, 1].

### Streaks

Inside each cell, a sum of sine waves in a random direction creates soft color
bands. The wave direction is constant per cell but random across cells.

### Hairline cracks

Two systems of thin lines are blended on top:

1. A finer Voronoi network inside the cell.
2. Contour lines of a smooth scalar field, offset randomly per cell so lines
   start and stop at the lead.

### Crisp lead with rounded corners

Let `e = (d2 - d1) / 2` be the distance from a pixel to the nearest cell border.
We shrink every cell by `lead + round` pixels, then dilate it back by `round`
using a Euclidean distance transform. The result is a lead line of exactly the
requested width with smoothly rounded convex corners.

---

## 7. Glass rose (rose window)

### Symmetric seed layout

Only one half-sector is generated randomly. It is then rotated `n_fold` times
and mirrored, giving the full rose. Each copy keeps the same original seed id,
so colors stay perfectly symmetric.

### Color recipe

```
t = 0.55 * r/R
  + 0.22 * cos(n_fold * θ)
  + 0.10 * cos(2 * n_fold * θ)
  + symmetric_jitter[id]
  + 0.1
```

where `(r, θ)` are polar coordinates around the center. The cosine terms create
color patterns that repeat in every wedge. The `symmetric_jitter[id]` term is Gaussian, `N(0, 0.05)`, sampled once per original seed id and reused for every copy; the constant `+0.1` shifts the whole palette upward. The whole expression is clipped to [0, 1].

The final image is cropped to a circle by blending the outside toward the lead
color.

---

## 8. Glass lighting model (`glass`)

`glass_crisp()` uses a different pipeline — streaks, cracks, and rounded lead lines, described in section 6 — rather than the facet/glow model presented here.

### Soft lead

The lead alpha is a smoothstep of `e / width` so borders are antialiased.
A bright rim (`bevel`) is added just inside the lead.

### Facet + glow

Each cell gets a random tilt direction. The pixel-seed displacement projected
onto this direction gives `f ∈ [-1, 1]`. The light multiplier is:

```
light = 1 + facet * f + glow * (0.45 - clamp(d1 / R, 0, 1)) + cell_var * noise
```

### Iridescence

The palette parameter is shifted by `irid * f`, so the hue changes across each
cell according to its tilt.

### Texture and bloom

* Texture: slow brightness ripples modulate the glass.
* Bloom: bright areas are blurred and added back, giving a soft glow.

## 9. Drawing language

The `demo_drawing_language.ipynb` notebook implements a tiny declarative graphics
language on top of `math_vis`. A picture is a list of `Layer`s; each layer is
built in five stages.

### Layer pipeline

1. **Layout** — `make_table` turns a `Rows` or `Grid` declaration into an
   element table with `x`, `y`, `row`, `col`, `u`, `v` columns.
   * `Rows` fills each row by repeatedly advancing `x` by `advance`.
   * `Grid` places corners on a regular mesh, applies warps, then builds quads.
2. **Columns** — `evaluate` runs column expressions in order through a `Ctx`,
   adding one value per element.
3. **Shape** — `geometry` produces an anchor and per-element relative vertices.
   Supported shapes: `circle`, `halfdisc`, `quad`.
4. **Style** — `layer_items` decides fill/alpha/stroke and builds shade copies.
5. **Color** — palette lookup `t -> palette(t)`, optional accents.

`render` draws the layers in order at `dpi*ss`, downsamples by `ss`, then
applies `finish` for grain and vignette.

### Isolated seeds (`stream`)

Every random draw uses its own deterministic stream:

```
def stream(master, *key):
    words = [master] + [zlib.crc32(str(k).encode()) for k in key]
    return np.random.default_rng(np.random.SeedSequence(words))
```

Inside a layer, `Ctx.begin(column)` resets the operator counter `_k`, and
`Ctx.rng()` increments it. A column's draws therefore depend only on
`(master, layer_name, column_name, k)`. Adding a new column or wrapping an
expression with a deterministic rescale does not change existing draws; renaming
the layer changes the stream and gives a different picture.

### Walk

`walk(step, per='row')` groups by row and applies `np.cumsum`:

```
h_j = sum_{k<=j} eps_k      (restarted per row)
```

The result has memory: a large positive step biases all later positions in the
same row. In the notebook a walk with `N(0, 0.007)` and an independent draw with
`N(0, 0.06)` are tuned to have a comparable vertical spread, but the walk reads
as continuous water while the independent draw reads as noise.

### Shade

A layer can draw `N` shrunken copies on top of the fill, each with alpha `a`
and spread `s`. Stacking `N` copies of the same dark tint gives effective
darkness

```
1 - (1 - a)^N
```

For small `a` this is approximately `N a`. The copies are scaled toward the
element center so the edge stays sharp while the interior darkens.

### Grid warp

`grid_vertices` displaces each corner `(x, y)` by

```
amp * f(x, y) * (cos θ, sin θ)
```

where `θ` is either constant or `π * g(x, y)` when a field name is supplied.
Because `f` is smooth, neighbouring corners move together and cell edges remain
joined. Folding appears when the displacement difference across a cell exceeds
the cell size, roughly

```
amp * |∇f| > 1
```

so a field with large gradients or a large amplitude tears the grid.

### What is not implemented

The notebook is a proof of concept, not a complete system. It does not yet
include:

* triangle, arc, or line shapes (only `circle`, `halfdisc`, `quad`);
* `scatter` or `along_path` layouts;
* blend modes between layers;
* YAML round-trip for layer definitions;
* a palette linter or accessibility checker.

