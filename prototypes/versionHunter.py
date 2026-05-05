import re
import requests
from github_utils import REPOSITORIOS, HEADERS, get_file_content, repo_name, run_analysis

AUTO_VERSION_TOOLS = [
    "setuptools_scm", "hatch-vcs", "poetry-dynamic-versioning",
    "tbump", "bumpversion", "bump2version",
]

ENV_TOOLS_CHECKS = [
    ("tox.ini", "tool.tox", "tox"),
    ("noxfile.py", None, "nox"),
    (None, "tool.poetry", "poetry"),
    (None, "hatch", "hatch"),
    (None, "pdm", "pdm"),
    ("Pipfile", None, "pipenv"),
]


def get_latest_release_or_tag(repo):
    info = {"type": [], "latest_tag": ""}

    resp = requests.get(f"https://api.github.com/repos/{repo}/releases?per_page=1", headers=HEADERS)
    if resp.status_code == 200 and resp.json():
        info["type"].append("Github Releases")
        info["latest_tag"] = resp.json()[0].get("tag_name", "")

    resp = requests.get(f"https://api.github.com/repos/{repo}/tags?per_page=1", headers=HEADERS)
    if resp.status_code == 200 and resp.json():
        if "Github Releases" not in info["type"]:
            info["type"].append("Release Tags")
        if not info["latest_tag"]:
            info["latest_tag"] = resp.json()[0].get("name", "")

    return info


def analyze_env_and_version(repo):
    print(f"[{repo}] Coletando dados...")
    pyproject = get_file_content(repo, "pyproject.toml") or ""
    setup_py = get_file_content(repo, "setup.py") or ""

    # Provisioning tools
    env_tools = []
    for file_check, toml_check, label in ENV_TOOLS_CHECKS:
        has_file = file_check and get_file_content(repo, file_check)
        has_toml = toml_check and toml_check in pyproject
        if has_file or has_toml:
            env_tools.append(label)
    if not env_tools:
        env_tools.append("pip/venv")

    # Versioning automation
    all_content = pyproject + setup_py
    versioning_automated = "Yes" if any(t in all_content for t in AUTO_VERSION_TOOLS) else "No"

    # Versioning strategy
    version_info = get_latest_release_or_tag(repo)
    strategy_parts = version_info["type"]
    tag = version_info["latest_tag"]

    if tag:
        if re.search(r"^v?20[12]\d\.\d+", tag):
            strategy_parts.append("Calendar Versioning (CalVer)")
        elif re.search(r"^v?\d+\.\d+", tag):
            strategy_parts.append("Semantic Versioning")
    else:
        strategy_parts.append("Semantic Versioning (Assumed)")

    return {
        "Repo Name": repo_name(repo),
        "Configuration and Provisioning tools": ", ".join(env_tools),
        "Is Versioning automated?": versioning_automated,
        "Versioning Strategy": ", ".join(strategy_parts),
    }


COLUNAS = ["Repo Name", "Configuration and Provisioning tools", "Is Versioning automated?", "Versioning Strategy"]
run_analysis(REPOSITORIOS, analyze_env_and_version, "analise_env_versao.csv", COLUNAS)
