# Pattern formation: where math meets code

Oct 21, 2026 · @Iman Mossavat

This tab is the plan. For plain-English explanations of every idea in it, read The ideas, explained.

## The method

Every calculation ends in a number, and every experiment measures that same number. When they agree, you have understood something. When they disagree, you have found the next question.

One worked example already exists. On paper, ripples start to grow when dB/dA drops below **0.61**, and the fastest-growing ripple at dB/dA = 0.5 is **16.4 px**. In the simulation, patterns switch on between 0.75 and 0.65, and the measured spacing at 0.5 is **16.4 px**. The small mismatch at the threshold is the next question: is the transition sudden, with memory?

Two working rules keep this honest:

- **Verified claims become tests.** Only then do they go into the repo docs, which stay short and stable.
- **Open questions stay in the notebook,** next to the experiment that raised them.

## The mental schema

Everything in this plan is one picture: **values living on a network, spreading along its links, while the links themselves slowly change.** Seven ideas hang on that picture, each one built on the one before.

&#91;embedded content: the schema · two layers, knobs, seed, measurements\]

Knobs and the seed act on the fast layer; the two layers shape each other; every stage ends in a measurement at the bottom.

1. **State, rule, steps.** An image is a state; a rule updates every pixel; we repeat. On a grid, the PDE becomes one small ODE per pixel.
2. **The Laplacian is the network.** Diffusion means "move toward the average of your neighbours". On any network this is the *graph Laplacian*. The grid kernel (centre −1, sides 0.2, corners 0.05) is one example; a vein network is another, with weighted links.
3. **Fixed points and stability.** A state that does not change is a fixed point. Nudge it: if the nudge dies, it is stable (ball in a bowl); if it grows, unstable (ball on a hill). For two chemicals this is a 2×2 matrix and its eigenvalues.
4. **Ripples and the growth curve.** Split any nudge into ripples of different sizes (Fourier modes). Each size grows or dies at its own rate. That curve tells you *whether* a pattern forms and *what spacing* it has.
5. **Transitions.** Turn one knob (control parameter). Measure one thing that is zero on one side and nonzero on the other (order parameter). The switch can be gradual or sudden; sudden ones have memory (hysteresis). Patterns also break symmetry: the rule does not prefer a position, so the random seed picks one.
6. **Ensembles and noise.** Many seeds give many images with the same statistics (self-averaging). Bigger grids make the switch sharper. Adding noise at every step acts like temperature; the distribution over images then obeys a Fokker–Planck equation.
7. **Layers and time scales.** A fast layer (chemistry, flow) settles on top of a slow layer (veins). Slow links that grow with traffic build their own highways. That is how local rules create long-range connections, and how the layer can have its own transition (trees versus loops).

## The stages

Eight stages, each one a question with a number that math predicts and code measures. Stages 0–4 are the chemistry layer, 5–6 add the vein layer, 7 brings in learned rules.

| # | Question | Math predicts | Code measures | What you learn | Status |
| --- | --- | --- | --- | --- | --- |
| 0 | Does the simulator reproduce known patterns? | Sims' presets; √D scaling of spacing | Spots, coral, worms, mitosis; spacing 7.9 → 11.5 → 16.4 px | State, rule, steps; dimensional reasoning | Done |
| 1 | When does a flat state break into a pattern? | Threshold dB/dA ≈ 0.61; spacing 16.4 px | Pattern strength vs dB/dA; spacing | Fixed points, stability, the growth curve | Half done |
| 2 | Is the switch gradual or sudden? | Gradual: strength grows from zero. Sudden: a jump and a loop | Sweep the knob down, then up; compare where the pattern appears and disappears | Bifurcations, hysteresis | Next |
| 3 | Does an ensemble behave like thermodynamics? | Spread across seeds shrinks with grid size; noise shrinks the hysteresis loop | N seeds × 3 grid sizes; noise strength T | Self-averaging, finite size, noise as temperature | Planned |
| 4 | How fast can local rules build long-range order? | Reach grows at the front speed, ∝ √D | Correlation length over time | Light cone, locality | Planned |
| 5 | Can traffic build its own roads? | Hu–Cai: trees below γ = 1, loops above | Loop count = edges − nodes + pieces, vs γ | Graph Laplacian, Kirchhoff, gradient flow, a second transition | Planned |
| 6 | What happens when roads and chemistry shape each other? | Open: no prediction yet | Patterns along veins; veins toward demand | Two time scales, coupled layers | Planned |
| 7 | Do learned rules know the threshold? | A learned reaction has a growth curve too | Stability analysis on a learned rule; flow matching samples near 0.61 | Local versus global rules | Optional, needs a GPU |

Stage 1 needs one more step: write the growth-curve calculation as a small function and test it. Stage 6 is the only one without a prediction, which makes it the research stage; do it only after 5 reproduces the published result.

## Grown networks: what shape, and can we steer it

Three published ingredients decide whether a grown network becomes a tree or a mesh of loops, so the shape is steerable.

- **Cost of thick links (γ).** With a steady load: trees below γ = 1, a uniform sheet above, the switch at γ = 1 (Katifori et al. 2010).
- **The load.** A steady flow from one source gives a tree. A fluctuating load (moving sinks) or random damage gives nested loops, even below γ = 1. Their lemon-leaf experiment: cut the main vein and flow reroutes through the loops.
- **Growth.** Local rules alone get stuck in poor networks; growing tissue lets them escape to much better ones (Ronellenfitsch and Katifori 2016).

| Target | Load | Growth | Expected shape |
| --- | --- | --- | --- |
| Leaf veins | fluctuating, damage | yes | nested loops (published) |
| Main arteries | steady, one pump | yes | branching tree (published, steady case) |
| City streets | many moving sources and sinks | outward | loops everywhere (hypothesis) |

**The fresh question.** Chemistry can create the load itself: if every spot consumes nutrients, the regime decides the sinks. Static spots should give trees feeding each spot; moving, dividing spots (mitosis) should give loops. I found no published answer.

**West-style scaling.** West's move was to measure how one quantity grows with size across many systems, then explain the exponent.

- Biology: metabolic rate ∝ mass^3/4, derived from space-filling, energy-minimising networks with fixed-size smallest tubes (West, Brown, Enquist 1997).
- Cities: road surface exponent 0.83, cable length 0.87, but wages 1.12 and patents 1.27 (Bettencourt et al. 2007).

Our model can test the infrastructure side: grow networks of several sizes and measure total length versus size. The superlinear social side comes from people interacting and is not in the model.

**Real cities and leaves.** Grown networks can match a real one *statistically* (loops per area, block sizes, hierarchy), not street by street. Given real constraints as input (coastline, where people live, the leaf outline), we can ask whether the *main* routes grow where the real ones are. Forcing an exact match makes the model memorise and explain nothing: the fewer knobs needed to get close, the more it understands. Runions et al. (2005) is the leaf-venation baseline.

**Citations, later.** No space and no pipes, but the same slow rule: reinforcement plus decay. Wang, Song and Barabási (2013) model citations with preferential attachment, aging and fitness, and report that rescaled citation histories collapse onto one curve.

## Minimum viable path

Build the network layer alone, check it against a published result, then couple it to the chemistry. Coupling first would leave a strange picture with no way to tell which half is wrong. About 85 new lines in total.

The network layer is an adaptive flow network on the grid: pixels are nodes, neighbours are links, each link e has a conductance Cₑ.

1. Sources and sinks s: fluid entering (+) or leaving (−) each node.
2. Fast: solve L(C) p = s, where L(C) is the graph Laplacian weighted by C.
3. Flow on each link: Qₑ = Cₑ × (pressure difference across it).
4. Slow (Hu–Cai): dCₑ/dt = Qₑ²/Cₑ − ν·Cₑ^γ. Busy links grow, idle ones shrink.

| Step | What | New code | Check |
| --- | --- | --- | --- |
| A | `networks.py`: links, pressure solve, flow, adaptation, loop count, drawing | \~60 lines | Steady load: 0 loops for γ < 1, loops for γ > 1 |
| B | Moving sinks, Q² averaged over a few positions | \~5 lines | Loops even for γ < 1 |
| C | Chemistry consumption becomes the sinks; chemistry spreads faster along wide links | \~20 lines | Static spots → trees, dividing spots → loops? |

Coupling uses the two time scales directly: many chemistry steps, then one adaptation step, repeated. Stability code, ensembles, noise, scaling and real data all build on A–C and are left out of the minimum.

## Questions the plan can answer

Each question is answered by a number, not by an image looking right.

- **Why patterns at all?** Because two chemicals spread at different speeds, and below a threshold ratio some ripple sizes grow (stage 1).
- **Why that spacing?** The growth curve has one fastest ripple; its size is the spacing (stages 0–1).
- **Is pattern formation a phase transition?** Is there an order parameter, a sharp threshold, symmetry breaking, and memory (stages 1–3)?
- **Is an ensemble of runs thermodynamic?** In which ways yes (self-averaging, sharpening with size) and which not (no energy, no equilibrium) (stage 3).
- **What does noise do?** Does it act like temperature and erase the memory of a sudden switch (stage 3)?
- **What can local rules not do quickly?** How long they need to coordinate distant pixels (stage 4).
- **How do systems escape that limit?** By growing their own transport network, and when that network has loops (stages 5–6).
- **Do neural models understand or imitate?** Whether a learned rule reproduces the threshold, or invents half-patterns where physics allows none (stage 7).
- **What did Sims' radial images do?** One process with a knob that changes with radius, so each ring of the image sits at a different point of the transition (stages 1–2, using Sims' "vary pattern: radial").

## Code rules

The code should read like the math, so you can check one against the other line by line.

- **Plain NumPy and SciPy.** Functions, no classes. Each function does one thing in roughly 20 lines or fewer.
- **One file per layer.** Every function names its mathematical object in its docstring.

| File | Holds | Size |
| --- | --- | --- |
| `math_vis/reaction_diffusion.py` | Laplacian, Gray–Scott step loop, spacing measurement, rendering | Exists; trim to the essentials |
| `math_vis/stability.py` | Uniform states, 2×2 Jacobian, growth rate per ripple size, threshold | New, about 60 lines |
| `math_vis/networks.py` | Grid graph, pressure solve, conductance update, loop count | New, about 80 lines |
| `notebooks/demo_pattern_formation.ipynb` | Stages 0–4, one section each | New |
| `notebooks/demo_transport_networks.ipynb` | Stages 5–6 | New |

- **Every notebook section has the same shape:** question → math (a few lines) → predicted number → experiment → measured number → verdict → open question.
- **Small grids by default.** 64–128 px, so every cell runs in seconds on a laptop. Large renders only for images.
- **A test only for a claim that held.** For example, the threshold lies between the simulated values on either side of it.

## What to learn

Eight skills make the schema solid. Each has a self-test: if you can do it on paper, then check it in code, you own it.

| Skill | You know it when you can… | Stage | Where to learn |
| --- | --- | --- | --- |
| 2×2 linear systems | Tell stable / unstable / oscillating from the trace and determinant alone | 1 | Strogatz, *Nonlinear Dynamics and Chaos*, linear systems chapter |
| Linearisation | Find the uniform states of Gray–Scott and write their Jacobian by hand | 1 | Strogatz, fixed points and phase plane |
| Fourier modes and the Laplacian | Show a ripple of wavelength L is an eigenvector of the Laplacian, and compute its eigenvalue for the grid kernel | 1, 4 | Any numerical PDE text; check against `radial_spectrum` |
| Turing growth curve | Derive the condition that some ripple grows, and why it needs dB ≠ dA | 1 | Murray, *Mathematical Biology II*, spatial pattern formation |
| Bifurcations and hysteresis | Sketch strength vs knob for a gradual and a sudden switch, and say what each predicts for an up/down sweep | 2 | Strogatz, bifurcation chapters |
| Stochastic dynamics | Write a noisy update step and say what the Fokker–Planck equation describes | 3 | Gardiner, *Stochastic Methods* (only the first chapters) |
| Graph Laplacian and Kirchhoff | Solve for pressures on a small network by hand, with weighted links | 5 | Hu and Cai 2013; Tero et al. 2010 |
| Gradient flow | Show the Hu–Cai update lowers an energy, and what γ < 1 does to its shape | 5 | Hu and Cai 2013 |

The book chapters are named from memory; the papers below were opened and read for this plan.

**Sources**

- [Karl Sims, Reaction-Diffusion Tutorial](https://karlsims.com/rd.html) and [RD Tool help](https://karlsims.com/rdtool-help.html)
- [Tero et al. 2010, Rules for biologically inspired adaptive network design](https://pdodds.w3.uvm.edu/files/papers/others/2010/tero2010a.pdf)
- [A mesoscopic model of biological transportation networks](https://arxiv.org/pdf/1806.00120) (states the Hu–Cai 2013 model and the γ = 1 transition)
- [Katifori, Szöllősi, Magnasco 2010, Damage and fluctuations induce loops in optimal transport networks](https://ar5iv.arxiv.org/html/0906.0006)
- [Ronellenfitsch, Katifori 2016, Global optimization, local adaptation, and the role of growth in distribution networks](https://arxiv.org/abs/1606.00331v4)
- [Runions et al. 2005, Modeling and visualization of leaf venation patterns](https://www.algorithmicbotany.org/papers/venation.sig2005.html)
- [West, Brown, Enquist 1997, A general model for the origin of allometric scaling laws in biology](https://experts.arizona.edu/en/publications/a-general-model-for-the-origin-of-allometric-scaling-laws-in-biol/)
- [Bettencourt et al. 2007, Growth, innovation, scaling, and the pace of life in cities](https://mae.engr.ucdavis.edu/dsouza/Bettencourt2007.pdf)
- [Wang, Song, Barabási 2013, Quantifying long-term scientific impact](https://arxiv.org/pdf/1306.3293)
- [Self-Organising Textures (Distill, 2021)](https://distill.pub/selforg/2021/textures)
- [Differentiable Programming of Reaction-Diffusion Patterns](https://ar5iv.labs.arxiv.org/html/2107.06862)
