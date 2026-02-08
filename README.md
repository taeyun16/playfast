# Playfast ⚡

> Lightning-Fast Google Play Store Scraper

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Built with Rust](https://img.shields.io/badge/built%20with-Rust-orange.svg)](https://www.rust-lang.org/)
[![CI](https://github.com/taeyun16/playfast/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/taeyun16/playfast/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/taeyun16/6a5cda65b343fffe18719b3a9d6d6a3b/raw/playfast-coverage.json)](https://github.com/taeyun16/playfast/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/playfast?logo=python)](https://pypi.org/project/playfast/)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://taeyun16.github.io/playfast/)

Playfast is a high-performance Google Play Store scraper built with **Rust + PyO3**, delivering **5-10x faster performance** with true parallel batch processing.

## ✨ Features

### Play Store Scraping

- 🚀 **Blazingly Fast**: Batch API is 5-10x faster than sequential
- ⚡ **True Parallel**: Rust core completely releases GIL
- 🦀 **Pure Rust**: HTTP + parsing all in Rust for maximum performance
- 🔒 **Type Safe**: Full Pydantic validation and type hints
- 💾 **Memory Efficient**: Only 1.5 KB per app, linear scaling
- 🌍 **Multi-Country**: 247 countries, 93 unique Play Stores
- 📦 **Batch API**: High-level functions for easy parallel processing

### APK Download (NEW!)

- ⬇️ **Direct Download**: Download APKs directly from Google Play Store
- 🔐 **Smart Authentication**: OAuth → AAS token exchange with auto-retry
- 💾 **Credential Management**: Save and reuse authentication tokens
- 🎯 **Version Control**: Download specific versions or latest
- ⚡ **Parallel Downloads**: Efficient batch downloading with ThreadPoolExecutor

### APK/DEX Analysis

- 🔍 **Entry Point Analysis**: Identify Activities, Services, deeplink handlers
- 📊 **Call Graph**: Method-to-method relationship tracking
- 🌐 **WebView Flow**: Track paths from entry points to WebView APIs
- 🔗 **Data Flow**: Intent → WebView.loadUrl() data tracking
- 🛡️ **Security Analysis**: Deeplink vulnerability detection

## 📊 Performance

**Batch Processing** makes bulk operations **5-10x faster** through true Rust parallelism!

| Method                   | Time    | Speedup     |
| ------------------------ | ------- | ----------- |
| **Batch API**            | **~3s** | **6-8x** 🚀 |
| RustClient + ThreadPool  | ~3-4s   | 6-7x        |
| AsyncClient (concurrent) | ~3-5s   | 5-7x        |
| Sequential               | ~20-30s | 1x          |

*Benchmark: Fetching 3 apps across 3 countries (9 requests total)*

## 🚀 Quick Start

### Installation

**Using pip** (traditional):

```bash
pip install playfast
```

**Using uv** (recommended - faster):

```bash
uv add playfast
```

**Using poetry**:

```bash
poetry add playfast
```

### Option 1: Batch API (Recommended - Easiest & Fastest)

```python
from playfast import fetch_apps

# Fetch multiple apps across countries (parallel!)
apps = fetch_apps(
    app_ids=["com.spotify.music", "com.netflix.mediaclient"],
    countries=["us", "kr", "jp"],
)
print(f"Fetched {len(apps)} apps in ~3 seconds!")
```

### Option 2: RustClient (Maximum Performance)

```python
from playfast import RustClient

client = RustClient()

# Get app information (GIL-free!)
app = client.get_app("com.spotify.music")
print(f"{app.title}: {app.score}⭐ ({app.ratings:,} ratings)")

# Get reviews
reviews, next_token = client.get_reviews("com.spotify.music")
for review in reviews[:5]:
    print(f"{review.user_name}: {review.score}⭐")
```

### Option 3: AsyncClient (Easy Async)

```python
import asyncio
from playfast import AsyncClient


async def main():
    async with AsyncClient() as client:
        app = await client.get_app("com.spotify.music")
        print(f"{app.title}: {app.score}⭐")


asyncio.run(main())
```

### Option 4: APK Download (NEW!)

```python
from playfast import ApkDownloader

# First-time setup with OAuth token
downloader = ApkDownloader(
    email="user@gmail.com", oauth_token="oauth2_4/..."  # Get from Google embedded setup
)
downloader.login()
downloader.save_credentials("~/.playfast/credentials.json")

# Subsequent use - just load credentials
downloader = ApkDownloader.from_credentials("~/.playfast/credentials.json")

# Download APK
apk_path = downloader.download("com.instagram.android")
print(f"Downloaded to: {apk_path}")

# Download specific version
apk_path = downloader.download("com.whatsapp", version_code=450814)
```

### Option 5: APK/DEX Analysis

```python
from playfast import ApkAnalyzer

# High-level API
analyzer = ApkAnalyzer("app.apk")
manifest = analyzer.manifest
classes = analyzer.classes

print(f"Package: {manifest.package_name}")
print(f"Activities: {len(manifest.activities)}")
print(f"Classes: {len(classes)}")

# Advanced: WebView flow analysis (low-level API)
from playfast.core import analyze_webview_flows_from_apk

flows = analyze_webview_flows_from_apk("app.apk", max_depth=10)
for flow in flows:
    print(f"{flow.entry_point} → {flow.webview_method}")
    if flow.is_deeplink_handler:
        print("  ⚠️  DEEPLINK HANDLER")
```

### Complete Workflow: Download → Analyze

```python
from playfast import ApkDownloader, ApkAnalyzer

# Download APK from Google Play
downloader = ApkDownloader.from_credentials("~/.playfast/credentials.json")
apk_path = downloader.download("com.instagram.android")

# Analyze the downloaded APK
analyzer = ApkAnalyzer(apk_path)
manifest = analyzer.manifest

print(f"📦 {manifest.package_name}")
print(f"🔢 Version: {manifest.version_name} ({manifest.version_code})")
print(f"📱 Activities: {len(manifest.activities)}")
print(f"🔐 Permissions: {len(manifest.permissions)}")
```

## 📚 Examples

See the [`examples/`](examples/) directory for more:

### Play Store Scraping

- [`01_async_client.py`](examples/01_async_client.py) - AsyncClient basics
- [`02_rust_client.py`](examples/02_rust_client.py) - RustClient for max performance
- [`03_batch_api.py`](examples/03_batch_api.py) - High-level batch API
- [`04_countries_and_categories.py`](examples/04_countries_and_categories.py) - Country optimization

### APK Download

- [`download/auth_setup.py`](examples/download/auth_setup.py) - Interactive authentication setup
- [`download/download_apk.py`](examples/download/download_apk.py) - Download APKs with CLI
- [`download/batch_download.py`](examples/download/batch_download.py) - Parallel batch downloading

### APK/DEX Analysis

- [`apk/basic.py`](examples/apk/basic.py) - ApkAnalyzer high-level API
- [`apk/entry_point_demo.py`](examples/apk/entry_point_demo.py) - Entry point & deeplink detection
- [`apk/call_graph_demo.py`](examples/apk/call_graph_demo.py) - Method call relationship analysis
- [`apk/security_audit.py`](examples/apk/security_audit.py) - Security audit
- [`webview/flow_demo.py`](examples/webview/flow_demo.py) - Complete WebView flow analysis
- [`webview/high_level_api.py`](examples/webview/high_level_api.py) - High-level ApkAnalyzer API

## 📖 Documentation

### Play Store Scraping

- **[Getting Started](docs/getting_started.md)** - Installation and first steps
- **[Quick Start](docs/quick_start.md)** - Practical examples
- **[API Reference](docs/api/)** - Complete API documentation
- **[Batch API Guide](docs/BATCH_API.md)** - Batch processing guide

### APK Download

- **[APK Download Implementation](docs/development/plans/APK_DOWNLOAD_IMPLEMENTATION.md)** - Architecture and design
- **Authentication**: Get OAuth token from [Google Embedded Setup](https://accounts.google.com/EmbeddedSetup/identifier?flowName=EmbeddedSetupAndroid)

### APK/DEX Analysis

- **[WebView Flow Analysis](docs/WEBVIEW_FLOW_ANALYSIS.md)** - Complete guide to WebView security analysis
- **[Core API Review](docs/development/CORE_API_REVIEW.md)** - Low-level API usage guide

## 🏗️ Architecture

Playfast uses **pure Rust** for maximum performance:

```bash
┌─────────────────────────────────────────────────────┐
│   Python High-level API                             │
│   - ApkDownloader (APK download)                    │
│   - ApkAnalyzer (APK/DEX analysis)                  │
│   - Batch API (Play Store scraping)                 │
│   - RustClient / AsyncClient                        │
│   - Pydantic Models                                 │
└────────────────────┬────────────────────────────────┘
                     │ PyO3 Bindings
                     ▼
┌─────────────────────────────────────────────────────┐
│   Rust Core (playfast.core)                        │
│   - Google Play API (gpapi - APK download)          │
│   - HTTP Client (reqwest)                           │
│   - HTML Parser (scraper)                           │
│   - DEX Parser (custom)                             │
│   - Parallel Processing (rayon + tokio)             │
│   - Complete GIL Release                            │
└─────────────────────────────────────────────────────┘
```

### API Layers

| Layer          | Components                                | Use Case                             |
| -------------- | ----------------------------------------- | ------------------------------------ |
| **High-level** | `ApkDownloader`, `ApkAnalyzer`, Batch API | General users (90% of use cases)     |
| **Mid-level**  | `RustClient`, `AsyncClient`               | Direct scraping control              |
| **Low-level**  | `playfast.core.*`                         | Security research, advanced analysis |

### Client Options for Play Store Scraping

| Method          | Speed  | Ease   | Best For       |
| --------------- | ------ | ------ | -------------- |
| **Batch API**   | ⚡⚡⚡ | ⭐⭐⭐ | Multiple items |
| **RustClient**  | ⚡⚡⚡ | ⭐⭐   | Single items   |
| **AsyncClient** | ⚡⚡   | ⭐⭐   | Async code     |

## 🌍 Multi-Country Optimization

Playfast optimizes global data collection:

```python
from playfast import get_unique_countries, get_representative_country

# Instead of 247 countries, use 93 unique stores (2.7x faster!)
unique = get_unique_countries()  # 93 unique Play Stores

# Get representative for any country
rep = get_representative_country(
    "fi"
)  # Finland → Vanuatu store (shared by 138 countries)
```

## 🔧 Development

```bash
# Clone repository
git clone https://github.com/taeyun16/playfast.git
cd playfast

# Install dependencies
uv sync

# Build Rust extension
uv run maturin develop --release

# Run tests
uv run pytest

# Run examples
uv run python examples/basic.py

# Run benchmarks
uv run python benchmarks/batch_apps_benchmark.py
```

See [Development Setup](docs/development/setup.md) for detailed instructions.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
1. Create a feature branch
1. Make your changes
1. Add tests
1. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [PyO3](https://github.com/PyO3/pyo3) (Rust-Python bindings)
- Inspired by [google-play-scraper](https://github.com/facundoolano/google-play-scraper)
- APK Download: [gpapi](https://github.com/EFForg/rs-google-play) by EFF
- HTTP: [reqwest](https://github.com/seanmonstar/reqwest)
- Parsing: [scraper](https://github.com/causal-agent/scraper)
- Async Runtime: [tokio](https://github.com/tokio-rs/tokio)

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Please respect Google Play Store's Terms of Service. Use responsibly with appropriate rate limiting.

______________________________________________________________________

**Made with ❤️ using Rust + Python**
