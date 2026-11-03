# Security Policy

## Supported versions

The latest `1.x` release receives security fixes. Older releases are supported
on a best-effort basis. Security fixes are documented in `CHANGELOG.md`.

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub:

1. Open the repository's **Security** tab.
2. Select **Report a vulnerability**.
3. Include the affected version, operating system, Python/Git/`gh` versions,
   reproduction steps, and the expected impact.

Do not open a public issue for an unpatched vulnerability. Do not include real
credentials or private keys in a report; rotate any exposed credential first.

## Scope

In scope:

- command injection or argument-handling flaws
- path traversal, unsafe symlink handling, or unsafe file permissions
- credential or secret leakage in output, logs, or backups
- bypasses of confirmation, safety-ref, backup, or no-force safeguards
- unsafe parsing of Git or GitHub CLI output

Out of scope:

- vulnerabilities in Git, `gh`, GitHub, or a remote server
- consequences of user-supplied pre-commit commands, which run with the user's
  permissions and are documented as trusted input
- running the application with elevated privileges
- social engineering

## Response

Reports are handled on a best-effort basis. The maintainer will acknowledge a
report, assess severity, prepare a fix, and coordinate disclosure. No response
or remediation SLA is offered unless a separate support agreement exists.

## Trusted repositories

Treat every repository, submodule, and workflow log as untrusted input. Git
hooks, `.gitattributes` filters, `core.hooksPath`, submodule operations, and the
optional `gitcreate.precommit` command can execute code with your permissions.
Review a repository before running the app on it, and do not run the app with
elevated privileges.

## Security design notes

- The runtime has no third-party Python dependencies.
- Internal Git and `gh` commands use argument lists rather than shell strings.
  The optional user-configured pre-commit command is the documented exception.
- Secret values are read without echo, passed on standard input, and never
  printed by the application.
- Destructive actions use typed confirmations and local safety refs or patches.
- Recovery files are created exclusively with private (`0600`) permissions.
- Remote URLs displayed in reports and JSON are redacted; token query parameters
  and embedded credentials are not printed.
- External Git and `gh` output is stripped of terminal control sequences before
  display.
- The application never force-pushes or rewrites shared history automatically.
