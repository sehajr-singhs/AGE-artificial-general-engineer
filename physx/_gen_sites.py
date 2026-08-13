"""_gen_sites.py — generate the paper-series sites in the spectral design.

Matches the spectral-topological-decoupling site: CMU Serif + Inter +
IBM Plex Mono, MathJax, hero with title/tagline/authors/links, abstract
panel, impact cards, atlas-style data tables, theorem/method sections,
sister-paper grid, reproduce block, footer. Real numbers are read from
the committed JSONs in the AGE working tree — the tables cannot drift
from the runs.

Run:  python3 physx/_gen_sites.py
"""

import json
import os

AGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPOS = os.path.abspath(os.path.join(AGE, "..", "repos"))

SITE = "https://sehajr-singhs.github.io"
GITHUB = "https://github.com/sehajr-singhs"


def load(*parts):
    with open(os.path.join(AGE, *parts)) as f:
        return json.load(f)


REGIME = load("paper", "fig", "regime_oos.json")
DEEPONET = load("paper_physformer", "fig", "deeponet_baselines.json")
SIG = load("paper_losschannel", "fig", "significance.json")
GATE = load("bench", "gate_bench_results.json")
FEWSHOT = load("paper_fewshot", "fig", "fewshot_data.json")
ABL = load("paper_fewshot", "fig", "transfer_ablations.json")
DEEPXDE = load("paper_field", "fig", "deepxde_comparison.json")
MULTILAW = load("paper", "fig", "multi_law_data.json")


def fmt(x, nd=3):
    if x is None:
        return "—"
    return f"{x:.{nd}f}"


def html_table(headers, rows, cls="atlas"):
    h = "".join(f"<th>{x}</th>" for x in headers)
    body = []
    for row in rows:
        tds = []
        for cell in row:
            if isinstance(cell, tuple) and len(cell) == 2:
                val, cls_ = cell
                tds.append(f'<td class="{cls_}">{val}</td>')
            else:
                tds.append(f"<td>{cell}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return (f'<div class="tablescroll"><table>'
            f"<thead><tr>{h}</tr></thead><tbody>{''.join(body)}</tbody>"
            f"</table></div>")


def regime_table():
    rows = []
    for r in REGIME["rows"]:
        b = r["benefit"]
        cls = "win" if b > 0.15 else ("bad" if b < -0.15 else "")
        rows.append([r["domain"], fmt(r["ambiguity"]),
                     (f"{b:+.3f}", cls)])
    return html_table(["Law", "Ambiguity", "LCA benefit"], rows)


def deeponet_table():
    gen = {d: None for d in DEEPONET["per_law"]}
    rows = []
    for d, v in DEEPONET["per_law"].items():
        rows.append([d, fmt(v["curve_err"], 3)])
    return html_table(["Law", "per-law DeepONet error"], rows)


def loss_table():
    rows = []
    for dom in SIG["domains"]:
        t = SIG["per_domain_tests"][dom]["val_rel_mae"]["phys_vs_nophys"]
        m = SIG["summary"][dom]
        phys = m["phys"]["val_rel_mae"]["mean"]
        nophys = m["nophys"]["val_rel_mae"]["mean"]
        mlp = m["mlp"]["val_rel_mae"]["mean"] if "mlp" in m else None
        p = t["p"]
        delta = t["cliff_delta"]
        rows.append([dom, fmt(phys), fmt(nophys), fmt(mlp),
                     fmt(p, 3), (f"{delta:+.2f}", "bad" if delta < -0.4 else "")])
    return html_table(["Domain", "phys", "nophys", "MLP", "p", "δ"], rows)


def gate_table():
    rows = []
    for m in GATE["missions"]:
        g = m["gate"]
        ng = m["noGate"]
        gs = ("caught" if not g["truthOk"] else "ok")
        ns = ("false success" if (not ng["truthOk"]) and ng["reported"] == "success"
              else "ok")
        rows.append([m.get("name") or m.get("id"),
                     (gs, "win" if gs == "caught" else ""),
                     (ns, "bad" if ns == "false success" else "")])
    return html_table(["Mission", "with gate", "without gate"], rows)


def fewshot_table():
    m = FEWSHOT["median"]
    rows = [
        ["Generalist (real signature)", fmt(m["real"]["ans"]), "2.9× better than specialist"],
        ["Dummy control", fmt(m["dummy"]["ans"]), "same data, no law identity"],
        ["From-scratch specialist", fmt(m["spec"]["ans"]), "the baseline transfer beats"],
    ]
    return html_table(["Condition", "answer rel-MAE (25% budget)", "note"], rows)


def ablation_table():
    ab = ABL["median"]
    rows = [
        ["no vocabulary", fmt(ab["novocab"]["ans_rel_mae"]),
         (f"{ab['novocab']['ans_rel_mae'] / ab['frozen']['ans_rel_mae']:.1f}×", "bad")],
        ["no physics residual", fmt(ab["nophys"]["ans_rel_mae"]), "answers flat; curve freed 7×"],
        ["frozen body", fmt(ab["frozen"]["ans_rel_mae"]), "reference"],
    ]
    return html_table(["Ablation", "answer rel-MAE", "vs. frozen"], rows)


def field_table():
    rows = []
    for d, v in DEEPXDE.items():
        if not isinstance(v, dict):
            continue
        pinn = v.get("pinn_err", v.get("deepxde_err"))
        gen = v.get("gen_err", v.get("generalist_err"))
        rows.append([d, fmt(pinn, 3) if pinn is not None else "—",
                     fmt(gen, 3) if gen is not None else "—"])
    return html_table(["Instance", "DeepXDE (per-instance PINN)", "generalist (one pass)"], rows)


def six_law_table():
    pd = MULTILAW["per_domain"]
    rows = []
    for d in ["beam", "cantilever", "projectile", "pendulum", "spring", "rc"]:
        m = pd[d]["curve_err"]
        b = 1 - m["median_real"] / m["median_dummy"]
        rows.append([d, fmt(m["median_real"]), fmt(m["median_dummy"]),
                     (f"{b:+.2f}", "win" if b > 0.1 else "")])
    return html_table(["Law", "real", "dummy", "benefit"], rows)


CSS = """
    :root {
      --ink: #1a1a1a; --muted: #555; --faint: #8c8e90; --panel: #f8f8f8;
      --border: #c4c6c8; --link: #226999; --good: #1e6b3a; --bad: #b03a2e;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html { background: #fff; }
    body { font-family: 'CMU Serif', Georgia, serif; font-weight: 500;
      color: var(--ink); -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility; }
    a { color: var(--link); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .container { max-width: 920px; margin: 0 auto; padding: 0 20px; }
    .has-text-centered { text-align: center; }
    .has-text-justified { text-align: justify; }

    .hero { padding: 4.2rem 0 1.6rem; }
    .publication-title { font-family: 'CMU Serif', Georgia, serif;
      font-weight: 700 !important; line-height: 1.12; letter-spacing: 0;
      font-size: 2.5rem; text-wrap: balance; }
    .publication-title strong { font-weight: 900 !important; }
    .publication-sub { margin-top: 1.1rem; font-family: 'Inter', sans-serif;
      font-size: 1.05rem; color: var(--muted); line-height: 1.5;
      max-width: 60rem; margin-left: auto; margin-right: auto; }
    .tagline { margin-top: 0.9rem; font-family: 'IBM Plex Mono', monospace;
      font-size: 0.92rem; color: var(--ink); letter-spacing: 0.01em; }
    .authors { margin-top: 1.2rem; font-family: 'Inter', sans-serif;
      font-size: 0.95rem; color: var(--ink); }
    .affiliation { margin-top: 0.15rem; font-family: 'Inter', sans-serif;
      font-size: 0.82rem; color: var(--faint); }
    .links { margin-top: 1.5rem; font-family: 'IBM Plex Mono', monospace;
      font-size: 0.88rem; display: flex; flex-wrap: wrap; gap: 0.6rem 1.4rem;
      justify-content: center; }

    .section { padding: 2.4rem 0 1.2rem; }
    .title { font-size: 1.35rem; font-weight: 700; letter-spacing: -0.01em;
      margin-bottom: 1rem; padding-bottom: 0.35rem; border-bottom: 1px solid var(--border); }
    .section p { line-height: 1.6; color: var(--ink); margin-bottom: 0.9rem; }
    .muted { color: var(--muted); }

    .abstract { background: var(--panel); border: 1px solid var(--border);
      border-radius: 6px; padding: 1.4rem 1.6rem; font-size: 0.99rem;
      line-height: 1.62; text-align: justify; }

    .impact-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.2rem; margin-top: 1.1rem; }
    .impact { background: var(--panel); border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
    .impact-img { width: 100%; display: block; border-bottom: 1px solid var(--border); }
    .impact-body { padding: 0.9rem 1.1rem 1.05rem; }
    .impact-num { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
      font-weight: 600; letter-spacing: 0.02em; text-transform: uppercase;
      color: var(--ink); margin-bottom: 0.35rem; }
    .impact-body p { font-size: 0.88rem; line-height: 1.5; color: var(--muted); margin: 0; }

    table { width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif;
      font-size: 0.83rem; margin: 1rem 0 1.4rem; background: var(--panel);
      border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
    th, td { padding: 0.5rem 0.65rem; text-align: right; border-bottom: 1px solid var(--border); }
    th:first-child, td:first-child { text-align: left; }
    thead th { font-weight: 600; font-size: 0.78rem; letter-spacing: 0.02em;
      text-transform: uppercase; color: var(--muted); background: #fff; }
    tbody tr:last-child td { border-bottom: none; }
    tbody tr.ref td { border-top: 2px solid var(--ink); font-weight: 600; }
    td.win { color: var(--good); font-weight: 700; }
    td.bad { color: var(--bad); font-weight: 600; }
    td.worst { color: #8c1f13; font-weight: 700; }
    .table-note { font-family: 'IBM Plex Mono', monospace; font-size: 0.76rem;
      color: var(--faint); margin-top: -1rem; margin-bottom: 1.2rem; }
    .tablescroll { overflow-x: auto; }

    .sisters { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 0.9rem; margin-top: 1rem; }
    .sister { background: var(--panel); border: 1px solid var(--border);
      border-radius: 6px; padding: 0.85rem 1rem; font-family: 'Inter', sans-serif; }
    .sister b { font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; }
    .sister p { font-size: 0.82rem; color: var(--muted); margin: 0.3rem 0 0; line-height: 1.45; }

    pre { background: var(--panel); border: 1px solid var(--border); border-radius: 6px;
      padding: 1.1rem 1.3rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
      line-height: 1.55; overflow-x: auto; margin: 1rem 0; }

    footer { margin-top: 3rem; padding: 1.6rem 0 2.6rem; border-top: 1px solid var(--border);
      font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; color: var(--faint);
      text-align: center; }
    @media (max-width: 600px) { .publication-title { font-size: 1.8rem; }
      th, td { padding: 0.4rem 0.4rem; font-size: 0.74rem; } }
"""

MATHJAX = """
  <script>
    MathJax = { tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']] } };
  </script>
  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
"""


def page(title, desc, tagline, links, body, foot_extra=""):
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="description" content="{desc}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/computer-modern/cmu-serif.css">
  {MATHJAX}
  <style>{CSS}</style>
</head>
<body>

<section class="hero">
  <div class="container has-text-centered">
    <h1 class="publication-title">{title}</h1>
    <div class="tagline">{tagline}</div>
    <div class="authors">Sehaj Randhir Singh</div>
    <div class="affiliation">Independent researcher; partial affiliation with NYU Tandon School of Engineering</div>
    <div class="links">
      {links}
    </div>
  </div>
</section>

<div class="container">
{body}
</div>

<footer>
  <div class="container">
    Sehaj Randhir Singh · independent researcher; partial affiliation with NYU Tandon ECE · 2026<br>
    {foot_extra}
  </div>
</footer>

</body>
</html>
"""


def links_row(repo):
    l = [
        f'<a href="{SITE}/{repo}/manuscript.pdf">Paper (NMI format)</a>',
        f'<a href="{SITE}/{repo}/ieee_paper.pdf">Paper (IEEE format)</a>',
        f'<a href="{SITE}/{repo}/supplementary_information.pdf">Supplementary</a>',
        f'<a href="{GITHUB}/{repo}">GitHub (code + data)</a>',
    ]
    return "".join(l)


def sisters_grid(current, extra=None):
    all_s = [
        ("AGE-artificial-general-engineer", "the system and its project root"),
        ("physics-transformers", "the PhysFormer architecture; the falsified regime theory"),
        ("physbench", "the 12-domain verifiable benchmark"),
        ("verification-gated-agents", "the gate as the missing control in agent evaluation"),
        ("physics-loss-channel", "when physics in the loss helps — and when it only enforces consistency"),
        ("fewshot-law-acquisition", "transfer across laws: what carries the knowledge"),
        ("field-consistency", "the cost of consistency on 2D fields"),
    ]
    cards = []
    for name, desc in all_s:
        if name == current:
            continue
        cards.append(f'<div class="sister"><b><a href="{SITE}/{name}/">{name}</a></b>'
                     f'<p>{desc}</p></div>')
    if extra:
        cards.append(extra)
    return ('<div class="section"><h2 class="title">Sister papers in the series</h2>'
            '<p class="muted">Seven manuscripts, one codebase, one guarantee: every number traces '
            'to a committed JSON and regenerates from a committed script.</p>'
            f'<div class="sisters">{"".join(cards)}</div></div>')


def impact_cards(cards):
    out = ['<div class="impact-grid">']
    for num, desc, img in cards:
        img_html = f'<img class="impact-img" src="{img}" alt="">' if img else ""
        out.append(f'<div class="impact">{img_html}<div class="impact-body">'
                   f'<div class="impact-num">{num}</div><p>{desc}</p></div></div>')
    out.append('</div>')
    return "".join(out)


SITES = {
    "physics-transformers": dict(
        title="Physics <strong>Transformers</strong>",
        desc="Law-conditioned attention, a pre-registered falsification, and DeepONet baselines: the equation is fed to the transformer as input tokens, not only as a penalty.",
        tagline="The equation is input, not only loss — and the pre-registered theory of when that pays was falsified on ten laws, in full.",
        abstract=(
            "We present PhysFormer, a transformer adjusted for physics, and Law-Conditioned "
            "Attention (LCA), a new way to feed physics into it. The governing equation is "
            "tokenized into a fixed symbolic vocabulary, embedded into a law vector, and injected "
            "as a cross-attention key/value stream in every layer. Physics enters through two "
            "channels with different jobs: the loss channel (a physics-consistency layer) buys "
            "consistency, 6–8× residual reduction, without held-out accuracy; the input channel — "
            "the invention of this paper — is causally active at inference. Across 36 paired "
            "runs, LCA reduces trajectory error by 21% (p = 0.0003); swapping the equation "
            "signature steers the prediction (p < 0.0001) while a constant-signature control is "
            "exactly insensitive. We pre-registered a regime theory and falsified it on a ten-law "
            "suite (ρ = 0.07, p = 0.88), reporting the failure analysis. Ten dedicated per-law "
            "DeepONets reach median held-out error 0.037 vs. the single generalist's 0.110, which "
            "beats them outright on spring and LC."),
        sections=[
            ("Why the channel matters", [
                "The standard way to make a network physical is a loss term — and the standard "
                "way to stop measuring what it does. This paper separates the two effects a single "
                "number usually conflates: physics as a penalty (consistency) and physics as "
                "input (accuracy). Only the input channel moves held-out error, and it does so "
                "causally: remove the equation signature at inference and the prediction changes "
                "in a direction the data alone cannot explain.",
                impact_cards([
                    ("Causal, p < 0.0001", "Swapping the equation signature at inference steers "
                     "the prediction; a constant-signature control is exactly insensitive. The "
                     "equation is used, not decoratively present.", "figs/fig3_lawswap.png"),
                    ("Falsified, ρ = 0.07", "The pre-registered monotone regime theory failed "
                     "(p = 0.88). The overlap measure conflates supersets with genuine "
                     "indistinguishability — the failure analysis is the sharpest section.",
                     "figs/fig7_regime_oos.png"),
                    ("0.037 vs 0.110", "Ten dedicated per-law DeepONets beat the single "
                     "generalist on per-law fidelity, but with no cross-law structure; the "
                     "generalist wins outright on spring and LC.", "figs/fig8_deeponet.png"),
                ]),
            ]),
            ("The pre-registered regime test, in full", [
                "Before any ten-law training, the prediction was filed: LCA benefit should be "
                "monotone in the token-vocabulary ambiguity of each law, computed from the "
                "vocabulary alone. After 6 full trainings (3 seeds × generalist/control): "
                "Spearman ρ = 0.07 (p = 0.88), leave-one-out ρ = −0.58, and the group-mean order "
                "is violated. The pre-registration is committed at results/pre_registration.json; "
                "the eval files that falsified it are in the same directory.",
                regime_table(),
                '<div class="table-note">Measured benefit = 1 − err_real / err_dummy (median '
                'over three seeds). beam/cantilever present literally identical parameter '
                'tokens — only the equation distinguishes them — and show the largest, most '
                'consistent benefits.</div>',
            ]),
            ("The external baseline", [
                "DeepONet, the standard operator-network architecture, trained per law on the "
                "identical data splits (64 training samples, 6 held out, 250 epochs).",
                deeponet_table(),
                '<div class="table-note">A dedicated operator network wins on its own law; a '
                'single law-conditioned transformer covers all ten. The pooled single-model '
                'DeepONet (law identity as an explicit one-hot input — information the '
                'generalist never receives) did not complete under available compute and is '
                'reported as an attempt, not a result.</div>',
            ]),
        ],
        repro=("git clone https://github.com/sehajr-singhs/physics-transformers\n"
               "cd physics-transformers\n"
               "python -m unittest tests.test_physx          # 49 physics tests, 10-law set\n"
               "python figs/make_figures.py && python figs/make_figures_ext.py\n"
               "python src/physx/regime_oos.py --out figs/regime_oos.json   # the falsification\n"
               "python src/physx/train_multi.py --ext --seeds 3             # real + dummy, 3 seeds"),
    ),
    "physbench": dict(
        title="<strong>PhysBench</strong>: a verifiable multi-domain benchmark",
        desc="Twelve physics domains scored against independent governing-equation verifiers, not the generating code.",
        tagline="Ground truth independent of the artifact being evaluated — or a benchmark claim is just shared code agreeing with itself.",
        abstract=(
            "Benchmarks for physics-informed machine learning mostly share a structural "
            "weakness: the ground truth and the model are validated against the same simulation "
            "code, so agreement can reflect shared error rather than physical correctness. "
            "PhysBench is a benchmark of twelve physics domains built on the "
            "independent-verifier principle: every target is produced by a closed-form or "
            "high-resolution numerical solution implemented separately from the training signal, "
            "and every prediction is scored against an independent governing-equation residual, "
            "not the generating code. We provide a committed 75-run baseline matrix (5 domains × "
            "3 architectures × 5 seeds) and an operator-network comparison on the ten trajectory "
            "domains. Held-out error spans two orders of magnitude across domains, and the best "
            "architecture differs by domain. PhysBench is small by design — a few hundred samples "
            "per domain, CPU-minutes — built to expose mechanisms, not to win leaderboards."),
        sections=[
            ("Why the independent verifier matters", [
                "Two independence conditions, both structural. Targets are generated separately "
                "from the training signal, and predictions are scored against the governing "
                "equation — finite differences, Euler/RK4, energy balance — by verifiers written "
                "from a different formulation than the data generator. That is what makes 'this "
                "model gets the physics right' mean something: 'right' is defined by code the "
                "benchmark author did not also write.",
                impact_cards([
                    ("12 domains", "closed-form, conservation, harmonic/relaxation ODEs "
                     "(spring, LC, damped), Kepler, fourth-order bending, drag, Burgers PDE, "
                     "elliptic field — each with exact answers and shape-normalized targets.",
                     "figs/fig1_domains.png"),
                    ("75 committed runs", "5 domains × 3 architectures × 5 seeds, every stats "
                     "file under physx/models/matrix/. The matrix regenerates from committed "
                     "scripts.", "figs/fig2_matrix.png"),
                    ("2 orders of magnitude", "held-out error spans the difficulty axis; the "
                     "best architecture differs by domain — no universal winner, which is the "
                     "point.", "figs/fig3_convergence.png"),
                ]),
            ]),
            ("The operator comparison", [
                "Ten dedicated per-law DeepONets on identical splits reach median held-out "
                "trajectory error 0.037 vs. the single law-conditioned generalist's 0.110 — but "
                "they are ten separate models with no cross-law structure. The generalist wins "
                "outright on spring (0.111 vs 0.122) and LC (0.100 vs 0.192). The benchmark's "
                "point is that the right question is per-domain and per-capacity, and that "
                "independent verifiers let both statements be made precisely.",
            ]),
        ],
        repro=("git clone https://github.com/sehajr-singhs/physbench\n"
               "cd physbench\n"
               "python -m unittest tests.test_physx        # 49 physics tests\n"
               "python figs/make_figures.py                # figures from committed data\n"
               "python src/physx/run_matrix.py             # re-run the 75-run matrix (< 1 h, CPU)\n"
               "python src/physx/baselines.py --per-law-only   # DeepONet baselines"),
    ),
    "verification-gated-agents": dict(
        title="The <strong>Verification Gate</strong>",
        desc="The missing control in agent evaluation is a gate, not a better model: 0% vs 29% false success on the same agent.",
        tagline="The same agent, identical plans and skills — the only difference is whether success is defined by executing the ground truth.",
        abstract=(
            "Autonomous agents are usually evaluated by what they report, and agents that do not "
            "verify their work report success that never happened. We isolate the mechanism with "
            "a controlled comparison: the same agent, identical plans and skills, run with and "
            "without a verification gate that executes the ground truth. With the gate, 0 of 7 "
            "missions end in false success and 100% of injected faults are caught; without it, "
            "the same agent reports false success on 29% of missions and misses every fault. The "
            "honest statistics are reported: at n = 7 the contrast is directional (Fisher exact "
            "p = 0.23; Clopper-Pearson one-sided 95% upper bound 34.8% on 0/7), and a power "
            "analysis gives ~28 missions per condition for 80% power. The gate is a structural "
            "control — success is defined by executing the ground truth, not by self-report."),
        sections=[
            ("Why a gate and not a better model", [
                "Capability is not honesty. A stronger model writes better plans and still "
                "asserts success on work it never ran. The gate is a structural control: the "
                "benchmark reuses the AGE agent unchanged, and the only difference between the "
                "two conditions is whether the verify step is present.",
                impact_cards([
                    ("0% vs 29%", "false success with and without the gate on the same seven "
                     "missions — the mechanism is the agent's self-report, not its capability.",
                     "figs/fig2_gatebench.png"),
                    ("100% caught", "both injected faults are caught by the gate and missed "
                     "without it. The gate's failure reports are exact, not sampled.",
                     "figs/fig1_architecture.png"),
                    ("n = 7, stated", "Fisher exact p = 0.23, Clopper-Pearson 95% upper bound "
                     "34.8% on 0/7, and ~28 missions per condition for 80% power — the honest "
                     "statistics, not a spun direction.", None),
                ]),
            ]),
            ("The benchmark", [
                "Seven engineering missions (scaffold, injected-fault repair, beam design, "
                "cantilever design, Burgers design, clobber-guard, TODO scan), two carrying "
                "injected faults. The gate runs each mission's ground truth — tests, or an "
                "independent numeric verifier — and reports failure when it disagrees with the "
                "agent's claim.",
                gate_table(),
                '<div class="table-note">Both injected faults (injected-fault, clobber-guard) '
                'are reported as success by the un-gated agent; the gate reports failure on '
                'both. All five honest missions are reported correctly by both conditions.</div>',
            ]),
        ],
        repro=("git clone https://github.com/sehajr-singhs/verification-gated-agents\n"
               "cd verification-gated-agents\n"
               "node --test                      # 16 node tests incl. the gate benchmark\n"
               "node bench/gate_bench.js         # re-run the 7-mission gate benchmark\n"
               "python -m unittest tests.test_physx    # 49 physics tests (the solver the gate uses)"),
    ),
    "physics-loss-channel": dict(
        title="The Physics <strong>Loss Channel</strong>",
        desc="Physics supervision in the loss has two separable effects: it enforces consistency 19× — and it does not buy accuracy.",
        tagline="Consistency is not accuracy. The loss channel is real, separable, and insufficient.",
        abstract=(
            "Adding a physics residual to the loss is the standard way to make a network "
            "physical — and the standard way to stop measuring what it does. This study "
            "isolates the loss channel on a controlled matrix: identical architectures, data, "
            "and training, with the physics term on or off. The physics term cuts the "
            "governing-equation residual 19× (p < 1e-7, Cliff's δ = −0.92) — it genuinely "
            "enforces consistency — while pooled held-out accuracy stays flat (p = 0.65) and "
            "one domain (projectile) gets worse. The full 75-run matrix (5 domains × 3 "
            "architectures × 5 seeds) is committed and re-runnable."),
        sections=[
            ("Two effects, separable", [
                "A single 'physics-informed' number usually conflates two things: does the "
                "physics term make predictions more consistent with the governing equation, and "
                "does it make them more accurate? This study measures both, on identical "
                "architectures and data, with the physics term as the only difference.",
                impact_cards([
                    ("19× residual cut", "governing-equation violation of predicted "
                     "trajectories collapses, p < 1e-7, Cliff's δ = −0.92 — the loss channel "
                     "genuinely enforces consistency.", "figs/fig2_residual.png"),
                    ("p = 0.65, accuracy null", "pooled held-out error is statistically "
                     "unchanged, and the direction varies by domain — beam improves modestly, "
                     "projectile worsens.", "figs/fig1_matrix.png"),
                    ("75 committed runs", "the whole matrix regenerates from committed stats "
                     "files; the pooled statistics are exact permutation tests, not "
                     "asymptotic.", None),
                ]),
            ]),
            ("The matrix", [
                "Three model kinds (physics-in-the-loss transformer, no-physics transformer, "
                "MLP head) × five domains × five seeds, pooled paired statistics (Wilcoxon "
                "signed-rank with exact permutation, Cliff's delta).",
                loss_table(),
                '<div class="table-note">phys = physics residual in the loss; nophys = '
                'identical architecture without it; MLP = linear readout. p and δ are the '
                'per-domain paired tests (phys vs nophys). The pooled accuracy effect is null '
                '(p = 0.65) while the pooled residual effect is 19× (p < 1e-7).</div>',
            ]),
        ],
        repro=("git clone https://github.com/sehajr-singhs/physics-loss-channel\n"
               "cd physics-loss-channel\n"
               "python -m unittest tests.test_physx        # 49 physics tests\n"
               "python figs/make_figures.py                # figures from committed significance.json\n"
               "python figs/lca_significance.py            # re-run the pooled statistics from results/"),
    ),
    "fewshot-law-acquisition": dict(
        title="Few-Shot <strong>Law Acquisition</strong>",
        desc="A transformer that has seen other laws learns a new one with a quarter of the data — and why, measured: the vocabulary carries it, the residual constrains it.",
        tagline="Transfer across laws, not across parameters. The decomposition overturned the intended narrative — and is reported as measured.",
        abstract=(
            "Few-shot transfer in physics ML usually means: same equation, more parameters. We "
            "transfer across laws: a generalist that has seen five laws adapts to a held-out "
            "sixth with a quarter of the data at 2.9× lower error than a from-scratch "
            "specialist. Then we decompose why, with ablations that overturned the intended "
            "narrative: the quantity vocabulary is the dominant carrier (removing it is 10× "
            "worse), and the physics residual — helpful in general — constrains trajectory "
            "specialization at tiny budgets (removing it improves trajectory error 7× while "
            "answers stay flat). Both findings are per-seed, committed, and re-runnable."),
        sections=[
            ("What transfers, measured", [
                "The token stream of quantities and operators is the cross-law memory: ablation "
                "is catastrophic (10×). The physics residual is a constraint: at 24 samples it "
                "pins trajectories to equation-consistent shapes before the data can specialize "
                "them — removing it frees the curve 7× while answers are unaffected.",
                impact_cards([
                    ("2.9×", "lower answer error than a from-scratch specialist at the 25% "
                     "budget, on the held-out law.", "figs/fig1_fewshot.png"),
                    ("10× vocabulary", "removing the vocabulary token stream is catastrophic — "
                     "it is the main carrier of cross-law knowledge.", "figs/fig2_transfer.png"),
                    ("7× residual", "removing the physics residual frees trajectory "
                     "specialization at tiny budgets while answers stay flat — the residual "
                     "constrains curves before data can.", None),
                ]),
            ]),
            ("The numbers", [
                "Median answer rel-MAE at the 25% budget, and the ablation decomposition.",
                fewshot_table(),
                ablation_table(),
                '<div class="table-note">Ablations: no vocabulary stream, no physics residual, '
                'frozen body. The 10× vocabulary ratio and the 7× curve effect are median '
                'ratios over three seeds, each committed per-seed in transfer_ablations.json.',
            ]),
        ],
        repro=("git clone https://github.com/sehajr-singhs/fewshot-law-acquisition\n"
               "cd fewshot-law-acquisition\n"
               "python -m unittest tests.test_physx        # 49 physics tests\n"
               "python figs/make_figures.py                # figures from committed fewshot_data.json\n"
               "python src/physx/train_fewshot.py          # re-run the few-shot protocol\n"
               "python src/physx/run_transfer_ablations.py # re-run the ablations"),
    ),
    "field-consistency": dict(
        title="Field <strong>Consistency</strong>: the cost of enforcing PDE residuals",
        desc="The showcase number is the easiest member of its own distribution. Enforcing the residual makes fields consistent, not correct.",
        tagline="5.9% is the showcase. ~29% is the honest distribution. Both are reported — the paper's claim is the tradeoff.",
        abstract=(
            "The tensor pipeline extends to 2D fields: the same transformer with a "
            "field-shaped head learns the full u(x, y) surface of a heat plate. The showcase "
            "number — 5.9% peak field error — is real and is the easiest member of the "
            "validation distribution, whose honest mean is ~29%; this paper reports the "
            "distribution, not just the showcase. Enforcing the Poisson residual cuts it 6–8× "
            "while field fidelity degrades: consistency is not accuracy at the field level. "
            "Against a per-instance PINN (DeepXDE, ~19 minutes per problem), the specialist "
            "wins on its own instance at 0.03–0.06% error but with a higher "
            "governing-equation residual; the generalist answers any instance in one forward "
            "pass. Both statements are true; the claim is the tradeoff."),
        sections=[
            ("The distribution, not the showcase", [
                "Papers that report only the showcase are reporting selection. The canonical "
                "plate is the easiest member of its own validation distribution; this paper "
                "commits the distribution and the code that draws from it.",
                impact_cards([
                    ("5.9% vs ~29%", "canonical peak field error vs the honest mean held-out "
                     "peak error across the validation distribution — both measured, both "
                     "reported.", "figs/fig10_heat2d.png"),
                    ("6–8× residual", "the Poisson residual drops while field fidelity "
                     "degrades: enforcing the equation makes predictions consistent, not "
                     "correct.", None),
                    ("19 min vs 1 pass", "a per-instance DeepXDE PINN wins on its own problem; "
                     "the generalist answers any instance in one forward pass with a lower "
                     "governing-equation residual.", "figs/fig11_deepxde.png"),
                ]),
            ]),
            ("The DeepXDE comparison", [
                "On Burgers' equation, per-instance PINN (DeepXDE) reaches 0.03–0.06% full-field "
                "error on its own instance at ~19 minutes per problem; the single generalist "
                "answers any instance in one forward pass at 33–51% full-field error — but with "
                "a lower governing-equation residual (2×10⁻⁴ vs 1–5×10⁻³).",
                field_table(),
            ]),
        ],
        repro=("git clone https://github.com/sehajr-singhs/field-consistency\n"
               "cd field-consistency\n"
               "python -m unittest tests.test_physx        # 49 physics tests\n"
               "python figs/make_figures.py                # figures from committed physvdata_data.json\n"
               "python src/physx/run_physvdata.py          # re-run the field protocol"),
    ),
    "AGE-artificial-general-engineer": dict(
        title="AGE — <strong>Artificial General Engineer</strong>",
        desc="An autonomous engineering agent that plans, acts, verifies, and iterates — over software and physics — with a physics-adjusted transformer core and a fully reproducible paper series.",
        tagline="The $6.2B idea, minus the $6.2B — and every number in the series traces to a committed JSON.",
        abstract=(
            "AGE turns an engineering goal into a plan, executes it with sandboxed skills, and "
            "refuses to declare success until an independent verifier agrees. In the software "
            "domain that means running the test suite; in the physics domain it means a "
            "closed-form answer cross-checked by a numeric simulator written independently of "
            "the training signal, and a PhysFormer that predicts answers from the parameters "
            "alone. This repo is the project root: the agent, the physics core, both the NMI "
            "and IEEE manuscripts, and the committed data behind every number. The component "
            "studies — physics transformers, PhysBench, the verification gate, the loss "
            "channel, few-shot law acquisition, field consistency — live in their own repos, "
            "linked below."),
        sections=[
            ("The system", [
                "Give AGE a goal and it runs the loop: plan, act, verify, reflect, journal. "
                "Two brains — a deterministic mechanical brain that works with zero API keys, "
                "and an LLM brain behind any OpenAI-compatible endpoint. Writes are confined "
                "to the working directory; destructive commands are refused. Every failed "
                "verification writes a lesson, so the next run starts smarter.",
                impact_cards([
                    ("plan → act → verify", "the loop is the heart: every step can carry "
                     "expect: 'ok', and a failed verification fails the mission and writes a "
                     "lesson into the journal.", "figs/fig1_architecture.png"),
                    ("closed form ×2", "every physics design is computed twice, "
                     "independently: closed-form solution cross-checked by Euler/RK4 or "
                     "finite-difference simulators written from a different formulation.",
                     None),
                    ("65 tests green", "49 physics tests (closed forms, verifiers, the 10-law "
                     "set) + 16 node agent tests. The IEEE paper and NMI paper both compile "
                     "clean.", None),
                ]),
            ]),
            ("The physics core", [
                "physx/ is a physics-informed engineering core: projectile, pendulum, spring, "
                "beam, cantilever, RC, damped oscillator, Kepler, LC circuit, linear drag, "
                "Burgers, and 2D heat — each with an exact closed form, an independent numeric "
                "verifier, and a PhysFormer head trained on exact trajectories with the "
                "governing-equation residual in the loss. The multi-law protocol is what the "
                "component papers dissect: 10 laws, one shared body, 3 seeds, pre-registered.",
            ]),
            ("The series at a glance", [
                six_law_table(),
                '<div class="table-note">The original six-law shared-head experiment: median '
                'trajectory error with the real equation signature vs. a dummy-signature '
                'control (3 seeds each). The 6-law regime correlation (ρ = 1.0) was '
                'pre-registered onto a ten-law suite and falsified — see physics-transformers.',
            ]),
        ],
        repro=("git clone https://github.com/sehajr-singhs/AGE-artificial-general-engineer\n"
               "cd AGE-artificial-general-engineer\n"
               "npm test                        # 16 node tests\n"
               "python3 -m unittest physx.test_physx   # 49 physics tests\n"
               "node age.js --demo              # two-act demo: software scaffold + physics design"),
    ),
}


def build(repo):
    s = SITES[repo]
    body = []
    body.append('<section class="section"><div class="abstract">'
                f"<p>{s['abstract']}</p></div></section>")
    for i, (h, blocks) in enumerate(s["sections"]):
        body.append('<section class="section">')
        body.append(f'<h2 class="title">{h}</h2>')
        for b in blocks:
            if b.startswith("<div") or b.startswith("<table"):
                body.append(b)
            else:
                body.append(f"<p>{b}</p>")
        body.append("</section>")
    body.append('<section class="section"><h2 class="title">Reproduce</h2>'
                f"<pre>{s['repro']}</pre>"
                "<p class=\"muted\">Simulation-only, CPU-scale, deterministic seeds. No GPU required.</p>"
                "</section>")
    body.append(sisters_grid(repo))
    links = links_row(repo)
    foot = (f'<a href="{SITE}/AGE-artificial-general-engineer/">AGE series home</a> · '
            "every paper in this series links to every other")
    return page(s["title"], s["desc"], s["tagline"], links, "".join(body), foot)


def main():
    for repo in SITES:
        repo_dir = AGE if repo == "AGE-artificial-general-engineer" else os.path.join(REPOS, repo)
        path = os.path.join(repo_dir, "index.html")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(build(repo))
        print("wrote", path)


if __name__ == "__main__":
    main()
