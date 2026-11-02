# Enterprise Readiness Review

Review date: 2026-10-31

Scope: runtime, tests, CI, documentation, security posture, and release process.

## Executive summary

`git-create` is a deliberately safe, single-user Linux assistant with unusually
strong guardrails for a small tool. It does not force-push, does not rewrite
shared history automatically, confirms destructive operations, keeps local
recovery backups, avoids runtime third-party dependencies, and scans for common
secret patterns. Those are solid foundations.

It is **not yet enterprise-ready**. The main blockers are:

1. no declared repository license;
2. `github.com` is hardcoded, so GitHub Enterprise Server is unsupported;
3. no durable audit log or policy-as-code enforcement;
4. Linux-only support;
5. limited automated coverage of the 8,000+ line runtime;
6. no release provenance (tags, checksums, SBOM, signed artifacts).

This document separates release blockers from scale and polish work.

## What is already strong

- No runtime third-party Python dependencies.
- No `shell=True`; Git and `gh` commands use argument lists.
- No force-push and no automatic shared-history rewrite.
- Typed confirmations for destructive actions.
- Safety refs and private recovery patches for undo paths.
- Secret values are read without echo, passed on stdin, and not printed.
- Secret scanning covers tracked files, untracked files, and bounded history.
- Dry-run mode for worktree, submodule, remote, and backup-cleanup mutations.
- Structured JSON output for `info` and `audit`.
- Interactive tests use temporary repositories and fake `gh` scripts.
- CI runs tests on multiple Python versions and performs an offline self-check.

## Priority 0: release blockers

### 1. Declare a license

There is no `LICENSE` file. Without one, the default copyright rules apply:
enterprises cannot confidently redistribute, modify, or accept contributions.
This is a legal/product decision, not a code change.

Recommended choices:

- **Apache-2.0** if patent grants and enterprise contribution terms matter.
- **MIT** for the simplest permissive model.

Do not add a license without owner approval. After choosing, add `LICENSE`,
update `README.md`, and update `CONTRIBUTING.md`.

### 2. Support GitHub Enterprise Server

The authentication, URL parsing, API, and audit paths assume `github.com`.
Relevant code includes `parse_github_url`, `ensure_gh`, `gh_auth_status`, the
branch-protection endpoints, and the GitHub audit.

Required changes:

- detect the host from the `origin` URL or an explicit configuration;
- pass `--hostname` or `HOST/OWNER/REPO` to every `gh` command;
- store host-specific authentication state;
- test against a GHES instance or a deterministic fake;
- document GHES version requirements.

### 3. Add an audit trail and policy file

Enterprise operators need evidence of what the tool did and guardrails that do
not depend on the operator remembering flags.

Recommended minimum:

- opt-in JSON Lines audit log with timestamp, repository, operation, command,
  outcome, and actor;
- central redaction of tokens, URLs with credentials, and secret values;
- policy file (JSON is standard-library friendly) controlling:
  - allowed remote hosts and protocols;
  - protected branches;
  - required signed commits;
  - allowed secret-scan exceptions;
  - whether dry-run is mandatory for selected actions;
  - audit-log destination.
- a `policy check` command that exits non-zero when a repository violates policy.

### 4. Decide platform scope

`README.md` declares Linux-only support. If enterprise users need macOS or
Windows, the following need work:

- pre-commit hook generation currently assumes a POSIX shell;
- tests and CI are Ubuntu-only;
- file permissions, ANSI behavior, and path handling need platform tests;
- Windows requires a different hook strategy and path normalization tests.

Either add macOS/Windows support explicitly, or keep Linux-only as a documented
constraint and make CI enforce it.

### 5. Deepen GitHub governance support

Branch protection currently supports a basic review policy. Enterprise
baselines usually require:

- required status checks and required workflows;
- linear history and signed commits;
- push restrictions and code-owner review;
- required deployments and conversation resolution;
- organization-level, environment-level, Codespaces, and Dependabot secrets;
- policy drift detection between desired and actual settings.

## Priority 1: scale and maintainability

### 6. Raise automated coverage

A local coverage run measured roughly **15% line coverage for `git-create`** and
about **20% overall**. The integration-heavy suite exercises real CLI behavior,
so this overstates untested behavior, but it is far below a typical enterprise
gate.

Add tests for:

- branch-protection enable/remove and secret set/delete failure paths;
- GHCR failure-log handling and pagination;
- conflict resolution for merge and rebase, including deleted files;
- backup cleanup, pre-commit hook lifecycle, and license generation;
- non-repository and unauthenticated CLI paths;
- version consistency and documentation links;
- path traversal, symlink, and permission edge cases.

Refactor pure helpers behind injectable command runners and prompt objects so
they can be unit-tested without monkeypatching module globals.

### 7. Modularize the source, keep the single-file artifact

The runtime is one file of more than 8,000 lines. This is excellent for copying
but expensive for review, ownership, and testing.

Recommended shape:

```text
src/git_create/
  cli.py
  app.py
  git_ops.py
  github_ops.py
  policy.py
  security.py
  ui.py
tools/build_single_file.py
dist/git-create
```

A deterministic build step can concatenate or bundle the modules into the
current single-file runtime, preserving the distribution constraint while
making review and testing practical.

### 8. Provide a non-interactive mutation API

Enterprise automation cannot drive a menu. Today only read-only or reporting
commands are scriptable (`check`, `info`, `audit`, `scan`, `secrets`).

Add explicit commands for repeatable operations, for example:

```bash
git-create branch create --name feature/x --switch
git-create tag create --name v1.2.3 --annotate --message "..."
git-create protect apply --policy policy.json
git-create secret set NAME --stdin
```

Dangerous commands should require an explicit confirmation token or policy
allowance. Every command needs stable JSON output and documented exit codes.

### 9. Release engineering

There are no tags, release assets, checksums, SBOMs, or provenance.

Recommended release flow:

- signed tag from a protected `main`;
- CI builds a versioned `git-create` artifact;
- publish `SHA256SUMS`, a CycloneDX or SPDX SBOM, and build provenance;
- generate release notes from `CHANGELOG.md`;
- verify that the tag, runtime `VERSION`, README, and changelog agree.

### 10. Improve secret scanning for CI

Current scanning is a useful guardrail but lacks enterprise integration:

- SARIF output for GitHub code scanning;
- allowlist/baseline files with expiry and justification;
- incremental scanning for pull requests;
- documented entropy/pattern limits and false-positive handling;
- policy for blocking pushes or merges based on findings.

### 11. Complete CI and supply-chain controls

This pass added action pinning, Dependabot, CodeQL, linting, Python 3.10-3.14,
timeouts, and concurrency cancellation. Remaining work:

- coverage reporting and a ratcheting threshold;
- type checking after annotation cleanup;
- actionlint validation for workflows;
- dependency review for pull requests;
- macOS job if macOS support is declared;
- branch protection and required status checks on the repository itself.

## Priority 2: polish

- Split the 1,300-line README into a short landing page plus `docs/` guides.
- Add a man page and shell completions.
- Add structured diagnostics for support without collecting telemetry.
- Document performance limits for very large repositories.
- Add packaging (pipx, Homebrew, distro packages) once licensing is resolved.
- Add a written retention policy for safety refs and recovery patches.

## Recommended sequence

1. **Decision phase:** choose license, platform scope, and GHES requirement.
2. **Governance phase:** audit log, policy file, branch-protection depth.
3. **Assurance phase:** coverage, type checking, SARIF, release provenance.
4. **Scale phase:** modular source plus deterministic single-file build.
5. **Distribution phase:** packaging and signed release artifacts.

## Adoption checklist

- [ ] License approved and `LICENSE` committed.
- [ ] Supported platform and Python versions documented and tested.
- [ ] GHES host support implemented or explicitly out of scope.
- [ ] Audit log destination and retention approved.
- [ ] Policy file reviewed by security.
- [ ] Branch protection requires reviews, checks, and signed commits.
- [ ] Private vulnerability reporting enabled.
- [ ] Dependabot and CodeQL alerts routed to an owner.
- [ ] Release artifacts are signed and checksummed.
- [ ] Backup retention and recovery drills are documented.

## Implemented in this review pass

- batch scan actions for status, safe file fixes, fast-forward pull, and normal push;
- locally signed baseline commits for new projects and GitHub signature fallback;
- guarded local/GitHub repository deletion with backups and typed confirmations;
- collision-resistant, private recovery backup files;
- exclusive file creation that refuses symlinks and overwrites;
- stricter branch-protection review-count validation;
- security policy, contribution guide, CODEOWNERS, issue/PR templates;
- Dependabot, CodeQL, pinned GitHub Actions, lint job, and Python 3.14 CI;
- version-consistency, batch-sync, and backup-safety tests;
- this roadmap.

## Open decisions

1. Which license will the project use?
2. Is GitHub Enterprise Server required, or is `github.com` sufficient?
3. Is Linux-only support acceptable?
4. Should policy configuration be a repository file, an environment variable,
   or both?
5. Is a modular source tree acceptable if the released artifact remains one
   executable file?
