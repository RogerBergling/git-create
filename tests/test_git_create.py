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
        self.assertIn("build", payload)
        self.assertIn("built_at", payload)

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

    def test_version_consistency(self) -> None:
        import runpy

        mod = runpy.run_path(str(APP), run_name="git_create_version_test")
        version = mod["VERSION"]
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"Current version: **{version}**.", readme)
        self.assertIn(f"## {version}", changelog)
        output = self.run_app("--version").stdout.strip()
        self.assertIn(f"git-create {version}", output)
        self.assertIn(mod["BUILD_NUMBER"], output)
        self.assertIn(mod["BUILD_DATE"], output)
        self.assertIn(mod["BUILD_TIME"], output)

    def test_backup_refs_are_unique(self) -> None:
        import runpy

        repo = self.make_repo()
        mod = runpy.run_path(str(APP), run_name="git_create_backup_test")
        first = mod["create_backup_ref"](repo, "same-label")
        second = mod["create_backup_ref"](repo, "same-label")
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertNotEqual(first, second)

    def test_optional_dockerignore_and_safe_fix_plan(self) -> None:
        import runpy

        repo = self.make_repo()
        mod = runpy.run_path(str(APP), run_name="git_create_dockerignore_test")
        report = mod["build_project_report"](repo, deep=False, scan_content=False)
        checks = {check.label: check for check in report.checks()}
        self.assertEqual(checks[".dockerignore"].level, "INFO")
        self.assertNotIn(".dockerignore", mod["safe_file_fix_plan"](repo))
        (repo / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
        self.assertIn(".dockerignore", mod["safe_file_fix_plan"](repo))

    def test_path_resolution_and_text_fallback(self) -> None:
        import runpy

        repo = self.make_repo()
        mod = runpy.run_path(str(APP), run_name="git_create_path_test")
        paths = mod["resolve_user_paths"](f"{repo}, {repo.parent}")
        self.assertEqual(paths[0], repo.resolve())
        self.assertEqual(paths[1], repo.parent.resolve())
        globals_dict = mod["ask_path"].__globals__
        globals_dict["choose_directory"] = lambda start, prompt: None
        globals_dict["ask"] = lambda prompt, default=None, allow_empty=False: str(repo)
        self.assertEqual(mod["ask_path"]("Directory"), repo.resolve())

    def test_exclusive_private_write(self) -> None:
        import runpy

        repo = self.make_repo()
        mod = runpy.run_path(str(APP), run_name="git_create_write_test")
        target = repo / "private.txt"
        self.assertTrue(mod["write_exclusive_text"](target, "first", 0o600))
        self.assertFalse(mod["write_exclusive_text"](target, "second", 0o600))
        self.assertEqual(target.read_text(encoding="utf-8"), "first")
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        link = repo / "private-link"
        link.symlink_to(target)
        self.assertFalse(mod["write_exclusive_text"](link, "third", 0o600))
        self.assertEqual(target.read_text(encoding="utf-8"), "first")


if __name__ == "__main__":
    unittest.main()
