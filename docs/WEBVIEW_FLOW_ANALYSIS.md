# WebView Flow Analysis

Complete system for analyzing Android app call flows from entry points to WebView APIs, including deeplink and data flow analysis.

## Overview

This system analyzes Android APK files to identify how WebViews are accessed and what data flows into them, particularly useful for security analysis and understanding app behavior.

### What It Does

1. **Entry Point Analysis** - Identifies Activities, Services, BroadcastReceivers, and ContentProviders
1. **Deeplink Detection** - Finds which components handle deeplinks (custom URL schemes)
1. **Call Graph Construction** - Builds method-to-method call relationships
1. **WebView Flow Tracking** - Finds all paths from entry points to WebView APIs
1. **Data Flow Analysis** - Tracks Intent data flowing into WebView.loadUrl()

## Quick Start

### Simple Analysis

```python
from playfast import core

# One-line analysis (recommended API)
flows = core.find_webview_flows_from_apk("app.apk", max_depth=10)

for flow in flows:
    print(f"{flow.entry_point} → {flow.sink_method}")
    if flow.is_deeplink_handler:
        print("  ⚠️  DEEPLINK HANDLER")
```

### Detailed Analysis

```python
# Create analyzer
analyzer = core.create_data_flow_analyzer("app.apk")

# Get statistics
stats = analyzer.get_stats()
print(f"Entry points: {stats['entry_points']}")
print(f"Deeplink handlers: {stats['deeplink_handlers']}")

# Analyze all flows
all_flows = analyzer.find_webview_flows(max_depth=10)

# Find deeplink flows specifically
deeplink_flows = analyzer.find_deeplink_flows(
    ["WebView.loadUrl", "WebView.loadData", "WebView.loadDataWithBaseURL"],
    max_depth=10,
)

# Analyze data flows
data_flows = analyzer.analyze_data_flows(all_flows)
```

## Architecture

### Phase 1: Entry Point Analysis

Identifies Android components and their properties.

```python
from playfast import core

analyzer = core.analyze_entry_points_from_apk("app.apk")

# Get all entry points
entry_points = analyzer.get_all_entry_points()

# Find deeplink handlers
deeplink_handlers = analyzer.get_deeplink_handlers()

for handler in deeplink_handlers:
    print(f"Deeplink: {handler.class_name}")
    for intent_filter in handler.intent_filters:
        if intent_filter.is_deeplink():
            for data in intent_filter.data_filters:
                scheme = data.get("scheme", "")
                host = data.get("host", "")
                print(f"  {scheme}://{host}")
```

**Key Classes:**

- `EntryPoint` - Represents a component (Activity, Service, etc.)
- `ComponentType` - Enum: Activity, Service, BroadcastReceiver, ContentProvider
- `PyEntryPointAnalyzer` - Main analyzer class

### Phase 2: Call Graph

Builds method-to-method call relationships.

```python
# Build call graph (optionally filter to specific packages)
call_graph = core.build_call_graph_from_apk("app.apk", ["com.example"])

# Find WebView methods
webview_methods = call_graph.find_methods("loadUrl")

# Find who calls a method
callers = call_graph.get_callers("android.webkit.WebView.loadUrl")

# Find paths between methods
paths = call_graph.find_paths("onCreate", "loadUrl", max_depth=10)

for path in paths:
    print(f"Path: {path}")
    print(f"Length: {path.length}")
```

**Key Classes:**

- `CallGraph` - The call graph structure
- `CallPath` - A path through the graph
- `MethodCall` - An edge in the graph

### Phase 3: WebView Flow Analysis

Integrates entry points and call graph to find complete flows.

```python
analyzer = core.create_data_flow_analyzer("app.apk")

# Analyze all WebView flows
flows = analyzer.find_webview_flows(max_depth=10)

for flow in flows:
    print(f"Entry: {flow.entry_point}")
    print(f"WebView: {flow.sink_method}")
    print(f"Paths: {flow.path_count}")
    print(f"Min depth: {flow.min_path_length}")

    # Get shortest path
    shortest = flow.get_shortest_path()
    if shortest:
        print(f"Path: {shortest}")

    # Get lifecycle methods involved
    lifecycle = flow.get_lifecycle_methods()
    print(f"Lifecycle: {lifecycle}")
```

**Key Classes:**

- `DataFlowAnalyzer` - Main analyzer
- `Flow` - A flow from entry point to sink method (e.g., WebView)
- `DataFlow` - A data flow from Intent to sink methods

## API Reference

### DataFlowAnalyzer

```python
class DataFlowAnalyzer:
    def find_webview_flows(self, max_depth: int = 10) -> list[Flow]:
        """Analyze WebView flows"""

    def find_deeplink_flows(
        self, sink_patterns: list[str], max_depth: int = 10
    ) -> list[Flow]:
        """Find only deeplink handlers that lead to sink patterns"""

    def analyze_data_flows(self, flows: list[Flow]) -> list[DataFlow]:
        """Analyze data flows for given flows"""

    def get_stats(self) -> dict[str, int]:
        """Get analysis statistics"""
```

### Flow

```python
class Flow:
    entry_point: str  # Entry point class name
    component_type: str  # Activity, Service, etc.
    sink_method: str  # Sink API being called (e.g., WebView.loadUrl)
    paths: list[CallPath]  # All paths from entry to sink
    is_deeplink_handler: bool  # Whether this is a deeplink handler
    min_path_length: int  # Shortest path length
    path_count: int  # Number of different paths

    def get_shortest_path(self) -> CallPath | None:
        """Get the shortest path"""

    def get_lifecycle_methods(self) -> list[str]:
        """Get all lifecycle methods involved"""
```

### DataFlow

```python
class DataFlow:
    source: str  # Data source (e.g., Intent.getStringExtra)
    sink: str  # Data sink (e.g., WebView.loadUrl)
    flow_path: list[str]  # Methods in the flow
    confidence: float  # Confidence score (0.0 - 1.0)
```

### Confidence Scores

Data flow confidence is calculated based on path length:

- **≥ 0.9**: Direct flow (≤ 3 hops) - Very likely
- **0.7 - 0.9**: Short flow (4-5 hops) - Likely
- **0.5 - 0.7**: Medium flow (6-8 hops) - Possible
- **< 0.5**: Long flow (> 8 hops) - Uncertain

## Use Cases

### Security Analysis: Finding Deeplink Vulnerabilities

```python
analyzer = core.create_data_flow_analyzer("target.apk")

# Find deeplink → WebView flows
deeplink_flows = analyzer.find_deeplink_flows(
    ["WebView.loadUrl", "WebView.loadData", "WebView.loadDataWithBaseURL"],
    max_depth=10,
)

if deeplink_flows:
    # Analyze data flows
    data_flows = analyzer.analyze_data_flows(deeplink_flows)

    # Filter high confidence flows
    risky = [df for df in data_flows if df.confidence >= 0.7]

    for df in risky:
        print(f"⚠️  POTENTIAL RISK:")
        print(f"   {df.source} → {df.sink}")
        print(f"   Confidence: {df.confidence:.2f}")
        print()
        print("   Review checklist:")
        print("   - [ ] URL validation present?")
        print("   - [ ] Only http/https allowed?")
        print("   - [ ] JavaScript interface safe?")
```

### Code Review: Understanding WebView Usage

```python
# Identify all WebView usage patterns
analyzer = core.create_data_flow_analyzer("app.apk")
flows = analyzer.find_webview_flows(max_depth=10)

# Group by entry point
from collections import defaultdict

by_entry = defaultdict(list)

for flow in flows:
    by_entry[flow.entry_point].append(flow)

# Report
for entry, entry_flows in by_entry.items():
    print(f"Component: {entry}")
    webview_apis = set(f.sink_method for f in entry_flows)
    print(f"  WebView APIs: {webview_apis}")
    print(f"  Total paths: {sum(f.path_count for f in entry_flows)}")
```

### Test Case Generation

```python
# Find all deeplink handlers
analyzer = core.analyze_entry_points_from_apk("app.apk")
handlers = analyzer.get_deeplink_handlers()

# Generate test URLs
test_urls = []
for handler in handlers:
    for intent_filter in handler.intent_filters:
        if intent_filter.is_deeplink():
            for data in intent_filter.data_filters:
                scheme = data.get("scheme", "https")
                host = data.get("host", "example.com")
                path = data.get("pathPrefix", "/")
                test_urls.append(f"{scheme}://{host}{path}")

print("Test URLs to check:")
for url in test_urls:
    print(f'  adb shell am start -a android.intent.action.VIEW -d "{url}"')
```

## Examples

See the `examples/` directory:

- `entry_point_analysis_demo.py` - Phase 1 demo
- `call_graph_demo.py` - Phase 2 demo
- `webview_flow_demo.py` - Complete integration demo

Run examples:

```bash
uv run python examples/webview_flow_demo.py app.apk
```

## Performance Considerations

### Typical Performance

**Call Graph Construction** (most expensive phase):

- **~10-11 classes/second**: For complex apps with many methods
- **49MB APK (669 classes)**: ~63 seconds
- **Memory usage**: Proportional to APK size and class count

**Entry Point Analysis**: Very fast (~3-4 seconds even for large apps)
**WebView Flow Analysis**: Depends on max_depth and graph size

### Large APKs

For apps with thousands of classes:

```python
# Use class filtering to reduce analysis scope
call_graph = core.build_call_graph_from_apk(
    "large_app.apk", class_filter=["com.example"]  # Only analyze app package
)
```

**Filtering Benefits**:

- Reduces analysis time proportionally to filtered classes
- Lower memory usage
- Faster path finding
- More focused results for security analysis

### Max Depth

The `max_depth` parameter controls how deep to search:

- `max_depth=5`: Fast, finds direct calls
- `max_depth=10`: Balanced (default)
- `max_depth=15`: Thorough, slower

```python
# Quick scan
flows = analyzer.find_webview_flows(max_depth=5)

# Deep analysis
flows = analyzer.find_webview_flows(max_depth=15)
```

### Parallel Processing

**✅ Recommended**: Use `build_call_graph_from_apk_parallel()` for **3x faster** analysis!

**Benchmark results** (49MB APK, 669 classes):

- **Sequential**: 435.6s
- **Parallel**: 142.2s
- **Speedup**: **3.06x** (67% time saved)

**When to use parallel**:

- Large APKs (>1,000 classes): Significant speedup
- Multiple APKs: Process each in parallel
- Time-critical analysis: 3x faster results

**API Usage**:

```python
from playfast import core

# Recommended: Parallel version (3x faster)
call_graph = core.build_call_graph_from_apk_parallel(
    "app.apk", class_filter=["com.example"]
)

# Or sequential if preferred
call_graph = core.build_call_graph_from_apk("app.apk", class_filter=["com.example"])

# Both return identical results
stats = call_graph.get_stats()
```

**For multiple APKs**, use Python's `multiprocessing`:

```python
from multiprocessing import Pool
from playfast import core


def analyze_apk(apk_path):
    return core.build_call_graph_from_apk_parallel(apk_path, None)


apk_list = ["app1.apk", "app2.apk", "app3.apk", ...]

with Pool(processes=4) as pool:  # 4 APKs in parallel
    results = pool.map(analyze_apk, apk_list)
```

See [PARALLEL_PROCESSING.md](performance/PARALLEL_PROCESSING.md) for optimization details.

## Limitations

### Current Limitations

1. **Static Analysis Only** - Cannot detect runtime code loading or reflection
1. **Heuristic Data Flow** - Data flow tracking uses path-based heuristics, not full taint analysis
1. **Native Code** - Cannot analyze native methods (JNI)
1. **Dynamic Features** - Cannot analyze dynamically loaded features

### False Positives/Negatives

**False Positives:**

- Data flow may be detected even if actual data doesn't flow (conservative analysis)

**False Negatives:**

- Complex indirect calls may be missed
- Reflection-based calls not tracked
- Obfuscated code may break method name matching

### Recommended Workflow

1. Run automated analysis to identify suspicious flows
1. Manually review high-confidence data flows
1. Use dynamic testing to confirm findings
1. Check for validation code in identified paths

## Troubleshooting

### No Flows Found

If analysis returns no flows:

1. **Check if app uses WebView**: `ApkAnalyzer("app.apk").find_webview_usage()`
1. **Increase max_depth**: Try `max_depth=15` or higher
1. **Check class filtering**: Remove filters to analyze all classes
1. **Verify APK**: Ensure DEX files are present and readable

### Performance Issues

If analysis is slow:

1. **Filter classes**: Only analyze app package, exclude libraries
1. **Reduce depth**: Lower `max_depth` parameter
1. **Simplify analysis**: Analyze entry points separately from call graph

### Unexpected Results

If results seem wrong:

1. **Check method name matching**: May need to adjust patterns
1. **Verify paths manually**: Use call graph to inspect individual paths
1. **Review confidence scores**: Low confidence may indicate uncertainty

## Contributing

To extend the analysis:

1. **Add new entry types**: Modify `entry_point_analyzer.rs`
1. **Improve data flow**: Enhance heuristics in `data_flow_analyzer.rs`
1. **Add patterns**: Update WebView method patterns in `find_webview_methods()`

## References

- [Android WebView Security](https://developer.android.com/training/articles/security-tips#WebView)
- [Deep Links](https://developer.android.com/training/app-links/deep-linking)
- [Call Graph Analysis](https://en.wikipedia.org/wiki/Call_graph)
