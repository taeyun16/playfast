# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.2] - 2025-10-31

### 🐛 Bug Fixes

- Resolve OpenSSL build failure and tag movement issues (4a32dcd)

### 🔧 Miscellaneous Tasks

- **release:** 0.5.2 (b457a16)

## [0.5.1] - 2025-10-31

### 🐛 Bug Fixes

- Add vendored OpenSSL for manylinux builds (96e4d7f)

### 🔧 Miscellaneous Tasks

- Update uv.lock for OpenSSL vendored feature (aaa9af1)
- **release:** 0.5.1 (06fb6f8)

## [0.5.0] - 2025-10-31

### 🐛 Bug Fixes

- Safe_release with auto-recovery and better error handling (7b11c7a)
- Add future annotations import to conftest.py for Python 3.11/3.12 (b95bead)
- Move standalone test scripts causing CI failure (b0b0ed5)
- Move integration test scripts requiring APK files to examples (5eeafb6)
- Improve safe_release to work seamlessly with pre-commit hooks (8ca9335)

### 📚 Documentation

- Specify branch in CI badge URL to improve cache consistency (8c26d5e)

### 🔧 Miscellaneous Tasks

- **release:** 0.5.0 (1e7d0a3)
- **release:** 0.5.0 (83d9104)

### 🚀 Features

- Add APK downloader and comprehensive type safety improvements (76f251b)

## [0.4.0] - 2025-10-14

### ♻️ Refactor

- Improve type hints and file handling in various scripts (8c22924)

### ⚡ Performance

- **ci:** Add path filters to skip CI on docs-only changes (2cb1466)

### 📚 Documentation

- Add semantic-release commit author configuration section (b7f07e7)
- Add multiple installation methods (pip, uv, poetry) (cf18f7d)
- Add CI/CD optimization guide with path filtering explanation (3f82b1a)

### 🔧 Miscellaneous Tasks

- Add project URLs for source, documentation, and changelog (b001425)
- **release:** 0.4.0 (ffc0e84)
- **release:** 0.4.0 (23b3c71)
- Apply mdformat and markdownlint fixes (b9209bc)
- Migrate pre-commit config to fix deprecated stage names (9065ace)
- Configure semantic-release commit author (310ed38)
- Bump version to 0.5.0 to resolve tag conflict (d11ccc5)

### 🚀 Features

- Add release workflow documentation and finalize release script (7dd6c55)
- Automate version synchronization across all files (66ca1d6)
- Enhance CI configuration with specific dependency groups for faster installs (649d9e5)

## [0.3.2] - 2025-10-14

### 🐛 Bug Fixes

- **release:** Remove aarch64 builds to avoid ring cross-compilation errors (6e505a1)

### 🔧 Miscellaneous Tasks

- **release:** 0.3.2 (3706b99)

## [0.3.1] - 2025-10-14

### ⚡ Performance

- **ci:** Add mold linker for faster Rust builds on Linux (2ac8114)
- **ci:** Optimize Windows builds with rust-lld linker (f72158c)
- **ci:** Skip full test suite on Windows/macOS to reduce CI time (7399f0d)
- **ci:** Remove Windows from CI to reduce build time by 44% (36101c9)

### 🐛 Bug Fixes

- Remove --strict flag from mkdocs build to allow documentation warnings (be8cb76)
- Create virtual environment before installing docs dependencies (1fced98)
- **ci:** Add sccache fallback when GitHub cache service is unavailable (26c9c63)
- **ci:** Temporarily disable sccache due to GitHub cache service outage (c356793)
- **release:** Remove Windows ARM64 due to target specification error (df29e2f)
- Replace OpenSSL with rustls for cross-platform compatibility (58e8975)

### 💄 Styling

- Format generate_changelog.py with ruff (ee1be49)

### 📚 Documentation

- Update copyright year to 2024-2025 (b840732)

### 🔧 Miscellaneous Tasks

- Use PyO3/maturin-action for standard cross-platform builds (1524233)
- Optimize test matrix to reduce CI time (e318baf)
- Optimize documentation workflow for faster builds (20c931d)
- Remove redundant build-test job (e728757)
- Optimize GitHub Actions workflows for faster builds (9adb91b)
- **release:** 0.3.1 (93027c7)

## [0.3.0] - 2025-10-14

### 🐛 Bug Fixes

- Separate release tasks for local and remote push (d181a87)

### 📚 Documentation

- Add setup guide for badges and GitHub Pages deployment (38eedfa)

### 🔧 Miscellaneous Tasks

- Remove setup guide and update README with actual Gist ID (9ac46f9)
- **release:** 0.3.0 (58d8130)

### 🚀 Features

- Add coverage badge and GitHub Pages documentation deployment (a2161da)

## [0.2.2] - 2025-10-14

### 🔧 Miscellaneous Tasks

- Replace Codecov with GitHub native coverage artifact upload (6df1985)
- **release:** 0.2.2 (306a506)

## [0.2.1] - 2025-10-14

### 🐛 Bug Fixes

- Use environment variable for version to avoid PowerShell parsing issues (6fc27ec)
- Use shell=True on Windows for uv command in changelog generation (eab572c)
- Use python directly in build_command for semantic-release compatibility (b3d1361)
- Disable build_command to avoid bash compatibility issues on Windows (68a3dad)

### 🔧 Miscellaneous Tasks

- Prepare for release 0.2.1 (f18d6f3)

## [0.2.0] - 2025-10-14

### 🐛 Bug Fixes

- Exclude CHANGELOG from pre-commit hooks to prevent semantic-release conflicts (42ea823)
- Skip uv-lock hook during semantic-release commits (d94dfd5)

### 📚 Documentation

- Add changelog for v0.1.0 (385cb29)
- Correct country/store counts (247 countries, 93 unique stores) (fbc7f70)

### 🔧 Miscellaneous Tasks

- Auto-sync CHANGELOG to docs via pre-commit hook (60e87a2)
- Update GitHub username from placeholder to taeyun16 (a769e82)
- Add GitHub Actions workflows for CI/CD and PyPI release (e7c054d)
- Configure semantic-release and git-cliff for automated releases (ec27b2d)
- Add Python script for CHANGELOG generation (5aa6a6e)
- **release:** 0.2.0 (d80e5cb)

### 🚀 Features

- Auto-sync CHANGELOG to docs folder during generation (8cdaf28)

## [0.1.0] - 2025-10-14

### 🔧 Miscellaneous Tasks

- Disable MD024 for changelog automation (2d2fe9c)

### 🚀 Features

- Initial implementation (3bc441a)

<!-- generated by git-cliff -->
