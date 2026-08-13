"""_assemble_repo.py — assemble a standalone GitHub repo for one paper.

Usage: python3 physx/_assemble_repo.py <paper_dir> <dest_dir> [--extra src=dest ...]

Copies, mirroring the house style:
  <paper_dir>/manuscript.tex|.pdf            -> manuscript.tex|.pdf
  <paper_dir>/supplementary_information.*    -> same
  <paper_dir>/fig/                           -> figs/
  physx/*.py                                 -> src/physx/  (plus README there)
  physx/models/<extra model jsons>           -> results/
  physx/test_physx.py                        -> tests/test_physx.py
  LICENSE / .gitignore / requirements.txt    -> from physx/_repo_templates/

--extra KEY=DEST copies an extra path (file or dir) into the repo.
"""

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_repo_templates")

PY_SRC = [
    "__init__.py", "agg_matrix.py", "baselines.py", "cache_problems.py",
    "dataset.py", "deepxde_baseline.py", "law_swap.py", "laws.py",
    "lca_significance.py", "physformer.py", "regime_analysis.py",
    "regime_oos.py", "residuals.py", "run_fidelity.py",
    "run_fidelity_heat2d.py", "run_matrix.py", "run_physvdata.py",
    "run_transfer_ablations.py", "significance.py", "sim.py", "solve.py",
    "test_physx.py", "train.py", "train_fewshot.py", "train_multi.py",
]


def copy_tree(src, dst, skip=()):
    for base, _dirs, files in os.walk(src):
        for f in files:
            if any(f.endswith(s) for s in skip) or f.endswith((".pyc",)):
                continue
            full = os.path.join(base, f)
            rel = os.path.relpath(full, src)
            out = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copy2(full, out)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    paper_dir = os.path.join(ROOT, sys.argv[1])
    dest = os.path.abspath(sys.argv[2])
    extras = []
    argv = sys.argv[3:]
    i = 0
    while i < len(argv):
        if argv[i] == "--extra":
            i += 1
            extras.append(argv[i])
        i += 1

    os.makedirs(dest, exist_ok=True)

    # papers at top level
    for name in ("manuscript.tex", "manuscript.pdf",
                 "supplementary_information.tex", "supplementary_information.pdf"):
        src = os.path.join(paper_dir, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest, name))

    # figs
    fig_src = os.path.join(paper_dir, "fig")
    if os.path.isdir(fig_src):
        copy_tree(fig_src, os.path.join(dest, "figs"),
                  skip=(".aux", ".log", ".out", ".toc"))

    # src/physx
    src_dir = os.path.join(dest, "src", "physx")
    os.makedirs(src_dir, exist_ok=True)
    for f in PY_SRC:
        full = os.path.join(ROOT, "physx", f)
        if os.path.exists(full):
            shutil.copy2(full, os.path.join(src_dir, f))

    # tests: thin re-export so `python -m unittest tests.test_physx` works
    # from the repo root (the suite itself lives in src/physx/test_physx.py
    # and uses package-relative imports)
    tests_dir = os.path.join(dest, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    with open(os.path.join(tests_dir, "__init__.py"), "w") as f:
        f.write("")
    with open(os.path.join(tests_dir, "test_physx.py"), "w") as f:
        f.write(
            "import os, sys\n"
            "sys.path.insert(0, os.path.join(os.path.dirname(__file__), \"..\", \"src\"))\n"
            "from physx.test_physx import *  # noqa: F401,F403\n"
        )

    # results + extras
    for extra in extras:
        src_path, _, dst_rel = extra.partition("->")
        src_path = os.path.join(ROOT, src_path.strip())
        dst_path = os.path.join(dest, dst_rel.strip())
        if os.path.isdir(src_path):
            copy_tree(src_path, dst_path, skip=(".pt", ".log", ".err"))
        elif os.path.exists(src_path):
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            shutil.copy2(src_path, dst_path)

    # templates
    for f in ("LICENSE", ".gitignore", "requirements.txt"):
        shutil.copy2(os.path.join(TEMPLATES, f), os.path.join(dest, f))
    print(f"assembled {dest}")


if __name__ == "__main__":
    main()
