# Generated file examples

These files are **showcase examples only**. The `git-create` application does
not use this directory as templates or configuration and does not require these
files to work. Like any other project content, they may be included when the
app scans for secrets or history.

They exist so you can see the shape of the files the app creates before running
the corresponding menu action.

| Example | App source | Menu action |
| --- | --- | --- |
| `Dockerfile.python` | Docker/GHCR template | 16 |
| `ghcr.yml` | GHCR workflow template | 16 |
| `gitignore` | `.gitignore` template | 11 |
| `dockerignore` | `.dockerignore` template | 11 / 16 |
| `editorconfig` | `.editorconfig` template | 11 |
| `gitattributes` | `.gitattributes` template | 11 |
| `env.example` | Derived from a real `.env` by option 11 | 11 |
| `README.project.md` | README template | 11 |

Files without a leading dot are named that way for visibility in the example
directory. To use one in a real project, copy it to the dotted name, for
example:

```bash
cp examples/generated/gitignore .gitignore
cp examples/generated/dockerignore .dockerignore
cp examples/generated/editorconfig .editorconfig
cp examples/generated/gitattributes .gitattributes
cp examples/generated/env.example .env.example
cp examples/generated/README.project.md README.md
mkdir -p .github/workflows
cp examples/generated/ghcr.yml .github/workflows/ghcr.yml
cp examples/generated/Dockerfile.python Dockerfile
```

Review and edit the copies before committing. The Dockerfile is a starter and
may need language-specific dependencies, a different entrypoint, or a
non-root runtime user. The GHCR workflow uses the placeholder image
`ghcr.io/owner/repository`; replace it with the real lowercase image name.

These files are repository documentation and examples, not application
dependencies.
