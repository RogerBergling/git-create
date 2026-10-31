## Summary

<!-- What changed and why? -->

## Validation

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `ruff check git-create tests`
- [ ] `./git-create --no-color check --offline`
- [ ] `./git-create --no-color secrets .`

## Safety review

- [ ] No force-push or automatic shared-history rewrite was added.
- [ ] Destructive actions still require explicit confirmation.
- [ ] Safety refs or recovery files are preserved or improved.
- [ ] Secret values are never printed, logged, or stored in the repository.
- [ ] New subprocess calls use argument lists, not `shell=True`.

## Documentation

- [ ] `README.md` updated for user-visible behavior.
- [ ] `CHANGELOG.md` updated under `Unreleased`.
- [ ] Python 3.9 compatibility preserved.
- [ ] No new runtime third-party dependencies.
