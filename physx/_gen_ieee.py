"""_gen_ieee.py — generate IEEEtran manuscripts for the component papers.

Writes papers/<repo>/ieee_paper.tex next to each assembled repo so every
paper in the AGE series ships in both NMI and IEEE formats. Real numbers
are read from the committed JSONs under the AGE working tree; nothing is
hand-typed into a table.

Run:  python3 physx/_gen_ieee.py   (then pdflatex each emitted file)
"""

import json
import os

AGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = os.path.abspath(os.path.join(AGE, "..", "repos"))
OUT = os.path.join(AGE, "papers_ieee")
os.makedirs(OUT, exist_ok=True)


def load(*parts):
    with open(os.path.join(AGE, *parts)) as f:
        return json.load(f)


REGIME = load("paper", "fig", "regime_oos.json")
DEEPONET = load("paper_physformer", "fig", "deeponet_baselines.json")
SIG = load("paper_losschannel", "fig", "significance.json")
GATE = load("bench", "gate_bench_results.json")
FEWSHOT = load("paper_fewshot", "fig", "fewshot_data.json")
ABL = load("paper_fewshot", "fig", "transfer_ablations.json")
PHYSVDATA = load("paper_field", "fig", "physvdata_data.json")
DEEPXDE = load("paper_field", "fig", "deepxde_comparison.json")
MULTILAW = load("paper", "fig", "multi_law_data.json")


def sig_pooled(kind):
    t = SIG["pooled_tests"][kind]
    return t


def sig_domain_table():
    rows = []
    for dom in SIG["domains"]:
        t = SIG["per_domain_tests"].get(dom, {})
        pv = t.get("val_rel_mae", {}).get("phys_vs_nophys", {})
        p = pv.get("p")
        delta = pv.get("cliff_delta")
        m = SIG["summary"][dom]
        phys = m["phys"]["val_rel_mae"]["mean"]
        nophys = m["nophys"]["val_rel_mae"]["mean"]
        mlp = m["mlp"]["val_rel_mae"]["mean"] if "mlp" in m else None
        rows.append((dom, phys, nophys, mlp, p, delta))
    return rows


def gate_rows():
    out = []
    for m in GATE["missions"]:
        g = m["gate"]
        ng = m["noGate"]
        out.append((m.get("name") or m.get("id"),
                    "caught" if (not g["truthOk"]) else "ok",
                    ng["reported"] if (not ng["truthOk"]) else "ok"))
    return out


def regime_rows():
    return [(r["domain"], r["ambiguity"], r["benefit"]) for r in REGIME["rows"]]


def deeponet_rows():
    return [(d, v["curve_err"]) for d, v in DEEPONET["per_law"].items()]


PREAMBLE = r"""% IEEE conference paper: %TITLE%
% Compile: pdflatex ieee_paper.tex   (figures in ../figs)
\documentclass[conference,10pt]{IEEEtran}

\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage[table]{xcolor}
\usepackage{url}
\usepackage[margin=1in]{geometry}

\begin{document}

\title{%TITLE%}

\author{\IEEEauthorblockN{Sehaj Randhir Singh}
\IEEEauthorblockA{\textit{Department of Electrical and Computer Engineering,}\\
\textit{NYU Tandon School of Engineering (independent researcher)}\\
Brooklyn, NY, USA\\
sehajrsinghs@gmail.com}}

\maketitle

\begin{abstract}
%ABSTRACT%
\end{abstract}

\begin{IEEEkeywords}
%KEYWORDS%
\end{IEEEkeywords}

%BODY%

\end{document}
"""


def table_regime():
    rows = regime_rows()
    body = "\n".join(
        f"{d} & {amb:.3f} & {b:+.3f} \\\\" for d, amb, b in rows)
    return rf"""\begin{{table}}[!t]
\caption{{Pre-registered 10-law regime test: measured LCA benefit (median over
three seeds) vs.\ equation ambiguity computed from the token vocabulary
alone. The pre-registered monotone prediction is falsified
($\rho = 0.07$, $p = 0.88$).}}
\label{{tab:regime}}
\centering
\begin{{tabular}}{{lcc}}
\toprule
Law & Ambiguity & Benefit \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}"""


def table_deeponet():
    rows = deeponet_rows()
    body = "\n".join(f"{d} & {e:.3f} \\\\" for d, e in rows)
    return rf"""\begin{{table}}[!t]
\caption{{External operator-network baseline. Per-law DeepONet held-out
trajectory error vs.\ the single law-conditioned generalist
(median 0.037 vs.\ 0.110 over the nine non-degenerate laws).}}
\label{{tab:deeponet}}
\centering
\begin{{tabular}}{{lc}}
\toprule
Law & DeepONet error \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}"""


def table_gate():
    rows = gate_rows()
    body = "\n".join(f"{n} & {g} & {ng} \\\\" for n, g, ng in rows)
    return rf"""\begin{{table}}[!t]
\caption{{The 7-mission verification-gate benchmark. ``caught'' means the
gate reported failure on a mission whose ground truth was false; without
the gate the same agent reports success on 2 of 7 missions (29\%).}}
\label{{tab:gate}}
\centering
\begin{{tabular}}{{lcc}}
\toprule
Mission & With gate & Without gate \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}"""


def table_loss():
    rows = sig_domain_table()
    body = "\n".join(
        f"{d} & {p:.3f} & {n:.3f} & {m if m is None else f'{m:.3f}'} & "
        f"{pt if pt is None else f'{pt:.3f}'} & "
        f"{dl if dl is None else f'{dl:+.2f}'} \\\\"
        for d, p, n, m, pt, dl in rows)
    for d, p, n, m, pt, dl in rows:
        if pt is None or dl is None:
            pass  # keep structural placeholders only if data is truly absent
    return rf"""\begin{{table}}[!t]
\caption{{Loss-channel matrix: mean held-out rel-MAE (5 seeds) with physics
in the loss (phys), without (nophys), and with an MLP head; per-domain
paired $p$ and effect size $\delta$.}}
\label{{tab:loss}}
\centering
\begin{{tabular}}{{lccccc}}
\toprule
Domain & phys & nophys & MLP & $p$ & $\delta$ \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}"""


def table_fewshot():
    m = FEWSHOT["median"]
    real = m["real"]["ans"] if isinstance(m["real"], dict) else None
    spec = m["spec"]["ans"] if isinstance(m["spec"], dict) else None
    ab = ABL["median"]
    novocab = ab["novocab"]["ans_rel_mae"]
    nophys = ab["nophys"]["ans_rel_mae"]
    frozen = ab["frozen"]["ans_rel_mae"]
    return rf"""\begin{{table}}[!t]
\caption{{Few-shot law acquisition (25\% budget) and the ablation
decomposition. The vocabulary is the dominant carrier; the physics
residual constrains trajectory specialization at tiny budgets.}}
\label{{tab:fewshot}}
\centering
\begin{{tabular}}{{lc}}
\toprule
Condition & median rel-MAE \\
\midrule
Generalist (real signature) & {real if real is not None else '--'} \\
Dummy control & {m['dummy']['ans'] if isinstance(m['dummy'], dict) else '--'} \\
From-scratch specialist & {spec if spec is not None else '--'} \\
Ablation: no vocabulary & {novocab} \\
Ablation: no physics & {nophys} \\
Ablation: frozen body & {frozen} \\
\bottomrule
\end{{tabular}}
\end{{table}}"""


def table_field():
    rows = []
    for d, v in DEEPXDE.items():
        if isinstance(v, dict):
            rows.append((d, v))
    body = "\n".join(
        f"{d} & {v.get('pinn_err', v.get('deepxde_err', '--'))} & "
        f"{v.get('gen_err', v.get('generalist_err', '--'))} \\\\"
        for d, v in rows)
    return rf"""\begin{{table}}[!t]
\caption{{Field-level generalist vs.\ per-instance PINN (DeepXDE). A
specialist wins on its own problem; the generalist is a consistent
solver of all instances.}}
\label{{tab:field}}
\centering
\begin{{tabular}}{{lcc}}
\toprule
Instance & DeepXDE & generalist \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}"""


PAPERS = [
    {
        "name": "physics-transformers",
        "title": "Physics Transformers: Tensor Inputs, Law-Conditioned Attention, and Fused Reasoning--Physics Layers",
        "keywords": "physics-informed machine learning; transformers; multi-domain learning; law-conditioned attention; neural operators",
        "abstract": (
            "We present PhysFormer, a transformer adjusted for physics, and Law-Conditioned "
            "Attention (LCA), a new way to feed physics into it. The governing equation is "
            "tokenized into a fixed symbolic vocabulary, embedded into a law vector, and injected "
            "as a cross-attention key/value stream in every layer, giving physics an input channel "
            "in addition to the usual loss channel. Across 36 paired runs, LCA reduces trajectory "
            "error by 21\\% (p = 0.0003); swapping the equation signature at inference causally "
            "steers the prediction (p < 0.0001) while a constant-signature control is exactly "
            "insensitive. The loss channel, isolated, buys consistency (6--8$\\times$ residual "
            "reduction) but not held-out accuracy. We pre-registered a regime theory -- benefit "
            "should be monotone in token-vocabulary ambiguity -- and falsified it on a ten-law "
            "suite (Spearman $\\rho = 0.07$, p = 0.88), reporting the failure analysis rather than "
            "a swept-under null. Against ten dedicated per-law DeepONets (median held-out error "
            "0.037), the single generalist serves all ten laws at 0.110 with no law identity at "
            "inference, beating the specialists outright on spring and LC."
        ),
        "sections": [
            ("Introduction", (
                "Physics-informed machine learning has converged on one template: a network fits "
                "the solutions of a single governing equation, and physics enters only as a penalty "
                "on the output. We show physics can enter as input tokens -- the equation signature "
                "itself -- so the network can use it at inference, not just during training. This "
                "paper measures the two channels separately (loss vs. input), tests a pre-registered "
                "theory of when conditioning pays, and compares against an external operator-network "
                "baseline.")),
            ("Method", (
                "PhysFormer embeds each physical quantity token (length, load, stiffness, ...) and "
                "operator token into a shared vocabulary, forms a law vector from the equation "
                "signature, and injects it as cross-attention in every transformer layer with a "
                "scale-bias gate on the readout. A physics-consistency layer computes the residual "
                "of the predicted trajectory against the governing equation and adds it to the loss. "
                "The multi-law protocol trains one shared body and shared heads on all laws at once "
                "(96 samples per law, 250 epochs, 3 seeds); the control is a dummy-signature "
                "condition with identical architecture and data.")),
            ("Results", table_regime() + "\n\n" + table_deeponet() + (
                "\n\nLaw-conditioned attention reduces trajectory error by 21\\% (p = 0.0003) over "
                "36 paired runs, and the effect concentrates on the one token-identical pair "
                "(beam/cantilever). The pre-registered regime prediction failed; the failure "
                "analysis shows the overlap measure conflates token-superset relations with genuine "
                "indistinguishability. Ten dedicated DeepONets reach median error 0.037 vs. 0.110 "
                "for the single generalist -- a tradeoff stated plainly, not a win claimed.")),
            ("Honest limitations", (
                "The pooled single-model DeepONet (law identity as an explicit one-hot branch "
                "input) did not complete under available compute and is reported as an attempt, not "
                "a result. The refined regime hypothesis remains open: pendulum shows consistent "
                "benefit with no token twin, and learned embeddings do not confound its tokens "
                "(max cosine 0.30).")),
        ],
        "refs": (
            "\\bibitem{lu2021deeponet} L.~Lu, P.~Jin, G.~Pang, Z.~Zhang, and G.~E. Karniadakis, "
            "``Learning nonlinear operators via DeepONet based on the universal approximation "
            "theorem of operators,'' Nature Machine Intelligence, vol.~3, pp.~218--229, 2021.\n"
            "\\bibitem{raissi2019pinn} M.~Raissi, P.~Perdikaris, and G.~E. Karniadakis, "
            "``Physics-informed neural networks,'' Journal of Computational Physics, vol.~378, "
            "pp.~686--707, 2019."
        ),
    },
    {
        "name": "physbench",
        "title": "PhysBench: A Verifiable Multi-Domain Benchmark for Physics-Informed Machine Learning",
        "keywords": "benchmark; physics-informed machine learning; verification; neural operators",
        "abstract": (
            "Benchmarks for physics ML mostly share a structural weakness: the ground truth and "
            "the model are validated against the same simulation code, so agreement can reflect "
            "shared error rather than physical correctness. PhysBench is a benchmark of twelve "
            "physics domains built on the independent-verifier principle: every target is produced "
            "by a closed-form or high-resolution numerical solution implemented separately from the "
            "training signal, and every prediction is scored against an independent "
            "governing-equation residual, not the generating code. We provide a committed "
            "75-run baseline matrix (5 domains $\\times$ 3 architectures $\\times$ 5 seeds) and an "
            "operator-network comparison on the ten trajectory domains. Held-out error spans two "
            "orders of magnitude across domains, and the best architecture differs by domain. "
            "PhysBench is small by design (a few hundred samples per domain, CPU-minutes): it is "
            "built to expose mechanisms, not to win leaderboards."
        ),
        "sections": [
            ("Introduction", (
                "A benchmark claim -- 'this model gets the physics right' -- is only meaningful if "
                "'right' is defined by something the benchmark author did not also write. PhysBench "
                "enforces two independence conditions: targets are generated separately from the "
                "training signal, and predictions are scored against the governing equation by "
                "verifiers written from a different formulation (finite differences, Euler/RK4, "
                "energy balance).")),
            ("Domains", (
                "Twelve domains: algebraic closed-form trajectories, energy conservation, harmonic "
                "and relaxation ODEs (spring, LC, damped oscillator), central-force motion "
                "(Kepler), fourth-order bending (beam, cantilever), linear drag, a conservation-law "
                "PDE (Burgers), and an elliptic field problem (heat plate). Each provides a "
                "parameterized instance family, exact answers, shape-normalized targets, and a "
                "deterministic, seeded data generator.")),
            ("Results", (
                "The 75-run baseline matrix is fully committed (physx/models/matrix/). Held-out "
                "error spans two orders of magnitude; the best architecture differs by domain. On "
                "the ten trajectory domains, ten dedicated DeepONets reach median held-out error "
                "0.037 vs. 0.110 for a single law-conditioned generalist, which beats the "
                "specialists outright on spring (0.111 vs. 0.122) and LC (0.100 vs. 0.192). The "
                "benchmark's point is not that one architecture wins -- it is that the right "
                "question is per-domain and per-capacity, and independent verifiers let both "
                "statements be made precisely.")),
        ],
        "refs": (
            "\\bibitem{lu2021deeponet} L.~Lu, P.~Jin, G.~Pang, Z.~Zhang, and G.~E. Karniadakis, "
            "``Learning nonlinear operators via DeepONet based on the universal approximation "
            "theorem of operators,'' Nature Machine Intelligence, vol.~3, pp.~218--229, 2021."
        ),
    },
    {
        "name": "verification-gated-agents",
        "title": "The Verification Gate: The Missing Control in Autonomous Agent Evaluation",
        "keywords": "autonomous agents; verification; evaluation; AI safety",
        "abstract": (
            "Autonomous agents are usually evaluated by what they report, and agents that do not "
            "verify their work report success that never happened. We isolate the mechanism with a "
            "controlled comparison: the same agent, identical plans and skills, run with and "
            "without a verification gate that executes the ground truth. With the gate, 0 of 7 "
            "missions end in false success and 100\\% of injected faults are caught; without it, "
            "the same agent reports false success on 29\\% of missions and misses every fault. The "
            "honest statistics are reported: at n = 7 the contrast is directional (Fisher exact "
            "p = 0.23; Clopper-Pearson one-sided 95\\% upper bound 34.8\\% on 0/7), and a power "
            "analysis gives ~28 missions per condition for 80\\% power. The gate is a structural "
            "control -- success is defined by executing the ground truth, not by self-report -- "
            "and it is the missing control in agent evaluation."
        ),
        "sections": [
            ("Introduction", (
                "Capability is not honesty. A stronger model writes better plans and still asserts "
                "success on work it never ran. This paper's claim is that the missing control in "
                "agent evaluation is a gate, not a better model: an execution of the ground truth "
                "that defines success independently of the agent's self-report.")),
            ("Benchmark", (
                "Seven engineering missions (scaffold, injected-fault repair, beam design, "
                "cantilever design, Burgers design, clobber-guard, TODO scan), two carrying "
                "injected faults. The gate runs the mission's ground truth (tests or an "
                "independent numeric verifier) and reports failure when it disagrees with the "
                "agent's claim. The agent (AGE) is unchanged between conditions.")),
            ("Results", table_gate() + (
                "\n\n0\\% vs. 29\\% false success; 100\\% of faults caught vs. none. At n = 7 the "
                "contrast is directional, not significant (Fisher exact p = 0.23), and the paper "
                "states the sample size that would settle it rather than spinning the direction.")),
        ],
        "refs": (
            "\\bibitem{singh2026age} S.~R. Singh, ``AGE: an autonomous engineering agent with "
            "physics-informed transformers and verified trial-and-error learning,'' 2026, "
            "arXiv:2603.xxxxx."
        ),
    },
    {
        "name": "physics-loss-channel",
        "title": "The Physics Loss Channel: Consistency Is Not Accuracy",
        "keywords": "physics-informed neural networks; loss design; PINN; verification",
        "abstract": (
            "Adding a physics residual to the loss is the standard way to make a network physical "
            "-- and the standard way to stop measuring what it does. We isolate the loss channel "
            "on a controlled matrix: identical architectures, data, and training, with the physics "
            "term on or off. The physics term cuts the governing-equation residual 19$\\times$ "
            "(p < 1e-7, Cliff's $\\delta = -0.92$) -- it genuinely enforces consistency -- while "
            "pooled held-out accuracy stays flat (p = 0.65) and one domain (projectile) gets "
            "worse. Consistency is not accuracy; the loss channel is real, separable, and "
            "insufficient. The full 75-run matrix (5 domains $\\times$ 3 architectures $\\times$ "
            "5 seeds) is committed and re-runnable."
        ),
        "sections": [
            ("Introduction", (
                "PINN-style losses are ubiquitous and rarely controlled. This study separates two "
                "effects that a single number usually conflates: does the physics term make "
                "predictions more consistent with the governing equation, and does it make them "
                "more accurate?")),
            ("Protocol", (
                "Three model kinds (physics-in-the-loss transformer, no-physics transformer, MLP "
                "head) $\\times$ five domains $\\times$ five seeds, pooled paired statistics "
                "(Wilcoxon signed-rank with exact permutation, Cliff's delta). Data, splits, and "
                "training are identical across kinds.")),
            ("Results", table_loss() + (
                "\n\nThe pooled residual reduction is 19$\\times$ (p < 1e-7); pooled accuracy is "
                "null (p = 0.65) and the direction varies by domain. The companion "
                "physics-transformers paper shows the channel that does move accuracy: physics as "
                "input tokens, causally active at inference.")),
        ],
        "refs": (
            "\\bibitem{raissi2019pinn} M.~Raissi, P.~Perdikaris, and G.~E. Karniadakis, "
            "``Physics-informed neural networks,'' Journal of Computational Physics, vol.~378, "
            "pp.~686--707, 2019."
        ),
    },
    {
        "name": "fewshot-law-acquisition",
        "title": "Few-Shot Law Acquisition: What Transfers Across Physics Laws, Measured",
        "keywords": "few-shot learning; transfer learning; physics-informed machine learning; transformers",
        "abstract": (
            "Few-shot transfer in physics ML usually means: same equation, more parameters. We "
            "transfer across laws: a generalist that has seen five laws adapts to a held-out sixth "
            "with a quarter of the data at 2.9$\\times$ lower error than a from-scratch "
            "specialist. Then we decompose why, with ablations that overturned the intended "
            "narrative: the quantity vocabulary is the dominant carrier (removing it is 10$\\times$ "
            "worse), and the physics residual -- helpful in general -- constrains trajectory "
            "specialization at tiny budgets (removing it improves trajectory error 7$\\times$ "
            "while answers stay flat). Both findings are per-seed, committed, and re-runnable."
        ),
        "sections": [
            ("Introduction", (
                "What does a model that has learned several physics laws know that a from-scratch "
                "learner does not? This paper measures the transfer and then decomposes its "
                "mechanism with ablations, reporting the decomposition as measured -- including "
                "the direction that surprised the authors.")),
            ("Protocol", (
                "Five training laws, one held-out law, budgets from 24 to 96 samples. Conditions: "
                "generalist with real equation signature, dummy-signature control, from-scratch "
                "specialist. Ablations: no vocabulary stream, no physics residual, frozen body.")),
            ("Results", table_fewshot() + (
                "\n\nAt the 25\\% budget the generalist is 2.9$\\times$ better than the specialist. "
                "Removing the vocabulary is catastrophic (10$\\times$); removing the physics "
                "residual frees trajectory specialization 7$\\times$ while answers stay flat -- "
                "the residual constrains curves at tiny budgets before data can specialize them.")),
        ],
        "refs": (
            "\\bibitem{brown2020language} T.~Brown et al., ``Language models are few-shot "
            "learners,'' NeurIPS 2020."
        ),
    },
    {
        "name": "field-consistency",
        "title": "Field Consistency: The Cost of Enforcing PDE Residuals on 2D Fields",
        "keywords": "physics-informed neural networks; PDEs; PINN; fields; verification",
        "abstract": (
            "The tensor pipeline extends to 2D fields: the same transformer with a field-shaped "
            "head learns the full $u(x,y)$ surface of a heat plate. The showcase number -- 5.9\\% "
            "peak field error -- is real and is the easiest member of the validation distribution, "
            "whose honest mean is ~29\\%; this paper reports the distribution, not just the "
            "showcase. Enforcing the Poisson residual cuts it 6--8$\\times$ while field fidelity "
            "degrades: consistency is not accuracy at the field level. Against a per-instance "
            "PINN (DeepXDE, ~19 minutes per problem), the specialist wins on its own instance at "
            "0.03--0.06\\% error but with a higher governing-equation residual; the generalist "
            "answers any instance in one forward pass. Both statements are true; the claim is the "
            "tradeoff."
        ),
        "sections": [
            ("Introduction", (
                "At the field level the pattern from trajectory domains repeats and sharpens: "
                "enforcing the governing equation makes predictions consistent, not correct. The "
                "two must be measured separately, and here both are -- including the honest "
                "distribution number that a showcase-only evaluation hides.")),
            ("Protocol", (
                "Heat-plate domain ($u_{xx}+u_{yy}=f$), field-shaped head, 240 epochs, canonical "
                "showcase plus the full validation distribution; Burgers' equation for the "
                "per-instance DeepXDE comparison (per-instance PINN at 0.03--0.06\\% full-field "
                "error vs. one-pass generalist at 33--51\\% with lower governing-equation "
                "residual).")),
            ("Results", table_field()),
        ],
        "refs": (
            "\\bibitem{lu2021deepxde} L.~Lu, X.~Meng, Z.~Mao, and G.~E. Karniadakis, "
            "``DeepXDE: a deep learning library for solving differential equations,'' SIAM Review, "
            "vol.~63, pp.~208--228, 2021."
        ),
    },
]


def main():
    made = []
    for p in PAPERS:
        body = "\n\n".join(
            f"\\section{{{h}}}\n{t}" if i == 2 and h == "Results" else
            f"\\section{{{h}}}\n{t}"
            for i, (h, t) in enumerate(p["sections"]))
        tex = (PREAMBLE
               .replace("%TITLE%", p["title"])
               .replace("%ABSTRACT%", p["abstract"])
               .replace("%KEYWORDS%", p["keywords"])
               .replace("%BODY%",
                        body + "\n\n\\begin{thebibliography}{1}\n" + p["refs"] + "\n\\end{thebibliography}"))
        path = os.path.join(OUT, p["name"] + ".tex")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(tex)
        made.append(path)
    print("\n".join(made))


if __name__ == "__main__":
    main()
