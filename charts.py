"""
charts.py — Visualisations for "Mining Deployment Tasks in Software Repositories"
One figure per research question.

Usage
-----
  python charts.py                               # defaults
  python charts.py evidence.csv repo_summary.csv
"""

import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import seaborn as sns

EVIDENCE_FILE     = "outputs/evidence.csv"
REPO_SUMMARY_FILE = "outputs/repo_summary.csv"

PIPELINE_STAGES = [
    "version_control_system",
    "code_management_analysis",
    "build_tool",
    "continuous_integration_server",
    "testing_tool",
    "configuration_provisioning",
    "delivery_deployment",
]

STAGE_LABELS = {
    "version_control_system":          "Version Control",
    "code_management_analysis":        "Code Mgmt & Analysis",
    "build_tool":                      "Build Tool",
    "continuous_integration_server":   "CI Server",
    "testing_tool":                    "Testing",
    "configuration_provisioning":      "Config & Provisioning",
    "delivery_deployment":             "CD / Deployment",
}


# ── utilities ─────────────────────────────────────────────────────────────────

def load_csv(path):
    return pd.read_csv(path)

def split_col(series):
    return [
        item.strip()
        for cell in series.dropna()
        for item in str(cell).split(",")
        if item.strip() and item.strip() not in ("-", "nan")
    ]

def top_counts(items, n=12):
    counts = Counter(items).most_common(n)
    return pd.DataFrame(counts, columns=["label", "count"])

def yes_pct(series):
    return (series.str.strip().str.lower() == "yes").mean() * 100


# ── RQ1 — What deployment tasks are present? ─────────────────────────────────

def plot_rq1(ev, rs):
    """
    Left:  Bar — how many repos have evidence for each pipeline stage
    Right: Bar — distribution of how many stages each repo covers (1–7)
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(
        "RQ1 – What deployment tasks are present in Python package repositories?",
        fontsize=13, fontweight="bold",
    )

    total_repos = ev["repo"].nunique()

    # ── left: repos per stage ────────────────────────────────────────────────
    cat_repo = (
        ev.groupby("task_category")["repo"]
        .nunique().reset_index()
        .rename(columns={"repo": "repos"})
    )
    cat_repo["label"] = cat_repo["task_category"].map(STAGE_LABELS).fillna(
        cat_repo["task_category"].str.replace("_", " ").str.title()
    )
    # sort by defined pipeline order
    order = {s: i for i, s in enumerate(PIPELINE_STAGES)}
    cat_repo["order"] = cat_repo["task_category"].map(order).fillna(99)
    cat_repo = cat_repo.sort_values("order")

    bars = sns.barplot(
        data=cat_repo, x="repos", y="label",
        ax=axes[0], palette="crest", order=cat_repo["label"]
    )
    axes[0].set_title(f"Repos with evidence per pipeline stage\n(n = {total_repos} repos)")
    axes[0].set_xlabel("Number of repos")
    axes[0].set_ylabel("")
    axes[0].set_xlim(0, total_repos + 10)
    for bar, (_, row) in zip(axes[0].patches, cat_repo.iterrows()):
        pct = row["repos"] / total_repos * 100
        axes[0].text(
            row["repos"] + 0.5, bar.get_y() + bar.get_height() / 2,
            f'{row["repos"]}  ({pct:.0f}%)', va="center", fontsize=8
        )

    # ── right: stage count distribution ──────────────────────────────────────
    # count how many distinct stages each repo covers
    stages_per_repo = (
        ev.groupby("repo")["task_category"]
        .nunique()
        .value_counts()
        .sort_index()
        .reset_index()
    )
    stages_per_repo.columns = ["stages_covered", "repos"]

    ax = axes[1]
    sns.barplot(
        data=stages_per_repo, x="stages_covered", y="repos",
        ax=ax, palette="crest",
    )
    ax.set_title(f"How many pipeline stages does each repo cover?\n(n = {total_repos} repos)")
    ax.set_xlabel("Number of pipeline stages covered (out of 7)")
    ax.set_ylabel("Number of repos")
    for bar, (_, row) in zip(ax.patches, stages_per_repo.iterrows()):
        pct = row["repos"] / total_repos * 100
        ax.text(
            bar.get_x() + bar.get_width() / 2, row["repos"] + 0.3,
            f'{row["repos"]}\n({pct:.0f}%)', ha="center", va="bottom", fontsize=8
        )

    plt.tight_layout()
    plt.savefig("outputs/rq1_deployment_tasks.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved outputs/rq1_deployment_tasks.png")


# ── RQ2 — What tools and actions are used? ───────────────────────────────────

def plot_rq2(ev, rs):
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle(
        "RQ2 – What tools and actions are used for automated deployment?",
        fontsize=13, fontweight="bold",
    )

    # top-left: top 15 tools by distinct repos
    total_repos = ev["repo"].nunique()
    tool_df = (
        ev.drop_duplicates(subset=["repo", "normalized_tool"])
        .groupby("normalized_tool")["repo"]
        .nunique()
        .reset_index()
        .rename(columns={"repo": "repos", "normalized_tool": "label"})
        .sort_values("repos", ascending=False)
        .head(15)
        .sort_values("repos")
    )
    bars = sns.barplot(data=tool_df, x="repos", y="label", ax=axes[0, 0], palette="crest")
    axes[0, 0].set_title(f"Top 15 tools by number of repos\n(n = {total_repos} repos)")
    axes[0, 0].set_xlabel("repos")
    axes[0, 0].set_ylabel("")
    axes[0, 0].set_xlim(0, total_repos + 8)
    for bar, val in zip(bars.patches, tool_df["repos"]):
        pct = val / total_repos * 100
        axes[0, 0].text(val + 0.5, bar.get_y() + bar.get_height() / 2,
                        f"{val}  ({pct:.0f}%)", va="center", fontsize=7.5)

    # top-right: distinct tools per pipeline stage
    stage_tool = (
        ev.groupby("task_category")["normalized_tool"]
        .nunique().reset_index()
        .rename(columns={"normalized_tool": "distinct_tools"})
    )
    stage_tool["label"] = stage_tool["task_category"].map(STAGE_LABELS).fillna(
        stage_tool["task_category"].str.replace("_", " ").str.title()
    )
    order = {s: i for i, s in enumerate(PIPELINE_STAGES)}
    stage_tool["order"] = stage_tool["task_category"].map(order).fillna(99)
    stage_tool = stage_tool.sort_values("distinct_tools")
    sns.barplot(data=stage_tool, x="distinct_tools", y="label", ax=axes[0, 1], palette="flare")
    axes[0, 1].set_title("Distinct tools per pipeline stage")
    axes[0, 1].set_xlabel("distinct tools")
    axes[0, 1].set_ylabel("")

    # bottom-left: testing tools
    test_df = top_counts(split_col(rs["testing_tools"]), n=10)
    sns.barplot(data=test_df, x="count", y="label", ax=axes[1, 0], palette="mako")
    axes[1, 0].set_title("Testing tools across repos")
    axes[1, 0].set_xlabel("repos")
    axes[1, 0].set_ylabel("")

    # bottom-right: code management / linting tools
    cm_df = top_counts(split_col(rs["code_management_tools"]), n=10)
    sns.barplot(data=cm_df, x="count", y="label", ax=axes[1, 1], palette="rocket")
    axes[1, 1].set_title("Code management & linting tools across repos")
    axes[1, 1].set_xlabel("repos")
    axes[1, 1].set_ylabel("")

    plt.tight_layout()
    plt.savefig("outputs/rq2_tools_and_actions.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved outputs/rq2_tools_and_actions.png")


# ── RQ3 — How automated are deployment pipelines? ────────────────────────────

def plot_rq3(ev, rs):
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle(
        "RQ3 – How automated are deployment pipelines in Python package repositories?",
        fontsize=13, fontweight="bold",
    )

    # left: automation flag adoption rates
    flags = {
        "CI present":               yes_pct(rs["ci_present"]),
        "Testing in CI":            yes_pct(rs["testing_in_ci"]),
        "CD / deployment present":  yes_pct(rs["cd_present"]),
        "Versioning automated":     yes_pct(rs["versioning_automated"]),
    }

    flag_df = pd.DataFrame(flags.items(), columns=["flag", "pct"]).sort_values("pct")

    bars = sns.barplot(
        data=flag_df,
        x="pct",
        y="flag",
        ax=axes[0],
        palette="crest"
    )

    axes[0].set_title(f"Automation flag adoption\n(n = {len(rs)} repos)")
    axes[0].set_xlabel("% of repos")
    axes[0].set_ylabel("")
    axes[0].set_xlim(0, 115)

    for bar, val in zip(bars.patches, flag_df["pct"]):
        axes[0].text(
            val + 1,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.0f}%",
            va="center",
            fontsize=9
        )

    # middle: deployment tools (CD repos only)
    cd_repos = rs[rs["cd_present"].str.strip().str.lower() == "yes"]

    dep_df = top_counts(split_col(cd_repos["deployment_tools"]), n=10)

    bars = sns.barplot(
        data=dep_df,
        x="count",
        y="label",
        ax=axes[1],
        palette="flare"
    )

    axes[1].set_title(
        f"Deployment tools used\n(repos with CD present, n = {len(cd_repos)})"
    )
    axes[1].set_xlabel("repos")
    axes[1].set_ylabel("")

    for bar, val in zip(bars.patches, dep_df["count"]):
        axes[1].text(
            val + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{val}",
            va="center",
            fontsize=9
        )

    # right: versioning strategies
    vs_df = top_counts(split_col(rs["versioning_strategy"]), n=8)
    vs_df["pct"] = vs_df["count"] / len(rs) * 100

    bars = sns.barplot(
        data=vs_df,
        x="pct",
        y="label",
        ax=axes[2],
        palette="mako"
    )

    axes[2].set_title("Versioning strategies")
    axes[2].set_xlabel("% of repos")
    axes[2].set_ylabel("")

    for bar, val in zip(bars.patches, vs_df["pct"]):
        axes[2].text(
            val + 1,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%",
            va="center",
            fontsize=9
        )

    plt.tight_layout()
    plt.savefig("outputs/rq3_automation_levels.png", dpi=150, bbox_inches="tight")
    plt.show()

    print("Saved outputs/rq3_automation_levels.png")


# ── RQ4 — Where are deployment tasks defined? ────────────────────────────────

def plot_rq4(ev, rs):
    """
    Left:  Bar — how many repos use each file type (at least once)
    Middle: Stacked bar — for each file type, which pipeline stages does it contribute to
            (read: "repos that define stage X inside file type Y")
    Right: Heatmap — same data as middle but shown as % of repos that use that file type
           (normalised per row so you can compare file types of very different sizes)
           Each cell answers: "of repos using this file type, what % use it for stage X?"
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    fig.suptitle(
        "RQ4 – Where are deployment tasks defined in source code?",
        fontsize=13, fontweight="bold",
    )

    total_repos = ev["repo"].nunique()

    # ── left: repos per file type ─────────────────────────────────────────────
    ftype_repos = (
        ev.groupby("file_type")["repo"]
        .nunique().reset_index()
        .rename(columns={"repo": "repos"})
        .sort_values("repos", ascending=True)
    )
    bars = sns.barplot(
        data=ftype_repos, x="repos", y="file_type",
        ax=axes[0], palette="crest"
    )
    axes[0].set_title(f"Repos that use each file type\n(n = {total_repos} repos total)")
    axes[0].set_xlabel("repos")
    axes[0].set_ylabel("")
    axes[0].set_xlim(0, total_repos + 10)
    for bar, val in zip(axes[0].patches, ftype_repos["repos"]):
        pct = val / total_repos * 100
        axes[0].text(
            val + 0.3, bar.get_y() + bar.get_height() / 2,
            f"{val}  ({pct:.0f}%)", va="center", fontsize=7.5
        )

    # ── build cross table: file_type × stage (unique repos) ──────────────────
    cross = (
        ev.groupby(["file_type", "task_category"])["repo"]
        .nunique().reset_index()
        .rename(columns={"repo": "repos"})
    )
    pivot = cross.pivot(index="file_type", columns="task_category", values="repos").fillna(0)
    stage_cols = [s for s in PIPELINE_STAGES if s in pivot.columns]
    pivot = pivot[stage_cols]
    pivot.columns = [STAGE_LABELS[c] for c in stage_cols]

    # total repos per file type (for normalisation)
    ftype_totals = ev.groupby("file_type")["repo"].nunique()
    pivot = pivot.loc[pivot.index.isin(ftype_totals.index)]

    # sort rows by total repos using file type (descending)
    pivot = pivot.loc[ftype_totals.loc[pivot.index].sort_values(ascending=False).index]

    # ── middle: stacked bar — absolute repo counts ────────────────────────────
    pivot.plot(
        kind="barh", stacked=True, ax=axes[1],
        colormap="tab10", width=0.7
    )
    axes[1].set_title(
        "Repos using each file type\nfor each pipeline stage (absolute)"
    )
    axes[1].set_xlabel("repos (can overlap — one repo may use\na file type for multiple stages)")
    axes[1].set_ylabel("")
    axes[1].legend(loc="upper right", fontsize=6.5, title="Stage", title_fontsize=7)

    # ── right: heatmap — normalised by total repos ───────────────────────────
    # Each cell: % of all repos that use this file type for this stage
    norm_pivot = pivot / total_repos * 100

    ax = axes[2]
    sns.heatmap(
        norm_pivot, ax=ax,
        cmap="YlOrRd",
        linewidths=0.4, linecolor="white",
        annot=True, fmt=".0f",
        annot_kws={"size": 7},
        cbar_kws={"label": "% of all repos"},
        vmin=0, vmax=100,
    )
    ax.set_title(
        "% of all repos that use\neach file type for each pipeline stage"
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=38, labelsize=7.5)
    ax.tick_params(axis="y", labelsize=8)

    plt.tight_layout()
    plt.savefig("outputs/rq4_task_locations.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved outputs/rq4_task_locations.png")


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    evidence_path = sys.argv[1] if len(sys.argv) > 1 else EVIDENCE_FILE
    summary_path  = sys.argv[2] if len(sys.argv) > 2 else REPO_SUMMARY_FILE

    for path in (evidence_path, summary_path):
        if not Path(path).exists():
            print(f"Error: '{path}' not found.")
            sys.exit(1)

    ev = load_csv(evidence_path)
    rs = load_csv(summary_path)

    print(f"Loaded {len(ev):,} evidence rows  ({ev['repo'].nunique()} unique repos)")
    print(f"Loaded {len(rs):,} repo-summary rows")
    print()

    # plot_rq1(ev, rs)
    # plot_rq2(ev, rs)
    plot_rq3(ev, rs)
    # plot_rq4(ev, rs)