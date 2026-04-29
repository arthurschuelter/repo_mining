import csv
import sys
from pathlib import Path
from collections import Counter

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

INPUT_FILE = "deployment_workflows.csv"

def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def plot(df: pd.DataFrame):
    all_kws = [k.strip() for kws in df["keywords_found"] for k in kws.split(",") if k.strip()]
    kw_counts = Counter(all_kws).most_common(14)
    kw_df = pd.DataFrame(kw_counts, columns=["keyword", "count"])

    wf_counts = Counter(df["workflow_file"].str.split("/").str[-1]).most_common(10)
    wf_df = pd.DataFrame(wf_counts, columns=["file", "count"])

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 1, figsize=(10, 10))

    sns.barplot(data=kw_df, x="keyword", y="count", ax=axes[0], palette="crest")
    axes[0].set_title("keyword frequency")
    axes[0].set_xlabel("")
    axes[0].tick_params(axis="x", rotation=40)

    sns.barplot(data=wf_df, x="count", y="file", ax=axes[1], palette="flare")
    axes[1].set_title("workflow files")
    axes[1].set_xlabel("matches")
    axes[1].set_ylabel("")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    if not Path(path).exists():
        print(f"Error: '{path}' not found. Run mine.py first.")
        sys.exit(1)
    df = load_csv(path)
    print(f"Loaded {len(df)} rows from {path}")
    plot(df)