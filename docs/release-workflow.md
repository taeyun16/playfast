# Release Workflow

This document describes the simplified release flow for Playfast.

## Overview

Release automation is split into two focused workflows:

- **semantic-release**: calculates next version from conventional commits
- **version workflow**: creates the release commit + tag on `main`/`master`
- **release workflow**: builds wheels/sdist and publishes when the tag is pushed
- **build_command hook**: syncs `CHANGELOG.md` to `docs/changelog.md` and keeps `uv.lock` aligned

No custom finalize/tag-move scripts are used.

## Automated Flow

1. Merge conventional commits to `main` or `master`.
1. `.github/workflows/version.yml` runs `semantic-release version`.
1. semantic-release updates versions in `pyproject.toml`, `Cargo.toml`, and `uv.lock`.
1. semantic-release updates `CHANGELOG.md` and syncs `docs/changelog.md`.
1. The workflow pushes the release commit and `vX.Y.Z` tag.
1. The tag triggers `.github/workflows/release.yml`, which builds and publishes artifacts.

The version workflow must use `secrets.RELEASE_TOKEN`, not the default `GITHUB_TOKEN`.
GitHub does not start most follow-up workflows from events created with `GITHUB_TOKEN`, so
the tag push would not trigger `release.yml` unless a PAT or GitHub App token is used.

Required repository secret:

| Name | Purpose |
| ---- | ------- |
| `RELEASE_TOKEN` | Fine-grained PAT or GitHub App token with `contents: write`, used to push release commits and tags |

## Commands

Local commands remain available for previewing or recovering a release manually.

### 1. Preview next version

```bash
uv run poe version_check
```

### 2. Create local release (no push)

```bash
uv run poe release
```

What this does:

1. Runs `check` (fmt, lint, type checks, tests)
1. Runs `semantic-release version --no-push`
1. Updates versions in:
   - `pyproject.toml`
   - `Cargo.toml`
   - `uv.lock`
1. Updates `CHANGELOG.md`
1. Syncs `docs/changelog.md` via `python -m scripts.sync_changelog`
1. Creates release commit + tag (`vX.Y.Z`)

### 3. Push local release

```bash
uv run poe release_push
```

Equivalent to:

```bash
git push origin main --follow-tags
```

Pushing the tag triggers the GitHub release workflow (`.github/workflows/release.yml`)
when the push is made with a normal user token or SSH key.

## Conventional Commits

Version bumps follow conventional commits:

- `feat:` -> minor
- `fix:`, `perf:`, `refactor:`, `docs:`, `chore:`, `ci:`, `build:` -> patch
- `BREAKING CHANGE:` -> major

## Troubleshooting

### Version workflow fails before checkout

Check that `RELEASE_TOKEN` exists in repository Actions secrets and has `contents: write`.

### Version tag was created but release workflow did not run

Check whether the tag was pushed with `GITHUB_TOKEN`. If so, push the tag with a PAT,
GitHub App token, SSH key, or the configured `RELEASE_TOKEN`.

### No version bump detected

Check recent commits:

```bash
git log --oneline -10
uv run poe version_check
```

### Release command failed during checks

Run checks directly and fix failures:

```bash
uv run poe check
```

### Tag already exists remotely

If needed, remove and re-push tag carefully:

```bash
git push origin :refs/tags/vX.Y.Z
git tag -d vX.Y.Z
git tag vX.Y.Z
git push origin vX.Y.Z
```

## Why this is simpler

- No commit amend loop
- No local tag relocation logic
- No duplicate release orchestration script
- Fewer moving parts while preserving automation
