# git-create

A safe, menu-driven Git and GitHub assistant for Linux. It is a **single
Python file with no third-party dependencies**. It helps you create, clone,
publish, verify, rename, commit, push, and diagnose projects without missing
important Git settings, SSH signing configuration, secret files, or remote
history problems.

The app is deliberately conservative:

- no `git push --force`
- no automatic history rewriting
- no automatic merge/rebase of diverged histories
- no overwriting existing project files
- no silent commits containing `.env`, keys, tokens, or other secrets

## Why I built this app

I built this app because I was learning Git myself and did not want to depend
on memory for every important step. Git is powerful, but a lot of its behavior
is invisible until something goes wrong:

- A project may have no repository, a local repository, a remote repository,
  or both — and each situation needs a different workflow.
- The same action can be harmless or destructive depending on the state of the
  working tree, the branch, and the remote.
- Git identity, SSH signing, the default branch, pull behavior, and GitHub
  authentication are easy to configure once and then forget.
- Secret files such as `.env`, private keys, and tokens can be committed by
  accident if `.gitignore` is missing or incomplete.
- A rejected push is not a reason to use `--force`. It is a signal to compare
  histories first.
- Renaming a folder, renaming a GitHub repository, committing, and pushing are
  related tasks, but Git does not treat them as one operation.

I wanted one menu that checks the things I usually forget, explains what the
next command will do and why, refuses unsafe shortcuts, and keeps the commands
visible so I can learn from them. The app is a checklist, a safety net, and a
teaching tool — not an autopilot that hides Git from me.

That is also why it prints the command before running it and why every major
action has a **What this does** and **Why** explanation. The goal is to make the
safe path the easy path while still learning what Git is doing.

## Why Python instead of a shell script or an ELF?

Python 3 is the best fit for this task:

- A single executable text file works on every Linux distribution without a
  build step.
- The standard library provides reliable subprocess handling, JSON parsing,
  path handling, file scanning, and text formatting.
- Shell would become fragile around JSON, quoting, menus, and secret scanning.
- A compiled ELF would need per-architecture builds, a toolchain, and more
  maintenance for no practical benefit here.

The program targets Python 3.9 or newer. It has been tested with Python 3.14,
Git 2.53, and GitHub CLI 2.46.

## Requirements

Required:

- Linux
- Python 3.9+
- Git 2.34+ for SSH commit signing (`git init -b` needs a slightly older Git,
  but the verification and signing features assume 2.34+)
- OpenSSH client (`ssh`, `ssh-keygen`) for SSH commit signing

Recommended for GitHub scenarios:

- [GitHub CLI](https://cli.github.com/) `gh` 2.x
- An SSH key configured for GitHub authentication and signing

Optional:

- Docker, if you want `.dockerignore` checks to be active
- `ssh-agent`, if your SSH key has a passphrase

No `pip install`, virtual environment, Makefile, or package manager is needed.

## Installation

From this repository, make the app executable:

```bash
chmod +x git-create
```

To copy it somewhere else, use a file path that does not collide with the
repository directory:

```bash
mkdir -p ~/bin
cp git-create ~/bin/git-create
chmod +x ~/bin/git-create
```

To run it as a Git subcommand from any directory, place it on `PATH`:

```bash
mkdir -p ~/.local/bin
ln -s "$(pwd)/git-create" ~/.local/bin/git-create
```

Then both forms work:

```bash
git-create
git create
```

The current working directory is always the source of truth. If you run the
script from a project root, that project is detected automatically. If you run
it from elsewhere, use **option 3** to select a project.

## Quick start

```bash
cd ~/Projects
git-create
```

Typical menu flow:

1. Run the automatic quick check at startup.
2. Choose **1** to run a full verification on the active project.
3. Use **4**, **5**, or **6** to create, clone, or publish a repository.
4. Use **8** for reviewed commits and normal pushes.
5. Use **7** whenever local and remote histories may have diverged.

The app never changes a Git configuration automatically. The settings wizard
shows a plan and asks for confirmation before writing anything.

## Git in plain English

If you are new to Git, these are the concepts the app uses. Read this once;
the in-app help (option **12**) repeats the important parts when you need them.

| Concept | Plain-English meaning |
| --- | --- |
| Working tree | The files you see and edit in the project folder. |
| Repository | The `.git` folder that stores the project's history and configuration. |
| Staging area / index | A waiting room for changes. You choose what goes into the next commit. |
| Commit | A saved, labeled snapshot of the staged changes, with an author, time, message, and optional signature. |
| Branch | A movable name pointing at a line of commits. `main` is the usual default branch. |
| Remote | A named copy of the repository somewhere else, usually GitHub. The default name is `origin`. |
| `origin/main` | Your local record of where the `main` branch was on the remote at the last fetch. |
| Upstream | The remote branch that your current local branch tracks. |
| Fetch | Downloads new remote information without changing your files or branch. |
| Pull (fast-forward) | Moves your branch forward to the remote commit without creating a merge commit. |
| Push | Uploads your local commits to the remote branch. |
| Diverged | Local and remote both have commits the other does not. Do not force; inspect first. |
| Commit signing | A cryptographic signature proving that a commit came from your SSH key. |
| `.gitignore` | Rules telling Git which files must never be staged or committed. |
| `.dockerignore` | Rules telling Docker which files must not be sent into an image build context. |

Git has three important places to remember:

```text
working tree  --git add-->  staging area  --git commit-->  local repository  --git push-->  remote
```

A commit records **the staging area**, not automatically everything in the
folder. That is why the app shows what is staged, scans it, and asks before
committing.

## What each command does and why

The app prints the exact command before running major actions. This table
explains the commands you will see.

| Command | What it does | Why the app uses it |
| --- | --- | --- |
| `git config --global ...` | Reads or writes settings in your personal Git configuration. | Sets identity, safer defaults, and SSH signing once for all repositories. |
| `git init -b main` | Creates a new `.git` repository whose first branch is `main`. | Starts history for a local project without creating commits yet. |
| `git status` | Shows changed, staged, and untracked files, plus branch state. | Helps you see exactly what would be committed. |
| `git add` | Copies selected changes into the staging area. | Lets you review a precise snapshot before committing. |
| `git diff --cached` | Shows the difference between the last commit and the staging area. | Verifies what the next commit will contain. |
| `git commit` | Saves the staged snapshot as a history entry. | Creates a checkpoint that can be reviewed, signed, and pushed. |
| `git push` | Uploads local commits to the remote branch. | Shares history with GitHub and other clones. |
| `git fetch` | Downloads remote refs and objects without changing your branch. | Lets you compare local and remote history safely. |
| `git pull --ff-only` | Fetches and fast-forwards the branch only if no merge is needed. | Updates a branch without creating an accidental merge commit. |
| `git log` | Shows commit history. | Helps you understand what happened and compare histories. |
| `git branch` | Lists or creates branch names. | The app creates a local backup branch before risky sync work. |
| `git remote -v` | Lists remote names and URLs. | Confirms where fetch and push will go. |
| `git merge-base` | Finds the common ancestor of two histories. | Shows whether local and remote history are related. |
| `git fsck` | Checks the integrity of the object database. | Detects missing or corrupt repository objects during deep verification. |
| `gh repo create` | Creates a GitHub repository, optionally from local source and with push. | Connects a local project to a new remote without manual API work. |
| `gh repo clone` | Clones a GitHub repository using your authenticated `gh` session. | Sets up a local working copy and remote in one step. |
| `gh repo rename` | Renames the repository on GitHub and updates the local remote. | Keeps local and remote names consistent; old GitHub URLs redirect. |
| `gh auth login` / `gh auth refresh` | Authenticates `gh` or adds OAuth scopes. | Enables GitHub operations and signing-key management. |
| `gh api user/ssh_signing_keys` | Reads the SSH signing keys registered on your GitHub account. | Verifies that the key used for signed commits is actually registered. |

## How the app teaches while you use it

- Before important actions it prints **What this does**, **Why**, and, when
  relevant, **Safety** notes.
- It prints the exact shell command before executing it.
- It explains what each global setting means in option **10 → 9**.
- Option **12** contains the Git concepts, command explanations, scenarios,
  and safety rules in the terminal.
- Verification messages include a short reason and, where useful, the command
  that fixes the problem.

Before a command runs, the output looks like this:

```text
What this does:
  git commit saves the staged snapshot as a new local commit with your message.
Why:
  The commit is a checkpoint you can review, sign, and push. It does not upload
  anything, so a signing or message problem does not affect the remote.
Safety:
  Only staged content is included. The secret scan already checked that content.
Command: git commit -m "Initial commit"
```

The command is printed after the explanation, immediately before execution.

## Menu reference

| Option | Function |
| --- | --- |
| `1` | Verify the active project: global settings, repository state, secrets, files, remote, signature, and GitHub metadata. |
| `2` | Scan a folder for Git repositories. Choose the folder and depth, then optionally make one active and verify it. |
| `3` | Select the active project by path. |
| `4` | **Scenario A**: create a new private/public GitHub repository with a README and clone it. |
| `5` | **Scenario B**: clone an existing GitHub repository, or clone any Git URL. |
| `6` | **Scenario C**: publish an existing local project: initialize, add safe files, review, sign, commit, create the GitHub repo, and push. |
| `7` | **Scenario D**: fetch and diagnose local/remote history. Creates an optional local backup branch. Never force-pushes. |
| `8` | Commit and push: review changes, stage all or selected paths, scan secrets, sign, commit, and push normally. |
| `9` | Rename the local folder and/or the GitHub repository, and optionally commit/push pending changes. |
| `10` | Check and fix global Git/GitHub settings, SSH signing, allowed signers, and `gh` authentication. |
| `11` | Check/add important project files: `.gitignore`, `.dockerignore`, `README.md`, `.editorconfig`, and `.env.example`. |
| `12` | Help, Git concepts, command explanations, and the scenario guide. |
| `0` | Exit. |

The defaults point at `~/Projects` when it exists. All paths are prompted, so
the script can live anywhere and work with repositories anywhere.

## Automatic checks on every run

Startup performs a fast, local quick check. It does not contact the network.
It reports failures and warnings for:

- Git and `gh` availability
- global identity (`user.name`, `user.email`)
- default branch, `pull.ff`, `push.default`, `fetch.prune`, editor
- SSH commit signing (`gpg.format`, `user.signingkey`, `commit.gpgsign`)
- `gpg.ssh.allowedSignersFile`
- GitHub HTTPS-to-SSH rewrite
- GitHub CLI authentication
- current repository state, working tree, upstream, and important files

Choose **1** for the full verification. Full verification adds:

- remote reachability
- local/remote default branch comparison
- GitHub repository metadata and name comparison
- whether the configured signing key is registered on GitHub
- `git fsck` object connectivity
- tracked-file secret scanning
- `.env` file permission checks
- large-file checks
- Docker ignore coverage
- commit signature status
- linked-worktree detection
- current remote divergence state

Status levels:

- `[OK]` check passed
- `[!]` warning; review before publishing
- `[X]` blocking problem or unsafe state
- `[i]` informational or optional
- `[-]` skipped

## Global settings checked

These are the settings the app recommends, including the examples from the
original workflow. In the app, choose **10 → 9** to see what each setting
means and why it matters.

```bash
git config --global user.name "Roger Bergling"
git config --global user.email "github@bergling.net"

git config --global init.defaultBranch main
git config --global pull.ff only
git config --global push.default simple
git config --global fetch.prune true
git config --global core.editor "nano"

git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/disk_bergling.pub
git config --global commit.gpgsign true

git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

Important additions beyond the original list:

- **`gpg.ssh.allowedSignersFile`** is required for local verification of SSH
  signatures. Without it, `git log --show-signature` and `git verify-commit`
  cannot confirm who signed a commit.
- **`push.default simple`** prevents surprising push behavior.
- **`fetch.prune true`** removes stale remote-tracking branches.
- The app verifies that the private key exists next to the configured `.pub`
  file and warns if its permissions are too open (recommended: `600`).
- The app can check whether the signing key is registered on GitHub with
  the `admin:ssh_signing_key` scope.

### GitHub signing-key setup

The settings menu can run these guided commands for you:

```bash
gh auth refresh -h github.com -s admin:ssh_signing_key
gh ssh-key add ~/.ssh/disk_bergling.pub --type signing
```

Reading the registered keys uses:

```bash
gh api user/ssh_signing_keys
```

## Project files checked

| File | Behavior |
| --- | --- |
| `README.md` | Warning when missing. |
| `.gitignore` | Failure when missing; checks secret and build rules. |
| `.dockerignore` | Warning when missing; extra context is shown if no Dockerfile is detected yet. |
| `LICENSE` | Informational; not generated automatically because the license is your choice. |
| `.env.example` | Required when `.env` exists; can be generated with blank values. |
| `.editorconfig` | Optional; template available. |
| `.gitattributes` | Informational; useful for line endings and Git LFS. |
| `SECURITY.md` | Informational; useful for public projects. |
| `.github/workflows/*.yml` | Informational; CI is optional. |

The `.gitignore` analysis checks for:

- `.env` and `.env.*`, while keeping `!.env.example`
- `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`
- `id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519`
- `.netrc`, `.npmrc`, `.pypirc`, `credentials.json`
- Terraform state files
- Python, Node, build, editor, and log output directories

The file wizard creates templates only when a file is missing. Existing files
are never overwritten. For an existing `.gitignore`, only missing secret rules
are appended after confirmation.

If an `.env` exists and `.env.example` does not, option 11 reads only the
**variable names** from `.env` and writes a template with blank values. Values
are never copied.

## Scenarios

### Scenario A: new private repository, then clone

Use this when you have no code yet and want a safe GitHub starting point.

Menu option **4** runs the equivalent of:

```bash
cd ~/Projects
gh repo create my-project --private --add-readme --clone
cd my-project
git status
git remote -v
git branch --show-current
```

It verifies the clone afterwards.

### Scenario B: clone an existing repository

Menu option **5** accepts `OWNER/REPO` or a full Git URL:

```bash
cd ~/Projects
gh repo clone OWNER/REPO
# or
git clone git@github.com:OWNER/REPO.git
```

It refuses to clone over an existing directory and verifies the result.

### Scenario C: local project becomes a new GitHub repository

Menu option **6** performs a safer, reviewed version of the original workflow:

1. Refuses to run inside an existing repository, so no accidental nested repo
   or overwritten history.
2. Creates `.gitignore` before staging, and optionally `README.md`,
   `.dockerignore`, and `.env.example`.
3. Initializes `main`.
4. Shows every change, then stages all files or selected paths.
5. Blocks sensitive filenames and common secret patterns. If a false positive
   is intentional, a typed `COMMIT` confirmation is required.
6. Creates a signed initial commit.
7. Runs `gh repo create NAME --private --source=. --remote=origin --push`.

Unlike `git add -p`, the app stages selected paths non-interactively, but it
shows the list and the staged diff before committing. This gives you the same
review opportunity without a fragile terminal hunk editor.

### Scenario D: local and remote repositories already exist

Menu option **7** is diagnostic first:

1. Fetches with prune.
2. Shows `git log --oneline --graph --decorate --all -n 30`.
3. Shows `git branch -avv`.
4. Shows the common ancestor and ahead/behind counts.
5. Offers a local backup branch named
   `backup/<branch>-YYYYMMDD-HHMMSS`.
6. Only offers a fast-forward pull when the local branch is behind and the
   working tree is clean.
7. Never runs `git push --force`.

If the histories are unrelated or diverged, it stops and explains the safe
next steps. The backup branch stays local until you decide to delete it.

### Rename a project or GitHub repository

Menu option **9** can:

- rename the local folder (using `mv` or, for linked worktrees,
  `git worktree move`)
- rename the GitHub repository with `gh repo rename`
- repair the `origin` URL if `gh` did not update it
- optionally commit and push any pending changes

Git does not track a directory name, so a local rename does not require a
commit. GitHub redirects the old repository name after a rename, but external
links and other local clones should still be updated. No history is rewritten.

### Commit and push

Menu option **8**:

1. Shows changed paths.
2. Stages all files or a numbered selection.
3. Refuses to continue if the index differs from the working tree, so the
   secret scan cannot approve different content from what will be committed.
4. Scans staged filenames and content for private keys and common token
   patterns.
5. Shows `git diff --cached --stat`.
6. Commits with your message, using SSH signing if configured.
7. Pushes normally and sets upstream on the first push if needed.
8. On a rejected push, stops and points to scenario D. It never force-pushes.

## Command line mode

The menu is the primary interface, but non-interactive checks are available for
scripts and CI:

```bash
git-create check [PATH] [--offline] [--json] [--strict]
git-create scan [PATH] [--depth N] [--json]
git-create --version
git-create --help
```

Examples:

```bash
git-create check
git-create check ~/Projects/my-project --offline
git-create check . --json
git-create check . --strict
git-create scan ~/Projects --depth 3
git-create scan . --json
```

`check` exit codes:

- `0`: no failures (warnings are allowed unless `--strict`)
- `1`: at least one failure, or a warning with `--strict`
- `2`: path is not a Git repository or is invalid

`--offline` skips remote, GitHub API, and `git fsck` checks. JSON output has
the same check sections and summary counts as the human-readable report.
Global options `--no-color` and `--debug` are accepted before or after the
subcommand. The `NO_COLOR` environment variable also disables colors.

## Safety model

- **No force push.** The app never passes `--force` or `--force-with-lease`.
- **No history rewrite.** It does not run `filter-repo`, `rebase -i`, `reset
  --hard`, or `clean -fdx`.
- **No destructive resets.** Staging can be cancelled. Risky staged paths are
  unstaged without touching working-tree files.
- **No silent secret commit.** Sensitive filenames and common secret patterns
  block the commit unless you deliberately type `COMMIT`.
- **No silent file overwrite.** Templates are created only when missing.
- **No silent config changes.** The global settings wizard prints the planned
  changes and asks for confirmation.
- **Backups before divergence work.** Scenario D offers a local backup branch
  before any fast-forward pull.
- **Read-only diagnosis.** Fetch is read-only. Push is a normal push.

Secrets that were already pushed cannot be fixed by deleting the file in a new
commit. Rotate the credential first, then consider history rewriting with a
dedicated tool.

## Limitations

- GitHub-specific operations require `gh`; generic Git remotes still work for
  verification, commit, and push.
- SSH signing verification requires `gpg.ssh.allowedSignersFile`.
- Renaming a repository on a non-GitHub host must be done manually.
- The secret scan is a guardrail, not a complete security scanner. It checks
  common private-key and token patterns and has file/size limits.
- Binary files and files larger than 1 MiB are not content-scanned.
- The app does not manage GitHub branch protection, secrets, releases, or
  organization permissions.
- `git fsck` is only run in full/deep verification.
- Menu actions are non-interactive where possible, so SSH keys with
  passphrases should be loaded into `ssh-agent` before pushing.

## Troubleshooting

### `gh` is not authenticated

```bash
gh auth login --hostname github.com --git-protocol ssh
gh auth status --hostname github.com
```

### Adding a signing key fails with a missing scope

```bash
gh auth refresh -h github.com -s admin:ssh_signing_key
gh ssh-key add ~/.ssh/<your-key>.pub --type signing
```

### SSH signing fails or signatures show as unknown

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/<your-key>.pub
git config --global commit.gpgsign true
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/<your-key>
gh auth refresh -h github.com -s admin:ssh_signing_key
gh ssh-key add ~/.ssh/<your-key>.pub --type signing
```

`gpg.ssh.allowedSignersFile` can be generated by option 10. It is needed for
local verification, not for creating the signature.

### Push rejected: non-fast-forward

Do not use `--force`. Run option **7** (scenario D), compare the graph, keep a
backup branch, and merge or rebase deliberately after reviewing the changes.

### Renamed folder but the shell still shows the old path

```bash
cd /path/to/new-name
```

The running app updates its own active project. A new shell starts in the new
path. If the folder was a linked worktree, option 9 uses `git worktree move` so
Git metadata stays correct.

### The secret scan reports a test fixture

Review the file. If it is definitely a harmless fixture and you intend to
publish it, the commit flow asks you to type `COMMIT`. Otherwise cancel; risky
paths are unstaged automatically.

## Development and validation

The application is intentionally one file. There is no build system and no
dependency file.

Validate syntax without creating bytecode in the repository:

```bash
python3 -c "compile(open('git-create').read(), 'git-create', 'exec')"
```

Run the non-interactive self-check:

```bash
./git-create check --offline
./git-create check --offline --json | python3 -m json.tool
./git-create scan . --depth 2
```

Run the menu:

```bash
./git-create
```

Use a temporary `HOME` when testing settings or signing changes so your real
Git configuration is not touched:

```bash
tmp=$(mktemp -d)
HOME="$tmp" ./git-create
```

## Repository layout

```text
git-create      # the complete application (Python, executable)
README.md       # this documentation
.gitignore      # repository hygiene for the app itself
.dockerignore   # keeps the Docker context clean if one is ever added
.editorconfig   # consistent indentation and line endings across editors
```

The application is still distributed as the single `git-create` file. The
README and `.gitignore` are repository files, not runtime dependencies.
