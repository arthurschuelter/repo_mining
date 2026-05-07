import csv
from collections import defaultdict
from pathlib import Path

from extractor import Evidence
import rules.candidate_files as candidates
from rules.rules import (
    PUBLISH_TOOLS,
    TASK_BUILD,
    TASK_CI_SERVER,
    TASK_CODE_MANAGEMENT,
    TASK_DEPLOYMENT,
    TASK_PROVISIONING,
    TASK_TESTING,
    TASK_VERSION_CONTROL,
    VERSION_AUTOMATION_TOOLS,
)

YES = "Yes"
NO = "No"
UNKNOWN = "-"


class Processor:
    """Aggregate evidence rows into repository summaries."""

    SUMMARY_FIELDS = [
        "repo_name",
        "repo_url",
        "pypi_rank",
        "sample_group",
        "ci_present",
        "ci_server",
        "ci_paths",
        "build_tools",
        "build_paths",
        "testing_tools",
        "testing_paths",
        "testing_in_ci",
        "cd_present",
        "deployment_tools",
        "deployment_paths",
        "code_management_tools",
        "provisioning_tools",
        "versioning_automated",
        "versioning_strategy",
    ]

    def summarize_repositories(self, repo_records: list[dict[str, str]], evidence_rows: list[Evidence]) -> list[dict[str, str]]:
        """Create one normalized summary row per repository from the mined evidence."""
        by_repo: dict[str, list[Evidence]] = defaultdict(list)
        for item in evidence_rows:
            by_repo[item.repo].append(item)

        summaries: list[dict[str, str]] = []
        for record in repo_records:
            repo_name = record["repo_name"]
            repo_url = record["repo_url"]
            evidence = by_repo.get(repo_name, [])
            summaries.append(self._summarize_repo(record, repo_name, repo_url, evidence))

        return summaries

    def write_csv(self, rows: list[dict[str, str]], path: str | Path, fieldnames: list[str] | None = None) -> None:
        """Persist rows to CSV using either the provided schema or the row keys."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if fieldnames is None:
            fieldnames = list(rows[0].keys()) if rows else []

        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            if rows:
                writer.writerows(rows)

    def _summarize_repo(
        self,
        record: dict[str, str],
        repo_name: str,
        repo_url: str,
        evidence: list[Evidence],
    ) -> dict[str, str]:
        """Aggregate all task-level evidence for a repository into a single summary row."""
        by_category: dict[str, list[Evidence]] = defaultdict(list)
        for item in evidence:
            by_category[item.task_category].append(item)

        ci_evidence = by_category[TASK_CI_SERVER]
        build_evidence = by_category[TASK_BUILD]
        testing_evidence = by_category[TASK_TESTING]
        deployment_evidence = [item for item in by_category[TASK_DEPLOYMENT] if item.normalized_tool in PUBLISH_TOOLS]
        code_mgmt_evidence = by_category[TASK_CODE_MANAGEMENT]
        provisioning_evidence = by_category[TASK_PROVISIONING]
        versioning_evidence = by_category[TASK_VERSION_CONTROL]

        ci_tools = self._sorted_tools(ci_evidence)
        build_tools = self._sorted_tools(build_evidence)
        testing_tools = self._sorted_tools(testing_evidence)
        deployment_tools = self._sorted_tools(deployment_evidence)
        code_management_tools = self._sorted_tools(code_mgmt_evidence)
        provisioning_tools = self._sorted_tools(provisioning_evidence)
        versioning_tools = {item.normalized_tool for item in versioning_evidence}

        testing_in_ci = YES if any(item.file_type in candidates.workflow_file_types for item in testing_evidence) else NO
        versioning_automated = YES if any(item.file_type in candidates.workflow_file_types for item in versioning_evidence) else NO
        versioning_strategy = self._build_versioning_strategy(versioning_tools)
        cd_present = YES if deployment_tools else NO
        ci_present = YES if ci_tools else NO

        summary = {
            "repo_name": repo_name,
            "repo_url": repo_url,
            "pypi_rank": record.get("pypi_rank", UNKNOWN) or UNKNOWN,
            "sample_group": record.get("sample_group", UNKNOWN) or UNKNOWN,
            "ci_present": ci_present,
            "ci_server": self._join_or_unknown(ci_tools),
            "ci_paths": self._join_or_unknown(self._unique_paths(ci_evidence)),
            "build_tools": self._join_or_unknown(build_tools),
            "build_paths": self._join_or_unknown(self._unique_paths(build_evidence)),
            "testing_tools": self._join_or_unknown(testing_tools),
            "testing_paths": self._join_or_unknown(self._unique_paths(testing_evidence)),
            "testing_in_ci": testing_in_ci,
            "cd_present": cd_present,
            "deployment_tools": self._join_or_unknown(deployment_tools),
            "deployment_paths": self._join_or_unknown(self._unique_paths(deployment_evidence)),
            "code_management_tools": self._join_or_unknown(code_management_tools),
            "provisioning_tools": self._join_or_unknown(provisioning_tools),
            "versioning_automated": versioning_automated,
            "versioning_strategy": versioning_strategy,
        }
        return summary

    def _build_versioning_strategy(self, versioning_tools: set[str]) -> str:
        """Convert versioning evidence into a human-readable versioning strategy label."""
        labels: list[str] = []
        if "github-releases" in versioning_tools:
            labels.append("GitHub Releases")
        if "release-tags" in versioning_tools:
            labels.append("Release Tags")
        if "semantic-versioning" in versioning_tools or versioning_tools.intersection({"python-semantic-release", "setuptools-scm", "bump2version"}):
            labels.append("Semantic Versioning")
        if "calendar-versioning" in versioning_tools:
            labels.append("Calendar Versioning (CalVer)")
        return ", ".join(labels) if labels else UNKNOWN

    def _sorted_tools(self, evidence: list[Evidence]) -> list[str]:
        """Return a sorted, unique list of normalized tools present in the evidence."""
        return sorted({item.normalized_tool for item in evidence})

    def _unique_paths(self, evidence: list[Evidence]) -> list[str]:
        """Return a sorted, unique list of file paths referenced by the evidence."""
        return sorted({item.file_path for item in evidence})

    def _join_or_unknown(self, values: list[str]) -> str:
        """Join a list of values for CSV output or fall back to the unknown marker."""
        return ", ".join(values) if values else UNKNOWN
