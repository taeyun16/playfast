"""High-level API for APK analysis.

This module provides a convenient Python wrapper around the Rust core
for analyzing Android APK files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from playfast import core


class ApkAnalyzer:
    """High-level interface for analyzing APK files.

    This class provides convenient methods for extracting information
    from Android APK files including DEX classes, methods, manifest data,
    and more.

    Example:
        >>> analyzer = ApkAnalyzer("app.apk")
        >>> manifest = analyzer.manifest
        >>> print(f"Package: {manifest.package_name}")
        >>> print(f"Activities: {len(manifest.activities)}")
        >>>
        >>> # Search for specific classes
        >>> activities = analyzer.find_activities(package="com.example")
        >>> for activity in activities:
        ...     print(activity.class_name)

    """

    def __init__(self, apk_path: str | Path, load_classes: bool = False) -> None:
        """Initialize the APK analyzer.

        Args:
            apk_path: Path to the APK file
            load_classes: If True, load all classes immediately (default: False)

        Raises:
            Exception: If APK cannot be opened or is invalid

        """
        self.apk_path = Path(apk_path)
        if not self.apk_path.exists():
            msg = f"APK file not found: {self.apk_path}"
            raise FileNotFoundError(msg)

        self._apk_path_str = str(self.apk_path)
        self._manifest: core.RustManifestInfo | None = None
        self._classes: list[core.RustDexClass] | None = None

        # Load basic APK info
        self._load_info()

        if load_classes:
            self.load_classes()

    def _load_info(self) -> None:
        """Load basic APK information."""
        dex_count, has_manifest, has_resources, dex_files = core.extract_apk_info(
            self._apk_path_str
        )
        self.dex_count = dex_count
        self.has_manifest = has_manifest
        self.has_resources = has_resources
        self.dex_files = dex_files

    @property
    def manifest(self) -> core.RustManifestInfo:
        """Get parsed AndroidManifest.xml.

        Returns:
            RustManifestInfo: Parsed manifest information

        """
        if self._manifest is None:
            self._manifest = core.parse_manifest_from_apk(self._apk_path_str)
        return self._manifest

    def load_classes(self, parallel: bool = True) -> list[core.RustDexClass]:
        """Load all classes from the APK.

        Args:
            parallel: Use parallel processing (default: True)

        Returns:
            List of RustDexClass objects

        """
        if self._classes is None:
            self._classes = core.extract_classes_from_apk(
                self._apk_path_str, parallel=parallel
            )
        return self._classes

    @property
    def classes(self) -> list[core.RustDexClass]:
        """Get all classes (loads if not already loaded).

        Returns:
            List of RustDexClass objects

        """
        return self.load_classes()

    def find_classes(
        self,
        package: str | None = None,
        exclude_packages: list[str] | None = None,
        name: str | None = None,
        limit: int | None = None,
        parallel: bool = True,
    ) -> list[core.RustDexClass]:
        """Find classes matching the specified criteria.

        Args:
            package: Package name prefix to match (e.g., "com.example")
            exclude_packages: List of package prefixes to exclude
            name: Class name substring to match
            limit: Maximum number of results
            parallel: Use parallel processing (default: True)

        Returns:
            List of matching RustDexClass objects

        Example:
            >>> # Find all Activity classes
            >>> activities = analyzer.find_classes(name="Activity")
            >>>
            >>> # Find classes in specific package
            >>> classes = analyzer.find_classes(package="com.example.ui")
            >>>
            >>> # Exclude system packages
            >>> app_classes = analyzer.find_classes(exclude_packages=["android", "androidx"])

        """
        # Build ClassFilter object
        # Note: packages parameter takes a list
        packages = [package] if package else None
        class_filter = core.ClassFilter(
            class_name=name,
            packages=packages,
            exclude_packages=exclude_packages,
        )
        return core.search_classes(
            self._apk_path_str,
            class_filter,
            limit=limit,
            parallel=parallel,
        )

    def find_methods(
        self,
        method_name: str | None = None,
        param_count: int | None = None,
        return_type: str | None = None,
        class_package: str | None = None,
        class_name: str | None = None,
        limit: int | None = None,
        parallel: bool = True,
    ) -> list[tuple[core.RustDexClass, core.RustDexMethod]]:
        """Find methods matching the specified criteria.

        Args:
            method_name: Method name substring to match
            param_count: Exact parameter count
            return_type: Return type to match
            class_package: Package name for class filter
            class_name: Class name for class filter
            limit: Maximum number of results
            parallel: Use parallel processing (default: True)

        Returns:
            List of (RustDexClass, RustDexMethod) tuples

        Example:
            >>> # Find onCreate methods
            >>> methods = analyzer.find_methods(method_name="onCreate")
            >>> for cls, method in methods:
            ...     print(f"{cls.class_name}.{method.name}")
            >>>
            >>> # Find getter methods (no parameters)
            >>> getters = analyzer.find_methods(method_name="get")
            >>>
            >>> # Find methods in specific class
            >>> string_methods = analyzer.find_methods(class_name="String")

        """
        # Build ClassFilter and MethodFilter objects
        packages = [class_package] if class_package else None
        class_filter = core.ClassFilter(
            class_name=class_name,
            packages=packages,
        )
        method_filter = core.MethodFilter(
            method_name=method_name,
            param_count=param_count,
            return_type=return_type,
        )
        return core.search_methods(
            self._apk_path_str,
            class_filter,
            method_filter,
            limit=limit,
            parallel=parallel,
        )

    # Convenience methods for common searches

    def find_activities(
        self, package: str | None = None, limit: int | None = None
    ) -> list[core.RustDexClass]:
        """Find Activity classes.

        Args:
            package: Optional package filter
            limit: Maximum number of results

        Returns:
            List of Activity classes

        """
        return self.find_classes(package=package, name="Activity", limit=limit)

    def find_services(
        self, package: str | None = None, limit: int | None = None
    ) -> list[core.RustDexClass]:
        """Find Service classes.

        Args:
            package: Optional package filter
            limit: Maximum number of results

        Returns:
            List of Service classes

        """
        return self.find_classes(package=package, name="Service", limit=limit)

    def find_receivers(
        self, package: str | None = None, limit: int | None = None
    ) -> list[core.RustDexClass]:
        """Find BroadcastReceiver classes.

        Args:
            package: Optional package filter
            limit: Maximum number of results

        Returns:
            List of BroadcastReceiver classes

        """
        return self.find_classes(package=package, name="Receiver", limit=limit)

    def get_app_classes(self, limit: int | None = None) -> list[core.RustDexClass]:
        """Get application classes (excluding android/androidx packages).

        Args:
            limit: Maximum number of results

        Returns:
            List of application classes

        """
        return self.find_classes(
            exclude_packages=["android", "androidx", "com.google", "kotlin", "kotlinx"],
            limit=limit,
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the APK.

        Returns:
            Dictionary with APK statistics

        """
        classes = self.load_classes()

        total_methods = sum(len(cls.methods) for cls in classes)
        total_fields = sum(len(cls.fields) for cls in classes)

        manifest = self.manifest

        return {
            "package_name": manifest.package_name,
            "version_name": manifest.version_name,
            "version_code": manifest.version_code,
            "min_sdk": manifest.min_sdk_version,
            "target_sdk": manifest.target_sdk_version,
            "dex_count": self.dex_count,
            "class_count": len(classes),
            "method_count": total_methods,
            "field_count": total_fields,
            "activity_count": len(manifest.activities),
            "service_count": len(manifest.services),
            "receiver_count": len(manifest.receivers),
            "provider_count": len(manifest.providers),
            "permission_count": len(manifest.permissions),
        }

    def get_all_packages(self) -> list[str]:
        """Get all unique package names used in the APK.

        Returns:
            Sorted list of unique package names

        Example:
            >>> packages = analyzer.get_all_packages()
            >>> print(f"Total packages: {len(packages)}")
            >>> print("Top-level packages:")
            >>> for pkg in packages[:10]:
            ...     print(f"  - {pkg}")

        """
        classes = self.load_classes()
        packages = set()

        for cls in classes:
            if cls.package_name:
                packages.add(cls.package_name)

        return sorted(packages)

    def get_package_groups(self) -> dict[str, list[str]]:
        """Group packages by top-level domain.

        Returns:
            Dictionary mapping top-level package to list of sub-packages

        Example:
            >>> groups = analyzer.get_package_groups()
            >>> for top_level, pkgs in groups.items():
            ...     print(f"{top_level}: {len(pkgs)} packages")

        """
        packages = self.get_all_packages()
        groups: dict[str, list[str]] = {}

        for pkg in packages:
            parts = pkg.split(".")
            if len(parts) >= 2:
                top_level = f"{parts[0]}.{parts[1]}"
            else:
                top_level = parts[0]

            if top_level not in groups:
                groups[top_level] = []
            groups[top_level].append(pkg)

        return groups

    def get_third_party_libraries(self) -> dict[str, int]:
        """Identify third-party libraries used in the APK.

        Returns:
            Dictionary mapping library name to package count

        Example:
            >>> libs = analyzer.get_third_party_libraries()
            >>> for lib, count in sorted(libs.items(), key=lambda x: -x[1])[:10]:
            ...     print(f"{lib}: {count} packages")

        """
        groups = self.get_package_groups()

        # Filter out app-specific packages
        app_package = self.manifest.package_name
        app_prefix = ".".join(app_package.split(".")[:2])

        third_party = {}
        for top_level, pkgs in groups.items():
            # Skip app's own packages
            if top_level == app_prefix:
                continue

            # Common third-party libraries
            if any(
                top_level.startswith(prefix)
                for prefix in [
                    "com.google",
                    "com.facebook",
                    "com.meta",
                    "androidx",
                    "android.support",
                    "com.android",
                    "kotlinx",
                    "kotlin",
                    "org.jetbrains",
                    "com.squareup",
                    "io.reactivex",
                    "com.jakewharton",
                    "org.chromium",
                    "com.fasterxml",
                    "com.github",
                ]
            ):
                third_party[top_level] = len(pkgs)

        return third_party

    def find_webview_usage(self) -> dict[str, Any]:
        """Find WebView usage in the APK.

        Returns:
            Dictionary with WebView usage information

        Example:
            >>> usage = analyzer.find_webview_usage()
            >>> print(f"WebView classes: {usage['class_count']}")
            >>> print(f"Methods using WebView: {usage['method_count']}")

        """
        # Find WebView classes
        webview_classes = self.find_classes(name="WebView")

        # Find methods that use WebView
        webview_methods = []
        classes = self.load_classes()

        for cls in classes:
            for method in cls.methods:
                has_webview = False

                # Check return type
                if "WebView" in method.return_type:
                    has_webview = True

                # Check parameters
                if not has_webview:
                    for param in method.parameters:
                        if "WebView" in param:
                            has_webview = True
                            break

                if has_webview:
                    webview_methods.append((cls, method))

        return {
            "class_count": len(webview_classes),
            "classes": [cls.class_name for cls in webview_classes],
            "method_count": len(webview_methods),
            "methods": [
                {
                    "class": cls.class_name,
                    "method": method.name,
                    "parameters": method.parameters,
                    "return_type": method.return_type,
                }
                for cls, method in webview_methods
            ],
        }

    # Data Flow Analysis (High-level API)

    def analyze_entry_points(self) -> dict[str, Any]:
        """Analyze Android entry points (Activity, Service, etc.).

        Returns:
            Dictionary with:
            - entry_points: List of EntryPoint objects
            - deeplink_handlers: List of deeplink-capable entry points
            - stats: Statistics dictionary

        Example:
            >>> apk = ApkAnalyzer("app.apk")
            >>> analysis = apk.analyze_entry_points()
            >>> print(f"Entry points: {len(analysis['entry_points'])}")
            >>> print(f"Deeplink handlers: {len(analysis['deeplink_handlers'])}")

        """
        if not hasattr(self, "_entry_analysis"):
            analyzer = core.analyze_entry_points_from_apk(self._apk_path_str)
            self._entry_analysis = {
                "analyzer": analyzer,
                "entry_points": analyzer.analyze(),
                "deeplink_handlers": analyzer.get_deeplink_handlers(),
                "stats": analyzer.get_stats(),
            }
        return self._entry_analysis

    def find_webview_flows(
        self, max_depth: int = 10, optimize: bool = True
    ) -> list[core.Flow]:
        """Find data flows from entry points to WebView APIs.

        This performs advanced data flow analysis to find complete paths
        from Android entry points (Activity, Service, etc.) to WebView methods.

        Args:
            max_depth: Maximum call chain depth to analyze
            optimize: Use optimized filtering (32.8x faster, default: True)

        Returns:
            List of Flow objects with entry point → WebView paths

        Example:
            >>> apk = ApkAnalyzer("app.apk")
            >>> flows = apk.find_webview_flows(max_depth=10)
            >>>
            >>> for flow in flows:
            ...     print(f"{flow.entry_point} → {flow.sink_method}")
            ...     print(f"  Paths: {flow.path_count}")
            ...     if flow.is_deeplink_handler:
            ...         print("  ⚠️  Deeplink vulnerability!")

        """
        if optimize:
            # Use optimized version with entry-point filtering (32.8x faster)
            analyzer = core.create_data_flow_analyzer(self._apk_path_str)
            return analyzer.find_webview_flows(max_depth)
        else:
            # Full analysis (slower but more comprehensive)
            return core.find_webview_flows_from_apk(self._apk_path_str, max_depth)

    def find_file_flows(self, max_depth: int = 10) -> list[core.Flow]:
        """Find data flows from entry points to file I/O operations.

        Args:
            max_depth: Maximum call chain depth

        Returns:
            List of Flow objects with entry point → File I/O paths

        Example:
            >>> flows = apk.find_file_flows()
            >>> for flow in flows:
            ...     print(f"{flow.entry_point} → {flow.sink_method}")

        """
        analyzer = core.create_data_flow_analyzer(self._apk_path_str)
        return analyzer.find_file_flows(max_depth)

    def find_network_flows(self, max_depth: int = 10) -> list[core.Flow]:
        """Find data flows from entry points to network operations.

        Args:
            max_depth: Maximum call chain depth

        Returns:
            List of Flow objects with entry point → Network paths

        Example:
            >>> flows = apk.find_network_flows()
            >>> for flow in flows:
            ...     print(f"{flow.entry_point} → {flow.sink_method}")

        """
        analyzer = core.create_data_flow_analyzer(self._apk_path_str)
        return analyzer.find_network_flows(max_depth)

    def find_sql_flows(self, max_depth: int = 10) -> list[core.Flow]:
        """Find data flows from entry points to SQL operations.

        Args:
            max_depth: Maximum call chain depth

        Returns:
            List of Flow objects with entry point → SQL paths

        Example:
            >>> flows = apk.find_sql_flows()
            >>> for flow in flows:
            ...     print(f"{flow.entry_point} → {flow.sink_method}")

        """
        analyzer = core.create_data_flow_analyzer(self._apk_path_str)
        return analyzer.find_sql_flows(max_depth)

    def find_custom_flows(
        self, sink_patterns: list[str], max_depth: int = 10
    ) -> list[core.Flow]:
        """Find data flows from entry points to custom sink patterns.

        Args:
            sink_patterns: List of method name patterns to find
            max_depth: Maximum call chain depth

        Returns:
            List of Flow objects

        Example:
            >>> # Find flows to Runtime.exec (command execution)
            >>> flows = apk.find_custom_flows(["Runtime.exec", "ProcessBuilder.start"], max_depth=15)
            >>>
            >>> # Find flows to native library loading
            >>> flows = apk.find_custom_flows(["System.loadLibrary"])

        """
        analyzer = core.create_data_flow_analyzer(self._apk_path_str)
        return analyzer.find_flows_to(sink_patterns, max_depth)

    def find_deeplink_flows(
        self, sink_type: str = "webview", max_depth: int = 10
    ) -> list[core.Flow]:
        """Find flows from deeplink handlers to sinks.

        Args:
            sink_type: Type of sink ("webview", "file", "network", "sql")
            max_depth: Maximum call chain depth

        Returns:
            List of Flow objects from deeplink handlers

        Example:
            >>> # Find deeplink → WebView flows (potential XSS)
            >>> flows = apk.find_deeplink_flows(sink_type="webview")
            >>>
            >>> for flow in flows:
            ...     print(f"⚠️  Deeplink vulnerability:")
            ...     print(f"  {flow.entry_point} → {flow.sink_method}")

        """
        if sink_type == "webview":
            all_flows = self.find_webview_flows(max_depth)
        elif sink_type == "file":
            all_flows = self.find_file_flows(max_depth)
        elif sink_type == "network":
            all_flows = self.find_network_flows(max_depth)
        elif sink_type == "sql":
            all_flows = self.find_sql_flows(max_depth)
        else:
            msg = f"Unknown sink type: {sink_type}"
            raise ValueError(msg)

        # Filter only deeplink handlers
        return [f for f in all_flows if f.is_deeplink_handler]

    def __repr__(self) -> str:
        return f"ApkAnalyzer('{self.apk_path.name}', dex_count={self.dex_count})"

    def __str__(self) -> str:
        manifest = self.manifest
        return (
            f"APK: {self.apk_path.name}\n"
            f"Package: {manifest.package_name}\n"
            f"Version: {manifest.version_name or 'N/A'}\n"
            f"DEX files: {self.dex_count}\n"
            f"Activities: {len(manifest.activities)}\n"
            f"Services: {len(manifest.services)}\n"
            f"Permissions: {len(manifest.permissions)}"
        )
