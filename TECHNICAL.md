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
    + jitter
```

where `diagonal_i = (x_i/W + y_i/H) / 2`.

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
```

where `(r, θ)` are polar coordinates around the center. The cosine terms create
color patterns that repeat in every wedge.

The final image is cropped to a circle by blending the outside toward the lead
color.

---

## 8. Glass lighting model (`glass`)

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
