import csv
import re
import subprocess
import tempfile
from pathlib import Path

REPOS = [
    "https://github.com/fastapi/fastapi",
    "https://github.com/pypa/wheel",
    "https://github.com/encode/httpx",

]

OUTPUT_FILE = "deployment_workflows.csv"

WORKFLOW_INCLUDE = ["publish", "release", "deploy"]

ACTIONS_PATTERNS = [
    r"pypa/gh-action-pypi-publish[^\s\"']*",
]

CLI_PATTERNS = [
    r"\btwine upload\b",
    r"\buv publish\b",
]

TOOL_MAP = {
    "uv publish":                    "astral_uv",
    "twine upload":                  "twine",
    "pypa/gh-action-pypi-publish":   "pypa",
}


def normalize(tool: str) -> str:
    for pattern, label in TOOL_MAP.items():
        if tool.startswith(pattern):
            return label
    return tool


def extract_tools(content: str) -> list[str]:
    found = set()

    for pattern in ACTIONS_PATTERNS:
        for match in re.findall(pattern, content):
            found.add(match.strip())

    run_blocks = re.findall(r"run:\s*\|?([\s\S]*?)(?=\n\s*\w+:|$)", content)
    for block in run_blocks:
        for pattern in CLI_PATTERNS:
            match = re.search(pattern, block)
            if match:
                found.add(match.group().strip())

    return sorted(normalize(t) for t in found)


def mine_repos(repos: list[str]) -> list[dict]:
    rows = []
    for repo_url in repos:
        print(f"\n-> Cloning: {repo_url}")
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                ["git", "clone", "--depth=1", repo_url, tmpdir],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"  git clone failed:\n{result.stderr.strip()}")
                continue

            workflow_dir = Path(tmpdir) / ".github" / "workflows"
            if not workflow_dir.exists():
                print("  No .github/workflows/ found.")
                continue

            for wf_file in sorted(workflow_dir.glob("*.y*ml")):
                if not any(kw in wf_file.name.lower() for kw in WORKFLOW_INCLUDE):
                    continue

                content = wf_file.read_text(encoding="utf-8", errors="ignore")
                tools = extract_tools(content)
                rel = str(wf_file.relative_to(Path(tmpdir)))

                print(f"  {rel} | {tools or '-'}")

                rows.append({
                    "repo":          repo_url,
                    "workflow_file": rel,
                    "tools":         ", ".join(tools) if tools else "-",
                })

    return rows


def save_csv(rows: list[dict], path: str) -> None:
    if not rows:
        print("Nothing found.")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n✓ Saved {len(rows)} rows -> {path}")


if __name__ == "__main__":
    results = mine_repos(REPOS)
    save_csv(results, OUTPUT_FILE)