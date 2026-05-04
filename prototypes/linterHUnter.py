from github_utils import REPOSITORIOS, get_workflows

LINTERS = ["flake8", "black", "ruff", "isort", "mypy", "pylint"]

print("Iniciando varredura por linters nos workflows...\n" + "-" * 50)

for repo in REPOSITORIOS:
    print(f"[{repo}] Buscando...")
    encontrados = [
        linter
        for path, content in get_workflows(repo).items()
        for linter in LINTERS
        if linter in content.lower()
    ]
    encontrados = list(dict.fromkeys(encontrados))  # remove duplicatas mantendo ordem

    if encontrados:
        print(f"  ✅ YES (CI automated) -> Ferramentas: {', '.join(encontrados)}")
    else:
        print(f"  ❌ NO -> Nenhuma ferramenta padrão encontrada nos workflows.")

    import time; time.sleep(1)

print("\n" + "-" * 50 + "\nVarredura concluída!")
