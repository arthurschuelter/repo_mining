import requests
import base64
import time

GITHUB_TOKEN = ""

REPOSITORIOS = [
    "python-hyper/h11", "fastapi/fastapi", "pypa/wheel", "pypa/packaging",
    "kjd/idna", "fsspec/s3fs", "pyparsing/pyparsing", "tartley/colorama",
    "jpadilla/pyjwt", "python-cffi/cffi", "benjaminp/six", "aio-libs/frozenlist",
    "python-attrs/attrs", "aio-libs/multidict", "encode/httpx", "scipy/scipy",
    "boto/s3transfer", "pytest-dev/iniconfig", "stub42/pytz", "giampaolo/psutil",
    "pypa/setuptools", "aws/aws-cli", "aio-libs/aiohttp", "jmespath/jmespath.py",
    "pygments/pygments", "python-jsonschema/jsonschema-specifications",
    "python-pillow/Pillow", "boto/boto3", "pypa/virtualenv",
    "open-telemetry/opentelemetry-python"
]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

API_SLEEP = 1  # segundos entre requisições


def get_file_content(repo, path):
    """Busca o conteúdo de um arquivo na API do GitHub e decodifica de Base64."""
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        data = resp.json()
        if "content" in data:
            return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
    return None


def get_workflows(repo):
    """Lista e baixa todos os arquivos YAML dentro de .github/workflows."""
    url = f"https://api.github.com/repos/{repo}/contents/.github/workflows"
    resp = requests.get(url, headers=HEADERS)
    workflows = {}
    if resp.status_code == 200:
        for file in resp.json():
            if file["name"].endswith((".yml", ".yaml")):
                content = get_file_content(repo, file["path"])
                if content:
                    workflows[file["path"]] = content
    return workflows


def repo_name(repo):
    """Retorna só o nome do repositório (sem o owner)."""
    return repo.split("/")[-1]


def run_analysis(repos, analyze_fn, output_csv, fieldnames):
    """Loop padrão: itera repos, chama analyze_fn, salva CSV."""
    import csv

    resultados = []
    for repo in repos:
        resultados.append(analyze_fn(repo))
        time.sleep(API_SLEEP)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resultados)

    print(f"\nConcluído! Arquivo '{output_csv}' gerado com sucesso.")
