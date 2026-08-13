# Author information

## Title

**An artificial general engineer that learns software and physical engineering through verified trial and error**

## Author and affiliation

1. **Sehaj Randhir Singh** — Independent Researcher; affiliated with the Department of Electrical and Computer Engineering, NYU Tandon School of Engineering, Brooklyn, NY, USA — *conceptualization, methodology, software, physics core, training, evaluation, validation, writing*

Corresponding author: Sehaj Randhir Singh, sehajrsinghs@gmail.com

## Submission metadata (to fill)

- ORCID iD: to be added
- Data availability DOI: to be minted on acceptance (Zenodo/figshare)
- Code availability DOI: to be minted on acceptance (Zenodo); repo: https://github.com/placeholder/age
- Preprint: none (or list arXiv ID if posted)
- Funding: independent research; none to declare
- Author contributions and competing interests sections already in manuscript

## Suggested reviewers (optional)

1. Someone working on physics-informed machine learning (e.g., a researcher in the PINN / SciML community)
2. Someone working on LLM agents / tool use / verification
3. Someone in computational mechanics (finite elements, structural analysis)

## Notes for the editor

- The work is a complete, reproducible system (~5,900 lines, zero dependencies in the agent; PyTorch in the physics core), with all artifacts committed.
- Statistical claims are multi-seed (mean ± std over 5 seeds, 75-run baseline matrix, pooled Wilcoxon signed-rank tests with Cliff's delta); baselines (MLP, no-physics transformer) are trained on identical budgets; an external per-instance DeepXDE PINN baseline is reported on the Burgers domain.
- Claims about the commercial entity Prometheus are limited to citation of public reporting; the author has no affiliation or competing interest.
