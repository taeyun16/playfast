"""High-level API for downloading APKs from Google Play Store.

This module provides a convenient Python wrapper around the Rust Google Play API
client for downloading Android APK files.
"""

from collections.abc import Callable
from pathlib import Path

from playfast import core


class ApkDownloader:
    """High-level interface for downloading APKs from Google Play Store.

    This class provides convenient methods for authenticating with Google Play
    and downloading APK files.

    Example:
        >>> # First-time setup with OAuth token
        >>> downloader = ApkDownloader(email="user@gmail.com", oauth_token="oauth2_4/...")
        >>> downloader.login()
        >>> downloader.save_credentials("~/.playfast/credentials.json")
        >>>
        >>> # Subsequent use with saved credentials
        >>> downloader = ApkDownloader.from_credentials("~/.playfast/credentials.json")
        >>>
        >>> # Download APK
        >>> apk_path = downloader.download("com.instagram.android", "/tmp/apks")
        >>> print(f"Downloaded to: {apk_path}")

    """

    def __init__(
        self,
        email: str,
        oauth_token: str | None = None,
        aas_token: str | None = None,
        device: str = "px_9a",
        locale: str = "en_US",
        timezone: str = "America/New_York",
    ) -> None:
        """Initialize the APK downloader.

        Args:
            email: Google account email
            oauth_token: OAuth token for first-time setup (starts with "oauth2_4/")
            aas_token: AAS token for returning users (starts with "aas_et/")
            device: Device codename (default: "px_9a" for Pixel 9a)
            locale: Locale string (default: "en_US")
            timezone: Timezone string (default: "America/New_York")

        Note:
            You must provide either oauth_token or aas_token.

            OAuth token can be obtained from Google's embedded setup page:
            https://accounts.google.com/EmbeddedSetup

            Available devices: px_9a, px_7a, px_6a, ad_g3_pro, etc.
            See gpapi documentation for full list.

        Raises:
            ValueError: If neither oauth_token nor aas_token is provided

        """
        self.email = email
        self._client = core.GpapiClient(
            email=email,
            oauth_token=oauth_token,
            aas_token=aas_token,
            device=device,
            locale=locale,
            timezone=timezone,
        )
        self._logged_in = False

    @classmethod
    def from_credentials(cls, credentials_path: str | Path) -> "ApkDownloader":
        """Create downloader from saved credentials file.

        This is the recommended way for returning users - just load and go!

        Args:
            credentials_path: Path to credentials JSON file

        Returns:
            ApkDownloader: Initialized and logged-in downloader

        Example:
            >>> downloader = ApkDownloader.from_credentials("~/.playfast/credentials.json")
            >>> apk_path = downloader.download("com.instagram.android")

        """
        credentials_path = Path(credentials_path).expanduser()
        client = core.GpapiClient.from_credentials(str(credentials_path))

        # Create wrapper instance
        instance = cls.__new__(cls)
        instance.email = (
            client.email if hasattr(client, "email") else "loaded_from_file"
        )
        instance._client = client
        instance._logged_in = True

        return instance

    def login(self) -> None:
        """Login to Google Play Store.

        If oauth_token was provided but no aas_token, this will first exchange
        the OAuth token for an AAS token. Then performs device checkin and
        authentication.

        After successful login, you can save credentials using save_credentials().

        Raises:
            RuntimeError: If login fails

        """
        self._client.login()
        self._logged_in = True

    def save_credentials(self, path: str | Path) -> None:
        """Save credentials to JSON file for future use.

        The file will contain email, aas_token, device, locale, and timezone.
        File permissions are set to 0600 (owner read/write only) on Unix.

        Args:
            path: File path to save credentials

        Example:
            >>> downloader.login()
            >>> downloader.save_credentials("~/.playfast/credentials.json")

        """
        path = Path(path).expanduser()
        self._client.save_credentials(str(path))

    def get_aas_token(self) -> str:
        """Get current AAS token.

        Returns:
            str: AAS token string

        Raises:
            RuntimeError: If not logged in or no AAS token available

        """
        return self._client.get_aas_token()

    def download(
        self,
        package_id: str,
        dest_path: str | Path = "/tmp/playfast_apks",
        version_code: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> str:
        """Download APK file from Google Play Store.

        Args:
            package_id: Package ID (e.g., "com.instagram.android")
            dest_path: Destination directory for the APK (default: /tmp/playfast_apks)
            version_code: Specific version code to download (default: latest)
            progress_callback: Optional callback function(current_bytes: int, total_bytes: int)
                Called periodically (every 0.5 seconds) with download progress.
                current_bytes: Number of bytes downloaded so far
                total_bytes: Total expected size in bytes (0 if size unknown)

        Returns:
            str: Path to the downloaded APK file

        Raises:
            RuntimeError: If not logged in or download fails

        Note:
            Progress is monitored by polling the file size during download.
            The callback is called approximately every 500ms with current and total bytes.
            Use this with progress bars like tqdm or rich for visual feedback.

        Example:
            >>> # Simple download
            >>> apk_path = downloader.download("com.instagram.android")
            >>> print(f"Downloaded to: {apk_path}")
            >>>
            >>> # Download with progress tracking
            >>> from tqdm import tqdm
            >>> with tqdm(total=0, unit="B", unit_scale=True) as pbar:
            ...
            ...     def update_progress(current, total):
            ...         if pbar.total != total:
            ...             pbar.total = total
            ...         pbar.n = current
            ...         pbar.refresh()
            ...
            ...     apk_path = downloader.download("com.app", progress_callback=update_progress)

        """
        if not self._logged_in:
            msg = "Not logged in. Call login() first."
            raise RuntimeError(msg)

        dest_path = Path(dest_path).expanduser()
        dest_path.mkdir(parents=True, exist_ok=True)

        apk_path = self._client.download_apk(
            package_id=package_id,
            dest_path=str(dest_path),
            version_code=version_code,
            progress_callback=progress_callback,
        )

        return apk_path

    def get_package_details(self, package_id: str) -> str:
        """Get package details from Google Play Store.

        Args:
            package_id: Package ID (e.g., "com.instagram.android")

        Returns:
            str: Package details in debug format

        Raises:
            RuntimeError: If not logged in or query fails

        Note:
            Currently returns debug format string.
            Future versions will return a structured dict.

        Example:
            >>> details = downloader.get_package_details("com.instagram.android")
            >>> print(details)

        """
        if not self._logged_in:
            msg = "Not logged in. Call login() first."
            raise RuntimeError(msg)

        return self._client.get_package_details(package_id)

    @property
    def is_logged_in(self) -> bool:
        """Check if logged in to Google Play Store.

        Returns:
            bool: True if logged in, False otherwise

        """
        return self._logged_in

    def __repr__(self) -> str:
        """String representation of the downloader.

        Returns:
            str: Representation string

        """
        status = "logged in" if self._logged_in else "not logged in"
        return f"ApkDownloader(email='{self.email}', {status})"
