# The ideas, explained

This tab explains, in plain words, every idea behind the plan. Read it top to bottom: each section builds on the one before.

## Every model in plain words

All the models in this project do the same basic thing: they take a random start and, step by step, turn it into a pattern. They differ in who wrote the rule and what each pixel is allowed to see.

**Gray–Scott (reaction–diffusion).** Every pixel holds two chemicals, A and B. Three things happen at every pixel, every step:

- **Feed:** A is slowly topped up.
- **Reaction:** B uses up A to make more B, and B slowly dies off.
- **Diffusion:** both spread to the neighbours, A faster than B.

Spots, stripes and mazes come out of these three rules alone. A human wrote the rule, and each pixel only sees its neighbours.

**Adaptive flow network (Tero; Hu and Cai).** Fluid flows through pipes. Pipes that carry a lot of flow get wider; pipes that carry little shrink and vanish. Over time the system grows its own network of main routes, like veins.

**Neural cellular automaton.** The same idea as Gray–Scott, but the rule at each pixel is a small neural network. You show it a target image or texture, and training adjusts the rule until it grows that target. Each pixel still only sees its neighbours.

**Flow matching.** A large neural network learns a "velocity": from this noisy image, move in this direction. Following that velocity turns pure noise into an image. The network usually sees the whole image at once.

**Fokker–Planck equation.** Not a pattern maker but a way to describe chance. If random kicks are added to any of the models above, the Fokker–Planck equation tells how the *probability* of each possible image changes over time.

## Turing's idea

In 1952 Alan Turing asked how a ball of identical cells can grow stripes, spots or fingers. His answer surprised everyone: **diffusion, which normally smooths things out, can create patterns.**

Normally diffusion is a smoother. Drop ink in water and it spreads until everything is the same colour. So you would expect two chemicals that react and spread to end up evenly mixed.

Turing showed that this fails when two conditions hold together:

1. **One chemical boosts itself locally.** Where there is a little more of it, it makes even more.
2. **The other chemical spreads faster and holds the first one back.**

Picture it in Gray–Scott. Where B is slightly high, it grows by eating the A nearby. A spreads fast, so the shortage of A spreads into the neighbourhood. The neighbours now lack A and cannot grow B. So the high spot stays high and its surroundings stay low. A small bump has become a spot, with an empty ring around it.

The short version: **short-range self-boost, long-range hold-back.** It only works if the two spreading speeds are different enough. If both chemicals spread at the same speed, the hold-back arrives exactly where the boost is, and nothing forms. Our simulation confirms this: with equal speeds, the image stays perfectly flat.

The spacing between spots is set by how far the hold-back reaches. That is why spacing grows with the square root of the diffusion speed: we measured 7.9, 11.5 and 16.4 pixels as diffusion doubled each time, a factor of about √2 per doubling.

## Stability analysis, step by step

This turns Turing's idea into a number you can check. The result for our coral settings: patterns appear when dB/dA drops below **0.61**, with spacing about **17–18 px** at the threshold.

**Step 1: the equations.** Here f is the feed rate, k the kill rate, and ∇² the Laplacian ("neighbours' average minus me"):

```latex
\frac{\partial A}{\partial t} = D_A \nabla^2 A - AB^2 + f(1-A), \qquad \frac{\partial B}{\partial t} = D_B \nabla^2 B + AB^2 - (k+f)B
```

**Step 2: find the flat states.** If A and B are the same everywhere, the Laplacian is zero. Setting both right-hand sides to zero gives:

- **Empty:** A = 1, B = 0.
- **Two mixed states,** where A·B = k + f and A(1 − A) = (k + f)²/f. These exist only if (k + f)²/f ≤ 1/4. For coral (f = 0.0545, k = 0.062) the value is 0.249, so they only just exist.

**Step 3: nudge a flat state.** Write A = A\* + small, B = B\* + small, and keep only first-order terms. The small changes then obey a matrix J (the Jacobian):

```latex
J = \begin{pmatrix} -B^{*2} - f & -2A^*B^* \\ B^{*2} & 2A^*B^* - (k+f) \end{pmatrix}
```

For the empty state, J has eigenvalues −f and −(k + f). Both are negative, so **the empty state is always stable**. Tiny ripples on it always die. This is why Gray–Scott needs a real seed (a blob of B), not just noise around the empty state.

**Step 4: nudge with a ripple.** Make the nudge a wave of wavenumber q (wavelength 2π/q). The Laplacian of a wave is just −q² times the wave, so each ripple size grows or shrinks on its own:

```latex
\text{growth rate } \sigma(q) = \text{largest eigenvalue of } \; J - q^2 \begin{pmatrix} D_A & 0 \\ 0 & D_B \end{pmatrix}
```

On our grid, −q² is replaced by the grid kernel's version, −0.6(1 − cos q), which is the same for long waves.

**Step 5: read off the threshold.** A 2×2 matrix is stable when its trace is negative and its determinant positive. Diffusion only makes the trace more negative, so the only way to become unstable is for the determinant to turn negative for some q. That needs D\_A and D\_B to be different enough: this is Turing's condition in one line.

For the mixed state A\* = 0.469, B\* = 0.248, the computer finds:

- **Threshold:** dB/dA = 0.612. Above it every ripple dies; below it some grow.
- **First ripple to grow:** wavelength 17.9 px.
- **Fastest ripple at dB/dA = 0.5:** 16.4 px. The simulation measured 16.4 px.

One honest caveat: this mixed state sits right at the edge of existing, so even a perfectly flat nudge barely grows or shrinks (growth rate +0.0001). The ripples below the threshold grow far faster than that, so the threshold still means what it says.

## What the threshold really does

Take the flat grey image and add one gentle ripple of a given size. The chart shows, for each size, whether that ripple grows (above zero) or dies (below zero), at three values of the knob dB/dA.

&#91;embedded content: computed in this session from the stability analysis above\]

- **At 0.75**, every ripple size is below zero. Whatever ripples the random start holds, they all fade, and the image ends flat.
- **At 0.612**, the top of the hump just touches zero. One ripple size, about 18 px, is balanced on the edge. This is the threshold.
- **At 0.55**, the hump pokes above zero. Ripples between about 12 and 24 px now grow; all others still die.

So the threshold does two things at once. **It decides whether a pattern exists at all**, and **it decides the pattern's size**: only ripples near the peak grow, and the fastest one wins. Turning the knob lifts or lowers the whole hump.

Growth cannot go on forever: A runs out and values stay between 0 and 1. So a growing ripple stops at a finite strength, and that finished ripple is the pattern you see.

## Control parameter, order parameter, phase transitions

A phase transition is when turning one knob smoothly makes the behaviour change *in kind*, like water turning to ice at 0 °C. Two words keep this precise.

- **Control parameter (λ):** the knob you turn. Temperature, for water. Here, λ = dB/dA: how fast B spreads compared with A. Another choice is a position along a path in (feed, kill) space.
- **Order parameter:** what you *measure*. It is zero on one side of the transition and nonzero on the other. Here, the pattern strength: how much B varies across the image, std(B). Zero means flat; above zero means a pattern.

Our sweep, three seeds each: std(B) is exactly 0 for λ = 1.0, 0.85 and 0.75; about 0.05–0.07 at 0.65; about 0.13 at 0.6 and below.

**Gradual or sudden.** Transitions come in two kinds.

- **Gradual:** just past the threshold the pattern is very faint, and it strengthens smoothly as you turn further. A magnet cooling below its critical temperature is like this.
- **Sudden:** the pattern jumps straight to full strength. It may appear *before* the threshold if pushed hard enough. It has memory (hysteresis): it disappears at a different λ than where it appeared. Boiling is like this.

Our pattern appeared at 0.65, slightly above the predicted 0.61, and jumped in strength. That hints at sudden. But the simulation starts from big random blobs, which is a strong push, so this is not proof. The clean test: start from a full pattern at 0.55, turn λ slowly up past 0.61, and see where it dies.

**Symmetry breaking.** The flat image looks the same everywhere, and so do the equations: no position is special. A pattern must put its spots *somewhere*. The rule cannot choose, so the random seed chooses. Freezing works the same way: liquid water looks the same everywhere, but a crystal must pick where its atoms sit.

## Karl Sims' radial images: two regimes, one process

The last two images on [Sims' Reaction-Diffusion Images page](https://karlsims.com/rd-images.html) have rings in the centre and branching fingers at the rim. **They look like one process whose knob changes with distance from the centre**, so each ring of the image sits at a different point in rule space.

Sims does not explain these two images on the page; it holds only pictures. But his [RD Tool help page](https://karlsims.com/rdtool-help.html) documents exactly this mechanism:

- **Vary pattern, radial:** a second (feed, kill) pair sets the centre, the main pair sets the outer areas, and the tool blends between them.
- **Regrow:** start a new pattern from a single seed at the centre.
- **Scale radial or ring:** make pattern size change across the image.
- **Orientation:** let diffusion run faster in one direction, giving streaks.

The images date from 2012–13, so I cannot confirm they were made with this tool, but the documented mechanism fits.

**Our experiment.** We grew patterns from one centre seed in three regimes, shown at 3,000, 6,000 and 9,000 steps (left to right):

&#91;image: Three regimes grown from one centre seed\]

- **Top row, coral (f = 0.0545, k = 0.062):** the pattern grows outward as a branching, fingered front.
- **Middle row, worms (f = 0.058, k = 0.065):** the seed cannot grow at all; it stays a dot.
- **Bottom row (f = 0.042, k = 0.059):** the seed grows as concentric target rings.

So rings in the centre and fingers at the rim match the bottom row inside and the top row outside. That is "vary pattern: radial". Our outlines come out squarish because the grid has four directions; Sims' are rounder, which suggests he does something about that.

**Why this matters for the phase-transition view.** It is not two processes glued together. It is one equation everywhere, with one knob that changes with radius. The image becomes a spatial bifurcation diagram: you can see the transition between regimes as a boundary in the picture. One caution: a pattern can invade a region that would not form one on its own, so the boundary in the image may sit away from the true threshold. That gap is itself worth measuring.

## Gray–Scott is not in equilibrium

This is the most important limit of the thermodynamics analogy. **Gray–Scott patterns only exist because material keeps flowing through the system.**

**What equilibrium means.** A closed system, left alone, settles down. A cup of coffee cools to room temperature and stays there. In equilibrium physics there is always an *energy* (more precisely, a free energy) that only goes downhill. The system ends at the bottom, and noise makes it visit each state with a probability set by that energy (the Boltzmann distribution).

**Why Gray–Scott is different.** A is fed in all the time, and B is removed all the time. It is an open, driven system, more like a candle flame or the whirlpool over a draining bath than like a cup of coffee. Stop the feed and the pattern fades. Such patterns are often called *dissipative structures*: they hold their shape only by using up a steady flow.

**A concrete check.** If the reaction were downhill on some energy, the effect of B on A's change would equal the effect of A on B's change. Here A's change contains −AB², so its dependence on B is −2AB. B's change contains +AB², so its dependence on A is +B². These differ, so no energy exists for the reaction.

**What this means in practice:**

- **No Boltzmann distribution.** Even with noise, the long-run probabilities are not set by an energy.
- **Patterns can move forever.** In the mitosis regime, spots keep dividing and dying; there is no final resting state.
- **Seeds pick attractors, not energies.** When different seeds give different final images, that reflects which basin of attraction each start fell into, as in your Newton basins, not a thermal balance.

**Where an energy does exist.** The vein layer (Hu–Cai) *is* downhill on an energy: pumping cost plus building cost. So that layer has a true landscape. Near a pattern's threshold, the dynamics often simplifies to something landscape-like too; that is the textbook picture to test, not a proven fact for Gray–Scott.

## Noise, ensembles and Fokker–Planck

Right now our randomness enters in one place only: the starting state. After that, every step is exact. Same seed, same image.

**An ensemble over seeds.** Run many seeds and you get many different images. Yet whole-image numbers barely change: the spacing was 7.9, 7.9 and 7.9 px for three seeds. This is **self-averaging**, the same reason a glass of water has a definite temperature although its molecules all differ. A testable sign of a real transition: as the grid gets bigger, the switch from "no pattern" to "pattern" should get sharper.

**Adding noise.** Add a small random kick to every pixel at every step. The update becomes a stochastic differential equation. Here X is the whole image (all A and B values), F is the Gray–Scott rule, and dW is random noise:

```latex
dX = F(X)\,dt + \sigma\, dW
```

The noise strength σ plays the role of temperature. A prediction to test: more noise should shrink the hysteresis loop, because noise helps the system escape a state that is only just stable.

**The Fokker–Planck equation.** Instead of following one noisy run, ask: what is the probability p(X, t) of seeing image X at time t? That probability obeys:

```latex
\frac{\partial p}{\partial t} = -\nabla \cdot \big( F\, p \big) + \frac{\sigma^2}{2} \nabla^2 p
```

In words: probability is carried along by the rule F (first term) and spread out by the noise (second term). It is exact, but X has one coordinate per value per pixel, about 130,000 for a 256×256 image, so nobody solves it directly. Running many noisy simulations is the practical way to sample it.

**Where equilibrium shows up, and where it does not.** If the rule were downhill on an energy V (F = −∇V), the long-run answer would be the Boltzmann-like form:

```latex
p(X) \propto \exp\!\big(-2V(X)/\sigma^2\big)
```

Gray–Scott has no such V (previous section). So its long-run distribution exists, but it is not of this form, and probability keeps circulating instead of resting.

**The useful simplification.** Near the threshold, the whole image is often summarised by one number: the pattern's amplitude a. The textbook picture is that a obeys a small equation with a real potential:

```latex
da = (\mu a - g a^3)\,dt + \sigma\, dW, \qquad V(a) = -\tfrac{\mu}{2}a^2 + \tfrac{g}{4}a^4
```

Below the threshold (μ < 0) V has one valley at a = 0: no pattern. Above it (μ > 0) there are two valleys at a ≠ 0: a pattern. Here a one-dimensional Fokker–Planck equation makes full sense, with valleys, a barrier and noise-driven hops. This is the cleanest bridge from Gray–Scott to a true phase transition, and something to test, not assume.

## Three ways from noise to a pattern

Gray–Scott, neural cellular automata and flow matching all turn randomness into a picture. The real differences are who writes the rule, what each pixel sees, and what the in-between steps mean.

|  | Gray–Scott | Neural cellular automaton | Flow matching |
| --- | --- | --- | --- |
| Who writes the rule | a human (chemistry) | training, from a target image or texture | training, from many example images |
| What each pixel sees | its neighbours | its neighbours | usually the whole image |
| Is the rule the same over time | yes | yes | no, it changes with time |
| In-between steps | a pattern growing | a pattern growing | noise fading into a picture |
| What it copies | nothing; it *is* the process | the process, approximately | the look of the final images |

**Neural cellular automata, in more detail.** "Growing Neural Cellular Automata" (Mordvintsev and colleagues, Distill 2020) trained a tiny network, applied at every pixel, to grow a target shape from one seed and repair it when damaged. "Self-Organising Textures" (Niklasson and colleagues, Distill 2021) trained it to match a texture's statistics instead. Its patterns keep moving instead of freezing, contain self-maintaining blobs that divide and collide, and still work on hexagonal grids they never saw.

**Differentiable Programming of Reaction-Diffusion Patterns** (arXiv 2107.06862) is closest to Gray–Scott. It keeps diffusion fixed (the same 3×3 Laplacian) and learns only the reaction, as a small network. Most models kept working at other grid resolutions, which the authors read as having learned an approximate equation rather than a grid trick. The models also ran on 3D shapes. From what I read, the paper does not ask *why* its learned rules make patterns. Our stability analysis could answer that for a learned reaction.

**Flow matching, in more detail.** It learns a velocity that carries noise to images. It only cares that the final images, taken together, look right, not how they got there. So it copies the look, not the process. On a 2D point cloud (each sample just two numbers) there are no neighbours, so the local-versus-global difference disappears; it only matters for images.

**A test that separates understanding from imitation.** Train each model on patterns made at several λ values, then ask for patterns near the threshold λ = 0.61. The real system gives either a flat image or a full pattern. A model that only learned the look may produce faint half-patterns that the real system never makes. For flow matching that is my prediction, not a known result.

## Local versus global rules

A local rule lets each pixel see only its neighbours. A global rule lets it see the whole image. **Local rules can still build long-range order, but it costs time.**

**First, a naming trap.** "Diffusion" means two different things here. Physical diffusion (ink spreading) is local. Diffusion *models* (the image generators) are close cousins of flow matching and usually use a global network. What makes a generator global is the network you choose, not the training method.

**The light cone.** Apply a neighbour-only rule once and information moves one pixel. Apply it 100 times and it can reach about 100 pixels. Each pixel's influence spreads like a growing circle. So a local rule needs at least as many steps as the distance it must coordinate. Gray–Scott shows this works: the spot spacing is the same across the whole image, though no pixel ever sees past its neighbours.

**In principle, local rules can do anything.** Some very simple cellular automata, like Conway's Game of Life and "Rule 110", are known to be able to carry out any computation, given enough time and space. The real questions are how long it takes and whether you can train it.

**What each is good at.**

- **Textures suit local rules.** A texture looks statistically the same everywhere, which is exactly what one rule repeated at every pixel produces. Local rules also work at any size and repair damage.
- **Compositions suit global rules.** "A face in the middle" needs a sense of *where*, which a local rule lacks unless something tells it. Global rules coordinate the whole image in few steps but are tied to one image size and do not repair themselves.

**Your genes analogy, mostly right.** Every cell carries the same genome, like every pixel sharing one rule. Development starts from one cell, like a neural automaton growing from one seed. Different cell types come from different *states* of the same rule; a common view is that cell types are stable states (attractors) of the gene network. Four refinements:

1. **The seed is not blank.** The egg already holds gradients from the mother; in fruit flies a protein runs from head end to tail end. That is the "sense of where" a local rule lacks.
2. **Not everything is neighbour to neighbour.** Signalling molecules spread across tissue, and hormones travel in the blood.
3. **It takes time.** Many cell divisions and signalling rounds, as the light cone predicts.
4. **One genome makes one kind of organism.** Diversity across species comes from different genomes. For "all images", the analogy is a local rule plus a genome-like input saying what to grow. In machine learning that input is called conditioning.

**The way out of the light cone: build highways.** Point 2 is the key. A system can grow its own transport network, so that signals travel far quickly. In the network models (next section) each pipe uses a local rule, yet the network becomes a global highway. Their flow is computed for the whole network at once, which is fair because pressure settles almost instantly compared with how slowly pipes grow. So **"global" often just means "fast compared with the other layer".**

## Networks that build themselves

Gray–Scott runs on a fixed grid. Living systems also build the grid: veins, vessels, roads. **Traffic builds roads, and roads carry traffic.** Three published ingredients decide what shape comes out.

**The basic model.** Each pipe has a width (conductance C). Fluid enters at sources and leaves at sinks. Pressure settles quickly; the flow Q through each pipe follows from it. Then, slowly, each pipe adapts. The Hu–Cai rule:

```latex
\frac{dC}{dt} = \frac{Q^2}{C} - \nu\, C^{\gamma}
```

The first term says busy pipes grow. The second says every pipe costs upkeep, growing with its size as C^γ. Tero and colleagues' slime-mould model (Science 2010) uses the same idea: dC/dt = f(|Q|) − C. Placed on a map of Tokyo-area cities, it grew a network with cost and efficiency similar to the real rail system; the real rail was somewhat more robust to broken links.

**What controls the shape.**

1. **The cost exponent γ.** With a steady load: below 1 the best network is a **tree** (no loops); above 1 it is a uniform **sheet**; γ = 1 is the transition (Hu and Cai 2013; Katifori and colleagues 2010).
2. **The load.** One steady source gives a tree. A **fluctuating** load (the sink keeps moving) gives loops inside loops. **Damage** (pipes that may break) gives loops too, even for γ below 1. Katifori's team cut the main vein of a lemon leaf and saw the flow reroute through its loops.
3. **Growth.** Local rules alone often get stuck in poor networks. If the tissue grows while the network forms, it escapes to much better ones (Ronellenfitsch and Katifori 2016).

| Target | Load | Growth | Expected shape |
| --- | --- | --- | --- |
| Leaf veins | fluctuating, damage | yes | nested loops (published) |
| Main arteries | steady, one pump | yes | branching tree (published, steady case) |
| City streets | many moving sources and sinks | outward | loops everywhere (my hypothesis) |
| Citations | none: no space, no flow | papers keep arriving | see below |

**Leaf veins.** Besides flow models, plants form veins by "canalization": the hormone auxin flows through tissue, and cells it passes through get better at carrying it, so channels reinforce themselves. Runions and colleagues (2005) grow realistic leaf venation from a leaf outline; that is the baseline to compare with.

**The fresh question: chemistry as the load.** If every Gray–Scott spot consumes nutrients, the spots become the sinks. Static spots should give trees feeding each spot. Moving, dividing spots (the mitosis regime) are a fluctuating load, so Katifori's result predicts loops. I found no published answer.

**Growing a real city or leaf.** You can match the *kind* of network, not the exact map: two runs with the same settings differ, as two oak leaves differ. Match statistics instead (loops per area, block sizes, how hierarchical it is). Given real constraints (coastline, where people live, the leaf outline), ask whether the *main* routes grow where the real ones are. Forcing an exact match makes the model memorise and explain nothing.

**Citations.** No space and no pipes, but the same slow rule of reinforcement plus decay. Wang, Song and Barabási (2013) model citations with three ingredients: preferential attachment (cited papers attract more citations), aging (interest fades), and fitness (each paper's own appeal). They report that, after rescaling, citation histories of individual papers collapse onto one curve.

## Geoffrey West: how things scale with size

West's key move was not a simulation. It was to **measure how one quantity grows with size across many systems**, then explain the exponent with a network argument.

**Biology.** West, Brown and Enquist (Science 1997) assume that nutrients travel through a branching network that fills the body, wastes as little energy as possible, and ends in smallest tubes of fixed size in every animal. From this they derive that metabolic rate grows as mass to the power 3/4. A mouse and an elephant follow the same law.

**Cities.** Bettencourt, West and colleagues (PNAS 2007) measured many quantities Y across cities of population N and fitted Y ∝ N^β. They found three groups:

- **β below 1, infrastructure:** doubling the population needs less than double the roads and cables. They call this economies of scale.
- **β about 1, individual needs:** housing and jobs grow exactly with population.
- **β above 1, social output:** wages, patents and also crime grow *faster* than population. They attribute this to more social interaction in bigger cities.

&#91;embedded content: Bettencourt et al. 2007, PNAS · selected exponents\]

**What our model can and cannot test.** The infrastructure side is about pipes, so it fits: grow networks for systems of different size, keep the smallest units fixed, and measure the exponent of total network length versus size. Then compare with West's theory and with the city values of 0.83 to 0.87. The social side comes from people interacting, not from pipes, so it is not in our model.

## Sources

Papers and pages opened during this work. Book references and the Game of Life / Rule 110 facts are from memory.

- [Karl Sims, Reaction-Diffusion Images](https://karlsims.com/rd-images.html), [Tutorial](https://karlsims.com/rd.html), [RD Tool help](https://karlsims.com/rdtool-help.html)
- [Thread: Differentiable Self-organizing Systems (Distill)](https://distill.pub/2020/selforg/), home of Growing Neural Cellular Automata
- [Self-Organising Textures (Distill, 2021)](https://distill.pub/selforg/2021/textures)
- [Differentiable Programming of Reaction-Diffusion Patterns](https://ar5iv.labs.arxiv.org/html/2107.06862)
- [Tero et al. 2010, Rules for biologically inspired adaptive network design](https://pdodds.w3.uvm.edu/files/papers/others/2010/tero2010a.pdf)
- [A mesoscopic model of biological transportation networks](https://arxiv.org/pdf/1806.00120) (states the Hu–Cai 2013 model)
- [Katifori, Szöllősi, Magnasco 2010, Damage and fluctuations induce loops in optimal transport networks](https://ar5iv.arxiv.org/html/0906.0006)
- [Ronellenfitsch, Katifori 2016, Global optimization, local adaptation, and the role of growth in distribution networks](https://arxiv.org/abs/1606.00331v4)
- [Runions et al. 2005, Modeling and visualization of leaf venation patterns](https://www.algorithmicbotany.org/papers/venation.sig2005.html)
- [West, Brown, Enquist 1997, A general model for the origin of allometric scaling laws in biology](https://experts.arizona.edu/en/publications/a-general-model-for-the-origin-of-allometric-scaling-laws-in-biol/)
- [Bettencourt et al. 2007, Growth, innovation, scaling, and the pace of life in cities](https://mae.engr.ucdavis.edu/dsouza/Bettencourt2007.pdf)
- [Wang, Song, Barabási 2013, Quantifying long-term scientific impact](https://arxiv.org/pdf/1306.3293)
