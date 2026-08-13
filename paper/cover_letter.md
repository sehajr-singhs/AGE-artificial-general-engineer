# Cover letter — Nature Machine Intelligence

**Date:** [date]
**Manuscript title:** An artificial general engineer that learns software and physical engineering through verified trial and error
**Manuscript type:** Article
**Corresponding author:** Sehaj Randhir Singh, Independent Researcher (affiliated with the Department of Electrical and Computer Engineering, NYU Tandon School of Engineering), sehajrsinghs@gmail.com

---

Dear Editors,

We are pleased to submit our manuscript, *"An artificial general engineer that
learns software and physical engineering through verified trial and error,"*
for consideration as an Article in *Nature Machine Intelligence*.

**Why this work matters now.** In June 2026, the founders of Prometheus
publicly described an "artificial general engineer" — AI that learns
engineering through real-world trial and error — backed by $12B in funding at
a $41B valuation. The ambition is to automate design and manufacturing of
physical products. Yet no complete, public, minimal instantiation of the
underlying architecture exists: the agent literature verifies weakly, and the
physics-informed machine learning literature predicts but does not act. Our
manuscript closes that gap with a concrete, reproducible system.

**What we report.** We present AGE, a complete autonomous engineering agent
built on four components: (1) a planner (a deterministic zero-dependency
"mechanical" brain or a language-model brain); (2) a sandboxed skill layer
(inspect, edit, run, verify); (3) a verification gate — every critical step
must pass tests or an *independent* numeric simulation, or the mission fails
and a lesson is journaled; and (4) episodic journal memory replayed into
future plans. For physics, AGE introduces PhysFormer, a transformer whose
reasoning layers are trained jointly with physics-consistency layers that
penalize violations of governing equations (PINN-style), together with
numerically independent simulators that verify every closed-form answer.
The paper's central methodological contribution is a new way to feed
physics into a transformer: **Law-Conditioned Attention (LCA)**. Each
governing equation is tokenized into a fixed 22-operator symbolic
vocabulary (∂ₜ, ∂ₓₓ, u·uₓ, EI·w″, energy conservation, …), embedded into a
law vector, and injected as a cross-attention key/value stream into every
layer — so attention is conditioned on the physics in force, not merely
penalized by it after the fact. Inputs are labeled by physical quantity
from a shared vocabulary, so the simply supported beam and the cantilever
present *identical* parameter tokens and only the law signature
disambiguates them. One shared transformer (shared body *and* shared heads)
then solves six physical laws at once — beam, cantilever, projectile,
pendulum, spring–mass, and RC. A controlled six-seed experiment against a
constant-signature ablation (identical architecture, data, and budget)
isolates the mechanism's contribution: feeding the equation into the
transformer significantly improves trajectory fidelity (p = 0.0003 over 36
paired runs, 21% median curve-error reduction) and cuts held-out answer
error on exactly the laws whose parameters do not identify them (beam 34%
vs 40%, cantilever 28% vs 35%), while an honest negative result on RC —
whose normalized trajectory is the same curve for every time constant —
localizes where law-conditioning does not pay. The generalist matches
single-law specialists within 1.1–2.8× on five of six laws at 37% of their
data per law.

Three further experiments turn the mechanism claim into causal, falsifiable
evidence. (1) *The equation is causally active at inference.* Because beam
and cantilever present literally identical parameter tokens, swapping the
law signature at inference on a trained problem isolates the equation
vector's effect: the prediction moves across the boundary between the two
bending solutions (steering index +0.090 vs −0.132 for a constant-signature
control, p < 0.0001; per-seed p = 0.031), while the control is provably
insensitive — the equation steers behavior, it does not merely label data.
(2) *Adaptation to a new law with a quarter of the data.* A generalist
pretrained on five laws adapts to a sixth, held-out law (cantilever) with
24 samples in 40 epochs, at 2.4–2.9× lower answer error than a from-scratch
specialist on the same data (median 0.20 vs 0.58); the law signature adds a
further 18% reduction. (3) *The two physics channels are cleanly
separated.* A controlled sweep (identical networks, budgets, seeds; only
the residual weight differs) on the 2D heat plate shows the residual-loss
channel cuts the predicted field's governing-equation violation 4–8×
without improving held-out field fidelity — consistency, not accuracy, is
what the loss channel buys, and field accuracy is carried by the data and
the LCA input channel. We also correct an over-optimistic earlier claim
(the canonical heat-plate 6% field error is the easiest member of the
validation distribution, whose mean is ~29%), reported explicitly in the
paper.
Results include: closed-form answers verified to relative residuals as low
as 2.6×10⁻⁹ by independent integrators across eight physics domains —
including a viscous Burgers conservation law with shock formation, verified
by an independent finite-volume upwind solver — a cantilever beam with
its own finite-difference verifier, and a two-dimensional steady-state heat
plate verified by a sparse finite-difference Poisson solve; a five-seed
baseline study (75 runs: 5 domains × 3 kinds × 5 seeds, mean ± std)
against equal-budget MLP and no-physics transformer baselines in which a
pooled Wilcoxon signed-rank test shows the physics term significantly
reduces governing-equation violation of the predicted trajectories
(p < 0.001, Cliff's δ = −0.92, ~19-fold median reduction) while leaving
scalar accuracy statistically unchanged — plus a per-instance DeepXDE PINN
baseline on the Burgers problem (the setup most favourable to a PINN),
with both models evaluated by identical metrics; a verification-gate
benchmark (7 missions × gate on/off) showing the gate eliminates false
successes (0% vs 29% without it), including a stale-bytecode failure mode
we found and fixed; and end-to-end natural-language design missions — beam,
cantilever, and Burgers — completed in a single planning iteration.

**What is distinctive.** The paper makes three transferable design claims,
each backed by controlled experiments: verification, not model confidence,
must be the arbiter of success; physics and data should be trained together
with a scale-free physics gradient (we document and fix two failure modes
that destabilize physics-informed training, and we report negative results
on two further capacity changes honestly); and memory should be episodic
and replayable. The entire system is ~5,900 lines of dependency-light code
that passes 54 unit tests and runs on a laptop — a fully auditable baseline
for the "general engineer" agenda that commercial efforts are pursuing at
much larger scale.

**Fit for Nature Machine Intelligence.** The work sits at the journal's
core intersection of machine learning, autonomous agents, and the physical
sciences. It is an empirical architecture paper with reproducible code,
honest characterization of failure modes, and a clear path from simulated
verification to real hardware. We believe it will interest the journal's
readership in agentic AI, physics-informed learning, and the automation of
engineering.

All code, data, model weights, significance-test outputs, and figure-
generation scripts are released with the manuscript. The authors declare no competing interests. This work
has not been published or submitted elsewhere.

Thank you for your consideration. We look forward to your response.

Sincerely,

Sehaj Randhir Singh
Independent Researcher
Department of Electrical and Computer Engineering, NYU Tandon School of Engineering
sehajrsinghs@gmail.com

---

*The figure-data JSONs, model weights, significance-test outputs, and test
logs cited in the manuscript are committed alongside the code in this
repository. ORCID and repository DOIs will be completed before submission.*
