"""_deliver.py — assemble fresh submission packages for all papers.

For each paper this writes, into the user's Downloads folder:
  NMI_<name>_manuscript.pdf
  NMI_<name>_SI.pdf
  NMI_<name>_code_data.zip   (paper dir + full physx source, data JSONs, checkpoints)

Run from the age/ project root:  python3 physx/_deliver.py
"""

import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")

# (paper dir, deliverable stem)
PAPERS = [
    ("paper",            "NMI_AGE_artificial_general_engineer"),
    ("paper_physformer", "NMI_physics_transformers"),
    ("paper_physbench",  "NMI_physbench"),
    ("paper_verify",     "NMI_verify_gated_agents"),
    ("paper_losschannel","NMI_loss_channel_study"),
    ("paper_fewshot",    "NMI_fewshot_law_acquisition"),
    ("paper_field",      "NMI_field_consistency"),
]

EXCLUDE_SUFFIXES = (".aux", ".log", ".out", ".toc", ".bbl", ".blg", ".synctex.gz")


def _skip(name):
    return name.endswith(EXCLUDE_SUFFIXES) or "__pycache__" in name or name.endswith(".pyc")


def build_zip(paper_dir, stem):
    zip_path = os.path.join(DOWNLOADS, stem + "_code_data.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        # paper directory (tex, pdf, md, fig/*)
        for base, _dirs, files in os.walk(os.path.join(ROOT, paper_dir)):
            for f in files:
                if _skip(f):
                    continue
                full = os.path.join(base, f)
                rel = os.path.relpath(full, ROOT)
                z.write(full, rel.replace(os.sep, "/"))
        # whole physx package (source, JSON artifacts, checkpoints)
        for base, _dirs, files in os.walk(os.path.join(ROOT, "physx")):
            for f in files:
                if _skip(f):
                    continue
                full = os.path.join(base, f)
                rel = os.path.relpath(full, ROOT)
                z.write(full, rel.replace(os.sep, "/"))
    return zip_path


def main():
    if not os.path.isdir(DOWNLOADS):
        sys.exit(f"Downloads folder not found: {DOWNLOADS}")
    made = []
    for paper_dir, stem in PAPERS:
        ms = os.path.join(ROOT, paper_dir, "manuscript.pdf")
        si = os.path.join(ROOT, paper_dir, "supplementary_information.pdf")
        for src, dst_name in ((ms, stem + "_manuscript.pdf"),
                              (si, stem + "_SI.pdf")):
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(DOWNLOADS, dst_name))
        zip_path = build_zip(paper_dir, stem)
        size_mb = os.path.getsize(zip_path) / 1e6
        made.append(f"{stem}: manuscript+SI copied, zip {size_mb:.1f} MB")
    print("\n".join(made))
    print(f"\n{len(made)} papers delivered to {DOWNLOADS}")


if __name__ == "__main__":
    main()
