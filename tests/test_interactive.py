"""Integration-style tests for interactive menu actions.

These tests load the single-file app with runpy, replace prompts, and use
temporary repositories. They do not contact GitHub.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import runpy
import subprocess
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "git-create"


class InteractiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="git-create-interactive-")
        base = Path(self.temp.name)
        self.home = base / "home"
        self.repo = base / "repo"
        self.home.mkdir()
        self.repo.mkdir()
        self.original_env = os.environ.copy()
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["NO_COLOR"] = "1"
        os.environ["HOME"] = str(self.home)
        subprocess.run(["git", "config", "--file", str(self.home / ".gitconfig"), "user.name", "Test User"], check=True)
        subprocess.run(["git", "config", "--file", str(self.home / ".gitconfig"), "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.repo, check=True)
        (self.repo / "README.md").write_text("# test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qm", "init"],
            cwd=self.repo,
            check=True,
        )

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)
        self.temp.cleanup()

    def load(self) -> dict:
        return runpy.run_path(str(APP), run_name="git_create_interactive")

    def patch_globals(self, method, ask=None, confirm=None, ask_path=None) -> None:
        globals_dict = method.__globals__
        if ask:
            globals_dict["ask"] = ask
        if confirm:
            globals_dict["confirm"] = confirm
        if ask_path:
            globals_dict["ask_path"] = ask_path

    def install_fake_gh(self):
        fakebin = Path(self.temp.name) / "bin"
        fakebin.mkdir(exist_ok=True)
        log = Path(self.temp.name) / "gh.log"
        payload = Path(self.temp.name) / "gh.payload"
        secret = Path(self.temp.name) / "gh.secret"
        fake = fakebin / "gh"
        fake.write_text(
            "#!/bin/sh\n"
            'printf \'%s\\n\' "$*" >> "$GH_LOG"\n'
            'if [ "$1" = "auth" ]; then\n'
            '  printf \'github.com\\n  Logged in to github.com account test\\n\'\n'
            '  exit 0\n'
            'fi\n'
            'if [ "$1" = "repo" ] && [ "$2" = "create" ]; then\n'
            '  name="$3"\n'
            '  git init -q --bare -b main "$PWD/$name.git"\n'
            '  git clone -q "$PWD/$name.git" "$PWD/$name" 2>/dev/null\n'
            '  exit 0\n'
            'fi\n'
            'if [ "$1" = "api" ]; then\n'
            '  case "$*" in\n'
            '    *"/commits/"*) printf \'{"verified":true,"reason":"valid"}\\n\' ;;\n'
            '    *"--method PUT"*) cat > "$GH_PAYLOAD"; printf \'{}\\n\' ;;\n'
            '    *) printf \'{}\\n\' ;;\n'
            "  esac\n"
            'elif [ "$1" = "secret" ]; then\n'
            '  case "$2" in\n'
            '    set) cat > "$GH_SECRET"; printf \'stored\\n\' ;;\n'
            '    list) printf \'EXISTING_SECRET\\n\' ;;\n'
            '    delete) printf \'deleted\\n\' ;;\n'
            "  esac\n"
            "fi\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        os.environ["PATH"] = str(fakebin) + os.pathsep + os.environ.get("PATH", "")
        os.environ["GH_LOG"] = str(log)
        os.environ["GH_PAYLOAD"] = str(payload)
        os.environ["GH_SECRET"] = str(secret)
        return log, payload, secret

    def test_remote_add_and_remove(self) -> None:
        mod = self.load()
        remote = Path(self.temp.name) / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        app = mod["App"]()
        app.project = self.repo
        options = iter(["2", "5", "0"])

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Choose an option"):
                return next(options)
            if prompt.startswith('Type "REMOVE REMOTE'):
                return "REMOVE REMOTE origin"
            if prompt.startswith("New remote name"):
                return "origin"
            if prompt.startswith("Remote URL"):
                return str(remote)
            if prompt.startswith("Remote to remove"):
                return "origin"
            return default if default is not None else ""

        self.patch_globals(mod["App"].remotes_action, ask=ask, confirm=lambda p, d=False: True)
        app.remotes_action()
        self.assertEqual(mod["remote_urls"](self.repo), {})

    def test_remote_branch_rename(self) -> None:
        mod = self.load()
        remote = Path(self.temp.name) / "rename-remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-q", "-u", "origin", "main"], cwd=self.repo, check=True)
        subprocess.run(["git", "branch", "feature"], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-q", "-u", "origin", "feature"], cwd=self.repo, check=True)
        subprocess.run(["git", "fetch", "-q", "origin"], cwd=self.repo, check=True)
        app = mod["App"]()
        app.project = self.repo

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Remote branch to rename"):
                return "origin/feature"
            if prompt.startswith("New remote branch name"):
                return "renamed-feature"
            if prompt.startswith('Type "DELETE REMOTE'):
                return "DELETE REMOTE origin/feature"
            return default if default is not None else ""

        self.patch_globals(mod["App"].rename_remote_branch, ask=ask, confirm=lambda p, d=False: True)
        app.rename_remote_branch(self.repo)
        heads = subprocess.run(
            ["git", "--git-dir", str(remote), "for-each-ref", "--format=%(refname:short)", "refs/heads"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.split()
        self.assertIn("main", heads)
        self.assertIn("renamed-feature", heads)
        self.assertNotIn("feature", heads)
        backups = mod["git_out"](self.repo, "for-each-ref", "--format=%(refname)", "refs/git-create-backups")
        self.assertIn("before-remote-rename-feature", backups)

    def test_scenario_a_creates_local_initial_commit(self) -> None:
        mod = self.load()
        self.install_fake_gh()
        app = mod["App"]()
        app.project = None
        parent = Path(self.temp.name)

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Description"):
                return "demo repository"
            return default if default is not None else ""

        globals_dict = mod["App"].scenario_a.__globals__
        globals_dict["ask_path"] = lambda prompt, default=None, **kwargs: parent
        globals_dict["ask_repo_name"] = lambda prompt, default: "new-project"
        globals_dict["ask_visibility"] = lambda default: "private"
        globals_dict["ask"] = ask
        globals_dict["confirm"] = lambda prompt, default=False: "Run a full verification" not in prompt
        app.scenario_a()
        target = parent / "new-project"
        remote = parent / "new-project.git"
        self.assertTrue((target / "README.md").is_file())
        self.assertTrue((target / ".gitignore").is_file())
        shown = subprocess.run(
            ["git", "--git-dir", str(remote), "show", "main:README.md"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn("# new-project", shown)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(status, "")

    def test_github_commit_verification_fallback(self) -> None:
        mod = self.load()
        self.install_fake_gh()
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:owner/repo.git"],
            cwd=self.repo,
            check=True,
        )
        sha = mod["git_out"](self.repo, "rev-parse", "HEAD")
        verification = mod["github_commit_verification"](self.repo, "owner", "repo", sha)
        self.assertIsNotNone(verification)
        self.assertTrue(verification["verified"])

    def test_scan_dispatches_batch_fix(self) -> None:
        mod = self.load()
        app = mod["App"]()
        app.project = self.repo
        calls = []
        app.batch_fix_repos = lambda repos: calls.append(list(repos))

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Maximum depth"):
                return "3"
            if prompt.startswith("Number to activate"):
                return "f"
            return default if default is not None else ""

        globals_dict = mod["App"].scan_action.__globals__
        globals_dict["ask_scan_paths"] = lambda prompt, default=None: [Path(self.temp.name)]
        globals_dict["ask"] = ask
        globals_dict["print_scan_results"] = lambda *args, **kwargs: None
        app.scan_action()
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0])

    def test_scan_multiple_roots_collects_all_repositories(self) -> None:
        mod = self.load()
        roots = []
        for name in ("alpha", "beta"):
            repo = Path(self.temp.name) / "roots" / name
            repo.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            (repo / "README.md").write_text(f"# {name}\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qm", "init"],
                cwd=repo,
                check=True,
            )
            roots.append(repo)
        app = mod["App"]()
        app.project = self.repo
        calls = []
        app.batch_status_repos = lambda repos: calls.append(list(repos))

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Maximum depth"):
                return "3"
            if prompt.startswith("Number to activate"):
                return "s"
            return default if default is not None else ""

        globals_dict = mod["App"].scan_action.__globals__
        globals_dict["ask_scan_paths"] = lambda prompt, default=None: roots
        globals_dict["ask"] = ask
        globals_dict["print_scan_results"] = lambda *args, **kwargs: None
        app.scan_action()
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(calls[0]), 2)

    def test_batch_safe_file_fixes(self) -> None:
        mod = self.load()
        app = mod["App"]()
        app.project = self.repo
        self.patch_globals(mod["App"].batch_fix_repos, confirm=lambda p, d=False: True)
        app.batch_fix_repos([{"path": str(self.repo), "name": self.repo.name}])
        self.assertTrue((self.repo / ".gitignore").is_file())
        self.assertFalse((self.repo / ".dockerignore").exists())
        for name in (".editorconfig", ".gitattributes"):
            self.assertFalse((self.repo / name).exists(), name)
        self.assertIn("*.pem", (self.repo / ".gitignore").read_text(encoding="utf-8"))
        (self.repo / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
        app.batch_fix_repos([{"path": str(self.repo), "name": self.repo.name}])
        self.assertTrue((self.repo / ".dockerignore").is_file())
        self.assertIn(".env", (self.repo / ".dockerignore").read_text(encoding="utf-8"))
        (self.repo / ".dockerignore").write_text(".git\n", encoding="utf-8")
        app.batch_fix_repos([{"path": str(self.repo), "name": self.repo.name}])
        repaired = (self.repo / ".dockerignore").read_text(encoding="utf-8")
        self.assertIn(".git\n", repaired)
        self.assertIn(".env", repaired)

    def test_batch_dry_run_makes_no_changes(self) -> None:
        mod = self.load()
        app = mod["App"](dry_run=True)
        app.project = self.repo
        app.batch_fix_repos([{"path": str(self.repo), "name": self.repo.name}])
        self.assertFalse((self.repo / ".gitignore").exists())

    def test_batch_push_dry_run_does_not_push(self) -> None:
        mod = self.load()
        remote = self.add_origin()
        (self.repo / "dry-run-push.txt").write_text("not pushed\n", encoding="utf-8")
        subprocess.run(["git", "add", "dry-run-push.txt"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qm", "dry run"],
            cwd=self.repo,
            check=True,
        )
        app = mod["App"](dry_run=True)
        app.project = self.repo
        app.batch_push_repos([{"path": str(self.repo), "name": self.repo.name}])
        result = subprocess.run(
            ["git", "--git-dir", str(remote), "show", "main:dry-run-push.txt"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_batch_status_reports_untracked_files(self) -> None:
        mod = self.load()
        (self.repo / "visible-status.txt").write_text("untracked\n", encoding="utf-8")
        app = mod["App"]()
        app.project = self.repo
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            app.batch_status_repos([{"path": str(self.repo), "name": self.repo.name}])
        self.assertIn("visible-status.txt", output.getvalue())

    def test_batch_pull_fast_forward(self) -> None:
        mod = self.load()
        remote = self.add_origin()
        clone = Path(self.temp.name) / "batch-clone"
        subprocess.run(["git", "clone", "-q", "-b", "main", str(remote), str(clone)], check=True)
        (clone / "remote-update.txt").write_text("from remote\n", encoding="utf-8")
        subprocess.run(["git", "add", "remote-update.txt"], cwd=clone, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qm", "remote update"],
            cwd=clone,
            check=True,
        )
        subprocess.run(["git", "push", "-q", "origin", "main"], cwd=clone, check=True)
        app = mod["App"]()
        app.project = self.repo
        self.patch_globals(mod["App"].batch_pull_repos, confirm=lambda p, d=False: True)
        app.batch_pull_repos([{"path": str(self.repo), "name": self.repo.name}])
        self.assertTrue((self.repo / "remote-update.txt").is_file())

    def test_batch_push_ahead_commit(self) -> None:
        mod = self.load()
        remote = self.add_origin()
        (self.repo / "local-update.txt").write_text("from local\n", encoding="utf-8")
        subprocess.run(["git", "add", "local-update.txt"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qm", "local update"],
            cwd=self.repo,
            check=True,
        )
        app = mod["App"]()
        app.project = self.repo
        self.patch_globals(
            mod["App"].batch_push_repos,
            ask=lambda prompt, default=None, allow_empty=False: "PUSH ALL",
        )
        app.batch_push_repos([{"path": str(self.repo), "name": self.repo.name}])
        shown = subprocess.run(
            ["git", "--git-dir", str(remote), "show", "main:local-update.txt"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(shown, "from local\n")

    def test_dry_run_remote_add_does_not_change_anything(self) -> None:
        mod = self.load()
        remote = Path(self.temp.name) / "dry-run-remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        app = mod["App"](dry_run=True)
        app.project = self.repo
        options = iter(["2", "0"])

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Choose an option"):
                return next(options)
            if prompt.startswith("New remote name"):
                return "origin"
            if prompt.startswith("Remote URL"):
                return str(remote)
            return default if default is not None else ""

        self.patch_globals(mod["App"].remotes_action, ask=ask, confirm=lambda p, d=False: True)
        app.remotes_action()
        self.assertEqual(mod["remote_urls"](self.repo), {})

    def test_worktree_add_and_remove(self) -> None:
        mod = self.load()
        worktree = Path(self.temp.name) / "wt"
        app = mod["App"]()
        app.project = self.repo
        options = iter(["2", "3", "0"])

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Choose an option"):
                return next(options)
            if prompt.startswith("Branch for the new worktree"):
                return "wt-branch"
            if prompt.startswith("Worktree path to remove"):
                return str(worktree)
            if prompt.startswith('Type "REMOVE WORKTREE'):
                return f"REMOVE WORKTREE {worktree}"
            return default if default is not None else ""

        self.patch_globals(
            mod["App"].worktrees_action,
            ask=ask,
            confirm=lambda p, d=False: True,
            ask_path=lambda prompt, default=None, **kwargs: worktree,
        )
        app.worktrees_action()
        self.assertFalse(worktree.exists())

    def test_tag_create_and_delete(self) -> None:
        mod = self.load()
        app = mod["App"]()
        app.project = self.repo

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Tag name"):
                return "v1.0.0"
            if prompt.startswith("Commit to tag"):
                return "HEAD"
            if prompt.startswith("Tag type"):
                return "a"
            if prompt.startswith("Tag message"):
                return "Release"
            if prompt.startswith("Tag to delete"):
                return "v1.0.0"
            if prompt.startswith("Choose an option"):
                return "0"
            return default if default is not None else ""
        self.patch_globals(mod["App"].create_tag, ask=ask, confirm=lambda p, d=False: True)
        app.create_tag(self.repo)
        self.assertIn("v1.0.0", mod["tag_names"](self.repo))

    def add_origin(self) -> Path:
        remote = Path(self.temp.name) / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=self.repo, check=True)
        subprocess.run(["git", "push", "-q", "-u", "origin", "main"], cwd=self.repo, check=True)
        return remote

    def add_submodule(self) -> None:
        subrepo = Path(self.temp.name) / "subrepo"
        subrepo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=subrepo, check=True)
        (subrepo / "sub.txt").write_text("sub\n", encoding="utf-8")
        subprocess.run(["git", "add", "sub.txt"], cwd=subrepo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qm", "init"],
            cwd=subrepo,
            check=True,
        )
        subprocess.run(
            ["git", "-c", "protocol.file.allow=always", "submodule", "add", str(subrepo), "sub"],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "-c", "user.name=Test User", "-c", "user.email=test@example.com", "commit", "-qm", "sub"],
            cwd=self.repo,
            check=True,
        )

    def test_dry_run_worktree_add_does_not_create_anything(self) -> None:
        mod = self.load()
        worktree = Path(self.temp.name) / "dry-run-wt"
        app = mod["App"](dry_run=True)
        app.project = self.repo
        options = iter(["2", "0"])

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Choose an option"):
                return next(options)
            if prompt.startswith("Branch for the new worktree"):
                return "dry-run-branch"
            return default if default is not None else ""

        self.patch_globals(
            mod["App"].worktrees_action,
            ask=ask,
            confirm=lambda p, d=False: True,
            ask_path=lambda prompt, default=None, **kwargs: worktree,
        )
        app.worktrees_action()
        self.assertFalse(worktree.exists())
        self.assertNotIn("dry-run-branch", mod["local_branch_names"](self.repo))

    def test_dry_run_submodule_removal_keeps_submodule(self) -> None:
        mod = self.load()
        self.add_submodule()
        app = mod["App"](dry_run=True)
        app.project = self.repo
        options = iter(["10", "0"])

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Choose an option"):
                return next(options)
            if prompt.startswith("Submodule path to remove"):
                return "sub"
            if prompt.startswith('Type "REMOVE SUBMODULE'):
                return "REMOVE SUBMODULE sub"
            return default if default is not None else ""

        self.patch_globals(mod["App"].worktrees_action, ask=ask, confirm=lambda p, d=False: True)
        app.worktrees_action()
        self.assertTrue((self.repo / "sub").exists())
        self.assertIn("sub", mod["git_out"](self.repo, "submodule", "status"))

    def test_submodule_removal(self) -> None:
        mod = self.load()
        self.add_submodule()
        app = mod["App"]()
        app.project = self.repo
        options = iter(["10", "0"])

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Choose an option"):
                return next(options)
            if prompt.startswith("Submodule path to remove"):
                return "sub"
            if prompt.startswith('Type "REMOVE SUBMODULE'):
                return "REMOVE SUBMODULE sub"
            return default if default is not None else ""

        self.patch_globals(mod["App"].worktrees_action, ask=ask, confirm=lambda p, d=False: True)
        app.worktrees_action()
        self.assertFalse((self.repo / "sub").exists())
        submodules = mod["git_out"](self.repo, "submodule", "status")
        self.assertEqual(submodules, "")

    def test_branch_protection_with_fake_gh(self) -> None:
        mod = self.load()
        log, payload, _ = self.install_fake_gh()
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:owner/repo.git"],
            cwd=self.repo,
            check=True,
        )
        app = mod["App"]()
        app.project = self.repo
        options = iter(["2", "0"])

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Choose an option"):
                return next(options)
            if prompt.startswith("Required approving reviews"):
                return "1"
            return default if default is not None else ""

        def confirm(prompt, default=False):
            return "Enforce protection" not in prompt

        self.patch_globals(mod["App"].branch_protection_action, ask=ask, confirm=confirm)
        app.branch_protection_action(self.repo)
        self.assertIn(
            "api --method PUT repos/owner/repo/branches/main/protection --input -",
            log.read_text(encoding="utf-8"),
        )
        body = json.loads(payload.read_text(encoding="utf-8"))
        self.assertEqual(body["required_pull_request_reviews"]["required_approving_review_count"], 1)
        self.assertTrue(body["required_conversation_resolution"])
        self.assertFalse(body["enforce_admins"])

    def test_actions_secret_set_with_fake_gh(self) -> None:
        mod = self.load()
        log, _, secret = self.install_fake_gh()
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:owner/repo.git"],
            cwd=self.repo,
            check=True,
        )
        app = mod["App"]()
        app.project = self.repo
        options = iter(["2", "0"])

        def ask(prompt, default=None, allow_empty=False):
            if prompt.startswith("Choose an option"):
                return next(options)
            if prompt.startswith("Secret name"):
                return "MY_TOKEN"
            return default if default is not None else ""

        self.patch_globals(mod["App"].actions_secrets_action, ask=ask, confirm=lambda p, d=False: True)
        globals_dict = mod["App"].actions_secrets_action.__globals__
        globals_dict["getpass"] = types.SimpleNamespace(getpass=lambda prompt: "s3cret-value")
        globals_dict["sys"] = types.SimpleNamespace(stdin=types.SimpleNamespace(isatty=lambda: True))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            app.actions_secrets_action(self.repo)
        self.assertEqual(secret.read_text(encoding="utf-8"), "s3cret-value")
        self.assertIn("secret set MY_TOKEN", log.read_text(encoding="utf-8"))
        self.assertNotIn("s3cret-value", output.getvalue())

    def test_audit_with_fake_gh(self) -> None:
        mod = self.load()
        fakebin = Path(self.temp.name) / "bin"
        fakebin.mkdir()
        fake = fakebin / "gh"
        fake.write_text(
            "#!/bin/sh\n"
            "case \"$1\" in\n"
            "  api) echo '[]'; exit 0;;\n"
            "  run) echo 'FAKE-RUN'; exit 0;;\n"
            "esac\n"
            "exit 0\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        subprocess.run(["git", "remote", "add", "origin", "git@github.com:owner/repo.git"], cwd=self.repo, check=True)
        env = self.env.copy()
        env["PATH"] = str(fakebin) + os.pathsep + env.get("PATH", "")
        old = os.environ.copy()
        os.environ.update(env)
        try:
            app = mod["App"]()
            app.project = self.repo
            app.github_security_audit(self.repo)
        finally:
            os.environ.clear()
            os.environ.update(old)
        self.assertEqual(mod["parse_github_url"]("git@github.com:owner/repo.git"), ("owner", "repo"))


if __name__ == "__main__":
    unittest.main()
