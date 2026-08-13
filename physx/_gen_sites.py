"""_gen_sites.py — generate the house-style GitHub Pages site for each repo.

Matches the look of the author's existing project sites (serif title,
KPI grid, abstract panel, honest-gaps section, mono reproduce block,
cross-linked footer). Writes index.html into the root of each repo
under Desktop/repos/ and into the AGE working tree.

Run:  python3 physx/_gen_sites.py
"""

import os

AGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = os.path.abspath(os.path.join(AGE, "..", "repos"))

SITES = [
    {
        "repo": "AGE-artificial-general-engineer",
        "title": "AGE — Artificial General Engineer",
        "subtitle": "An autonomous engineering agent that plans, acts, verifies, and iterates — "
                    "over software projects and physics designs — with a physics-adjusted "
                    "transformer (PhysFormer) core and an honest, fully reproducible paper series.",
        "byline": "Sehaj Randhir Singh &middot; independent, affiliated with NYU Tandon ECE &middot; 2026",
        "code": "https://github.com/sehajr-singhs/AGE-artificial-general-engineer",
        "paper": "nmi_paper.pdf",
        "si": "supplementary_information.pdf",
        "ieee": "ieee_paper.pdf",
        "kpis": [
            ("65", "Tests green", "49 physics (closed forms, verifiers, 10-law set) + 16 node agent tests"),
            ("8+", "Physics domains", "projectile, pendulum, spring, beam, cantilever, RC, damped, Kepler, LC, drag, Burgers, heat"),
            ("3.9%", "PhysFormer projectile error", "12.7% beam; answers verified against independent numeric simulators"),
            ("0%", "False success with the gate", "29% without it — the verify step is what makes the loop trustworthy"),
        ],
        "abstract": (
            "AGE turns an engineering goal into a plan, executes it with sandboxed skills, and refuses to "
            "declare success until an independent verifier agrees. In the software domain that means running "
            "the test suite; in the physics domain it means a closed-form answer cross-checked by a numeric "
            "simulator written independently of the training signal, and a PhysFormer that predicts answers "
            "from the parameters alone. The papers in this repo measure the mechanism, not just the demo: "
            "the equation is causally active (p < 0.0001), a pre-registered theory of when conditioning pays "
            "was tested on ten laws and falsified honestly, and every number in every manuscript reads from a "
            "committed JSON.",
        ),
        "sections": [
            ("The system", (
                "<span class='lead'>Give AGE a goal and it runs the loop.</span> "
                "scaffold a project, explain a repo, find the TODOs, make the test suite pass, or design a "
                "beam — it plans, acts, verifies, reflects, and journals a lesson every time a verification "
                "fails, so the next run starts smarter. Two brains: a deterministic mechanical brain that "
                "works with zero API keys, and an LLM brain behind any OpenAI-compatible endpoint. Writes are "
                "confined to the working directory; destructive commands are refused.",
            )),
            ("The physics core", (
                "<span class='lead'>Every design is computed twice, independently.</span> "
                "physx/ evaluates the closed-form solution, then cross-checks it with a numeric simulator "
                "(Euler/RK4, finite differences) written from a different formulation. The PhysFormer — a "
                "transformer with reasoning layers plus physics-consistency layers — predicts answers from "
                "the parameters alone, trained on exact closed-form trajectories with the governing-equation "
                "residual in the loss. Answers spanning orders of magnitude are learned in log space.",
            )),
            ("What survives contact with reality", (
                "The two headline numbers are the negative ones. The pre-registered regime theory — that "
                "equation conditioning pays monotonically in token ambiguity — was falsified on a ten-law "
                "suite (ρ = 0.07, p = 0.88), and the failure analysis is the paper's sharpest section. "
                "And the loss channel cuts the governing-equation residual 19× while leaving held-out "
                "accuracy flat: physics as a penalty buys consistency, not accuracy. Physics as input tokens "
                "is what moves the numbers. Both results are in this repo, with the data to re-run them.",
            )),
        ],
        "reproduce": (
            "git clone https://github.com/sehajr-singhs/AGE-artificial-general-engineer\n"
            "cd AGE-artificial-general-engineer\n"
            "npm test                        # 16 node tests: loop, skills, sandboxing, physics, journal\n"
            "python3 -m unittest physx.test_physx   # 49 physics tests\n"
            "node age.js --demo              # two-act demo: software scaffold + physics design"
        ),
        "figs": [],
        "sisters": [
            ("physics-transformers", "the PhysFormer architecture and the falsified regime theory"),
            ("physbench", "the 12-domain verifiable benchmark"),
            ("verification-gated-agents", "the gate as the missing control in agent evaluation"),
            ("physics-loss-channel", "when physics supervision in the loss helps — and when it only enforces consistency"),
            ("fewshot-law-acquisition", "transfer across laws: what carries the knowledge"),
            ("field-consistency", "the cost of consistency on 2D fields"),
        ],
    },
    {
        "repo": "physics-transformers",
        "title": "Physics Transformers",
        "subtitle": "The governing equation is fed to a transformer as input tokens, not only as a "
                    "penalty — and a pre-registered theory of when that should pay was tested on ten laws "
                    "and falsified. The failure is the paper's sharpest result.",
        "byline": "Sehaj Randhir Singh &middot; independent, affiliated with NYU Tandon ECE &middot; 2026",
        "code": "https://github.com/sehajr-singhs/physics-transformers",
        "paper": "manuscript.pdf",
        "si": "supplementary_information.pdf",
        "ieee": None,
        "kpis": [
            ("ρ = 0.07", "Pre-registered prediction", "falsified: p = 0.88, leave-one-out ρ = −0.58, reported in full"),
            ("21%", "Trajectory error cut", "law-conditioned attention, 36 paired runs, p = 0.0003"),
            ("p < 0.0001", "Equation swap steers prediction", "constant-signature control exactly insensitive"),
            ("0.037 / 0.110", "DeepONet vs generalist", "ten dedicated operators vs one model, no law identity"),
        ],
        "abstract": (
            "PhysFormer is a transformer adjusted for physics. Physics enters through two channels with "
            "different jobs: a loss channel (a differentiable physics-consistency layer that buys "
            "consistency, 6–8× residual reduction, without held-out accuracy) and an input channel — the "
            "invention of this paper — which tokenizes the governing equation into a symbolic vocabulary and "
            "injects it as a cross-attention stream in every layer. One shared transformer solves ten laws "
            "at once, beam and cantilever presenting literally identical parameter tokens with only the "
            "equation to distinguish them. The causal test (p < 0.0001), the falsified pre-registration, and "
            "the DeepONet external baseline are all measured, all committed, and all re-runnable.",
        ),
        "sections": [
            ("What survived contact with the mathematics", (
                "<span class='lead'>The equation is causally active.</span> Swapping the equation signature "
                "at inference steers the prediction while a constant-signature control is exactly insensitive; "
                "the effect concentrates on the one token-identical pair (beam/cantilever). "
                "<span class='lead'>The regime theory failed — and that is the result.</span> Filed before "
                "any ten-law training: benefit should be monotone in token-vocabulary ambiguity. Measured "
                "after 6 full trainings: ρ = 0.07, p = 0.88. The overlap measure conflates supersets with "
                "genuine indistinguishability, and the refined hypothesis is left as an open problem, not a "
                "swept-under null. The pre-registration is committed in results/pre_registration.json.",
            )),
            ("External baseline", (
                "Ten dedicated per-law DeepONets on identical splits reach median held-out error 0.037 vs. "
                "the single generalist's 0.110 — but they are ten separate models with no cross-law "
                "structure. The generalist beats the per-law specialists outright on spring (0.111 vs 0.122) "
                "and LC (0.100 vs 0.192) while serving all ten laws with one set of weights. A tradeoff, "
                "stated plainly; the pooled single-model DeepONet did not complete under available compute "
                "and is reported as an attempt, not a result.",
            )),
        ],
        "reproduce": (
            "git clone https://github.com/sehajr-singhs/physics-transformers\n"
            "cd physics-transformers\n"
            "python -m unittest tests.test_physx          # 49 physics tests, 10-law set\n"
            "python figs/make_figures.py && python figs/make_figures_ext.py\n"
            "python src/physx/regime_oos.py --out figs/regime_oos.json   # the falsification\n"
            "python src/physx/train_multi.py --ext --seeds 3             # real + dummy, 3 seeds"
        ),
        "figs": ["figs/fig7_regime_oos.png", "figs/fig8_deeponet.png"],
        "fig_captions": [
            "Pre-registered prediction vs. measured benefit (left) and the failure analysis (right).",
            "External operator-network baseline: ten dedicated DeepONets vs. the single generalist.",
        ],
        "sisters": [
            ("AGE-artificial-general-engineer", "the system these components came from"),
            ("physbench", "the 12-domain verifiable benchmark"),
            ("verification-gated-agents", "the gate as the missing control in agent evaluation"),
            ("physics-loss-channel", "the loss channel isolated"),
            ("fewshot-law-acquisition", "transfer across laws"),
            ("field-consistency", "the cost of consistency on 2D fields"),
        ],
    },
    {
        "repo": "physbench",
        "title": "PhysBench",
        "subtitle": "A verifiable 12-domain benchmark for physics ML: targets generated separately from the "
                    "training signal, predictions scored against governing-equation residuals written from "
                    "scratch.",
        "byline": "Sehaj Randhir Singh &middot; independent, affiliated with NYU Tandon ECE &middot; 2026",
        "code": "https://github.com/sehajr-singhs/physbench",
        "paper": "manuscript.pdf",
        "si": "supplementary_information.pdf",
        "ieee": None,
        "kpis": [
            ("12", "Physics domains", "closed-form, conservation, ODE, fourth-order bending, PDE, elliptic field"),
            ("75", "Baseline runs", "5 domains × 3 architectures × 5 seeds, all committed under physx/models/matrix"),
            ("2 orders", "Difficulty span", "held-out error spans ~2 orders of magnitude across domains"),
            ("0.037 / 0.110", "DeepONet vs generalist", "10 dedicated operators vs 1 law-conditioned generalist"),
        ],
        "abstract": (
            "Most physics-ML benchmarks validate models against the same code that generated the data, so "
            "agreement can just mean shared bugs. PhysBench enforces two independence conditions: every "
            "target comes from a closed-form or high-resolution numerical solution implemented separately "
            "from the training signal, and every prediction is scored against an independent "
            "governing-equation residual — finite differences, Euler/RK4, energy balance — not against the "
            "generating code. Twelve domains, a committed 75-run baseline matrix, an operator-network "
            "comparison on the ten trajectory domains, and per-domain difficulty analysis showing that the "
            "best architecture differs by domain.",
        ),
        "sections": [
            ("The independent-verifier principle", (
                "<span class='lead'>Two independence conditions, both structural.</span> Targets are "
                "generated separately from the training signal, and predictions are scored against the "
                "governing equation rather than the generating code. That is what makes a benchmark claim "
                "survive contact with a reviewer: 'right' is defined by something the benchmark author did "
                "not also write.",
            )),
            ("What the matrix shows", (
                "Held-out error spans two orders of magnitude across domains, and the best architecture "
                "differs by domain — there is no universal winner, which is the point. The comparison is "
                "per-domain and per-capacity: the generalist wins outright on spring and LC while ten "
                "dedicated DeepONets win on per-law fidelity elsewhere.",
            )),
        ],
        "reproduce": (
            "git clone https://github.com/sehajr-singhs/physbench\n"
            "cd physbench\n"
            "python -m unittest tests.test_physx        # 49 physics tests\n"
            "python figs/make_figures.py                # figures from committed data\n"
            "python src/physx/run_matrix.py             # re-run the 75-run matrix (< 1 h, CPU)\n"
            "python src/physx/baselines.py --per-law-only   # DeepONet baselines"
        ),
        "figs": ["figs/fig2_matrix.png"],
        "fig_captions": ["The 75-run baseline matrix: mean training rel-MAE, five seeds."],
        "sisters": [
            ("AGE-artificial-general-engineer", "the system these components came from"),
            ("physics-transformers", "the PhysFormer architecture measured on this benchmark"),
            ("verification-gated-agents", "the gate as the missing control in agent evaluation"),
            ("physics-loss-channel", "the loss channel isolated"),
            ("fewshot-law-acquisition", "transfer across laws"),
            ("field-consistency", "the cost of consistency on 2D fields"),
        ],
    },
    {
        "repo": "verification-gated-agents",
        "title": "Verification-Gated Agents",
        "subtitle": "The missing control in agent evaluation is a gate, not a better model. A gate that "
                    "runs the ground truth catches every injected fault; the same agent without it reports "
                    "false success 29% of the time.",
        "byline": "Sehaj Randhir Singh &middot; independent, affiliated with NYU Tandon ECE &middot; 2026",
        "code": "https://github.com/sehajr-singhs/verification-gated-agents",
        "paper": "manuscript.pdf",
        "si": "supplementary_information.pdf",
        "ieee": None,
        "kpis": [
            ("0%", "False success with the gate", "vs 29% without it (2 of 7 missions), same agent"),
            ("100%", "Injected faults caught", "both faults detected by the gate; zero by the un-gated agent"),
            ("n = 7", "Mission set", "7 engineering missions, 2 with injected faults, all in bench/"),
            ("p = 0.23", "Fisher exact (honest)", "the contrast is directional but not significant at n = 7 — stated, not spun"),
        ],
        "abstract": (
            "Autonomous agents are usually evaluated by what they report — and agents that do not verify "
            "their work report success that never happened. This paper isolates the mechanism: the same "
            "agent, identical plans and skills, run with and without a verification gate that executes the "
            "ground truth. With the gate, 0 of 7 missions end in false success and 100% of injected faults "
            "are caught; without it, the same agent reports false success on 29% of missions and misses "
            "every fault. The honest statistics are included: at n = 7 the contrast is directional "
            "(Fisher exact p = 0.23), and the power analysis says what sample would settle it (~28 "
            "missions per condition for 80% power). The gate benchmark is committed and re-runnable.",
        ),
        "sections": [
            ("Why a gate and not a better model", (
                "<span class='lead'>Capability is not honesty.</span> A stronger model writes better plans "
                "and still asserts success on work it never ran. The gate is a structural control: success "
                "is defined by executing the ground truth, not by the agent's self-report. The benchmark "
                "reuses the AGE agent unchanged — the only difference between the two conditions is whether "
                "the verify step is present.",
            )),
            ("Honest limits", (
                "n = 7 missions is a demonstration, not a benchmark, and the paper says so: Fisher exact "
                "p = 0.23, Clopper-Pearson 95% upper bound 34.8% on 0/7, and a power analysis for the "
                "sample that would settle the contrast. The point is the mechanism — the gate is the "
                "missing control in agent evaluation — not a claimed win at a sample size that cannot "
                "support one.",
            )),
        ],
        "reproduce": (
            "git clone https://github.com/sehajr-singhs/verification-gated-agents\n"
            "cd verification-gated-agents\n"
            "node --test                      # 16 node tests incl. the gate benchmark\n"
            "node bench/gate_bench.js         # re-run the 7-mission gate benchmark\n"
            "python -m unittest tests.test_physx    # 49 physics tests (the solver the gate uses)"
        ),
        "figs": ["figs/fig2_gatebench.png"],
        "fig_captions": ["Gate vs no-gate on the 7-mission benchmark: 0% vs 29% false success."],
        "sisters": [
            ("AGE-artificial-general-engineer", "the agent this benchmark gates"),
            ("physics-transformers", "the PhysFormer architecture"),
            ("physbench", "the 12-domain verifiable benchmark"),
            ("physics-loss-channel", "the loss channel isolated"),
            ("fewshot-law-acquisition", "transfer across laws"),
            ("field-consistency", "the cost of consistency on 2D fields"),
        ],
    },
    {
        "repo": "physics-loss-channel",
        "title": "The Physics Loss Channel",
        "subtitle": "Physics supervision in the loss has two separable effects: it enforces consistency "
                    "dramatically — and it does not buy accuracy. The channel matters.",
        "byline": "Sehaj Randhir Singh &middot; independent, affiliated with NYU Tandon ECE &middot; 2026",
        "code": "https://github.com/sehajr-singhs/physics-loss-channel",
        "paper": "manuscript.pdf",
        "si": "supplementary_information.pdf",
        "ieee": None,
        "kpis": [
            ("19×", "Governing-equation residual cut", "p < 1e-7, effect size δ = −0.92 — the loss channel works"),
            ("p = 0.65", "Pooled accuracy effect", "null — consistency does not transfer to held-out answers"),
            ("hurt", "Projectile answers", "physics-in-the-loss actively degrades one domain; reported, not hidden"),
            ("75", "Matrix runs", "3 architectures × 5 domains × 5 seeds, all committed"),
        ],
        "abstract": (
            "Adding a physics residual to the loss is the standard way to make a network physical — and the "
            "standard way to stop measuring what it does. This study isolates the loss channel on a "
            "controlled matrix: identical architectures, data, and training, with the physics term on or "
            "off. The physics term cuts the governing-equation residual 19× (p < 1e-7) — it genuinely "
            "enforces consistency — while pooled held-out accuracy stays flat (p = 0.65) and one domain "
            "(projectile) gets worse. Consistency is not accuracy; the loss channel is real, separable, and "
            "insufficient. The full 75-run matrix is committed and re-runnable.",
        ),
        "sections": [
            ("Two effects, separable", (
                "<span class='lead'>The loss channel buys consistency.</span> The governing-equation "
                "violation of predicted trajectories collapses — 19× overall, significant at p < 1e-7. "
                "<span class='lead'>It does not buy accuracy.</span> Pooled held-out error is unchanged "
                "(p = 0.65) and the direction varies by domain: beam improves modestly, projectile worsens. "
                "Any paper claiming a PINN-style loss 'helps' without separating these two effects is "
                "measuring the wrong thing.",
            )),
            ("What the input channel is for", (
                "The companion physics-transformers paper shows the channel that does move accuracy: physics "
                "as input tokens (law-conditioned attention), causally active at inference. Together the two "
                "papers decompose 'physics-informed' into its channels and show each one does a different "
                "job.",
            )),
        ],
        "reproduce": (
            "git clone https://github.com/sehajr-singhs/physics-loss-channel\n"
            "cd physics-loss-channel\n"
            "python -m unittest tests.test_physx        # 49 physics tests\n"
            "python figs/make_figures.py                # figures from committed significance.json\n"
            "python figs/lca_significance.py            # re-run the pooled statistics from results/"
        ),
        "figs": ["figs/fig2_residual.png"],
        "fig_captions": ["Residual reduction (loss channel on vs off) across the matrix."],
        "sisters": [
            ("AGE-artificial-general-engineer", "the system these components came from"),
            ("physics-transformers", "the input channel — where accuracy actually comes from"),
            ("physbench", "the 12-domain verifiable benchmark"),
            ("verification-gated-agents", "the gate as the missing control"),
            ("fewshot-law-acquisition", "transfer across laws"),
            ("field-consistency", "the cost of consistency on 2D fields"),
        ],
    },
    {
        "repo": "fewshot-law-acquisition",
        "title": "Few-Shot Law Acquisition",
        "subtitle": "A transformer that has seen other laws learns a new one with a quarter of the data — "
                    "and the decomposition of why is measured, not assumed: the vocabulary carries it; the "
                    "residual constrains it.",
        "byline": "Sehaj Randhir Singh &middot; independent, affiliated with NYU Tandon ECE &middot; 2026",
        "code": "https://github.com/sehajr-singhs/fewshot-law-acquisition",
        "paper": "manuscript.pdf",
        "si": "supplementary_information.pdf",
        "ieee": None,
        "kpis": [
            ("2.9×", "Lower error than a specialist", "at 25% of the data, adapting to a held-out law"),
            ("10×", "Vocabulary dominance", "removing the vocabulary token stream is catastrophic; it is the main carrier"),
            ("7×", "Residual constraint", "the physics residual constrains trajectory specialization at tiny budgets"),
            ("24", "Samples", "the few-shot regime — and the honest limits of what one held-out law can prove"),
        ],
        "abstract": (
            "Few-shot transfer in physics ML usually means: same equation, more parameters. This paper "
            "transfers across laws: a generalist that has seen five laws adapts to a held-out sixth with a "
            "quarter of the data at 2.9× lower error than a from-scratch specialist. Then it decomposes why, "
            "with ablations that overturned the intended narrative: the quantity vocabulary is the dominant "
            "carrier (removing it is 10× worse), and the physics residual — helpful in general — constrains "
            "trajectory specialization at tiny budgets (removing it improves trajectory error 7× while "
            "answers stay flat). The decomposition is measured three ways and reported as measured.",
        ),
        "sections": [
            ("What transfers, measured", (
                "<span class='lead'>The vocabulary is the memory.</span> The token stream of quantities and "
                "operators carries the cross-law structure; ablation is catastrophic. <span class='lead'>The "
                "residual is a constraint.</span> At 24 samples the physics term pins trajectories to "
                "equation-consistent shapes before the data can specialize them — removing it frees the "
                "curve 7× while answers are unaffected. Both findings are per-seed, committed, and "
                "re-runnable.",
            )),
            ("Honest limits", (
                "One held-out law, 24 samples, CPU-minutes of training. The decomposition is genuine and "
                "the direction is surprising, but the transfer story is one domain pair; the paper says so "
                "and lays out the multi-pair test that would generalize it.",
            )),
        ],
        "reproduce": (
            "git clone https://github.com/sehajr-singhs/fewshot-law-acquisition\n"
            "cd fewshot-law-acquisition\n"
            "python -m unittest tests.test_physx        # 49 physics tests\n"
            "python figs/make_figures.py                # figures from committed fewshot_data.json\n"
            "python src/physx/train_fewshot.py          # re-run the few-shot protocol\n"
            "python src/physx/run_transfer_ablations.py # re-run the ablations"
        ),
        "figs": ["figs/fig2_transfer.png"],
        "fig_captions": ["Few-shot transfer: generalist vs specialist vs ablations, per budget."],
        "sisters": [
            ("AGE-artificial-general-engineer", "the system these components came from"),
            ("physics-transformers", "the architecture the transfer happens in"),
            ("physbench", "the 12-domain verifiable benchmark"),
            ("verification-gated-agents", "the gate as the missing control"),
            ("physics-loss-channel", "the loss channel isolated"),
            ("field-consistency", "the cost of consistency on 2D fields"),
        ],
    },
    {
        "repo": "field-consistency",
        "title": "Field Consistency — the Cost of Consistency",
        "subtitle": "Enforcing PDE residuals on 2D fields makes predictions more consistent and less "
                    "accurate. The honest number on the validation distribution is five times the "
                    "showcase — and the paper reports both.",
        "byline": "Sehaj Randhir Singh &middot; independent, affiliated with NYU Tandon ECE &middot; 2026",
        "code": "https://github.com/sehajr-singhs/field-consistency",
        "paper": "manuscript.pdf",
        "si": "supplementary_information.pdf",
        "ieee": None,
        "kpis": [
            ("5.9%", "Canonical heat-plate error", "peak field error on the showcase instance — the easiest member of the distribution"),
            ("~29%", "Honest expected error", "mean held-out peak error across the validation distribution, reported openly"),
            ("6–8×", "Residual drop", "governing-equation violation falls while fidelity degrades — consistency ≠ accuracy"),
            ("19 min", "Per-instance DeepXDE", "a specialist wins on its own problem; the generalist is a consistent solver of all"),
        ],
        "abstract": (
            "The tensor pipeline extends to 2D fields: the same PhysFormer with a field-shaped head learns "
            "the full u(x, y) surface of the heat plate. The showcase number (5.9% peak field error) is "
            "real — and it is the easiest member of the validation distribution, whose honest mean is ~29%. "
            "The paper reports the distribution, not just the showcase. And the loss-channel tradeoff "
            "sharpens at the field level: enforcing the Poisson residual cuts it 6–8× while field fidelity "
            "degrades. Against a per-instance PINN (DeepXDE, ~19 min per problem), the specialist wins on "
            "its own instance at 0.03–0.06% error but with a higher governing-equation residual; the "
            "generalist answers any instance in one forward pass. Both statements are true; the paper's "
            "claim is the tradeoff.",
        ),
        "sections": [
            ("The distribution, not the showcase", (
                "<span class='lead'>5.9% is the easiest case.</span> The canonical plate is the easiest "
                "member of its own validation distribution; the honest expected peak error is ~29%. Papers "
                "that report only the showcase are reporting selection. This one commits the distribution "
                "and the code that draws from it.",
            )),
            ("Consistency is not accuracy", (
                "At the field level the pattern from the trajectory domains repeats and sharpens: the "
                "physics residual drops 6–8× while held-out fidelity degrades. Enforcing the equation makes "
                "predictions consistent, not correct — the two must be measured separately, and here both "
                "are.",
            )),
        ],
        "reproduce": (
            "git clone https://github.com/sehajr-singhs/field-consistency\n"
            "cd field-consistency\n"
            "python -m unittest tests.test_physx        # 49 physics tests\n"
            "python figs/make_figures.py                # figures from committed physvdata_data.json\n"
            "python src/physx/run_physvdata.py          # re-run the field protocol"
        ),
        "figs": ["figs/fig10_heat2d.png", "figs/fig11_deepxde.png"],
        "fig_captions": [
            "Heat-plate field prediction: canonical vs. honest distribution error.",
            "Generalist vs per-instance DeepXDE: fidelity vs. consistency tradeoff.",
        ],
        "sisters": [
            ("AGE-artificial-general-engineer", "the system these components came from"),
            ("physics-transformers", "the architecture the fields are predicted with"),
            ("physbench", "the 12-domain verifiable benchmark"),
            ("verification-gated-agents", "the gate as the missing control"),
            ("physics-loss-channel", "the loss channel isolated"),
            ("fewshot-law-acquisition", "transfer across laws"),
        ],
    },
]

CSS = """
  :root{
    --bg:#ffffff; --ink:#1a1a1a; --muted:#6a6a6a; --hair:#e6e6e6;
    --panel:#f5f5f5; --panel-edge:#e4e4e4; --link:#1f6fb2;
    --good:#2f8558; --warn:#b23c1e; --grid:#ececec;
    --serif:Georgia,'Times New Roman',serif;
    --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
    --mono:'SFMono-Regular',Consolas,'Liberation Mono','Courier New',monospace;
  }
  html{background:#ffffff;}
  *{box-sizing:border-box;}
  body{max-width:860px;margin:0 auto;padding:44px 24px 96px;background:#ffffff;color:var(--ink);
    font-family:var(--sans);font-size:17px;line-height:1.7;
    -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;}
  a{color:var(--link);text-decoration:none;} a:hover{text-decoration:underline;}
  h1,h2,.envlabel{font-family:var(--serif);text-wrap:balance;}
  h1{font-size:35px;line-height:1.18;font-weight:700;text-align:center;margin:0 0 16px;letter-spacing:-.01em;}
  .subtitle{text-align:center;color:var(--muted);font-size:19px;line-height:1.55;margin:0 auto 14px;max-width:660px;}
  .byline{text-align:center;color:var(--muted);font-size:15.5px;margin:0 0 14px;}
  .toplinks{text-align:center;font-size:16px;margin:0 0 8px;} .toplinks a{margin:0 7px;white-space:nowrap;}
  h2{font-size:26px;font-weight:700;text-align:center;margin:60px 0 6px;padding-top:34px;border-top:1px solid var(--hair);}
  p{margin:16px 0;} .lead{font-weight:700;}
  .note{color:var(--muted);font-size:15px;} .center{text-align:center;}
  .abstract{background:var(--panel);border:1px solid var(--panel-edge);padding:22px 26px;border-radius:8px;}
  .abstract p{margin:0;text-align:justify;}
  .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:26px 0 8px;}
  .kpi{background:var(--panel);border:1px solid var(--panel-edge);border-radius:10px;padding:16px 16px 14px;}
  .kpi .big{font-family:var(--serif);font-size:30px;font-weight:700;line-height:1.05;font-variant-numeric:tabular-nums;letter-spacing:-.01em;}
  .kpi .lab{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-top:9px;}
  .kpi .sub{font-size:13.5px;color:var(--muted);margin-top:5px;line-height:1.4;}
  .kpi .up{color:var(--good);font-weight:700;}
  .kpi .down{color:var(--warn);font-weight:700;}
  @media (max-width:640px){.kpis{grid-template-columns:repeat(2,1fr);}}
  .figwrap{margin:22px 0 4px;text-align:center;}
  .figwrap img{max-width:100%;border:1px solid var(--panel-edge);border-radius:8px;}
  .figcap{color:var(--muted);font-size:14px;margin:6px auto 0;max-width:720px;}
  .tablescroll{overflow-x:auto;}
  table{border-collapse:collapse;margin:16px auto;font-size:14.5px;font-family:var(--serif);width:100%;}
  th,td{border:1px solid var(--hair);padding:7px 12px;text-align:left;vertical-align:top;}
  th{background:var(--panel);font-weight:700;}
  td.win{font-weight:700;color:var(--good);} td.num{font-variant-numeric:tabular-nums;}
  pre{background:var(--panel);border:1px solid var(--panel-edge);padding:16px 18px;overflow-x:auto;
    font-size:13.5px;font-family:var(--mono);line-height:1.55;border-radius:8px;}
  code{font-family:var(--mono);font-size:.92em;}
  .sisters{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:18px 0;}
  .sister{background:var(--panel);border:1px solid var(--panel-edge);border-radius:8px;padding:12px 14px;font-size:15px;}
  .sister b{font-family:var(--serif);}
  .foot{margin-top:56px;padding-top:22px;border-top:1px solid var(--hair);color:var(--muted);font-size:14px;text-align:center;}
  @media (prefers-reduced-motion:reduce){*{transition:none!important;}}
"""


def site_url(repo):
    return f"https://sehajr-singhs.github.io/{repo}/"


def top_links(s):
    links = [f"[<a href='{s['code']}'>Code</a>]",
             f"[<a href='{s['paper']}'>Paper</a>]"]
    if s.get("si"):
        links.append(f"[<a href='{s['si']}'>Supplementary</a>]")
    if s.get("ieee"):
        links.append(f"[<a href='{s['ieee']}'>IEEE format</a>]")
    return "\n  ".join(links)


def kpis(s):
    out = ['<div class="kpis">']
    for big, lab, sub in s["kpis"]:
        out.append(f'  <div class="kpi"><div class="big">{big}</div>'
                   f'<div class="lab">{lab}</div><div class="sub">{sub}</div></div>')
    out.append('</div>')
    return "\n".join(out)


def figs(s):
    out = []
    for i, (f, cap) in enumerate(zip(s.get("figs", []), s.get("fig_captions", []))):
        out.append(f'<div class="figwrap"><img src="{f}" alt="Figure {i+1}">'
                   f'<p class="figcap">{cap}</p></div>')
    return "\n".join(out)


def sisters(s):
    out = ['<div class="sisters">']
    for name, desc in s["sisters"]:
        out.append(f'  <div class="sister"><b><a href="{site_url(name)}">{name}</a></b>'
                   f'<br>{desc}</div>')
    out.append('</div>')
    return "\n".join(out)


def render(s):
    sections = "".join(
        f"<h2>{h}</h2><p>{body}</p>" for h, body in s["sections"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{s['title']}</title>
<meta name="description" content="{s['subtitle']}">
<style>{CSS}</style>
</head>
<body>

<h1>{s['title']}</h1>
<p class="subtitle">{s['subtitle']}</p>
<p class="byline">{s['byline']}</p>
<p class="toplinks">
  {top_links(s)}
</p>

{kpis(s)}

<h2>The result</h2>
<div class="abstract">
  <p>{s['abstract']}</p>
</div>

{sections}

{figs(s)}

<h2>Sister papers in this series</h2>
<p class="note center">Seven manuscripts, one codebase, one guarantee: every number traces to a
committed JSON and regenerates from a committed script.</p>
{sisters(s)}

<h2>Reproduce</h2>
<pre>{s['reproduce']}</pre>
<p class="note">Simulation-only, CPU-scale, deterministic seeds. No GPU required.</p>

<div class="foot">
  Sehaj Randhir Singh &middot; independent, affiliated with NYU Tandon ECE &middot; 2026<br>
  <a href="{site_url('AGE-artificial-general-engineer')}">AGE series home</a> &middot;
  every paper in this series links to every other
</div>

</body>
</html>
"""


def main():
    for s in SITES:
        if s["repo"] == "AGE-artificial-general-engineer":
            repo_dir = AGE
        else:
            repo_dir = os.path.join(REPOS, s["repo"])
        path = os.path.join(repo_dir, "index.html")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(render(s))
        print("wrote", path)


if __name__ == "__main__":
    main()
