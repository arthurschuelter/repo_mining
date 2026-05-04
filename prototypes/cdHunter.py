from github_utils import REPOSITORIOS, get_workflows, repo_name, run_analysis

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
        "CD Present?": "No",
        "What is the deployment tool?": "-",
        "Where is the deployment tool defined?": "-",
    }

    for path, content in get_workflows(repo).items():
        content_lower = content.lower()
        for keyword, tool_name in CD_TOOLS:
            if keyword in content_lower:
                result["CD Present?"] = "Yes"
                result["What is the deployment tool?"] = tool_name
                result["Where is the deployment tool defined?"] = f"{repo_name(repo)}/{path}"
                return result  # achou, pode parar

    return result


COLUNAS = ["Repo Name", "CD Present?", "What is the deployment tool?", "Where is the deployment tool defined?"]
run_analysis(REPOSITORIOS, analyze_cd, "analise_cd_repos.csv", COLUNAS)
