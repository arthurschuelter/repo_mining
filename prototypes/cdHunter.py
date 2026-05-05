from github_utils import REPOSITORIOS, get_workflows, repo_name, run_analysis

# --- Constantes ---
KEY_CD = "CD Present?"
KEY_TOOL = "What is the deployment tool?"
KEY_TOOL_LOC = "Where is the deployment tool defined?"

CD_TOOLS = [
    ("pypa/gh-action-pypi-publish", "pypa/gh-action-pypi-publish"),
    ("twine", "twine"),
    ("flit publish", "flit"),
    ("poetry publish", "poetry"),
    ("hatch publish", "hatch"),
    ("uv publish", "astral_uv"),
]


def analyze_cd(repo):
    print(f"[{repo}] Analisando CD...")
    result = {
        "Repo Name": repo_name(repo),
        KEY_CD: "No",
        KEY_TOOL: "-",
        KEY_TOOL_LOC: "-",
    }

    for path, content in get_workflows(repo).items():
        content_lower = content.lower()
        for keyword, tool_name in CD_TOOLS:
            if keyword in content_lower:
                result[KEY_CD] = "Yes"
                result[KEY_TOOL] = tool_name
                result[KEY_TOOL_LOC] = f"{repo_name(repo)}/{path}"
                return result

    return result


COLUNAS = ["Repo Name", KEY_CD, KEY_TOOL, KEY_TOOL_LOC]
run_analysis(REPOSITORIOS, analyze_cd, "analise_cd_repos.csv", COLUNAS)
