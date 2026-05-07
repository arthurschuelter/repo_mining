import configparser
import re
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
import rules.candidate_files as candidates
from rules.rules import (
    CI_SERVER_TOOLS,
    PYPROJECT_BUILD_TOOLS_MAPPER,
    PYPROJECT_TOOLS_MAPPER,
    RULES,
    TASK_BUILD,
    TASK_CI_SERVER,
    TASK_CODE_MANAGEMENT,
    TASK_TESTING,
    TASK_VERSION_CONTROL,
    match_build_requirement,
)


@dataclass(frozen=True)
class Evidence:
    """Represent one mined rule connecting a repository file to a task/tool."""

    repo: str
    file_path: str
    file_type: str
    job_name: str
    step_name: str
    task_category: str
    normalized_tool: str
    raw_match: str

    def as_dict(self) -> dict[str, str]:
        """Convert the evidence object into a dictionary ready for CSV serialization."""
        return asdict(self)


class Extractor:
    """Discover candidate files in a repository and extract normalized deployment evidence."""


    def __init__(self):
        pass


    def discover_candidate_files(self, repo_root: Path):
        """
        Discover candidate files based on filepath.
        Iterate over a list of candidate files and files that contains specific keywords.
        """
        
        candidate_files= {}

        # Add each file that match file_patters
        for pattern in candidates.file_patterns:
            for path in repo_root.glob(pattern):
                if self._should_scan(path):
                    candidate_files[str(path.relative_to(repo_root))] = path

        keyword_tokens = ("release", "publish", "bump", "towncrier")

        # Add each file that contains names in keyword_tokens on its path
        for path in repo_root.rglob("*"):
            if not self._should_scan(path):
                continue
            name = path.name.lower()
            if any(token in name for token in keyword_tokens):
                candidate_files[str(path.relative_to(repo_root))] = path

        return sorted(candidate_files.values(), key=lambda item: str(item.relative_to(repo_root)).lower())


    def extract_repository(self, repo_name: str, repo_root: Path) -> list[Evidence]:

        repo_root = repo_root.resolve()
        evidence: list[Evidence] = []

        # Iterate over files that are candidates to find information about deployment pipeline
        for path in self.discover_candidate_files(repo_root):
            relative_path = str(path.relative_to(repo_root)).replace("\\", "/")

            # Determine the file type based on file name
            file_type = self._define_file_type(relative_path)

            # If its a pyproject.toml file
            if file_type == "pyproject":
                evidence.extend(self._extract_pyproject_evidence(repo_name, path, relative_path))
                evidence.extend(self._extract_text_evidence(repo_name, path, relative_path, file_type))
                continue

            # If its a setup.cfg file
            if file_type == "setup_cfg":
                evidence.extend(self._extract_setup_cfg_evidence(repo_name, path, relative_path))
                evidence.extend(self._extract_text_evidence(repo_name, path, relative_path, file_type))
                continue

            # If its a setup.py file
            if file_type == "setup_py":
                evidence.extend(self._extract_setup_py_evidence(repo_name, path, relative_path))
                evidence.extend(self._extract_text_evidence(repo_name, path, relative_path, file_type))
                continue

            # If its a workflow file
            if file_type in candidates.workflow_file_types:
                evidence.extend(self._build_ci_server_evidence(repo_name, relative_path, file_type))
                evidence.extend(self._extract_workflow_evidence(repo_name, path, relative_path, file_type))
                evidence.extend(self._extract_text_evidence(repo_name, path, relative_path, file_type))
                continue

            evidence.extend(self._extract_text_evidence(repo_name, path, relative_path, file_type))

        return self._remove_duplicate_evidences(evidence)


    def _extract_workflow_evidence(self, repo_name: str, path: Path, relative_path: str, file_type: str) -> list[Evidence]:
        """Extract step-level and file-level evidence from a workflow configuration file."""
        content = self._read_text(path)
        evidence: list[Evidence] = []

        for job_name, step_name, snippet in self._iter_workflow_contexts(content):
            evidence.extend(
                self._scan_patterns(
                    text=snippet,
                    repo_name=repo_name,
                    relative_path=relative_path,
                    file_type=file_type,
                    job_name=job_name,
                    step_name=step_name,
                )
            )

        evidence.extend(
            self._scan_patterns(
                text=content,
                repo_name=repo_name,
                relative_path=relative_path,
                file_type=file_type,
                job_name="",
                step_name="",
            )
        )

        return evidence


    def _extract_pyproject_evidence(self, repo_name: str, path: Path, relative_path: str) -> list[Evidence]:
        """Extract build, tooling, and versioning evidence from a pyproject file."""
        content = self._read_text(path)
        evidence: list[Evidence] = []

        try:
            data = tomllib.loads(content)
        except tomllib.TOMLDecodeError:
            return evidence

        build_system = data.get("build-system", {})
        build_backend = str(build_system.get("build-backend", "")).strip()
        backend_tool = PYPROJECT_BUILD_TOOLS_MAPPER.get(build_backend)
        if backend_tool:
            evidence.append(
                Evidence(
                    repo=repo_name,
                    file_path=relative_path,
                    file_type="pyproject",
                    job_name="",
                    step_name="",
                    task_category=TASK_BUILD,
                    normalized_tool=backend_tool,
                    raw_match=build_backend,
                )
            )

        build_requires = build_system.get("requires", [])
        for requirement in build_requires:
            tool = match_build_requirement(str(requirement))
            if tool:
                evidence.append(self._simple_evidence(repo_name, relative_path, "pyproject", TASK_BUILD, tool, requirement))

        tool_section = data.get("tool", {})
        for section_name, value in tool_section.items():
            alias = PYPROJECT_TOOLS_MAPPER.get(section_name)
            if not alias:
                continue
            normalized_tool, task_category = alias
            evidence.append(
                Evidence(
                    repo=repo_name,
                    file_path=relative_path,
                    file_type="pyproject",
                    job_name="",
                    step_name="",
                    task_category=task_category,
                    normalized_tool=normalized_tool,
                    raw_match=f"[tool.{section_name}]",
                )
            )
            if normalized_tool in {"tox", "nox"}:
                evidence.append(
                    Evidence(
                        repo=repo_name,
                        file_path=relative_path,
                        file_type="pyproject",
                        job_name="",
                        step_name="",
                        task_category=TASK_TESTING,
                        normalized_tool=normalized_tool,
                        raw_match=f"[tool.{section_name}]",
                    )
                )

        return evidence


    def _extract_setup_cfg_evidence(self, repo_name: str, path: Path, relative_path: str) -> list[Evidence]:
        """Extract structured evidence from setuptools-style setup.cfg configuration."""
        parser = configparser.ConfigParser()
        content = self._read_text(path)
        evidence: list[Evidence] = []

        try:
            parser.read_string(content)
        except configparser.Error:
            return evidence

        if parser.has_section("metadata") and parser.has_option("metadata", "name"):
            setup_value = parser.get("metadata", "name")
            if setup_value:
                evidence.append(self._simple_evidence(repo_name, relative_path, "setup_cfg", TASK_BUILD, "setuptools", setup_value))

        if parser.has_section("options") and parser.has_option("options", "use_scm_version"):
            raw_value = parser.get("options", "use_scm_version")
            if raw_value.strip().lower() in {"1", "true", "yes"}:
                evidence.append(self._simple_evidence(repo_name, relative_path, "setup_cfg", TASK_VERSION_CONTROL, "setuptools-scm", raw_value))

        for section_name in parser.sections():
            lowered = section_name.lower()
            if "tool:pytest" in lowered:
                evidence.append(self._simple_evidence(repo_name, relative_path, "setup_cfg", TASK_TESTING, "pytest", section_name))
            if "flake8" in lowered:
                evidence.append(self._simple_evidence(repo_name, relative_path, "setup_cfg", TASK_CODE_MANAGEMENT, "flake8", section_name))

        return evidence


    def _extract_setup_py_evidence(self, repo_name: str, path: Path, relative_path: str) -> list[Evidence]:
        """Extract lightweight build evidence from a legacy setup.py file."""
        content = self._read_text(path)
        evidence: list[Evidence] = []
        if re.search(r"\bsetuptools\b", content):
            evidence.append(self._simple_evidence(repo_name, relative_path, "setup_py", TASK_BUILD, "setuptools", "setuptools"))
        return evidence


    def _extract_text_evidence(
        self,
        repo_name: str,
        path: Path,
        relative_path: str,
        file_type: str,
    ) -> list[Evidence]:
        """Scan a generic text-like file for known workflow, tooling, and release signals."""
        content = self._read_text(path)
        evidence = self._scan_patterns(
            text=content,
            repo_name=repo_name,
            relative_path=relative_path,
            file_type=file_type,
            job_name="",
            step_name="",
        )

        return evidence


    def _scan_patterns(
        self,
        text: str,
        repo_name: str,
        relative_path: str,
        file_type: str,
        job_name: str,
        step_name: str,
    ) -> list[Evidence]:
        """Match the configured regex rules inside a text fragment and build evidence rows."""
        evidence: list[Evidence] = []
        for rule in RULES:
            for pattern in rule.patterns:
                for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                    evidence.append(
                        Evidence(
                            repo=repo_name,
                            file_path=relative_path,
                            file_type=file_type,
                            job_name=job_name,
                            step_name=step_name,
                            task_category=rule.task_category,
                            normalized_tool=rule.normalized_tool,
                            raw_match=match.group().strip(),
                        )
                    )
        return evidence


    def _build_ci_server_evidence(self, repo_name: str, relative_path: str, file_type: str) -> list[Evidence]:
        """
        Create a evidence row describing which CI server a file belongs to.
        """

        return [
            Evidence(
                repo=repo_name,
                file_path=relative_path,
                file_type=file_type,
                job_name="",
                step_name="",
                task_category=TASK_CI_SERVER,
                normalized_tool=CI_SERVER_TOOLS[file_type],
                raw_match=relative_path,
            )
        ]


    def _iter_workflow_contexts(self, content: str) -> list[tuple[str, str, str]]:
        """Extract workflow snippets annotated with their job and step names when available."""
        contexts = []
        lines = content.splitlines()
        current_job = ""
        current_step = ""
        inside_jobs = False
        line_number = 0

        while line_number < len(lines):
            line = lines[line_number]
            stripped = line.strip()
            indent = len(line) - len(line.lstrip(" "))

            if stripped == "jobs:":
                inside_jobs = True
                line_number += 1
                continue

            if inside_jobs and indent == 2 and stripped.endswith(":") and not stripped.startswith("-"):
                current_job = stripped[:-1].strip().strip("\"'")
                current_step = ""
                line_number += 1
                continue

            if stripped.startswith("- name:"):
                current_step = stripped.split(":", 1)[1].strip().strip("\"'")
                line_number += 1
                continue

            if indent >= 6 and stripped.startswith("name:"):
                current_step = stripped.split(":", 1)[1].strip().strip("\"'")
                line_number += 1
                continue

            if stripped.startswith("uses:"):
                contexts.append((current_job, current_step, stripped.split(":", 1)[1].strip()))
                line_number += 1
                continue

            if stripped.startswith("run:"):
                remainder = stripped.split(":", 1)[1].strip()
                if remainder in {"", "|", ">", "|-", ">-"}:
                    block_lines: list[str] = []
                    base_indent = indent
                    line_number += 1
                    while line_number < len(lines):
                        candidate = lines[line_number]
                        candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                        if candidate.strip() and candidate_indent <= base_indent:
                            break
                        block_lines.append(candidate.strip())
                        line_number += 1
                    contexts.append((current_job, current_step, "\n".join(block_lines)))
                    continue

                contexts.append((current_job, current_step, remainder))
                line_number += 1
                continue

            line_number += 1

        return contexts


    def _define_file_type(self, relative_path: str) -> str:
        """
        Map a file name to its type.
        """

        lowered = relative_path.lower()
        file_name = Path(relative_path).name.lower()

        for file_type, rule in candidates.file_type_mapper.items():
            if any(lowered.startswith(prefix) for prefix in rule.get("startswith", ())):
                return file_type
            if lowered in rule.get("equals", ()):
                return file_type
            if any(lowered.endswith(suffix) for suffix in rule.get("endswith", ())):
                return file_type
            if any(token in file_name for token in rule.get("name_contains", ())):
                return file_type
        return "text"


    def _simple_evidence(
        self,
        repo_name: str,
        relative_path: str,
        file_type: str,
        task_category: str,
        normalized_tool: str,
        raw_match: str,
    ) -> Evidence:
        """Create a simple evidence row for structured config discoveries."""
        return Evidence(
            repo=repo_name,
            file_path=relative_path,
            file_type=file_type,
            job_name="",
            step_name="",
            task_category=task_category,
            normalized_tool=normalized_tool,
            raw_match=raw_match,
        )


    def _read_text(self, path: Path) -> str:
        """Read a text file using UTF-8 with best-effort error handling."""
        return path.read_text(encoding="utf-8", errors="ignore")


    def _remove_duplicate_evidences(self, evidence: list[Evidence]) -> list[Evidence]:
        """Remove duplicate evidence rows while preserving unique signal identities."""
        unique = {
            (
                item.repo,
                item.file_path,
                item.file_type,
                item.job_name,
                item.step_name,
                item.task_category,
                item.normalized_tool,
                item.raw_match,
            ): item
            for item in evidence
        }
        return sorted(
            unique.values(),
            key=lambda item: (
                item.repo.lower(),
                item.file_path.lower(),
                item.task_category,
                item.normalized_tool,
                item.job_name.lower(),
                item.step_name.lower(),
                item.raw_match.lower(),
            ),
        )


    def _should_scan(self, path: Path) -> bool:
        """Filter out directories, excluded locations, large files, and excluded extensions."""
        if not path.is_file():
            return False
        if any(part in candidates.discarded_files for part in path.parts):
            return False
        if path.suffix.lower() not in candidates.possible_file_extensions:
            return False
        return True
