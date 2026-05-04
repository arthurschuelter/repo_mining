from dataclasses import dataclass

TASK_VERSION_CONTROL = "version_control_system"
TASK_CODE_MANAGEMENT = "code_management_analysis"
TASK_BUILD = "build_tool"
TASK_CI_SERVER = "continuous_integration_server"
TASK_TESTING = "testing_tool"
TASK_PROVISIONING = "configuration_provisioning"
TASK_DEPLOYMENT = "delivery_deployment"

PUBLISH_TOOLS = {
    "astral_uv",
    "flit",
    "hatch",
    "poetry",
    "pypa/gh-action-pypi-publish",
    "twine",
}

VERSION_AUTOMATION_TOOLS = {
    "bump2version",
    "python-semantic-release",
    "release-drafter",
    "setuptools-scm",
    "towncrier",
}

VERSION_STRATEGY_TOOLS = {
    "calendar-versioning",
    "github-releases",
    "release-tags",
    "semantic-versioning",
}

CI_SERVER_TOOLS = {
    "github_actions": "GitHub Actions",
    "circleci": "CircleCI",
    "travis_ci": "Travis CI",
    "azure_pipelines": "Azure Pipelines",
    "jenkins": "Jenkins",
}

BUILD_TOOLS = (
    "setuptools",
    "hatchling",
    "flit",
    "pdm-backend",
    "meson",
    "poetry-core"
)

PYPROJECT_BUILD_TOOLS_MAPPER= {
    "flit_core.buildapi": "flit",
    "hatchling.build": "hatchling",
    "mesonpy": "meson",
    "pdm.backend": "pdm-backend",
    "poetry.core.masonry.api": "poetry-core",
    "setuptools.build_meta": "setuptools",
    "setuptools.build_meta:__legacy__": "setuptools",
}

PYPROJECT_TOOLS_MAPPER = {
    "black": ("black", TASK_CODE_MANAGEMENT),
    "coverage": ("coverage", TASK_TESTING),
    "hatch": ("hatch", TASK_PROVISIONING),
    "isort": ("isort", TASK_CODE_MANAGEMENT),
    "mypy": ("mypy", TASK_CODE_MANAGEMENT),
    "nox": ("nox", TASK_PROVISIONING),
    "pdm": ("pdm", TASK_PROVISIONING),
    "pre-commit": ("pre-commit", TASK_CODE_MANAGEMENT),
    "pylint": ("pylint", TASK_CODE_MANAGEMENT),
    "pyright": ("pyright", TASK_CODE_MANAGEMENT),
    "pytest": ("pytest", TASK_TESTING),
    "ruff": ("ruff", TASK_CODE_MANAGEMENT),
    "semantic_release": ("python-semantic-release", TASK_VERSION_CONTROL),
    "setuptools_scm": ("setuptools-scm", TASK_VERSION_CONTROL),
    "towncrier": ("towncrier", TASK_VERSION_CONTROL),
    "tox": ("tox", TASK_PROVISIONING),
}

@dataclass(frozen=True)
class Rule:
    """Describe a text pattern that maps to a normalized tool and task category."""
    patterns: tuple[str, ...]
    normalized_tool: str
    task_category: str

RULES = (
    Rule((r"pypa/gh-action-pypi-publish[^\s\"']*",), "pypa/gh-action-pypi-publish", TASK_DEPLOYMENT),
    Rule((r"astral-sh/setup-uv[^\s\"']*",), "astral-sh/setup-uv", TASK_PROVISIONING),
    Rule((r"actions/setup-python[^\s\"']*",), "actions/setup-python", TASK_PROVISIONING),
    Rule((r"release-drafter/release-drafter[^\s\"']*",), "release-drafter", TASK_VERSION_CONTROL),
    Rule((r"\btwine\s+upload\b",), "twine", TASK_DEPLOYMENT),
    Rule((r"\buv\s+publish\b",), "astral_uv", TASK_DEPLOYMENT),
    Rule((r"\bflit\s+publish\b",), "flit", TASK_DEPLOYMENT),
    Rule((r"\bhatch\s+publish\b",), "hatch", TASK_DEPLOYMENT),
    Rule((r"\bpoetry\s+publish\b",), "poetry", TASK_DEPLOYMENT),
    Rule((r"\bpython\s+-m\s+build\b", r"\bpython\s+setup\.py\s+sdist\b"), "build", TASK_BUILD),
    Rule((r"\bpytest\b",), "pytest", TASK_TESTING),
    Rule((r"\bunittest\b",), "unittest", TASK_TESTING),
    Rule((r"\bcoverage\b",), "coverage", TASK_TESTING),
    Rule((r"\btox\b",), "tox", TASK_TESTING),
    Rule((r"\btox\b",), "tox", TASK_PROVISIONING),
    Rule((r"\bnox\b",), "nox", TASK_TESTING),
    Rule((r"\bnox\b",), "nox", TASK_PROVISIONING),
    Rule((r"\bpre-commit\b",), "pre-commit", TASK_CODE_MANAGEMENT),
    Rule((r"\bruff\b",), "ruff", TASK_CODE_MANAGEMENT),
    Rule((r"\bblack\b",), "black", TASK_CODE_MANAGEMENT),
    Rule((r"\bisort\b",), "isort", TASK_CODE_MANAGEMENT),
    Rule((r"\bflake8\b",), "flake8", TASK_CODE_MANAGEMENT),
    Rule((r"\bmypy\b",), "mypy", TASK_CODE_MANAGEMENT),
    Rule((r"\bpyright\b",), "pyright", TASK_CODE_MANAGEMENT),
    Rule((r"\bpylint\b",), "pylint", TASK_CODE_MANAGEMENT),
    Rule((r"\bpip\b",), "pip", TASK_PROVISIONING),
    Rule((r"\bvenv\b", r"\bvirtualenv\b"), "venv", TASK_PROVISIONING),
    Rule((r"\bhatch\b",), "hatch", TASK_PROVISIONING),
    Rule((r"\bpdm\b",), "pdm", TASK_PROVISIONING),
    Rule((r"\bbump2version\b",), "bump2version", TASK_VERSION_CONTROL),
    Rule((r"\bsetuptools[-_]?scm\b",), "setuptools-scm", TASK_VERSION_CONTROL),
    Rule((r"\bpython-semantic-release\b", r"\bsemantic-release\b"), "python-semantic-release", TASK_VERSION_CONTROL),
    Rule((r"\btowncrier\b",), "towncrier", TASK_VERSION_CONTROL),
    Rule((r"\bsemantic versioning\b", r"\bsemver\b"), "semantic-versioning", TASK_VERSION_CONTROL),
    Rule((r"\bcalendar versioning\b", r"\bcalver\b"), "calendar-versioning", TASK_VERSION_CONTROL),
    Rule((r"(^|\n)\s*release\s*:",), "github-releases", TASK_VERSION_CONTROL),
    #Rule((r"(^|\n)\s*workflow_dispatch\s*:",), "manual-dispatch", TASK_VERSION_CONTROL),
    Rule((r"\brefs/tags\b|(^|\n)\s*tags\s*:",), "release-tags", TASK_VERSION_CONTROL)
)

def match_build_requirement(requirement: str) -> str | None:
    """Map a build-system requirement string to the normalized tool used by the miner."""
    lowered = requirement.lower()
    for tool in BUILD_TOOLS:
        if tool in lowered:
            return tool
    return None
