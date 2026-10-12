# The Mathematics Behind the Images

By **Iman Mossavat**, Fontys ICT.

> For implementation details, code recipes, and function-specific notes, see **[TECHNICAL.md](TECHNICAL.md)**.

How can a grid of random numbers become a flowing landscape? Why do a few simple geometric rules produce intricate patterns? And how can repetition, randomness, and symmetry create images that feel both structured and surprising?

The experiments in `math_vis` explore questions like these. Each image begins with a small set of mathematical rules. The visual result is often much more complex than the rules themselves.

This page explores some of the ideas behind the images. It is not a formal introduction to every topic, but a starting point for anyone curious about the mathematics hiding inside generative art.

## 1. From randomness to structure

Imagine filling a grid with random numbers. At first, every location is independent of its neighbours. The result is a field of visual noise.

Now blur the grid with a Gaussian filter. Nearby values begin to influence one another, and broad regions of similar values emerge. Increase the blur and the structures become larger and smoother. Decrease it and finer details return.

A small change in one parameter can transform the character of an entire image.

**The mathematical idea:** Gaussian convolution, spatial correlation, and random fields.

**Try exploring:** What happens when you gradually increase the smoothing scale? At what point does fine-grained noise become a landscape of broad shapes?

## 2. When numbers become motion

A flow field turns a static mathematical field into a map of directions.

At each position, a scalar value determines an angle. That angle becomes a direction vector:

$$
v(x,y) = (\cos\theta(x,y),\ \sin\theta(x,y))
$$

Place a point in the field and repeatedly move it a small distance in the direction indicated by the field. Its path traces a curve. Repeat this for many starting points and a whole network of flowing lines appears.

The field is mathematical, but the image makes its structure visible. Smooth regions produce coherent motion; changes in direction bend and separate the paths.

**The mathematical idea:** Vector fields, trigonometry, and numerical integration.

**Try exploring:** Predict what will happen before increasing the strength of the angle variation. Will the paths become more orderly, more tangled, or something else?

## 3. Geometry from a collection of points

Scatter points across a plane and ask a simple question: which point is closest to each location?

The answer divides the plane into Voronoi cells. Every cell contains the locations closest to one particular seed point. A set of points has become a tessellation.

But the story does not end there. Move each seed toward the centre of its cell, then repeat the process. This is called Lloyd relaxation. The cells tend to become more evenly distributed, creating a different kind of geometry.

**The mathematical idea:** Distance, geometric partitioning, and iterative algorithms.

**Try exploring:** Compare a Voronoi diagram made from random points with one produced after several rounds of relaxation. What changes, and what stays the same?

## 4. Patterns built from tiles

A small collection of tiles can generate a surprisingly elaborate image. In a Truchet-style pattern, each tile connects curves across its edges. Rotating or reflecting tiles changes how those curves meet their neighbours.

Local choices combine into global structure. Paths may weave across the canvas, form loops, or create unexpected large-scale patterns.

The interesting part is that the complexity does not need to be designed one line at a time. It emerges from the rules governing the connections.

**The mathematical idea:** Combinatorics, symmetry, connectivity, and emergent structure.

**Try exploring:** What changes when tile orientations are chosen independently at random rather than guided by a smooth spatial field?

## 5. Symmetry through repetition

Many intricate designs can be constructed from a much smaller piece. Create one sector of a pattern, rotate it around a centre, and reflect it where appropriate. The repeated copies produce a complete radial design.

Trigonometric functions can also introduce repeating colour patterns. By changing the number of repetitions or the relative contribution of different terms, the same underlying geometry can produce very different visual effects.

**The mathematical idea:** Rotations, reflections, polar coordinates, and periodic functions.

**Try exploring:** Change the number of repeated sectors. How does the symmetry change? Can you predict the visual effect before rendering the image?

## 6. Random walks and island-like structures

Randomness can also create shapes that remain close to one another.

In a random walk, each step introduces a random displacement. Add a preferred direction, or a restoring force that pulls the walk toward an anchor point, and the resulting positions form clusters rather than spreading without limit.

A second layer of rules can govern which shapes appear next. For example, a Markov chain can make triangles tend to occur in runs, followed by runs of rectangles.

Simple stochastic rules begin to suggest a miniature world.

**The mathematical idea:** Random walks, stochastic processes, and Markov chains.

**Try exploring:** What happens when the restoring force becomes stronger? How does the balance between randomness and drift change the resulting clusters?

## 7. A small drawing language

So far each image has been produced by its own script. A drawing language asks a
different question: can we describe a picture as a small set of reusable rules?

The answer starts with two observations.

First, **memory changes the character of randomness**. If every element gets an
independent random displacement, the result looks like static. If each
displacement is the cumulative sum of small random steps — a random walk — then
nearby elements stay close together and smooth, wave-like bands appear. The same
average amount of randomness produces two different textures, depending on whether
the random values remember what came before.

Second, **one field can wear many hats**. A single smooth scalar field can displace
grid corners, select colors, and control transparency. Because the field is shared,
shape and color move together, creating a coherence that separate fields would not
give. Changing which role the field plays changes the picture, even when the
geometry stays the same.

These two ideas — random walks for memory, and shared fields for coherence — are
enough to build surprisingly varied pictures from a tiny grammar: layout,
columns, shape, style, color.

**The mathematical idea:** Cumulative sums, random walks, and multiscale fields.

**Try exploring:** Where else do you see memory in randomness? What happens if a
field that drives position also drives color, or if two independent fields drive
them instead?

## Beyond the image

These examples are starting points, not finished explanations. An attractive result can invite a question, but understanding comes from investigating why the result appears.

A useful habit is to **notice, predict, experiment, and explain**. Change one parameter, anticipate its effect, compare the outcome with your prediction, and try to connect the difference to the underlying mathematics.

The notebooks in this repository are evolving experiments. Over time, I hope to develop more of them into opportunities for mathematical exploration, with clearer explanations, questions, and ideas for further investigation.

If you find an unexpected pattern, have a different way to explain one of these ideas, or want to explore another mathematical process, contributions are welcome.
