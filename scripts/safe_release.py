"""Safe release workflow with conflict prevention and pre-commit integration."""

import os
from pathlib import Path
import subprocess
import sys


def run(
    cmd: list[str],
    check: bool = True,
    cwd: Path | None = None,
    capture_output: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run command and return result."""
    print(f"$ {' '.join(cmd)}")
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)
    return subprocess.run(
        cmd, check=check, capture_output=capture_output, text=True, cwd=cwd, env=cmd_env
    )


def run_interactive(
    cmd: list[str],
    check: bool = True,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run command with live output (no capture)."""
    print(f"$ {' '.join(cmd)}")
    cmd_env = os.environ.copy()
    if env:
        cmd_env.update(env)
    result = subprocess.run(cmd, check=check, text=True, cwd=cwd, env=cmd_env)
    return result


def main() -> None:
    """Execute safe release workflow."""
    print("\n=== Safe Release Workflow ===\n")

    # 0. Check we're in the right directory
    if not Path("pyproject.toml").exists():
        print("ERROR: Run this from project root!")
        sys.exit(1)

    # 1. Check clean working tree
    result = run(["git", "status", "--porcelain"], check=False)
    if result.stdout.strip():
        print("ERROR: Working tree is not clean!")
        print("Commit or stash changes first.")
        print(result.stdout)
        sys.exit(1)
    print("OK: Working tree is clean\n")

    # 2. Sync with remote
    print("Step 1: Syncing with remote...")
    run(["git", "fetch", "origin", "--tags"])

    # Check if behind
    local = run(["git", "rev-parse", "@"]).stdout.strip()
    try:
        remote = run(["git", "rev-parse", "@{u}"]).stdout.strip()
    except subprocess.CalledProcessError:
        print("WARNING: No upstream branch set")
        remote = local

    if local != remote:
        print("ERROR: Local branch is not in sync with remote!")
        print("Run: git pull --tags origin main")
        sys.exit(1)

    print("   OK: In sync with remote\n")

    # 3. Check for existing unreleased commits
    result = run(["git", "describe", "--tags", "--abbrev=0"], check=False)
    if result.returncode == 0:
        last_tag = result.stdout.strip()
        print(f"Step 2: Checking commits since {last_tag}")

        # Count commits since last tag
        result = run(["git", "rev-list", f"{last_tag}..HEAD", "--count"])
        commit_count = int(result.stdout.strip())

        if commit_count == 0:
            print("   No new commits since last release")
            print("   Nothing to release!")
            sys.exit(0)

        print(f"   {commit_count} new commit(s) to release\n")
    else:
        print("Step 2: No previous tags found (first release)\n")

    # 4. Preview next version
    print("Step 3: Calculating next version...")
    result = run(["semantic-release", "version", "--print"], check=False)
    if result.returncode != 0:
        print("ERROR: Failed to calculate next version")
        print(result.stderr)
        sys.exit(1)

    next_version = result.stdout.strip()
    print(f"   Next version: {next_version}\n")

    # 5. Confirm
    response = input(f"Create release {next_version}? [y/N]: ")
    if response.lower() != "y":
        print("Release cancelled")
        sys.exit(0)

    # 6. Create release (local only)
    print("\nStep 4: Creating release (local only)...")
    print("   Running: check → semantic-release → changelog → finalize")
    print("   (This may take a few minutes...)\n")

    try:
        # Run release with SKIP=uv-lock to prevent lockfile updates during release
        result = run_interactive(
            ["uv", "run", "poe", "release"], env={"SKIP": "uv-lock"}
        )
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Release failed: {e}")
        print("\nPossible causes:")
        print("  - Tests failed (run: uv run poe test)")
        print("  - Type checks failed (run: uv run poe pyright)")
        print("  - No commits since last release")
        sys.exit(1)

    # 7. Verify release was created
    print("\nStep 5: Verifying release...\n")
    result = run(["git", "log", "-1", "--oneline"])
    release_commit = result.stdout.strip()
    print(f"   Commit: {release_commit}")

    # Check tag on HEAD
    result = run(["git", "describe", "--tags", "--exact-match"], check=False)
    if result.returncode == 0:
        created_tag = result.stdout.strip()
        print(f"   Tag: {created_tag}")
    else:
        print("\nERROR: No tag found on HEAD")
        print("The finalize_release script should have created a tag")
        print("Check the release output above for errors")
        sys.exit(1)

    # 8. Final confirmation before push
    print("\n" + "=" * 50)
    response = input("\nPush to remote? [y/N]: ")
    if response.lower() == "y":
        print("\nStep 6: Pushing to remote...")

        # Try to push main branch
        try:
            run_interactive(["git", "push", "origin", "main"], check=True)
            print("   OK: main branch pushed")
        except subprocess.CalledProcessError:
            print("\nERROR: Push rejected (remote has changes)")
            print("\nThis usually means:")
            print("  - Someone else pushed to main")
            print("  - You have multiple machines with uncommitted work")
            print("\nRecommended fix:")
            print("  1. Abort this release: git reset --hard HEAD~1")
            print(f"  2. Delete the tag: git tag -d {created_tag}")
            print("  3. Pull latest changes: git pull origin main")
            print("  4. Re-run: uv run poe safe_release")
            print("\nThis ensures a clean, conflict-free release.")
            sys.exit(1)

        # Push tag with force (in case it was moved)
        print(f"\nPushing tag {created_tag}...")
        try:
            run_interactive(
                ["git", "push", "origin", created_tag, "--force"], check=True
            )
            print(f"   OK: Tag {created_tag} pushed")
        except subprocess.CalledProcessError:
            print(f"\nERROR: Failed to push tag {created_tag}")
            print("This is unexpected. Try manually:")
            print(f"  git push origin {created_tag} --force")
            sys.exit(1)

        print("\n" + "=" * 50)
        print("✅ Release pushed successfully!")
        print("\nThe GitHub Release workflow will now:")
        print("  1. Build wheels for Linux, Windows, macOS")
        print("  2. Publish to PyPI")
        print("  3. Create GitHub Release with artifacts")
        print("\nMonitor progress at:")
        print("  https://github.com/taeyun16/playfast/actions")
    else:
        print("\n" + "=" * 50)
        print("Release created locally (not pushed)")
        print("\nTo push manually later:")
        print("  git push origin main")
        print(f"  git push origin {created_tag} --force")
        print("\nTo undo this release:")
        print("  git reset --hard HEAD~1")
        print(f"  git tag -d {created_tag}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Command failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nRelease cancelled by user")
        sys.exit(1)
