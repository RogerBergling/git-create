"""Black-box tests for the single-file git-create application.

Run with:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "git-create"


class GitCreateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="git-create-test-")
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["NO_COLOR"] = "1"
        self.env["GIT_TERMINAL_PROMPT"] = "0"
        subprocess.run(
            ["git", "config", "--file", str(self.home / ".gitconfig"), "user.name", "Test User"],
            check=True,
        )
        subprocess.run(
            ["git", "config", "--file", str(self.home / ".gitconfig"), "user.email", "test@example.com"],
            check=True,
        )
        subprocess.run(
            ["git", "config", "--file", str(self.home / ".gitconfig"), "init.defaultBranch", "main"],
            check=True,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_app(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(APP), "--no-color", *args],
            cwd=str(cwd or ROOT),
            env=self.env,
            text=True,
            capture_output=True,
            timeout=60,
        )

    def make_repo(self) -> Path:
        repo = Path(self.temp.name) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        (repo / "README.md").write_text("# test\n", encoding="utf-8")
        (repo / ".gitignore").write_text(".env\n.env.*\n!.env.example\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md", ".gitignore"], cwd=repo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qm", "init"],
            cwd=repo,
            check=True,
        )
        return repo

    def test_version(self) -> None:
        result = self.run_app("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn("git-create", result.stdout)

    def test_non_repository_exit_code(self) -> None:
        result = self.run_app("check", "--offline", str(Path(self.temp.name) / "missing"))
        self.assertEqual(result.returncode, 2)

    def test_check_json(self) -> None:
        repo = self.make_repo()
        result = self.run_app("check", "--offline", "--json", str(repo))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["summary"]["FAIL"], 0)
        self.assertIn("sections", payload)

    def test_info_json(self) -> None:
        repo = self.make_repo()
        result = self.run_app("info", "--json", str(repo))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["branch"], "main")
        self.assertIn("remotes", payload)
        self.assertNotIn("origin", payload["remote_branches"])
        self.assertIn("worktrees", payload)
        self.assertIn("submodules", payload)

    def test_scan_json(self) -> None:
        repo = self.make_repo()
        result = self.run_app("scan", "--json", str(repo.parent))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["repositories"]), 1)
        self.assertEqual(payload["repositories"][0]["name"], "repo")

    def test_history_secret_detection(self) -> None:
        repo = self.make_repo()
        leaked = repo / "leaked.txt"
        leaked.write_text("AKIA" + "ABCDEFGHIJKLMNOP" + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "leaked.txt"], cwd=repo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qm", "secret"],
            cwd=repo,
            check=True,
        )
        leaked.unlink()
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qam", "remove"],
            cwd=repo,
            check=True,
        )
        result = self.run_app("secrets", "--json", str(repo))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["findings"])

    def test_untracked_secret_is_reported(self) -> None:
        repo = self.make_repo()
        (repo / "notes.txt").write_text("token=AKIA" + "ABCDEFGHIJKLMNOP" + "\n", encoding="utf-8")
        result = self.run_app("check", "--offline", "--json", str(repo))
        payload = json.loads(result.stdout)
        labels = [
            check["label"]
            for section in payload["sections"]
            for check in section["checks"]
        ]
        self.assertIn("Potential secrets in untracked files", labels)

    def test_compiled_module_helpers(self) -> None:
        import runpy

        mod = runpy.run_path(str(APP), run_name="git_create_test")
        self.assertTrue(mod["is_sensitive_name"](".env"))
        self.assertFalse(mod["is_sensitive_name"](".env.example"))
        self.assertTrue(mod["dockerignore_covers"](".git\n.env\n*.pem\n", ".git/config"))
        self.assertIn("mit", mod["LICENSE_TEMPLATES"])
        self.assertIn("Managed by git-create", mod["PRE_COMMIT_HOOK"])


if __name__ == "__main__":
    unittest.main()
