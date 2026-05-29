"""Analysis script for autoresearch runs.

Generates:
  progress.png  — joules vs experiment index (à la Karpathy)
  hypotheses.md — human-readable log of every hypothesis, prediction, and outcome
"""

import argparse
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd


def load(path="results.tsv"):
    df = pd.read_csv(path, sep="\t")
    df.index.name = "experiment"
    df = df.reset_index()
    df["experiment"] += 1  # 1-based
    return df


def plot_progress(df, out="progress.png"):
    keeps   = df[df["status"] == "keep"].copy()
    reverts = df[df["status"] == "revert"]
    noisy   = df[(df["status"] == "revert") & (df["run_quality"] == "noisy")]
    crashes = df[df["status"] == "crash"]

    # Running best (only clean keeps)
    clean_keeps = df[(df["status"] == "keep") & (df["run_quality"] == "clean")].copy()
    clean_keeps["running_best"] = clean_keeps["joules"].cummin()

    # Two-panel layout: chart on top, description table below.
    fig = plt.figure(figsize=(14, 8.5))
    fig.patch.set_facecolor("#0d1117")
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1.6], hspace=0.18)
    ax = fig.add_subplot(gs[0])
    ax_tbl = fig.add_subplot(gs[1])
    ax.set_facecolor("#0d1117")
    ax_tbl.set_facecolor("#0d1117")

    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")
    ax.tick_params(colors="#8b949e")
    ax.xaxis.label.set_color("#8b949e")
    ax.yaxis.label.set_color("#8b949e")
    ax.title.set_color("#e6edf3")

    # All reverts (clean)
    clean_reverts = reverts[reverts["run_quality"] == "clean"]
    ax.scatter(clean_reverts["experiment"], clean_reverts["joules"],
               color="#30363d", s=60, zorder=2, label="Discarded (clean)")

    # Noisy reverts
    ax.scatter(noisy["experiment"], noisy["joules"],
               color="#6e40c9", s=60, marker="x", zorder=2, label="Discarded (noisy)")

    # Crashes
    if len(crashes):
        ax.scatter(crashes["experiment"], crashes["joules"],
                   color="#da3633", s=80, marker="X", zorder=3, label="Crash")

    # Kept experiments — big enough to host a number inside
    ax.scatter(keeps["experiment"], keeps["joules"],
               color="#3fb950", s=220, zorder=4, label="Kept",
               edgecolors="#0d1117", linewidths=1.5)

    # Number each kept experiment inside its dot (K1, K2, ...) for the legend table.
    keeps = keeps.reset_index(drop=True)
    keeps["tag"] = [f"K{i+1}" for i in range(len(keeps))]
    for _, row in keeps.iterrows():
        ax.text(row["experiment"], row["joules"], row["tag"],
                fontsize=7, color="#0d1117", weight="bold",
                ha="center", va="center", zorder=6)

    # Running best step line
    if len(clean_keeps):
        xs = [1] + list(clean_keeps["experiment"]) + [df["experiment"].max()]
        ys = [clean_keeps["running_best"].iloc[0]] + \
             list(clean_keeps["running_best"]) + \
             [clean_keeps["running_best"].iloc[-1]]
        ax.step(xs, ys, where="post", color="#58a6ff", linewidth=1.5,
                zorder=3, label="Running best")

    # Title with baseline / best
    baseline = df[df["experiment"] == 1]["joules"].values[0]
    best = clean_keeps["joules"].min() if len(clean_keeps) else baseline
    reduction = 100 * (1 - best / baseline)
    ax.set_title(
        f"Energy optimisation — baseline {baseline:.2f}J → best {best:.4f}J  "
        f"({reduction:.1f}% reduction)",
        fontsize=12, pad=12
    )

    ax.set_xlabel("Experiment #", fontsize=10)
    ax.set_ylabel("Joules", fontsize=10)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:g}J"))
    ax.set_xticks(range(1, int(df["experiment"].max()) + 1))
    ax.grid(True, color="#21262d", linewidth=0.6)
    ax.legend(fontsize=8, facecolor="#161b22", edgecolor="#30363d",
              labelcolor="#8b949e", loc="upper right")

    # ---- Description table below ----
    ax_tbl.axis("off")
    ax_tbl.set_title("Kept experiments", color="#e6edf3", fontsize=10,
                     loc="left", pad=6)

    headers = ["Tag", "Exp", "Joules", "Δ vs prev best", "Change"]
    rows = []
    running = baseline
    for _, row in keeps.iterrows():
        delta = (row["joules"] - running) / running * 100
        delta_str = f"{delta:+.0f}%" if running > 0 else "—"
        running = min(running, row["joules"])
        rows.append([
            row["tag"],
            int(row["experiment"]),
            f"{row['joules']:.4f}J",
            delta_str,
            str(row["description"])[:80],
        ])

    table = ax_tbl.table(
        cellText=rows,
        colLabels=headers,
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        colWidths=[0.05, 0.05, 0.09, 0.12, 0.69],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.25)

    # Style the table to match the dark theme
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("#21262d")
        cell.set_linewidth(0.5)
        if r == 0:
            cell.set_facecolor("#161b22")
            cell.set_text_props(color="#e6edf3", weight="bold")
        else:
            cell.set_facecolor("#0d1117")
            cell.set_text_props(color="#8b949e")
            if c == 0:
                cell.set_text_props(color="#3fb950", weight="bold")

    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Saved {out}")


def write_hypotheses(df, out="hypotheses.md"):
    lines = ["# Hypothesis log\n",
             f"Total experiments: {len(df)}  ",
             f"Kept: {(df['status']=='keep').sum()}  ",
             f"Reverted: {(df['status']=='revert').sum()}  ",
             f"Prediction held: {(df['prediction_held']=='yes').sum()} / "
             f"{(df['prediction_held'].isin(['yes','no'])).sum()} "
             f"(excluding unclear)\n",
             "---\n"]

    for _, row in df.iterrows():
        status_emoji = {"keep": "✅", "revert": "❌", "crash": "💥"}.get(row["status"], "?")
        quality_tag = "" if row["run_quality"] == "clean" else " *(noisy)*"
        held_emoji = {"yes": "✓", "no": "✗", "unclear": "~", "N/A": "—"}.get(
            str(row["prediction_held"]).strip(), "?")

        lines += [
            f"## Exp {row['experiment']} — {status_emoji} {row['status'].upper()}{quality_tag}",
            f"**Commit:** `{row['commit']}`  ",
            f"**Joules:** {row['joules']:.4f}J  |  "
            f"**Wall clock:** {row['wall_clock']:.3f}s  |  "
            f"**IPC:** {row['ipc']:.2f}  |  "
            f"**Instructions:** {int(row['instructions']):,}",
            "",
            f"**Hypothesis:** {row['hypothesis']}",
            "",
            f"**Prediction:** {row['prediction']}",
            "",
            f"**Prediction held:** {held_emoji} `{row['prediction_held']}`",
            "",
            f"**What changed:** {row['description']}",
            "",
            "---\n",
        ]

    Path(out).write_text("\n".join(lines))
    print(f"Saved {out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results.tsv")
    parser.add_argument("--plot", default="progress.png")
    parser.add_argument("--hypotheses", default="hypotheses.md")
    args = parser.parse_args()

    df = load(args.results)
    plot_progress(df, args.plot)
    write_hypotheses(df, args.hypotheses)


if __name__ == "__main__":
    main()
