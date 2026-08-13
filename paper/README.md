# AGE — Nature Machine Intelligence submission bundle

This directory contains the full submission package for the manuscript
**"An artificial general engineer that learns software and physical
engineering through verified trial and error"**.

## Contents

| File | Description |
|---|---|
| `manuscript.tex` → `manuscript.pdf` | Main article (compile with `pdflatex manuscript.tex`, twice for references) |
| `supplementary_information.tex` | Supplementary Information (SI 1–9) |
| `cover_letter.md` | Cover letter to the editor |
| `submission_checklist.md` | Author-facing and technical checklist |
| `author_info.md` | Author block, metadata, reviewer suggestions (placeholders) |
| `fig/` | Figure-generation script + all 13 figures + data JSONs |

## Reproducing everything

```bash
# 1. Train / re-verify models (weights are committed; this is optional)
#    The multi-seed baseline matrix (Table 2 / Fig 9) is run by:
python3 physx/run_matrix.py            # 75 runs: 5 domains x 3 kinds x 5 seeds

# 2. Significance tests over the matrix (Results, "Are these differences
#    significant?")
python3 physx/significance.py          # -> paper/fig/significance.json

# 3. External PINN baseline (Results, "Comparison against an external PINN
#    implementation") — requires the vendored DeepXDE wheel:
DDE_BACKEND=pytorch PYTHONPATH=vendor/deepxde python3 physx/deepxde_baseline.py

# 4. Regenerate all figures (from the age/ root)
python3 paper/fig/make_figures.py          # all figures
python3 paper/fig/make_figures.py --only fig4,fig10   # subset

# 4b. Multi-law (LCA) experiment — train 6 seeds x 2 conditions, then test
#     (Results, "Law-Conditioned Attention"; weights are committed):
python3 physx/train_multi.py --law real  --seed 0 --epochs 250 --per-domain 96
python3 physx/train_multi.py --law dummy --seed 0 --epochs 250 --per-domain 96
python3 physx/lca_significance.py         # -> paper/fig/multi_law_data.json

# 4c. Causal steering, few-shot adaptation, and physics-vs-data (Results):
python3 physx/law_swap.py                 # -> paper/fig/law_swap_data.json
python3 physx/train_fewshot.py --stage ft # fine-tune on 24 cantilever samples
python3 physx/run_physvdata.py --stages score  # -> paper/fig/physvdata_data.json

# 5. Compile the paper
cd paper && pdflatex manuscript.tex && pdflatex manuscript.tex
pdflatex supplementary_information.tex

# 6. Run the test suites and benchmarks
npm test                              # 16 agent tests
python3 -m unittest physx.test_physx   # 31 physics tests (47 total)
npm run bench:gate                    # verification-gate benchmark (Table 3)
```

## Traceability

Every quantitative claim in the manuscript maps to a committed artifact:

- `fig/fig*_data.json`, `fig/significance.json`,
  `fig/deepxde_comparison.json`, `fig/multi_law_data.json` — exact numbers
  used in the figures and the statistical tests.
- `../physx/models/*.log` — per-epoch training logs (ablation and baseline
  curves in Figs 6, 8c, 9 are parsed directly from these).
- `../physx/models/*.pt` + `*.stats.json` — trained weights and
  normalization statistics.
- `bench/gate_bench_results.json` — gate vs no-gate benchmark (Table 3).

## What changed in this revision (v4)

- New hard domains: viscous Burgers equation (nonlinear conservation law,
  shock formation) with Cole–Hopf closed form and an independent
  finite-volume upwind verifier, and steady-state heat conduction on a
  square plate (2D field, Poisson) with a sparse FD verifier
  (8 domains total).
- Multi-seed baseline study extended to 75 runs (5 domains × 3 kinds × 5
  seeds): MLP vs no-physics transformer vs transformer + physics, mean ±
  std, with per-domain and pooled Wilcoxon signed-rank tests + Cliff's
  delta (pooled physics-vs-nophysics trajectory residual: p < 0.001,
  δ = −0.92, ~19× median reduction; scalar accuracy not significantly
  different).
- External PINN baseline: per-instance DeepXDE training on three Burgers
  problems, evaluated with identical metrics (Fig 11).
- Trajectory fidelity: sigmoid-constrained shape head (Burgers field error
  123% → ~11%; cantilever curve 32% → ~16%).
- Verification-gate benchmark: 7 missions with the gate on/off, false-
  success rate 0% vs 29% (Table 3).
- Seeds control weight initialization as well as data/shuffling, so
  multi-seed runs are proper statistical replicates.
- New Figs 8 (Burgers), 9 (baselines), 10 (heat2d), 11 (DeepXDE), 12 (LCA
  architecture), 13 (multi-law results), 14 (law-swap causal steering), 15
  (physics-vs-data + few-shot).
- Causal steering: swapping the law signature at inference on identical
  inputs moves the prediction across the beam/cantilever boundary
  (steering index +0.090 vs −0.132, p < 0.0001); the constant-signature
  control is exactly insensitive (Fig 14).
- Few-shot adaptation: the generalist adapts to a held-out law with 25% of
  the specialist's data (Fig 15b).
- Physics-vs-data at the field level: identical networks with the
  physics-consistency loss on/off at two data fractions (Fig 15a).
- Negative results retained and reported: 3-layer/wider trajectory heads,
  hard-example physics weighting, and 512-sample runs all hurt at this
  data scale (documented in the paper).
