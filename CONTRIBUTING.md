# Contributing

## Project constraints

- The runtime is one executable Python file, `git-create`.
- The runtime uses the Python standard library only. Do not add runtime
  third-party dependencies.
- Supported runtime floor: Python 3.9.
- Supported platform: Linux.
- Safety rules are part of the product, not optional polish: no force-push, no
  silent destructive action, explicit confirmation for destructive operations,
  and no printing of secret values.

## Development setup

No installation is required to run the application:

```bash
git clone https://github.com/RogerBergling/git-create.git
cd git-create
python3 -m unittest discover -s tests -v
./git-create --no-color check --offline
```

Optional development tools are pinned in `requirements-dev.txt`:

```bash
python3 -m pip install -r requirements-dev.txt
ruff check git-create tests
```

`make verify` runs lint, tests, the offline self-check, and the history secret
scan.

## Making changes

- Keep changes focused and explain the user-visible behavior.
- Add or update tests for behavior changes. Tests must not require network
  access or real GitHub credentials.
- Update `README.md` for user-visible behavior and `CHANGELOG.md` under
  `Unreleased` until a release is cut.
- Use argument-list subprocess calls. Do not introduce `shell=True`.
- Never print, log, or commit secret values.
- Preserve existing confirmations and safety refs. A new destructive action
  needs an explicit confirmation design and a recovery path.
- Keep Python 3.9 compatibility; CI checks older supported versions.

## Pull request checklist

- [ ] Tests pass locally.
- [ ] `ruff check git-create tests` passes.
- [ ] `./git-create --no-color check --offline` passes.
- [ ] New or changed behavior is documented.
- [ ] `CHANGELOG.md` is updated.
- [ ] No secrets, credentials, or private data are included.
- [ ] Destructive paths retain confirmation and recovery safeguards.

## Security reports

Do not report vulnerabilities in a public issue. Follow `SECURITY.md`.

## Licensing

The repository does not yet declare a license. Until the maintainer adds a
`LICENSE` file, do not submit external contributions; contribution terms would
be ambiguous. See `docs/ENTERPRISE-READINESS.md`.
