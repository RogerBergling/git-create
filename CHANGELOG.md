# Changelog

All notable changes to `git-create` are recorded here.

## 1.9.0

- Added version, build number, build date, and build time to the main menu,
  `--version`, verification output, and JSON report metadata.

## 1.8.0

- Scenario A now creates an empty GitHub repository, builds README.md and
  .gitignore locally, signs the initial commit, and pushes it instead of
  starting from a GitHub web-created README commit.
- Verification offers to create a missing .gitignore directly and prints the
  running git-create version so stale copies are easy to identify.
- HEAD-signature verification now falls back to GitHub's commit verification for
  GitHub-signed commits that are not in the local allowed_signers file.
- `.dockerignore` is informational when no Dockerfile exists, and batch fix no
  longer creates it for non-Docker projects.
- Added an arrow-key directory picker with up/down navigation, go-up,
  select-current, type-path, hidden-directory, and cancel controls.
- Added batch actions after a folder scan: status, verify all, apply safe
  project-file fixes, fast-forward pull, and normal push across eligible
  repositories.
- Added comma-separated folder scanning and live Git output during pull/push,
  followed by each repository's short status. Push now uses an explicit refspec
  and requires a matching upstream branch name.
- Batch fix now skips optional `.editorconfig` and `.gitattributes` files to
  avoid creating untracked noise; use option 11 when those files are wanted.
- Extended dry-run mode to batch file fixes, batch pull, and batch push.
- Hardened recovery backups with collision-resistant names and exclusive,
  private file creation that refuses symlinks and overwrites.
- Added a security policy, contribution guide, CODEOWNERS, issue and pull
  request templates, Dependabot, and CodeQL.
- Added an enterprise readiness review and prioritized adoption roadmap.
- Hardened CI with pinned actions, Python 3.10-3.14, Ruff linting, timeouts, and
  concurrency cancellation.
- Added version-consistency and backup-safety tests.

## 1.7.0

- Added worktree list/add/remove/prune operations.
- Added submodule list/update/sync/add/deinit/remove operations with safety
  confirmations.
- Added repository-local pre-commit commands and managed pre-commit hook
  installation/removal.
- Added MIT, ISC, and BSD-3 license generation.
- Added a GitHub security/CI audit covering branch protection, Actions secret
  names, workflow runs, and GHCR runs.
- Added failed GHCR workflow log inspection (`gh run view --log-failed`).
- Added branch-protection and repository Actions-secret management.
- Added interactive conflict-file resolution with editor, ours/theirs, and stage
  choices; merges/rebase are never continued automatically.
- Added safety-backup listing and cleanup.
- Added a dry-run mode for worktree, submodule, remote, and backup-cleanup
  changes.
- Added `git-create info --json` for status, remotes, branches, tags, worktrees,
  submodules, and stashes.
- Added `git-create audit --json` for branch protection, Actions secret names,
  workflow runs, and GHCR runs.
- Added multi-account `gh auth switch`.
- Added remote branch rename.
- Added automated tests and GitHub Actions CI.
- Added this changelog.

## 1.5.0

- Added amend-last-commit support and interactive hunk staging.
- Added release-asset upload and changelog preview.
- Added GitHub pull request, issue, and review helpers.
- Added generic remote management.
- Added repository-local identity/signing configuration.
- Removed all app-imposed file-size blocking; large files are informational.
- Added README screenshots and safety documentation.

## 1.4.0

- Added stash management.
- Added guided merge/rebase with safety refs and conflict continue/abort.
- Added annotated/signed tags and GitHub release creation.
- Added the read-only repository inspector.
- Added local batch verification for scanned repositories.

## 1.3.0

- Added branch create/switch/rename/delete and remote branch management.
- Added undo/revert helpers for local changes and commits.
- Added Dockerfile and GHCR workflow generation.
- Added linked-worktree-aware renaming.
- Added generated-file examples.

## 1.2.0

- Added history secret scanning.
- Added untracked-file secret scanning.
- Added publishing for already-initialized repositories without a remote.
- Added `.gitattributes` generation.
- Added a full staged-diff review before commits.

## 1.1.0

- Added the menu-driven application.
- Added project and global verification.
- Added scenarios A-D for create/clone/publish/diagnose.
- Added SSH signing, secret, and GitHub safety checks.
- Added a learning-focused README.

## 1.0.0

- Initial project documentation.
