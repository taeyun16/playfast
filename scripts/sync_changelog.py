"""Synchronize release-generated files."""

from pathlib import Path
import shutil
import sys
import tomllib


def _project_version(pyproject_path: Path) -> str:
    """Read the project version from pyproject.toml."""
    data = tomllib.loads(pyproject_path.read_text())
    return str(data["project"]["version"])


def sync_uv_lock_version(version: str) -> None:
    """Keep the editable playfast package entry in uv.lock in sync."""
    lock_path = Path("uv.lock")
    if not lock_path.exists():
        print("uv.lock not found; skipping lockfile version sync.")
        return

    lines = lock_path.read_text().splitlines(keepends=True)
    in_package = False
    package_name_seen = False
    changed = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "[[package]]":
            in_package = True
            package_name_seen = False
            continue

        if not in_package:
            continue

        if stripped.startswith("name = "):
            package_name_seen = stripped == 'name = "playfast"'
            continue

        if package_name_seen and stripped.startswith("version = "):
            newline = "\n" if line.endswith("\n") else ""
            replacement = f'version = "{version}"{newline}'
            if line != replacement:
                lines[index] = replacement
                changed = True
            break

    if changed:
        lock_path.write_text("".join(lines))
        print(f"Synchronized uv.lock playfast version -> {version}")
    else:
        print("uv.lock playfast version already synchronized.")


def main() -> None:
    """Copy changelog into docs and sync release metadata."""
    src = Path("CHANGELOG.md")
    dst = Path("docs/changelog.md")
    version = _project_version(Path("pyproject.toml"))

    if not src.exists():
        print("CHANGELOG.md not found; skipping docs sync.")
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"Synchronized {src} -> {dst}")

    sync_uv_lock_version(version)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - defensive CLI error path
        print(f"Failed to sync changelog: {exc}", file=sys.stderr)
        sys.exit(1)
