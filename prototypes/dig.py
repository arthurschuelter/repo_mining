from github_utils import REPOSITORIOS, get_file_content, get_workflows, repo_name, run_analysis

# --- Constantes ---
KEY_CI = "CI Testing Integrated?"
KEY_CD = "CD Present?"
KEY_DEPLOY_TOOL = "Deployment Tool"
KEY_DEPLOY_LOC = "Deployment Tool Location"
KEY_CODE_MGMT = "Code Management Automated?"
KEY_VERSIONING = "Versioning Automated?"
VAL_NO_MANUAL = "No/Manual Check"
VAL_CLI_TOOLS = "CLI tools (twine/flit/poetry)"

CD_KEYWORDS = [
    ("pypa/gh-action-pypi-publish", "gh-action-pypi-publish"),
    ("twine", VAL_CLI_TOOLS),
    ("flit publish", VAL_CLI_TOOLS),
    ("poetry publish", VAL_CLI_TOOLS),
]

AUTO_VERSION_TOOLS = ["setuptools_scm", "tbump"]
CI_KEYWORDS = ["pytest", "tox", "nox"]


def analyze_repo(repo):
    print(f"[{repo}] Analisando...")
    result = {
        "Repositorio": repo,
        KEY_CI: VAL_NO_MANUAL,
        KEY_CD: "No",
        KEY_DEPLOY_TOOL: "None",
        KEY_DEPLOY_LOC: "None",
        KEY_CODE_MGMT: VAL_NO_MANUAL,
        "Provisioning Tools": "N/A",
        KEY_VERSIONING: VAL_NO_MANUAL,
        "Versioning Strategy": "Check Releases (Usually SemVer)",
    }

    if get_file_content(repo, ".pre-commit-config.yaml"):
        result[KEY_CODE_MGMT] = "Yes (pre-commit)"

    pyproject = get_file_content(repo, "pyproject.toml") or ""
    setup_py = get_file_content(repo, "setup.py") or ""
    if any(t in pyproject + setup_py for t in AUTO_VERSION_TOOLS):
        result[KEY_VERSIONING] = "Yes"

    for path, content in get_workflows(repo).items():
        content_lower = content.lower()

        if any(kw in content_lower for kw in CI_KEYWORDS):
            result[KEY_CI] = "Yes"

        for keyword, tool_name in CD_KEYWORDS:
            if keyword in content_lower:
                result[KEY_CD] = "Yes"
                result[KEY_DEPLOY_TOOL] = tool_name
                result[KEY_DEPLOY_LOC] = path
                break

    return result


COLUNAS = [
    "Repositorio", KEY_CI, KEY_CD,
    KEY_DEPLOY_TOOL, KEY_DEPLOY_LOC,
    KEY_CODE_MGMT, "Provisioning Tools",
    KEY_VERSIONING, "Versioning Strategy",
]
run_analysis(REPOSITORIOS, analyze_repo, "analise_repositorios_completa.csv", COLUNAS)
