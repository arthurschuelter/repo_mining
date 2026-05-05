# Prototype Scripts

These scripts were developed during the exploratory phase of our MSR
study on deployment pipeline characterization in Python package
repositories (RQ1–RQ4).

They use the GitHub REST API to investigate deployment signals and
informed the design of the formal `repo_mining` pipeline, particularly:

| Script | Informed component |
|---|---|
| `dig.py` | Overall pipeline architecture |
| `cdHunter.py` | `TASK_DEPLOYMENT` rules in `rules/rules.py` |
| `linterHUnter.py` | `TASK_CODE_MANAGEMENT` rules in `rules/rules.py` |
| `versionHunter.py` | `TASK_VERSION_CONTROL` rules + `Processor` logic |

> ⚠️ Tokens have been removed. Do not commit API credentials.
