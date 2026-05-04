from github_utils import REPOSITORIOS, get_file_content, get_workflows, repo_name, run_analysis

CD_KEYWORDS = [
    ("pypa/gh-action-pypi-publish", "gh-action-pypi-publish"),
    ("twine", "CLI tools (twine/flit/poetry)"),
    ("flit publish", "CLI tools (twine/flit/poetry)"),
    ("poetry publish", "CLI tools (twine/flit/poetry)"),
]

AUTO_VERSION_TOOLS = ["setuptools_scm", "tbump"]
CI_KEYWORDS = ["pytest", "tox", "nox"]


def analyze_repo(repo):
    print(f"[{repo}] Analisando...")
    result = {
        "Repositorio": repo,
        "CI Testing Integrated?": "No/Manual Check",
        "CD Present?": "No",
        "Deployment Tool": "None",
        "Deployment Tool Location": "None",
        "Code Management Automated?": "No/Manual Check",
        "Provisioning Tools": "N/A",
        "Versioning Automated?": "No/Manual Check",
        "Versioning Strategy": "Check Releases (Usually SemVer)",
    }

    if get_file_content(repo, ".pre-commit-config.yaml"):
        result["Code Management Automated?"] = "Yes (pre-commit)"

    pyproject = get_file_content(repo, "pyproject.toml") or ""
    setup_py = get_file_content(repo, "setup.py") or ""
    if any(t in pyproject + setup_py for t in AUTO_VERSION_TOOLS):
        result["Versioning Automated?"] = "Yes"

    for path, content in get_workflows(repo).items():
        content_lower = content.lower()

        if any(kw in content_lower for kw in CI_KEYWORDS):
            result["CI Testing Integrated?"] = "Yes"

        for keyword, tool_name in CD_KEYWORDS:
            if keyword in content_lower:
                result["CD Present?"] = "Yes"
                result["Deployment Tool"] = tool_name
                result["Deployment Tool Location"] = path
                break

    return result


COLUNAS = [
    "Repositorio", "CI Testing Integrated?", "CD Present?",
    "Deployment Tool", "Deployment Tool Location",
    "Code Management Automated?", "Provisioning Tools",
    "Versioning Automated?", "Versioning Strategy",
]
run_analysis(REPOSITORIOS, analyze_repo, "analise_repositorios_completa.csv", COLUNAS)
