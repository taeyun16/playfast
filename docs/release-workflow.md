# Release Workflow

This document describes the simplified release flow for Playfast.

## Overview

Release automation is now intentionally minimal:

- **semantic-release**: calculates next version from conventional commits
- **single release command**: creates local release commit + tag
- **single push command**: pushes branch and tag
- **build_command hook**: syncs `CHANGELOG.md` to `docs/changelog.md`

No custom finalize/tag-move scripts are used.

## Commands

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
1. Updates `CHANGELOG.md`
1. Syncs `docs/changelog.md` via `python -m scripts.sync_changelog`
1. Creates release commit + tag (`vX.Y.Z`)

### 3. Push release

```bash
uv run poe release_push
```

Equivalent to:

```bash
git push origin main --follow-tags
```

Pushing the tag triggers the GitHub release workflow (`.github/workflows/release.yml`).

## Conventional Commits

Version bumps follow conventional commits:

- `feat:` -> minor
- `fix:`, `perf:`, `refactor:`, `docs:`, `chore:`, `ci:` -> patch
- `BREAKING CHANGE:` -> major

## Troubleshooting

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
