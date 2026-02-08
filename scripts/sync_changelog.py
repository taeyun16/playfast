"""Synchronize root changelog into docs for MkDocs."""

from pathlib import Path
import shutil
import sys


def main() -> None:
    """Copy root CHANGELOG into docs/changelog for MkDocs navigation."""
    src = Path("CHANGELOG.md")
    dst = Path("docs/changelog.md")

    if not src.exists():
        print("CHANGELOG.md not found; skipping docs sync.")
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"Synchronized {src} -> {dst}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - defensive CLI error path
        print(f"Failed to sync changelog: {exc}", file=sys.stderr)
        sys.exit(1)
