# AGE — IEEE paper submission bundle

**Title:** AGE: An Autonomous Engineering Agent with Physics-Informed Transformers and Verified Trial-and-Error Learning

**Author:** Sehaj Randhir Singh (Department of Electrical and Computer Engineering, NYU Tandon School of Engineering — independent researcher), sehajrsinghs@gmail.com

## Files

| File | Description |
|---|---|
| `ieee_manuscript.tex` → `ieee_manuscript.pdf` | IEEE conference-format paper (IEEEtran, two-column) |
| `README.md` | This file |

Figures are shared with the NMI bundle (`../paper/fig/`), so regenerate
them there first:

```bash
cd ../paper && pdflatex manuscript.tex   # not required; figures already exist
python3 fig/make_figures.py --only fig1,fig2,fig4,fig9,fig10,fig11
```

Then compile:

```bash
cd paper_ieee && pdflatex ieee_manuscript.tex && pdflatex ieee_manuscript.tex
```

## What to fill before submission

- [ ] Conference/journal target (e.g., IEEE Access, IJCNN, ICMLA, IROS) and
      the corresponding IEEEtran style option.
- [ ] ORCID iD.
- [ ] Code/data availability DOIs (repo: https://github.com/placeholder/age).
- [ ] Section V-D (DeepXDE comparison) numbers — populated automatically by
      `physx/deepxde_baseline.py` once all three per-instance trainings run.

## Reproducibility pointers

- Baseline matrix (Table 1): `python3 physx/run_matrix.py`
- Significance tests: `python3 physx/significance.py`
- DeepXDE comparison: `DDE_BACKEND=pytorch PYTHONPATH=vendor/deepxde python3 physx/deepxde_baseline.py`
- Gate benchmark (Table 2): `npm run bench:gate`
- Tests: `npm test` (16) + `python3 -m unittest physx.test_physx` (21) = 37
