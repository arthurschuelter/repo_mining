"""
charts.py — Visualisations for "Mining Deployment Tasks in Software Repositories"
Produces four figures, one per research question:

  RQ1  – What deployment tasks are present?
  RQ2  – What tools and actions are used for automated deployment?
  RQ3  – How automated are deployment pipelines?
  RQ4  – Where are deployment tasks defined in source code?

Usage
-----
  python charts.py                               # defaults
  python charts.py evidence.csv repo_summary.csv
"""

import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

EVIDENCE_FILE     = "outputs/evidence.csv"
REPO_SUMMARY_FILE = "outputs/repo_summary.csv"

# Pipeline stages from Shahin et al. [1], in logical order
PIPELINE_STAGES = [
    "version_control_system",
    "code_management_analysis",
    "build_tool",
    "continuous_integration_server",
    "testing_tool",
    "configuration_provisioning",
    "continuous_delivery_deployment",
]

STAGE_LABELS = {
    "version_control_system":          "Version Control",
    "code_management_analysis":        "Code Mgmt & Analysis",
    "build_tool":                      "Build Tool",
    "continuous_integration_server":   "CI Server",
    "testing_tool":                    "Testing",
    "configuration_provisioning":      "Config & Provisioning",
    "continuous_delivery_deployment":  "CD / Deployment",
}


# ── utilities ─────────────────────────────────────────────────────────────────

def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def split_col(series: pd.Series) -> list:
    return [
        item.strip()
        for cell in series.dropna()
        for item in str(cell).split(",")
        if item.strip() and item.strip() not in ("-", "nan")
    ]


def top_counts(items: list, n: int = 12) -> pd.DataFrame:
    counts = Counter(items).most_common(n)
    return pd.DataFrame(counts, columns=["label", "count"])


def yes_pct(series: pd.Series) -> float:
    return (series.str.strip().str.lower() == "yes").mean() * 100


# ── RQ1 — What deployment tasks are present? ─────────────────────────────────

def plot_rq1(ev: pd.DataFrame, rs: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle(
        "RQ1 – What deployment tasks are present in Python package repositories?",
        fontsize=13, fontweight="bold",
    )

    # left: unique repos per pipeline stage
    cat_repo = (
        ev.groupby("task_category")["repo"]
        .nunique()
        .reset_index()
        .rename(columns={"repo": "repos"})
        .sort_values("repos", ascending=True)
    )
    cat_repo["label"] = cat_repo["task_category"].map(STAGE_LABELS).fillna(
        cat_repo["task_category"].str.replace("_", " ").str.title()
    )
    total_repos = ev["repo"].nunique()

    sns.barplot(data=cat_repo, x="repos", y="label", ax=axes[0], palette="crest")
    axes[0].set_title(f"Pipeline stage presence (unique repos, n={total_repos})")
    axes[0].set_xlabel("Number of repos")
    axes[0].set_ylabel("")
    for bar, val in zip(axes[0].patches, cat_repo["repos"]):
        pct = val / total_repos * 100
        axes[0].text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                     f"{pct:.0f}%", va="center", fontsize=8)
    axes[0].set_xlim(0, total_repos + 8)

    # right: heatmap — repo × stage coverage (top 30 repos by stage count)
    present = (
        ev.groupby(["repo", "task_category"])
        .size().reset_index(name="n")
        .assign(present=1)
        .pivot(index="repo", columns="task_category", values="present")
        .fillna(0)
    )
    stage_cols = [s for s in PIPELINE_STAGES if s in present.columns]
    present = present[stage_cols]
    present.columns = [STAGE_LABELS.get(c, c) for c in stage_cols]
    present = present.loc[present.sum(axis=1).sort_values(ascending=False).index].head(30)

    sns.heatmap(
        present, ax=axes[1], cmap="Blues",
        linewidths=0.4, linecolor="white",
        cbar_kws={"label": "Stage present"},
        yticklabels=[r.split("/")[-1] for r in present.index],
    )
    axes[1].set_title("Pipeline stage coverage per repo (top 30 by stage count)")
    axes[1].tick_params(axis="x", rotation=35)
    axes[1].tick_params(axis="y", labelsize=7)

    plt.tight_layout()
    plt.savefig("outputs/rq1_deployment_tasks.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved outputs/rq1_deployment_tasks.png")


# ── RQ2 — What tools and actions are used? ───────────────────────────────────

def plot_rq2(ev: pd.DataFrame, rs: pd.DataFrame):
    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.suptitle(
        "RQ2 – What tools and actions are used for automated deployment?",
        fontsize=13, fontweight="bold",
    )

    # top-left: top 15 normalised tools overall
    tool_df = top_counts(ev["normalized_tool"].dropna().tolist(), n=15)
    sns.barplot(data=tool_df, x="count", y="label", ax=axes[0, 0], palette="crest")
    axes[0, 0].set_title("Top 15 normalised tools (all evidence rows)")
    axes[0, 0].set_xlabel("occurrences")
    axes[0, 0].set_ylabel("")

    # top-right: unique tools per pipeline stage
    stage_tool = (
        ev.groupby("task_category")["normalized_tool"]
        .nunique().reset_index()
        .rename(columns={"normalized_tool": "unique_tools"})
        .sort_values("unique_tools", ascending=True)
    )
    stage_tool["label"] = stage_tool["task_category"].map(STAGE_LABELS).fillna(
        stage_tool["task_category"].str.replace("_", " ").str.title()
    )
    sns.barplot(data=stage_tool, x="unique_tools", y="label", ax=axes[0, 1], palette="flare")
    axes[0, 1].set_title("Unique tools per pipeline stage")
    axes[0, 1].set_xlabel("distinct tools")
    axes[0, 1].set_ylabel("")

    # bottom-left: CI server distribution
    ci_df = top_counts(split_col(rs["ci_server"]), n=10)
    sns.barplot(data=ci_df, x="count", y="label", ax=axes[1, 0], palette="mako")
    axes[1, 0].set_title("CI server distribution across repos")
    axes[1, 0].set_xlabel("repos")
    axes[1, 0].set_ylabel("")

    # bottom-right: build tools
    build_df = top_counts(split_col(rs["build_tools"]), n=12)
    sns.barplot(data=build_df, x="count", y="label", ax=axes[1, 1], palette="rocket")
    axes[1, 1].set_title("Build tools across repos")
    axes[1, 1].set_xlabel("repos")
    axes[1, 1].set_ylabel("")

    plt.tight_layout()
    plt.savefig("outputs/rq2_tools_and_actions.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved outputs/rq2_tools_and_actions.png")


# ── RQ3 — How automated are deployment pipelines? ────────────────────────────

def plot_rq3(ev: pd.DataFrame, rs: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle(
        "RQ3 – How automated are deployment pipelines in Python package repositories?",
        fontsize=13, fontweight="bold",
    )

    # left: automation flag adoption rates
    flags = {
        "CI present":              yes_pct(rs["ci_present"]),
        "Testing in CI":           yes_pct(rs["testing_in_ci"]),
        "CD / deployment present": yes_pct(rs["cd_present"]),
        "Versioning automated":    yes_pct(rs["versioning_automated"]),
    }
    flag_df = pd.DataFrame(flags.items(), columns=["flag", "pct"]).sort_values("pct")
    bars = sns.barplot(data=flag_df, x="pct", y="flag", ax=axes[0], palette="crest")
    axes[0].set_title(f"Automation flag adoption (n={len(rs)} repos)")
    axes[0].set_xlabel("% of repos")
    axes[0].set_ylabel("")
    axes[0].set_xlim(0, 115)
    for bar, val in zip(bars.patches, flag_df["pct"]):
        axes[0].text(val + 1, bar.get_y() + bar.get_height() / 2,
                     f"{val:.0f}%", va="center", fontsize=9)

    # middle: deployment tools (CD repos only)
    cd_repos = rs[rs["cd_present"].str.strip().str.lower() == "yes"]
    dep_df = top_counts(split_col(cd_repos["deployment_tools"]), n=10)
    sns.barplot(data=dep_df, x="count", y="label", ax=axes[1], palette="flare")
    axes[1].set_title(f"Deployment tools used\n(repos with CD, n={len(cd_repos)})")
    axes[1].set_xlabel("repos")
    axes[1].set_ylabel("")

    # right: versioning strategies
    vs_df = top_counts(split_col(rs["versioning_strategy"]), n=8)
    sns.barplot(data=vs_df, x="count", y="label", ax=axes[2], palette="mako")
    axes[2].set_title("Versioning strategies")
    axes[2].set_xlabel("repos")
    axes[2].set_ylabel("")

    plt.tight_layout()
    plt.savefig("outputs/rq3_automation_levels.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Saved outputs/rq3_automation_levels.png")


# ── RQ4 — Where are deployment tasks defined? ────────────────────────────────

def plot_rq4(ev: pd.DataFrame, rs: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle(
        "RQ4 – Where are deployment tasks defined in source code?",
        fontsize=13, fontweight="bold",
    )

    # left: evidence rows by file type
    ftype_df = top_counts(ev["file_type"].dropna().tolist(), n=10)
    sns.barplot(data=ftype_df, x="count", y="label", ax=axes[0], palette="crest")
    axes[0].set_title("Evidence rows by file type")
    axes[0].set_xlabel("occurrences")
    axes[0].set_ylabel("")

    # middle: unique repos per file type (with % annotation)
    total_repos = ev["repo"].nunique()
    ftype_repos = (
        ev.groupby("file_type")["repo"]
        .nunique().reset_index()
        .rename(columns={"repo": "repos"})
        .sort_values("repos", ascending=False).head(10)
        .sort_values("repos")
    )
    bars = sns.barplot(data=ftype_repos, x="repos", y="file_type", ax=axes[1], palette="flare")
    axes[1].set_title(f"Unique repos per file type (n={total_repos} repos)")
    axes[1].set_xlabel("repos")
    axes[1].set_ylabel("")
    for bar, val in zip(bars.patches, ftype_repos["repos"]):
        pct = val / total_repos * 100
        axes[1].text(val + 0.3, bar.get_y() + bar.get_height() / 2,
                     f"{pct:.0f}%", va="center", fontsize=8)
    axes[1].set_xlim(0, total_repos + 8)

    # right: heatmap — file type × pipeline stage (unique repos)
    cross = (
        ev.groupby(["file_type", "task_category"])["repo"]
        .nunique().reset_index().rename(columns={"repo": "repos"})
    )
    pivot = cross.pivot(index="file_type", columns="task_category", values="repos").fillna(0)
    top_ftypes = ev["file_type"].value_counts().head(8).index
    pivot = pivot.loc[pivot.index.isin(top_ftypes)]
    stage_cols = [s for s in PIPELINE_STAGES if s in pivot.columns]
    pivot = pivot[stage_cols]
    pivot.columns = [STAGE_LABELS.get(c, c) for c in pivot.columns]

    sns.heatmap(
        pivot, ax=axes[2], cmap="YlOrRd",
        annot=True, fmt=".0f",
        linewidths=0.4, linecolor="white",
        cbar_kws={"label": "unique repos"},
    )
    axes[2].set_title("Repos per file type × pipeline stage")
    axes[2].tick_params(axis="x", rotation=40)

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

    plot_rq1(ev, rs)
    plot_rq2(ev, rs)
    plot_rq3(ev, rs)
    plot_rq4(ev, rs)