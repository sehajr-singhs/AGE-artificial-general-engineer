"""make_figures.py — generate the figures for the AGE manuscript.

  fig1_architecture.png  system-level schematic (agent loop + modules)
  fig2_physformer.png    PhysFormer architecture (reasoning + physics layers)
  fig3_convergence.png   training convergence (projectile, spring)
  fig4_predictions.png   PhysFormer vs exact answers on held-out problems
  fig5_deflection.png    beam deflection curve: exact vs PhysFormer prediction
  fig6_ablations.png     ablations: physics loss on/off; shape-norm vs global-norm
  fig7_cantilever.png    cantilever beam: deflection curve + held-out predictions

Per-epoch ablation curves are parsed from the training logs written by
physx/train.py, so every number is traceable to a real run.

usage: python3 paper/fig/make_figures.py [--only fig4,fig6]
"""

import argparse
import json
import math
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)

from physx import dataset, sim  # noqa: E402
from physx.physformer import build  # noqa: E402

OUT = HERE
plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "figure.dpi": 200,
})


# ------------------------------------------------------------------ fig 1
def fig1_architecture():
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 46)
    ax.axis("off")

    def box(x, y, w, h, text, fc, fs=9, lw=1.2):
        from matplotlib.patches import FancyBboxPatch
        b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                           fc=fc, ec="#333333", lw=lw)
        ax.add_patch(b)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color="#111111")
        return b

    def arrow(x1, y1, x2, y2, color="#444444", style="-|>"):
        from matplotlib.patches import FancyArrowPatch
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                     mutation_scale=14, color=color, lw=1.4))

    # goal in
    box(2, 38, 14, 6, "Goal\n(engineering task)", "#eaf2fb")
    # planner
    box(24, 36, 20, 9, "Planner\nmechanical brain | LLM brain", "#dff0d8")
    # skills
    box(54, 33, 20, 14, "Skills (embodiment)\ninspect · read · search\nedit · run · verify · physx", "#fcf8e3")
    # environment
    box(80, 34, 17, 12, "Sandboxed\nenvironment\n(code / physics)", "#f2dede")
    # verifier
    box(54, 15, 20, 9, "Verification gate\nexpect: ok — tests /\nnumeric simulators", "#e8d5f5")
    # reflect
    box(24, 14, 20, 9, "Reflect\n(done? or next plan)", "#f5d5e8")
    # journal
    box(2, 13, 16, 7, "Journal\nepisodic memory\n+ lessons", "#d9edf7")

    arrow(16, 41, 24, 41)
    arrow(44, 41, 54, 40)
    arrow(74, 40, 80, 40)
    arrow(88.5, 34, 88.5, 24, style="-|>")
    arrow(80, 19.5, 74, 19.5)
    arrow(54, 19.5, 44, 19.5)
    arrow(24, 18.5, 18, 17.5)
    arrow(10, 13, 10, 38, style="-|>", color="#777777")
    ax.text(10, 25.5, "lessons\nreplayed", ha="center", fontsize=7, color="#666666")

    ax.set_title("Figure 1 — AGE: an artificial general engineer that learns through "
                 "verified trial and error", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1_architecture.png"), bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------ fig 2
def fig2_physformer():
    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 50)
    ax.axis("off")

    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    def box(x, y, w, h, text, fc, fs=9):
        b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                           fc=fc, ec="#333333", lw=1.2)
        ax.add_patch(b)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color="#111111")

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=14, color="#444444", lw=1.4))

    box(2, 40, 18, 8, "Problem parameters\n(L, P, E, I, h) →\n(param_id, value) tokens", "#eaf2fb")
    box(28, 41, 18, 7, "Embeddings\nparam embedding +\nvalue projection + pos", "#fcf8e3")
    box(28, 28, 18, 9, "Reasoning layers\nTransformer encoder\n(self-attention + FFN)", "#dff0d8")
    box(2, 14, 18, 10, "Answer head\n→ scalar\n(max deflection)", "#d9edf7")
    box(28, 14, 18, 10, "Trajectory head\n→ deflection curve\nw(x), 50 points", "#d9edf7")
    box(56, 14, 18, 9, "Physics-consistency\nlayer: residual of\ngoverning equation", "#f2dede")
    box(80, 15, 18, 11, "Loss\nw_d · data MSE\n+ w_p · physics\nresidual", "#e8d5f5")

    arrow(20, 44, 28, 44.5)
    arrow(37, 41, 37, 37)
    arrow(37, 28, 37, 25.5)
    arrow(20, 19, 28, 19)
    arrow(46, 19, 56, 19)
    arrow(74, 18.5, 80, 19.5)
    # data path from trajectory head to loss (dashed)
    ax.add_patch(FancyArrowPatch((46, 16), (80, 17), arrowstyle="-|>",
                                 mutation_scale=14, color="#888888", lw=1.1,
                                 linestyle=(0, (3, 2))))
    ax.text(63, 16.8, "data (exact trajectory)", fontsize=6.5, color="#666666")

    ax.set_title("Figure 2 — PhysFormer: a transformer adjusted for physics "
                 "(reasoning layers + physics layers, together)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig2_physformer.png"), bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------- fig 3 data
def run_logged(domain, epochs, samples, batch_size, d_model, n_layers, seed=0):
    """Small training run with per-epoch logging (returns list of logs)."""
    from physx.train import make_batches, evaluate

    problems = dataset.generate(domain, n=samples, seed=seed)
    st = dataset.stats(problems, domain)
    ans_stats = dataset.answer_stats(problems, domain)
    tstats = dataset.traj_stats(problems)
    n_val = max(4, samples // 8)
    train_p, val_p = problems[:-n_val], problems[-n_val:]
    model = build(domain, st, d_model=d_model, n_layers=n_layers)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    logs = []
    shape_norm = domain in ("beam", "rc")
    for epoch in range(1, epochs + 1):
        model.train()
        for pids, vals, y, traj_n, params, peaks in make_batches(
                train_p, st, ans_stats, tstats, batch_size, shuffle=True,
                seed=seed + epoch, shape_norm=shape_norm):
            opt.zero_grad()
            ans_pred, traj_pred = model(pids, vals)
            loss_ans = torch.nn.functional.mse_loss(ans_pred, y)
            loss_traj = torch.nn.functional.mse_loss(traj_pred, traj_n)
            if shape_norm:
                traj_real = traj_pred * peaks
            else:
                traj_real = traj_pred * torch.tensor(tstats[1], dtype=torch.float32) \
                    + torch.tensor(tstats[0], dtype=torch.float32)
            phys = model.physics_residual(traj_real, params).mean()
            phys_w = 0.05 * min(1.0, epoch / 10)
            phys_norm = phys / (phys.detach().abs() + 1e-6)
            loss = loss_ans + loss_traj + phys_w * phys_norm
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        with torch.no_grad():
            mae, pres = evaluate(model, st, ans_stats, tstats, val_p,
                                 shape_norm=shape_norm)
        logs.append({"epoch": epoch, "val_rel_mae": mae, "phys_resid": pres})
    return logs


def fig3_convergence():
    print("[fig3] training projectile (logged) ...")
    proj = run_logged("projectile", epochs=25, samples=600, batch_size=32,
                      d_model=48, n_layers=3, seed=1)
    print("[fig3] training spring (logged) ...")
    spring = run_logged("spring", epochs=25, samples=300, batch_size=32,
                        d_model=48, n_layers=3, seed=2)

    with open(os.path.join(OUT, "fig3_data.json"), "w") as f:
        json.dump({"projectile": proj, "spring": spring}, f, indent=1)

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.4))
    for ax, key, color, label in [
        (axes[0], "projectile", "#1f77b4", "Projectile (range)"),
        (axes[0], "spring", "#ff7f0e", "Spring (natural frequency)"),
    ]:
        ep = [d["epoch"] for d in proj if d] if key == "projectile" else [d["epoch"] for d in spring]
        mae = [d["val_rel_mae"] for d in (proj if key == "projectile" else spring)]
        ax.plot(ep, mae, "-o", ms=3, color=color, label=label)
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Validation relative error")
    axes[0].set_yscale("log")
    axes[0].legend(frameon=False)
    axes[0].set_title("(a) Answer accuracy", fontsize=9)

    for key, color, label in [
        ("projectile", "#1f77b4", "Projectile"),
        ("spring", "#ff7f0e", "Spring"),
    ]:
        logs = proj if key == "projectile" else spring
        ep = [d["epoch"] for d in logs]
        pr = [d["phys_resid"] for d in logs]
        axes[1].plot(ep, pr, "-o", ms=3, color=color, label=label)
    axes[1].axhline(0.1, color="#999999", lw=0.8, ls=":")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Physics residual (governing equation)")
    axes[1].set_yscale("log")
    axes[1].legend(frameon=False)
    axes[1].set_title("(b) Physics consistency", fontsize=9)

    fig.suptitle("Figure 3 — PhysFormer converges on data and physics together "
                 "(physics loss ramps in after epoch 10)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(OUT, "fig3_convergence.png"), bbox_inches="tight")
    plt.close(fig)
    print("[fig3] done")


# ------------------------------------------------------------- fig 4 data
def load_model(domain):
    models_dir = os.path.join(ROOT, "physx", "models")
    path = os.path.join(models_dir, f"{domain}.pt")
    stats_file = os.path.join(models_dir, f"{domain}.stats.json")
    with open(stats_file) as f:
        meta = json.load(f)
    st = meta["param_stats"]
    arch = meta.get("arch", {})
    model = build(domain, st, d_model=arch.get("d_model", 48),
                  n_layers=arch.get("n_layers", 3),
                  nhead=arch.get("nhead", 4), dim_ff=arch.get("dim_ff", 96),
                  traj_hidden=arch.get("traj_hidden", 64),
                  traj_steps=arch.get("traj_steps", 50),
                  kind=arch.get("kind", "physformer"),
                  sigmoid_traj=arch.get("sigmoid_traj", False))
    model.load_state_dict(torch.load(path, map_location="cpu", weights_only=True))
    model.eval()
    return model, meta


def predict_batch(model, meta, problems):
    st = meta["param_stats"]
    ans_mean, ans_std = meta["answer_stats"]
    domain = meta["domain"]
    keys = st["keys"]
    pids = torch.tensor([list(range(len(keys)))] * len(problems), dtype=torch.long)
    vals = torch.tensor([dataset.normalize(p["params"], st) for p in problems], dtype=torch.float32)
    with torch.no_grad():
        ans, _ = model(pids, vals)
    y = ans.numpy() * ans_std + ans_mean
    preds = np.array([dataset.answer_inverse(domain, a) for a in y])
    true = np.array([p["answer"] for p in problems])
    return preds, true


def fig4_predictions():
    print("[fig4] evaluating trained models on held-out problems ...")
    domains = [("beam", True, "#1f77b4", "Beam (max deflection)"),
               ("cantilever", True, "#2ca02c", "Cantilever (max deflection)"),
               ("projectile", False, "#ff7f0e", "Projectile (range)"),
               ("heat2d", False, "#9467bd", "Heat2D (peak temperature)")]
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 6.4))
    axes = axes.ravel()
    summaries = {}
    for ax, (domain, log, color, label) in zip(axes, domains):
        try:
            model, meta = load_model(domain)
        except FileNotFoundError:
            print(f"[fig4] skipping {domain}: model not trained yet")
            ax.set_visible(False)
            continue
        model, meta = load_model(domain)
        problems = dataset.generate(domain, n=250, seed=42 + (domain == "beam") * 7)
        preds, true = predict_batch(model, meta, problems)
        rel = np.abs(preds - true) / np.abs(true)
        rel[rel == np.inf] = 1.0
        mean_rel = float(rel.mean())
        if log:
            # R^2 in log10 space for the wide-range domain
            lp, lt = np.log10(preds), np.log10(true)
            ss_res = float(((lp - lt) ** 2).sum())
            ss_tot = float(((lt - lt.mean()) ** 2).sum())
            r2 = 1 - ss_res / ss_tot
        else:
            r2 = 1 - float(((preds - true) ** 2).sum() / ((true - true.mean()) ** 2).sum())
        summaries[domain] = {"mean_rel_error": mean_rel, "r2": r2, "n": len(problems)}
        if log:
            ax.scatter(true, preds, s=6, alpha=0.6, color=color)
            lim = [np.min([true.min(), preds.min()]) * 0.8, np.max([true.max(), preds.max()]) * 1.2]
            ax.plot(lim, lim, "k--", lw=0.8)
            ax.set_xscale("log"); ax.set_yscale("log")
            ax.set_xlabel("Exact max deflection (m)")
            ax.set_ylabel("PhysFormer prediction (m)")
            ax.set_title(f"{label} — rel. err {mean_rel * 100:.1f}%, R² = {r2:.3f}", fontsize=8.5)
        else:
            ax.scatter(true, preds, s=6, alpha=0.6, color=color)
            lim = [min(true.min(), preds.min()), max(true.max(), preds.max())]
            ax.plot(lim, lim, "k--", lw=0.8)
            ax.set_xlabel("Exact range (m)")
            ax.set_ylabel("PhysFormer prediction (m)")
            ax.set_title(f"{label} — rel. err {mean_rel * 100:.1f}%, R² = {r2:.3f}", fontsize=8.5)
    fig.suptitle("Figure 4 — PhysFormer predictions vs exact answers on held-out problems "
                 "(250 per domain)", fontsize=10)
    for ax in axes:
        ax.set_visible(True)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(OUT, "fig4_predictions.png"), bbox_inches="tight")
    plt.close(fig)
    with open(os.path.join(OUT, "fig4_data.json"), "w") as f:
        json.dump(summaries, f, indent=1)
    print("[fig4] done", summaries)


# ------------------------------------------------------------- fig 5 data
def fig5_deflection():
    print("[fig5] beam deflection curves ...")
    params = {"L": 4.0, "P": 3000.0, "E": 2e11, "I": 5e-6, "h": 0.2}
    model, meta = load_model("beam")
    st = meta["param_stats"]
    keys = st["keys"]
    pids = torch.tensor([list(range(len(keys)))], dtype=torch.long)
    vals = torch.tensor([dataset.normalize(params, st)], dtype=torch.float32)
    tmean, tstd = meta["traj_stats"]
    ans_mean, ans_std = meta["answer_stats"]
    traj_norm = meta.get("traj_norm", "global")
    with torch.no_grad():
        ans, traj = model(pids, vals)
    if traj_norm == "shape":
        # trajectory head predicts the normalized shape; scale comes from the
        # answer head (max deflection)
        y = float(ans[0]) * ans_std + ans_mean
        wmax = dataset.answer_inverse("beam", y)
        w_pred = traj[0, :, 0].numpy() * wmax
    else:
        traj_real = traj * torch.tensor(tstd, dtype=torch.float32) \
            + torch.tensor(tmean, dtype=torch.float32)
        w_pred = traj_real[0, :, 0].numpy()

    x = np.linspace(0, params["L"], 50)
    w_exact = sim.beam_traj(params, 50)[:, 0]

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.4))
    axes[0].plot(x, w_exact * 1e3, "k-", lw=1.6, label="Exact (closed form)")
    axes[0].plot(x, w_pred * 1e3, "--", color="#1f77b4", lw=1.6, label="PhysFormer")
    axes[0].fill_between(x, w_exact * 1e3, w_pred * 1e3, color="#1f77b4", alpha=0.15)
    axes[0].set_xlabel("Position along beam (m)")
    axes[0].set_ylabel("Deflection (mm)")
    axes[0].legend(frameon=False)
    axes[0].set_title(f"(a) Deflection curve — max error "
                      f"{np.max(np.abs(w_pred - w_exact)) / np.max(np.abs(w_exact)) * 100:.1f}% "
                      f"of peak", fontsize=9)

    mae = np.abs(w_pred - w_exact) / np.max(np.abs(w_exact))
    axes[1].plot(x, mae, color="#d62728", lw=1.4)
    axes[1].set_xlabel("Position along beam (m)")
    axes[1].set_ylabel("|pred − exact| / peak deflection")
    axes[1].set_title("(b) Normalized error profile", fontsize=9)
    axes[1].set_ylim(bottom=0)

    fig.suptitle("Figure 5 — PhysFormer deflection curve for a 4 m simply supported beam, "
                 "P = 3 kN, E = 2 × 10¹¹ Pa, I = 5 × 10⁻⁶ m⁴", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(OUT, "fig5_deflection.png"), bbox_inches="tight")
    plt.close(fig)
    print("[fig5] done")


# ------------------------------------------------------------- fig 6 data
def parse_train_log(path):
    """Parse a physx/train.py log into per-epoch metrics."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.search(r"epoch\s+(\d+)/(\d+).*?val_rel_mae ([0-9.eE+-]+) phys_resid ([0-9.eE+-]+)", line)
            if m:
                rows.append({"epoch": int(m.group(1)), "val_rel_mae": float(m.group(3)),
                             "phys_resid": float(m.group(4))})
    return rows


def fig6_ablations():
    """Two ablations, both parsed from real training logs:
    (a) physics loss on vs off (same architecture, 40 epochs, 256 samples);
    (b) shape-norm vs global-norm trajectories (physics residual shows the
        global-norm trajectory collapses physically)."""
    print("[fig6] parsing ablation training logs ...")
    models_dir = os.path.join(ROOT, "physx", "models")
    nophys = parse_train_log(os.path.join(models_dir, "abl_beam_nophys.log"))
    phys64 = parse_train_log(os.path.join(models_dir, "abl_beam_phys64.log"))
    globaln = parse_train_log(os.path.join(models_dir, "abl_beam_global.log"))

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.4))
    if nophys and phys64:
        axes[0].plot([r["epoch"] for r in nophys], [r["val_rel_mae"] for r in nophys],
                     "-o", ms=3, color="#d62728", label="Without physics loss")
        axes[0].plot([r["epoch"] for r in phys64], [r["val_rel_mae"] for r in phys64],
                     "-o", ms=3, color="#1f77b4", label="With physics loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Validation relative error")
    axes[0].set_yscale("log")
    axes[0].legend(frameon=False)
    axes[0].set_title("(a) Physics loss on vs off (beam)", fontsize=9)

    if globaln and phys64:
        axes[1].plot([r["epoch"] for r in globaln], [r["phys_resid"] for r in globaln],
                     "-o", ms=3, color="#d62728", label="Global trajectory norm")
        axes[1].plot([r["epoch"] for r in phys64], [r["phys_resid"] for r in phys64],
                     "-o", ms=3, color="#1f77b4", label="Shape norm (per-problem)")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Physics residual of predicted trajectory")
    axes[1].set_yscale("log")
    axes[1].legend(frameon=False)
    axes[1].set_title("(b) Shape norm vs global norm (beam)", fontsize=9)

    fig.suptitle("Figure 6 — Ablations: physics loss and shape/scale decoupling "
                 "(beam, 40 epochs, 256 samples)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(OUT, "fig6_ablations.png"), bbox_inches="tight")
    plt.close(fig)
    with open(os.path.join(OUT, "fig6_data.json"), "w") as f:
        json.dump({"phys_off": nophys, "phys_on": phys64, "global_norm": globaln},
                  f, indent=1)
    print("[fig6] done")


# ------------------------------------------------------------- fig 7 data
def fig7_cantilever():
    print("[fig7] cantilever deflection curves + held-out predictions ...")
    params = {"L": 4.0, "P": 3000.0, "E": 2e11, "I": 5e-6, "h": 0.2}
    model, meta = load_model("cantilever")
    st = meta["param_stats"]
    keys = st["keys"]
    pids = torch.tensor([list(range(len(keys)))], dtype=torch.long)
    vals = torch.tensor([dataset.normalize(params, st)], dtype=torch.float32)
    ans_mean, ans_std = meta["answer_stats"]
    with torch.no_grad():
        ans, traj = model(pids, vals)
    y = float(ans[0]) * ans_std + ans_mean
    wmax = dataset.answer_inverse("cantilever", y)
    w_pred = traj[0, :, 0].numpy() * wmax

    x = np.linspace(0, params["L"], 50)
    w_exact = sim.cantilever_traj(params, 50)[:, 0]

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.4))
    axes[0].plot(x, w_exact * 1e3, "k-", lw=1.6, label="Exact (closed form)")
    axes[0].plot(x, w_pred * 1e3, "--", color="#2ca02c", lw=1.6, label="PhysFormer")
    axes[0].fill_between(x, w_exact * 1e3, w_pred * 1e3, color="#2ca02c", alpha=0.15)
    axes[0].set_xlabel("Position along cantilever (m)")
    axes[0].set_ylabel("Deflection (mm)")
    axes[0].legend(frameon=False)
    axes[0].set_title(f"(a) Deflection curve — max error "
                      f"{np.max(np.abs(w_pred - w_exact)) / np.max(np.abs(w_exact)) * 100:.1f}% "
                      f"of peak", fontsize=9)

    problems = dataset.generate("cantilever", n=250, seed=137)
    preds, true = predict_batch(model, meta, problems)
    rel = np.abs(preds - true) / np.abs(true)
    mean_rel = float(rel.mean())
    lp, lt = np.log10(preds), np.log10(true)
    r2 = 1 - float(((lp - lt) ** 2).sum() / ((lt - lt.mean()) ** 2).sum())
    axes[1].scatter(true, preds, s=6, alpha=0.6, color="#2ca02c")
    lim = [np.min([true.min(), preds.min()]) * 0.8, np.max([true.max(), preds.max()]) * 1.2]
    axes[1].plot(lim, lim, "k--", lw=0.8)
    axes[1].set_xscale("log"); axes[1].set_yscale("log")
    axes[1].set_xlabel("Exact max deflection (m)")
    axes[1].set_ylabel("PhysFormer prediction (m)")
    axes[1].set_title(f"(b) Held-out predictions — rel. err {mean_rel * 100:.1f}%, R² = {r2:.3f}", fontsize=9)

    fig.suptitle("Figure 7 — Cantilever beam: PhysFormer deflection curve and generalization "
                 "(L = 4 m, P = 3 kN, E = 2 × 10¹¹ Pa, I = 5 × 10⁻⁶ m⁴)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(OUT, "fig7_cantilever.png"), bbox_inches="tight")
    plt.close(fig)
    with open(os.path.join(OUT, "fig7_data.json"), "w") as f:
        json.dump({"mean_rel_error": mean_rel, "r2": r2, "n": len(problems),
                   "curve_max_error": float(np.max(np.abs(w_pred - w_exact)) / np.max(np.abs(w_exact))),
                   "answer_rel_error": float(abs(wmax - sim.cantilever_closed(params)["answer"]) / sim.cantilever_closed(params)["answer"])},
                  f, indent=1)
    print("[fig7] done")


# ------------------------------------------------------------- fig 8 data
def fig8_burgers():
    """Burgers: nonlinear conservation law with shock formation. (a) predicted
    vs exact final field for a canonical and a shock-forming case; (b) held-out
    predictions of the peak velocity; (c) physics residual during training,
    physics-on vs physics-off (from the matrix logs)."""
    print("[fig8] Burgers field + generalization + residual ...")
    model, meta = load_model("burgers")
    st = meta["param_stats"]
    keys = st["keys"]
    ans_mean, ans_std = meta["answer_stats"]

    def predict(params):
        pids = torch.tensor([list(range(len(keys)))], dtype=torch.long)
        vals = torch.tensor([dataset.normalize(params, st)], dtype=torch.float32)
        with torch.no_grad():
            ans, traj = model(pids, vals)
        y = float(ans[0]) * ans_std + ans_mean
        peak = dataset.answer_inverse("burgers", y)
        field = traj[0, :, 0].numpy().reshape(sim.NT, sim.NX) * float(params["A"])
        return peak, field

    cases = [("canonical", {"nu": 0.05, "A": 1.5, "sigma": 0.3}),
             ("shock", {"nu": 0.02, "A": 2.0, "sigma": 0.2})]
    x = np.linspace(sim.XL, sim.XR, sim.NX)

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
    colors = {"canonical": "#1f77b4", "shock": "#d62728"}
    for name, params in cases:
        peak, field = predict(params)
        u_exact = sim.burgers_field(params["nu"], params["A"], params["sigma"], sim.TF)
        axes[0].plot(x, u_exact, "-", color=colors[name], lw=1.4,
                     label=f"{name} exact")
        axes[0].plot(x, field[-1], "--", color=colors[name], lw=1.4,
                     label=f"{name} PhysFormer")
        err = np.max(np.abs(field[-1] - u_exact)) / np.max(np.abs(u_exact))
        print(f"[fig8] {name}: final-field max err {err * 100:.1f}% of peak, "
              f"peak {peak:.4f} vs exact {sim.burgers_closed(params)['answer']:.4f}")
    axes[0].set_xlabel("x")
    axes[0].set_ylabel("u(x, t=0.4)")
    axes[0].legend(frameon=False, fontsize=7.5)
    axes[0].set_title("(a) Final-time field (exact vs PhysFormer)", fontsize=9)

    problems = dataset.generate("burgers", n=250, seed=999)
    preds, true = predict_batch(model, meta, problems)
    rel = np.abs(preds - true) / np.abs(true)
    mean_rel = float(rel.mean())
    r2 = 1 - float(((preds - true) ** 2).sum() / ((true - true.mean()) ** 2).sum())
    axes[1].scatter(true, preds, s=6, alpha=0.6, color="#2ca02c")
    lim = [min(true.min(), preds.min()) * 0.9, max(true.max(), preds.max()) * 1.1]
    axes[1].plot(lim, lim, "k--", lw=0.8)
    axes[1].set_xlabel("Exact peak velocity (m/s)")
    axes[1].set_ylabel("PhysFormer prediction (m/s)")
    axes[1].set_title(f"(b) Held-out predictions — rel. err {mean_rel * 100:.1f}%, "
                      f"R² = {r2:.3f}", fontsize=9)

    models_dir = os.path.join(ROOT, "physx", "models")
    phys_logs = [parse_train_log(os.path.join(models_dir, f"matrix_burgers_phys_s{s}.log"))
                 for s in range(5)]
    nophys_logs = [parse_train_log(os.path.join(models_dir, f"matrix_burgers_nophys_s{s}.log"))
                   for s in range(5)]
    for logs, color, label in [(phys_logs, "#1f77b4", "Physics loss on"),
                               (nophys_logs, "#d62728", "Physics loss off")]:
        for run in logs:
            if run:
                axes[2].plot([r["epoch"] for r in run], [r["phys_resid"] for r in run],
                             color=color, lw=0.8, alpha=0.5)
    axes[2].set_xlabel("Epoch")
    axes[2].set_ylabel("Physics residual of predicted field")
    axes[2].set_yscale("log")
    axes[2].set_title("(c) Burgers physics residual during training", fontsize=9)
    from matplotlib.lines import Line2D
    axes[2].legend(handles=[Line2D([0], [0], color="#1f77b4", lw=1.4, label="Physics loss on"),
                            Line2D([0], [0], color="#d62728", lw=1.4, label="Physics loss off")],
                   frameon=False, fontsize=7.5)

    fig.suptitle("Figure 8 — Viscous Burgers equation: a nonlinear conservation law "
                 "with shock formation", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(os.path.join(OUT, "fig8_burgers.png"), bbox_inches="tight")
    plt.close(fig)
    with open(os.path.join(OUT, "fig8_data.json"), "w") as f:
        json.dump({"mean_rel_error": mean_rel, "r2": r2, "n": len(problems),
                   "cases": {n: {"answer_rel_error": float(
                       abs(predict(p)[0] - sim.burgers_closed(p)["answer"]) / sim.burgers_closed(p)["answer"]),
                       "curve_max_error": float(np.max(np.abs(predict(p)[1][-1] - sim.burgers_field(p["nu"], p["A"], p["sigma"], sim.TF)))
                                                / np.max(np.abs(sim.burgers_field(p["nu"], p["A"], p["sigma"], sim.TF))))}
                              for n, p in cases}}, f, indent=1)
    print("[fig8] done")


# ------------------------------------------------------------- fig 9 data
def fig9_baselines():
    """Multi-seed baselines: MLP vs transformer (no physics) vs transformer +
    physics, mean +/- std over 5 seeds, from fig9_data.json (written by
    physx/run_matrix.py). The error bars are the seed-to-seed spread."""
    print("[fig9] multi-seed baselines bar chart ...")
    data_path = os.path.join(OUT, "fig9_data.json")
    if not os.path.exists(data_path):
        print("[fig9] fig9_data.json missing — run physx/run_matrix.py first")
        return
    with open(data_path) as f:
        data = json.load(f)

    domains = ["beam", "cantilever", "projectile", "burgers", "heat2d"]
    labels = {"beam": "Beam", "cantilever": "Cantilever",
              "projectile": "Projectile", "burgers": "Burgers", "heat2d": "Heat2D"}
    kinds = [("mlp", "MLP (no attention)", "#7f7f7f"),
             ("nophys", "Transformer, no physics", "#ff7f0e"),
             ("phys", "Transformer + physics", "#1f77b4")]
    xpos = np.arange(len(domains))
    width = 0.26

    fig, ax = plt.subplots(figsize=(9.5, 3.6))
    for j, (kind, label, color) in enumerate(kinds):
        means, errs = [], []
        for d in domains:
            st = (data.get(d, {}).get(kind, {}) or {}).get("val_rel_mae") or {}
            means.append(st.get("mean", float("nan")) * 100)
            errs.append(st.get("std", 0) * 100)
        ax.bar(xpos + (j - 1) * width, means, width, yerr=errs, capsize=3,
               color=color, label=label, alpha=0.92, error_kw={"lw": 1.0})
        for xi, m in zip(xpos + (j - 1) * width, means):
            if not np.isnan(m):
                ax.text(xi, m + 0.4, f"{m:.1f}", ha="center", fontsize=7)

    ax.set_xticks(xpos)
    ax.set_xticklabels([labels[d] for d in domains])
    ax.set_ylabel("Validation relative error (%) mean ± std, 5 seeds")
    ax.set_yscale("log")
    ax.set_ylim(1, 200)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Figure 9 — Baselines on identical budgets (256 samples, 60 epochs, "
                 "same architecture and heads)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig9_baselines.png"), bbox_inches="tight")
    plt.close(fig)
    print("[fig9] done")


# ----------------------------------------------------------- fig 10 data
def predict_field(domain, params):
    """(answer, field) for one problem, shape-norm reconstruction (scale = A
    for burgers/heat2d, the answer for the bending domains)."""
    model, meta = load_model(domain)
    st = meta["param_stats"]
    ans_mean, ans_std = meta["answer_stats"]
    keys = st["keys"]
    pids = torch.tensor([list(range(len(keys)))], dtype=torch.long)
    vals = torch.tensor([dataset.normalize(params, st)], dtype=torch.float32)
    with torch.no_grad():
        ans, traj = model(pids, vals)
    y = float(ans[0]) * ans_std + ans_mean
    pred = dataset.answer_inverse(domain, y)
    if meta.get("traj_norm", "global") == "shape":
        scale = float(params["A"]) if domain in ("burgers", "heat2d") else pred
    else:
        tmean, tstd = meta["traj_stats"]
        scale = float(tstd[0])
    field = traj[0, :, 0].numpy() * scale
    return pred, field


def fig10_heat2d():
    """Heat2D: exact vs predicted temperature field (canonical) + held-out."""
    print("[fig10] heat2d field + held-out predictions ...")
    n = sim.H2D_N
    params = {"A": 300.0, "k": 2.0, "l": 3.0}
    pred, field = predict_field("heat2d", params)
    x = np.linspace(0.0, 1.0, n)
    X, Y = np.meshgrid(x, x, indexing="ij")
    exact = sim.heat2d_traj(params).reshape(n, n)
    pred2 = field.reshape(n, n)

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.9))
    vmax = max(exact.max(), pred2.max())
    im0 = axes[0].pcolormesh(X, Y, exact, vmin=0, vmax=vmax, cmap="inferno")
    axes[0].set_title(f"Exact  T(x,y)  (peak {exact.max():.0f} K)", fontsize=9)
    im1 = axes[1].pcolormesh(X, Y, pred2, vmin=0, vmax=vmax, cmap="inferno")
    axes[1].set_title(f"PhysFormer  (peak {pred2.max():.0f} K, answer {pred:.0f} K)", fontsize=9)
    axes[2].pcolormesh(X, Y, np.abs(pred2 - exact), cmap="Reds")
    axes[2].set_title("|error|  (K)", fontsize=9)
    for ax in axes:
        ax.set_aspect("equal")
        ax.set_xlabel("x")
        ax.set_ylabel("y")
    fig.colorbar(im1, ax=axes[:2], shrink=0.85, pad=0.02)

    # held-out scatter
    problems = dataset.generate("heat2d", n=250, seed=77)
    model, meta = load_model("heat2d")
    preds, true = predict_batch(model, meta, problems)
    rel = np.abs(preds - true) / np.abs(true)
    rel[rel == np.inf] = 1.0
    mean_rel = float(rel.mean())
    r2 = 1 - float(((preds - true) ** 2).sum() / ((true - true.mean()) ** 2).sum())
    ax = fig.add_axes([0.05, 0.06, 0.9, 0.5])
    ax.scatter(true, preds, s=6, alpha=0.6, color="#9467bd")
    lim = [min(true.min(), preds.min()), max(true.max(), preds.max())]
    ax.plot(lim, lim, "k--", lw=0.8)
    ax.set_xlabel("Exact peak temperature (K)")
    ax.set_ylabel("PhysFormer prediction (K)")
    ax.set_title(f"Held-out peak temperature (250 problems) — rel. err {mean_rel * 100:.1f}%, "
                 f"R² = {r2:.3f}", fontsize=9)

    fig.suptitle("Figure 10 — Heat2D: steady-state Poisson field with two source modes",
                 fontsize=10)
    fig.savefig(os.path.join(OUT, "fig10_heat2d.png"), bbox_inches="tight")
    plt.close(fig)
    with open(os.path.join(OUT, "fig10_data.json"), "w") as f:
        json.dump({"mean_rel_error": mean_rel, "r2": r2, "n": len(problems),
                   "canonical": {"answer_pred": pred, "answer_exact": params["A"],
                                  "field_peak_error": float(np.max(np.abs(pred2 - exact)) /
                                                            (exact.max() + 1e-12))}}, f, indent=1)
    print(f"[fig10] done  held-out {mean_rel * 100:.1f}%  R2={r2:.3f}")


# ----------------------------------------------------------- fig 11 data
def fig11_deepxde():
    """DeepXDE per-instance PINN vs PhysFormer on the same Burgers instances."""
    print("[fig11] DeepXDE comparison ...")
    path = os.path.join(OUT, "deepxde_comparison.json")
    if not os.path.exists(path):
        print("[fig11] deepxde_comparison.json missing — run physx/deepxde_baseline.py")
        return
    with open(path) as f:
        data = json.load(f)
    insts = list(data["instances"].keys())
    labels = {"canonical": "Canonical\n(ν=0.05)", "mild": "Mild\n(ν=0.10)",
              "shock": "Shock\n(ν=0.02)"}

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
    metrics = [("answer_err", "Answer error (%) — peak velocity", "#1f77b4"),
               ("curve_err", "Field error (%) — full (x,t) solution", "#2ca02c"),
               ("phys_resid", "Governing-equation residual (FD, model grid)", "#d62728")]
    for ax, (key, title, color) in zip(axes, metrics):
        dxe, pfe = [], []
        for inst in insts:
            row = data["instances"][inst]
            dxe.append(row["deepxde"][key] * (100 if key != "phys_resid" else 1))
            pfe.append(row["physformer"][key] * (100 if key != "phys_resid" else 1))
        xpos = np.arange(len(insts))
        w = 0.36
        ax.bar(xpos - w / 2, dxe, w, color="#ff7f0e", label="DeepXDE PINN (per-instance)")
        ax.bar(xpos + w / 2, pfe, w, color=color, label="PhysFormer (one network, all)")
        ax.set_xticks(xpos)
        ax.set_xticklabels([labels[i] for i in insts], fontsize=8)
        ax.set_title(title, fontsize=9)
        if key == "phys_resid":
            ax.set_yscale("log")
        for xi, m in zip(xpos, dxe):
            ax.text(xi - w / 2, m, f"{m:.2f}", ha="center", va="bottom", fontsize=7)
        for xi, m in zip(xpos, pfe):
            ax.text(xi + w / 2, m, f"{m:.2f}", ha="center", va="bottom", fontsize=7)
        ax.legend(frameon=False, fontsize=7.5)
    fig.suptitle("Figure 11 — External PINN baseline (DeepXDE) on viscous Burgers", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(os.path.join(OUT, "fig11_deepxde.png"), bbox_inches="tight")
    plt.close(fig)
    print("[fig11] done")


# ------------------------------------------------------- fig 12: LCA architecture


def fig12_lca():
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 52)
    ax.axis("off")

    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    def box(x, y, w, h, text, fc, fs=8.5):
        b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4",
                           fc=fc, ec="#333333", lw=1.2)
        ax.add_patch(b)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color="#111111")

    def arrow(x1, y1, x2, y2, color="#444444", ls="-"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=13, color=color, lw=1.3,
                                     linestyle=ls))

    # left: law signature path (the invention)
    box(1, 40, 17, 10, "Governing equation\nEI w'' = M(x)", "#fcf8e3")
    box(1, 25, 17, 10, "Operator vocabulary\n{first_time_deriv, 2nd_space_deriv,\n self_advection, ...} (22 ops)", "#fcf8e3")
    box(1, 8, 17, 10, "Binary signature\n[0 1 0 0 1 ... 0 1]\n(per-domain law)", "#fcf8e3")
    box(22, 26, 15, 10, "Law embedding\nMLP → law vector\n(d_model)", "#f5e6f0")

    # middle: token sequence + shared transformer
    box(42, 40, 24, 10, "Input tokens: physical quantities\n(length, force, modulus, inertia,\n thickness) + z-scored values", "#eaf2fb")
    box(42, 24, 24, 12, "Shared transformer body\nLayer 1: self-attn + law cross-attn\nLayer 2: self-attn + law cross-attn\nLayer 3: self-attn + law cross-attn", "#dff0d8")
    box(42, 6, 24, 10, "Shared heads (one set for ALL laws)\nanswer head → scalar\ntrajectory head → 50×2 curve", "#d9edf7")

    # right: physics consistency
    box(72, 24, 26, 10, "Physics-consistency layer\nresidual of THIS sample's law\n(per-domain governing equation)", "#f2dede")
    box(72, 8, 26, 10, "Loss\nanswer MSE + trajectory MSE\n+ scale-free physics residual", "#e8d5f5")

    arrow(18, 45, 22.5, 43)   # equation -> embedding (via vocab)
    arrow(18, 30, 22.5, 32)   # vocab -> embedding
    arrow(18, 13, 22.5, 28)   # signature -> embedding
    arrow(37, 31, 42, 31)     # law vector -> transformer
    arrow(66, 35, 72, 31)     # body -> physics layer (trajectory)
    arrow(66, 16, 72, 18)     # heads -> loss
    ax.add_patch(FancyArrowPatch((37, 27), (42, 27), arrowstyle="-|>",
                                 mutation_scale=13, color="#888888", lw=1.2,
                                 linestyle=(0, (3, 2))))
    ax.text(39.4, 26.6, "per-layer", fontsize=6.5, color="#666666", ha="center")
    ax.text(39.4, 25.0, "conditioning", fontsize=6.5, color="#666666", ha="center")
    ax.text(52, 47, "beam and cantilever present the SAME token sequence —\n"
                     "only the law signature differs", fontsize=7, color="#333333",
            ha="center")
    ax.text(8.5, 47, "each governing equation is tokenized into a fixed\n"
                     "operator vocabulary and fed INTO the transformer",
            fontsize=7, color="#333333", ha="center")
    ax.set_title("Figure 12 — Law-Conditioned Attention: the governing equation "
                 "is part of the input\n(one shared transformer + shared heads, "
                 "six physical laws)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig12_lca.png"), bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------- fig 13: multi-law results


def fig13_multi_law():
    import json as _json
    import glob as _glob
    base = os.path.join(OUT, "..", "..", "physx", "models")
    evals = _glob.glob(os.path.join(base, "lca_real_s*.eval.json"))
    if not evals:
        print("[fig13] no LCA eval files yet, skipping")
        return
    domains = ["beam", "cantilever", "projectile", "pendulum", "spring", "rc"]
    real = {d: [] for d in domains}
    dummy = {d: [] for d in domains}
    spec = {}
    for p in evals:
        with open(p) as f:
            ev = _json.load(f)
        for d in domains:
            real[d].append(ev["generalist"][d]["ans_rel_mae"])
        # dummy evals may be written by the same runs' training (saved at the
        # same time); collect from lca_dummy eval files
    for p in _glob.glob(os.path.join(base, "lca_dummy_s*.eval.json")):
        with open(p) as f:
            ev = _json.load(f)
        for d in domains:
            dummy[d].append(ev["generalist"][d]["ans_rel_mae"])
    # specialists: mean over whatever the eval files recorded
    for p in evals:
        with open(p) as f:
            ev = _json.load(f)
        for d, r in ev.get("specialists", {}).items():
            if r:
                spec.setdefault(d, []).append(r["ans_rel_mae"])

    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    x = np.arange(len(domains))
    w = 0.26
    def col(vals):
        return np.mean(vals), np.std(vals) if len(vals) > 1 else 0.0
    r_m, r_s = zip(*[col(real[d]) for d in domains])
    d_m, d_s = zip(*[col(dummy[d]) for d in domains])
    s_m = [np.mean(spec[d]) if d in spec else float("nan") for d in domains]
    ax.bar(x - w, r_m, w, yerr=r_s, label="LCA generalist (one model)",
           color="#2a7ab5", capsize=3, alpha=0.92)
    ax.bar(x, d_m, w, yerr=d_s, label="dummy-law ablation (no equation info)",
           color="#c95b5b", capsize=3, alpha=0.92)
    ax.bar(x + w, s_m, w, label="per-domain specialist",
           color="#7a7a7a", capsize=3, alpha=0.92)
    ax.set_xticks(x)
    ax.set_xticklabels(["beam\n(5 params)", "cantilever\n(5 params)", "projectile\n(2 params)",
                        "pendulum\n(2 params)", "spring\n(3 params)", "RC\n(3 params)"])
    ax.set_ylabel("held-out answer relative error")
    ax.set_ylim(0, max(max(r_m) * 1.25, max(s_m) * 1.2, 0.35))
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    ax.set_title("Figure 13 — One transformer, six physical laws: Law-Conditioned "
                 "Attention vs. the dummy-law ablation\n(mean $\\pm$ std over 6 seeds; "
                 "beam/cantilever present identical parameter tokens)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig13_multi_law.png"), bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------- fig 14: law-swap steering


def _law_swap_panel(model, law, src, tgt, probs_src, meta_src):
    """Return a representative (median-SI) sample's curves for one direction."""
    from physx import laws as _laws
    st_src, _ = meta_src
    qids = _laws.DOMAIN_QUANTITIES[src]
    sig_src = torch.tensor(_laws.signature(src), dtype=torch.float32)
    sig_tgt = torch.tensor(_laws.signature(tgt), dtype=torch.float32)
    rows = []
    with torch.no_grad():
        for p in probs_src:
            params = p["params"]
            pids = torch.tensor([qids], dtype=torch.long)
            vals = torch.tensor([dataset.normalize(params, st_src)], dtype=torch.float32)
            peak = float(np.abs(np.array(p["traj"])).max()) or 1.0
            _, t_n = model(pids, vals, sig_src.unsqueeze(0))
            _, t_s = model(pids, vals, sig_tgt.unsqueeze(0))
            pred_native = t_n[0, :, 0].numpy() * peak
            pred_swap = t_s[0, :, 0].numpy() * peak
            truth_src = np.array(p["traj"], dtype=np.float32)[:, 0]
            truth_tgt = sim.trajectory(tgt, params, 50)[:, 0]
            def cerr(a, b):
                denom = np.abs(b).max() or 1.0
                return float(np.mean(np.abs(a - b) / denom))
            e_ss = cerr(pred_swap, truth_src)
            e_st = cerr(pred_swap, truth_tgt)
            si = (e_ss - e_st) / (e_ss + e_st + 1e-12)
            rows.append((si, params, pred_native, pred_swap, truth_src, truth_tgt))
    rows.sort(key=lambda r: r[0])
    return rows[len(rows) // 2]


def fig14_law_swap():
    import glob as _glob
    from physx import laws as _laws
    from physx.physformer import PhysFormerLCA
    from physx.train_multi import TOTAL_PARAMS
    base = os.path.join(OUT, "..", "..", "physx", "models")
    if not os.path.exists(os.path.join(OUT, "law_swap_data.json")):
        print("[fig14] law_swap_data.json missing, skipping")
        return
    data = json.load(open(os.path.join(OUT, "law_swap_data.json")))
    # regenerate held-out problems + stats (same protocol as the experiment)
    probs = {d: dataset.generate(d, n=96, seed=0 + 100 * i)
             for i, d in enumerate(["beam", "cantilever"])}
    metas = {d: (dataset.stats(probs[d], d), dataset.answer_stats(probs[d], d))
             for d in ["beam", "cantilever"]}
    val = {d: probs[d][-12:] for d in ["beam", "cantilever"]}

    fig, axes = plt.subplots(2, 2, figsize=(9.8, 7.2))
    for row, law in enumerate(("real", "dummy")):
        pt = os.path.join(base, f"lca_{law}_s0.pt")
        model = PhysFormerLCA(_laws.SHARED_HEAD_DOMAINS, _laws.VOCAB_SIZE,
                              law_mode=law, n_params=TOTAL_PARAMS, traj_hidden=64)
        model.load_state_dict(torch.load(pt, map_location="cpu", weights_only=True))
        model.eval()
        for col, (src, tgt) in enumerate((("beam", "cantilever"), ("cantilever", "beam"))):
            ax = axes[row][col]
            si, params, pn, ps, ts, tt = _law_swap_panel(model, law, src, tgt,
                                                         val[src], metas[src])
            x = np.linspace(0, params["L"], 50)
            ax.plot(x, ts, "-", color="#2a7ab5", lw=1.6, label=f"{src} exact")
            ax.plot(x, tt, "--", color="#e08a1e", lw=1.6, label=f"{tgt} exact")
            ax.plot(x, pn, "-.", color="#3f9b4f", lw=1.4, label="native pred")
            ax.plot(x, ps, "-", color="#c0392b", lw=1.8, label="swapped pred")
            ax.set_title(f"{law.upper()} model: {src} tokens + {tgt} signature  (SI={si:+.2f})",
                         fontsize=8.5)
            ax.set_xlabel("x (m)", fontsize=8)
            ax.set_ylabel("deflection w (m)", fontsize=8)
            ax.tick_params(labelsize=7)
            ax.legend(fontsize=6.5, framealpha=0.9)
    su = data["summary"]
    fig.suptitle("Figure 14 — Causal steering by the governing equation: swapping the law "
                 "signature at inference moves the prediction\n"
                 f"(beam->cantilever: steering index real {su['si']['real_median']:+.3f} vs "
                 f"dummy {su['si']['dummy_median']:+.3f}, Wilcoxon p={su['si']['wilcoxon_p']:.2e}; "
                 f"disruption real {su['disruption']['real_median']:.2f} vs "
                 f"dummy {su['disruption']['dummy_median']:.2f})", fontsize=9.5)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(OUT, "fig14_law_swap.png"), bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------- fig 15: physics vs data + few-shot


def fig15_physvdata_fewshot():
    pv = os.path.join(OUT, "physvdata_data.json")
    fs = os.path.join(OUT, "..", "..", "physx", "models", "fewshot")
    has_pv = os.path.exists(pv)
    has_fs = os.path.exists(os.path.join(fs, "real_s0_ft.eval.json"))
    if not (has_pv or has_fs):
        print("[fig15] no sweep/fewshot data yet, skipping")
        return
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
    if has_pv:
        rows = json.load(open(pv))
        ax = axes[0]
        for w, color, lab in ((0.05, "#2a7ab5", "physics-supervised (w_phys=0.05)"),
                              (0.0, "#c95b5b", "data-only (w_phys=0)")):
            ns = sorted({r["n"] for r in rows if r["w_phys"] == w})
            xs, ys, es = [], [], []
            for n in ns:
                vals = [r["field_max_err"] for r in rows if r["w_phys"] == w and r["n"] == n]
                xs.append(n)
                ys.append(np.mean(vals))
                es.append(np.std(vals) if len(vals) > 1 else 0.0)
            ax.errorbar(xs, ys, yerr=es, marker="o", capsize=3, color=color,
                        label=lab, lw=1.6)
        ax.set_xlabel("training samples (heat2d)")
        ax.set_ylabel("held-out field max error")
        ax.set_title("(a) Physics supervision vs. data-only,\n2D field fidelity", fontsize=9)
        ax.legend(fontsize=7.5)
        ax.grid(alpha=0.3)
        ax.set_xticks([64, 256])
    if has_fs:
        ax = axes[1]
        labels = {"real": "LCA (real sig)", "dummy": "dummy sig", "spec": "specialist"}
        means, stds = [], []
        names = []
        for law in ("real", "dummy", "spec"):
            ps = sorted(os.listdir(fs))
            vals = []
            for p in ps:
                if p.startswith(f"{law}_s") and p.endswith("_ft.eval.json"):
                    vals.append(json.load(open(os.path.join(fs, p)))["ans_rel_mae"])
                elif law == "spec" and p.startswith("spec_s") and p.endswith(".eval.json"):
                    vals.append(json.load(open(os.path.join(fs, p)))["ans_rel_mae"])
            if vals:
                names.append(labels[law])
                means.append(np.mean(vals))
                stds.append(np.std(vals) if len(vals) > 1 else 0.0)
        x = np.arange(len(names))
        colors = ["#2a7ab5", "#c95b5b", "#7a7a7a"]
        ax.bar(x, means, 0.5, yerr=stds, color=colors[:len(names)], capsize=3)
        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=8)
        ax.set_ylabel("held-out cantilever answer error")
        ax.set_title("(b) Few-shot adaptation to a new law:\n24 samples, 40 epochs", fontsize=9)
        ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig15_physvdata_fewshot.png"), bbox_inches="tight")
    plt.close(fig)


def all_figures():
    os.makedirs(OUT, exist_ok=True)
    fig1_architecture()
    fig2_physformer()
    fig3_convergence()
    fig4_predictions()
    fig5_deflection()
    fig6_ablations()
    fig7_cantilever()
    fig8_burgers()
    fig9_baselines()
    fig10_heat2d()
    fig11_deepxde()
    fig12_lca()
    fig13_multi_law()
    fig14_law_swap()
    fig15_physvdata_fewshot()
    print("all figures written to", OUT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="generate AGE manuscript figures")
    ap.add_argument("--only", default=None, help="comma-separated subset, e.g. fig6,fig7")
    args = ap.parse_args()
    FNS = {"fig1": fig1_architecture, "fig2": fig2_physformer, "fig3": fig3_convergence,
           "fig4": fig4_predictions, "fig5": fig5_deflection, "fig6": fig6_ablations,
           "fig7": fig7_cantilever, "fig8": fig8_burgers, "fig9": fig9_baselines,
           "fig10": fig10_heat2d, "fig11": fig11_deepxde, "fig12": fig12_lca,
           "fig13": fig13_multi_law, "fig14": fig14_law_swap,
           "fig15": fig15_physvdata_fewshot}
    if args.only:
        for name in args.only.split(","):
            FNS[name.strip()]()
    else:
        all_figures()
    print("done")
