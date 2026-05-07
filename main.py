import argparse
import csv
from pathlib import Path

from extractor import Evidence, Extractor
from miner import Miner
from processor import Processor

DEFAULT_OUTPUT_DIR = Path("outputs")
EVIDENCE_FIELDS = list(Evidence.__dataclass_fields__.keys())


def parse_args() -> argparse.Namespace:
    """Build and parse the command-line arguments for the mining pipeline."""
    parser = argparse.ArgumentParser(description="Mine deployment evidence from Python package repositories.")
    parser.add_argument("--repos_csv", help="CSV catalog with repo_name/repo_url columns.")
    parser.add_argument(
        "--output_dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where evidence.csv and repo_summary.csv will be written.",
    )
    return parser.parse_args()


def load_repo_records(path: str | Path) -> list[dict[str, str]]:
    """Load repository metadata from the input catalog."""
    catalog_path = Path(path)
    with catalog_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw_row in reader:
            repo_name = raw_row.get("repo_name", "")
            repo_url = raw_row.get("repo_url", "")

            if not repo_name or not repo_url:
                continue

            rows.append(
                {
                    "repo_name": repo_name,
                    "repo_url": repo_url,
                    "pypi_rank": raw_row.get("pypi_rank", "") or raw_row.get("repo_rank", ""),
                }
            )

    return rows


def process_records(
    repo_records: list[dict[str, str]],
    miner: Miner,
    extractor: Extractor,
    processor: Processor,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Run extraction and aggregation for every repository and write the output CSV files."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    data_rows: list[Evidence] = []

    for record in repo_records:
        repo_name = record["repo_name"]
        repo_url = record["repo_url"]
        print(f"\n-> Processing: {repo_name} ({repo_url})")
        repo_root = miner.download_repo(repo_url)
        if repo_root is None:
            print("  unable to access repository")
            continue

        try:
            repo_data = extractor.extract_repository(repo_name, repo_root)
            data_rows.extend(repo_data)
            print(f"  collected {len(repo_data)} data rows")
        finally:
            miner.cleanup_repo(repo_root)

    evidence_dict_rows = [item.as_dict() for item in data_rows]
    summary_rows = processor.summarize_repositories(repo_records, data_rows)

    evidence_csv = output_path / "evidence.csv"
    summary_csv = output_path / "repo_summary.csv"

    processor.write_csv(evidence_dict_rows, evidence_csv, EVIDENCE_FIELDS)
    processor.write_csv(summary_rows, summary_csv, Processor.SUMMARY_FIELDS)

    generated = {
        "evidence": evidence_csv,
        "summary": summary_csv,
    }
    return generated


def main() -> None:
    """Execute the repository mining pipeline from the command line."""
    args = parse_args()
    repo_records = load_repo_records(args.repos_csv)

    if not repo_records:
        raise SystemExit("No repositories found in the input CSV.")

    miner = Miner()
    extractor = Extractor()
    processor = Processor()
    generated = process_records(
        repo_records=repo_records,
        miner=miner,
        extractor=extractor,
        processor=processor,
        output_dir=args.output_dir,
    )

    print("\nGenerated files:")
    for name, path in generated.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
