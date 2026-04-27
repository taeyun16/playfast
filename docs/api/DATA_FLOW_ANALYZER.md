# Data Flow API Refactoring

## 개요

WebView 전용이었던 flow 분석 API를 범용 Data Flow 분석 API로 리팩토링했습니다.

## 변경 사항

### Before (WebView 특화)

```python
from playfast import core

# WebView만 분석 가능
analyzer = core.create_webview_analyzer_from_apk("app.apk")
flows = analyzer.analyze_flows(max_depth=10)

# 또는
flows = core.analyze_webview_flows_from_apk("app.apk", max_depth=10)
```

### After (범용 + 편의 메서드)

```python
from playfast import core

# 1. 범용 API - 원하는 sink 패턴 지정
analyzer = core.create_data_flow_analyzer("app.apk")
flows = analyzer.find_flows_to(["loadUrl", "evaluateJavascript"], max_depth=10)

# 2. 편의 메서드 - 일반적인 sink 타입
webview_flows = analyzer.find_webview_flows(max_depth=10)
file_flows = analyzer.find_file_flows(max_depth=10)
network_flows = analyzer.find_network_flows(max_depth=10)
sql_flows = analyzer.find_sql_flows(max_depth=10)

# 3. One-liner 편의 함수
flows = core.find_webview_flows_from_apk("app.apk", max_depth=10)
flows = core.find_file_flows_from_apk("app.apk", max_depth=10)
flows = core.find_network_flows_from_apk("app.apk", max_depth=10)
```

## 새로운 API

### Core Types

#### `DataFlowAnalyzer`

범용 데이터 플로우 분석기

```python
analyzer = core.create_data_flow_analyzer("app.apk")
```

**Methods:**

- `find_flows_to(patterns: List[str], max_depth: int) -> List[Flow]` - 범용 sink 검색
- `find_webview_flows(max_depth: int) -> List[Flow]` - WebView 편의 메서드
- `find_file_flows(max_depth: int) -> List[Flow]` - 파일 I/O 편의 메서드
- `find_network_flows(max_depth: int) -> List[Flow]` - 네트워크 편의 메서드
- `find_sql_flows(max_depth: int) -> List[Flow]` - SQL 편의 메서드
- `find_deeplink_flows(patterns: List[str], max_depth: int) -> List[Flow]` - Deeplink 전용
- `analyze_data_flows(flows: List[Flow]) -> List[DataFlow]` - Intent → Sink 데이터 플로우
- `get_stats() -> Dict` - 통계 정보

#### `Flow`

범용 플로우 정보 (이전 `WebViewFlow`)

```python
flow = Flow(
    entry_point="com.example.MainActivity",
    component_type="Activity",
    sink_method="android.webkit.WebView.loadUrl(...)",
    paths=[...],
    is_deeplink_handler=False,
    min_path_length=3,
    path_count=2,
)
```

**Attributes:**

- `entry_point: str` - 진입점 클래스명
- `component_type: str` - 컴포넌트 타입 (Activity, Service, etc.)
- `sink_method: str` - Sink 메서드 (WebView.loadUrl, File.write, etc.)
- `paths: List[CallPath]` - 호출 경로들
- `is_deeplink_handler: bool` - Deeplink 핸들러 여부
- `min_path_length: int` - 최단 경로 길이
- `path_count: int` - 경로 개수

**Methods:**

- `get_shortest_path() -> CallPath` - 최단 경로 가져오기
- `get_lifecycle_methods() -> List[str]` - 관련된 lifecycle 메서드들

#### `DataFlow`

Intent → Sink 데이터 플로우 정보

```python
data_flow = DataFlow(
    source="Intent.getStringExtra",
    sink="WebView.loadUrl",
    flow_path=["MainActivity.onCreate", "loadWebView", "WebView.loadUrl"],
    confidence=0.9,
)
```

### Convenience Functions

```python
# 범용
flows = core.find_flows_from_apk("app.apk", ["loadUrl", "write"], max_depth=10)

# WebView
flows = core.find_webview_flows_from_apk("app.apk", max_depth=10)

# File I/O
flows = core.find_file_flows_from_apk("app.apk", max_depth=10)

# Network
flows = core.find_network_flows_from_apk("app.apk", max_depth=10)
```

## 사용 예제

### Example 1: WebView 분석 (기존과 동일)

```python
from playfast import core

# Create analyzer
analyzer = core.create_data_flow_analyzer("app.apk")

# Find WebView flows
flows = analyzer.find_webview_flows(max_depth=10)

for flow in flows:
    print(f"{flow.entry_point} → {flow.sink_method}")
    if flow.is_deeplink_handler:
        print("  ⚠️  Deeplink handler!")
```

### Example 2: 파일 쓰기 분석 (새로운 기능)

```python
from playfast import core

# Find file write flows
flows = core.find_file_flows_from_apk("app.apk", max_depth=10)

for flow in flows:
    print(f"{flow.entry_point} → {flow.sink_method}")
    print(f"  Path length: {flow.min_path_length}")
```

### Example 3: 커스텀 sink 분석

```python
from playfast import core

analyzer = core.create_data_flow_analyzer("app.apk")

# Custom patterns for specific security analysis
custom_sinks = [
    "Runtime.exec",  # Command execution
    "ProcessBuilder.start",  # Process creation
    "System.loadLibrary",  # Native library loading
]

flows = analyzer.find_flows_to(custom_sinks, max_depth=15)

for flow in flows:
    print(f"⚠️  Security-sensitive: {flow.entry_point} → {flow.sink_method}")
```

### Example 4: Deeplink → WebView (보안 분석)

```python
from playfast import core

analyzer = core.create_data_flow_analyzer("app.apk")

# Find WebView flows
webview_flows = analyzer.find_webview_flows(max_depth=10)

# Filter only deeplink handlers
deeplink_flows = [f for f in webview_flows if f.is_deeplink_handler]

# Analyze data flows
data_flows = analyzer.analyze_data_flows(deeplink_flows)

# High confidence flows (likely vulnerable)
for df in data_flows:
    if df.confidence >= 0.7:
        print(f"⚠️  Intent → WebView: {df.source} → {df.sink}")
        print(f"   Confidence: {df.confidence:.2f}")
```

## Backward Compatibility

기존 API는 모두 유지되며 내부적으로 새로운 API를 호출합니다:

```python
# ✅ 여전히 작동 (deprecated)
flows = core.analyze_webview_flows_from_apk("app.apk")
analyzer = core.create_webview_analyzer_from_apk("app.apk")

# Type aliases
WebViewFlow = Flow  # Rust type alias
WebViewFlowAnalyzer = DataFlowAnalyzer  # Rust type alias
```

## 마이그레이션 가이드

### 기본 사용 (변경 불필요)

기존 코드는 수정 없이 계속 작동합니다.

### 새로운 기능 활용

```python
# Before
flows = core.analyze_webview_flows_from_apk("app.apk", max_depth=10)

# After (더 명확한 네이밍)
flows = core.find_webview_flows_from_apk("app.apk", max_depth=10)

# After (재사용 가능한 analyzer)
analyzer = core.create_data_flow_analyzer("app.apk")
webview_flows = analyzer.find_webview_flows(max_depth=10)
file_flows = analyzer.find_file_flows(max_depth=10)  # 추가 분석 가능!
```

## 성능 최적화 함께 사용

병렬 처리 + 필터링 최적화와 함께 사용:

```python
from playfast import core

# 1. Entry points 분석
entry_analyzer = core.analyze_entry_points_from_apk("app.apk")
entry_points = entry_analyzer.analyze()

# 2. 패키지 추출
packages = set()
for ep in entry_points:
    parts = ep.class_name.split(".")
    if len(parts) >= 2:
        packages.add(".".join(parts[:2]))

# 3. 최적화된 call graph (32.8x faster!)
graph = core.build_call_graph_from_apk_parallel("app.apk", list(packages))

# 4. 범용 Data Flow Analyzer
analyzer = core.DataFlowAnalyzer(entry_analyzer.analyzer, graph)
webview_flows = analyzer.find_webview_flows(max_depth=10)
file_flows = analyzer.find_file_flows(max_depth=10)
```

## 아키텍처

```
┌─────────────────────────┐
│  DataFlowAnalyzer       │  (범용 분석기)
├─────────────────────────┤
│ find_flows_to(patterns) │  ← 모든 메서드가 이것을 사용
│                         │
│ ┌─────────────────────┐ │
│ │ find_webview_flows  │ │  (편의 메서드)
│ │ find_file_flows     │ │
│ │ find_network_flows  │ │
│ │ find_sql_flows      │ │
│ └─────────────────────┘ │
└─────────────────────────┘
         ↓ uses
┌─────────────────────────┐
│  EntryPointAnalyzer     │  (진입점 분석)
│  CallGraph              │  (호출 그래프)
└─────────────────────────┘
```

## 지원하는 Sink 타입

### WebView (보안 - XSS, JS injection)

- `loadUrl`, `loadData`, `loadDataWithBaseURL`
- `evaluateJavascript`, `addJavascriptInterface`
- `setWebViewClient`, `setWebChromeClient`

### File I/O (보안 - Path traversal, 데이터 유출)

- `FileOutputStream`, `FileWriter`
- `RandomAccessFile.write`, `Files.write`

### Network (보안 - SSRF, 데이터 유출)

- `HttpURLConnection`, `OkHttp`
- `URLConnection.connect`, `Socket.connect`

### SQL (보안 - SQL injection)

- `execSQL`, `rawQuery`
- `SQLiteDatabase.query`

### Custom (확장 가능)

원하는 패턴을 `find_flows_to()`에 전달하여 커스텀 sink 분석 가능

## 이점

1. **확장성**: WebView뿐 아니라 모든 종류의 sink 분석 가능
1. **명확한 의도**: 함수명이 실제 기능을 더 정확히 표현
1. **재사용성**: 한 번 생성한 analyzer로 여러 sink 분석 가능
1. **편의성**: 일반적인 use case를 위한 편의 메서드 제공
1. **호환성**: 기존 코드 수정 불필요 (backward compatible)
1. **보안 분석**: 다양한 보안 취약점 탐지 가능

## 참고

- 파일: `src/dex/data_flow_analyzer.rs`
- 성능 최적화: [OPTIMIZATION_SUMMARY.md](../performance/OPTIMIZATION_SUMMARY.md)
- 날짜: 2025-10-29
