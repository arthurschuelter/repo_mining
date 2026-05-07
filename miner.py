import shutil
import subprocess
import tempfile
from pathlib import Path


class Miner:
    """Handle repository download and temporary directory lifecycle."""

    def download_repo(self, repo_url: str) -> Path | None:
        """Clone a repository into a temporary directory and return its local path."""
        temp_dir = Path(tempfile.mkdtemp(prefix="repo_mining_"))
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(temp_dir)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(result.stderr.strip())
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None

        return temp_dir

    def cleanup_repo(self, repo_root: Path | None) -> None:
        """Remove the temporary directory created for a cloned repository."""
        if repo_root:
            shutil.rmtree(repo_root, ignore_errors=True)
