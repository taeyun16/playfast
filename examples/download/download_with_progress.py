#!/usr/bin/env python3
"""
Download APK with progress bar using tqdm.

This example demonstrates downloading APKs with real-time progress tracking.

Requirements:
    pip install tqdm

Usage:
    python download_with_progress.py PACKAGE_ID [VERSION_CODE]

Examples:
    # Download latest version
    python download_with_progress.py com.instagram.android

    # Download specific version
    python download_with_progress.py com.whatsapp 450814

    # Download multiple apps in parallel
    python download_with_progress.py com.app1 com.app2 com.app3
"""

import sys
from pathlib import Path
from playfast import ApkDownloader

try:
    from tqdm import tqdm
except ImportError:
    print("Error: tqdm is required for this example")
    print("Install it with: pip install tqdm")
    sys.exit(1)


def download_with_progress(
    downloader: ApkDownloader,
    package_id: str,
    version_code: int | None = None,
    output_path: Path | None = None
) -> str:
    """Download APK with tqdm progress bar.

    Args:
        downloader: Initialized ApkDownloader instance
        package_id: Package ID (e.g., "com.instagram.android")
        version_code: Optional specific version code
        output_path: Optional custom output directory

    Returns:
        str: Path to downloaded APK file
    """
    if output_path is None:
        output_path = Path("/tmp/playfast_apks")

    print(f"📦 Downloading {package_id}...")
    print(f"⏳ Preparing download...\n")

    # Create progress bar
    # Note: Total size is unknown at start (only base APK is downloaded, not all splits)
    # The bar will show bytes downloaded without percentage until complete
    with tqdm(
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        desc=f"Downloading {package_id}",
        miniters=1
    ) as pbar:

        def progress_callback(current_bytes: int, total_bytes: int) -> None:
            """Update progress bar with current download progress."""
            # Update to current position (total is unknown, so just show bytes)
            pbar.n = current_bytes
            pbar.refresh()

        # Start download with progress callback
        apk_path = downloader.download(
            package_id=package_id,
            dest_path=str(output_path),
            version_code=version_code,
            progress_callback=progress_callback
        )

    print(f"✅ Downloaded to: {apk_path}")
    print(f"📁 File size: {Path(apk_path).stat().st_size / (1024 * 1024):.2f} MB")

    return apk_path


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # Parse arguments
    package_ids = []
    version_code = None

    for arg in sys.argv[1:]:
        if arg.isdigit():
            version_code = int(arg)
        else:
            package_ids.append(arg)

    if not package_ids:
        print("Error: No package ID provided")
        print(__doc__)
        sys.exit(1)

    # Find credentials file
    creds_paths = [
        Path.home() / ".config" / "playfast" / "creds.json",
        Path.home() / ".config" / "playfast" / "credentials.json",
        Path.home() / ".playfast" / "credentials.json",
        Path("credentials.json"),
    ]

    creds_path = None
    for path in creds_paths:
        if path.exists():
            creds_path = path
            break

    if not creds_path:
        print("❌ Error: Credentials file not found")
        print("\nSearched in:")
        for path in creds_paths:
            print(f"  - {path}")
        print("\nPlease create credentials first:")
        print("  1. Get OAuth token from:")
        print("     https://accounts.google.com/EmbeddedSetup")
        print("  2. Run: python examples/download/setup_credentials.py")
        sys.exit(1)

    print(f"🔑 Loading credentials from: {creds_path}")

    # Initialize downloader
    try:
        downloader = ApkDownloader.from_credentials(str(creds_path))
        print(f"✅ Logged in as: {downloader.email}\n")
    except Exception as e:
        print(f"❌ Failed to initialize downloader: {e}")
        sys.exit(1)

    # Setup output directory
    output_path = Path("/tmp/playfast_apks")
    output_path.mkdir(parents=True, exist_ok=True)

    # Download each package
    for package_id in package_ids:
        try:
            download_with_progress(
                downloader=downloader,
                package_id=package_id,
                version_code=version_code,
                output_path=output_path
            )
            print()
        except Exception as e:
            print(f"❌ Failed to download {package_id}: {e}")
            print()


if __name__ == "__main__":
    main()
