# Changelog

All notable changes to `git-create` are recorded here.

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
