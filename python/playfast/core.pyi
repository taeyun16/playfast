from collections.abc import Callable
from typing import Any

# ============================================================================
# Google Play Store Types
# ============================================================================

class RustAppInfo:
    app_id: str
    title: str
    developer: str
    icon: str
    score: float
    ratings: int
    price: float
    currency: str
    free: bool
    description: str | None
    summary: str | None
    installs: str | None
    min_installs: int | None
    score_text: str | None
    released: str | None
    updated: str | None
    version: str | None
    required_android_version: str | None
    content_rating: str | None
    content_rating_description: str | None
    ad_supported: bool | None
    contains_ads: bool | None
    in_app_purchases: bool | None
    editors_choice: bool | None
    developer_id: str | None
    developer_email: str | None
    developer_website: str | None
    developer_address: str | None
    privacy_policy: str | None
    genre: str | None
    genre_id: str | None
    category: str | None
    video: str | None
    video_image: str | None
    screenshots: list[str]
    similar: list[str]
    permissions: list[RustPermission]

class RustReview:
    review_id: str
    user_name: str
    user_image: str
    content: str
    score: int
    thumbs_up: int
    created_at: int
    reply_content: str | None
    reply_at: int | None

class RustSearchResult:
    app_id: str
    title: str
    developer: str
    icon: str
    score: float | None
    price: float
    currency: str

class RustPermission:
    group: str
    permissions: list[str]
    def __len__(self) -> int: ...

def parse_app_page(html: str, app_id: str) -> RustAppInfo: ...
def parse_review_batch(html: str) -> list[RustReview]: ...
def parse_search_results(html: str) -> list[RustSearchResult]: ...
def extract_continuation_token(html: str) -> str | None: ...
def parse_batchexecute_list_response(response_text: str) -> list[RustSearchResult]: ...
def build_list_request_body(
    category: str | None, collection: str, num: int = 100
) -> str: ...
def build_reviews_request_body(
    app_id: str, sort: int, continuation_token: str | None, lang: str, country: str
) -> str: ...
def parse_batchexecute_reviews_response(
    response_text: str,
) -> tuple[list[RustReview], str | None]: ...

# Single request functions (HTTP + parsing)
def fetch_and_parse_app(
    app_id: str, lang: str, country: str, timeout: int = 30
) -> RustAppInfo: ...
def fetch_and_parse_reviews(
    app_id: str,
    lang: str,
    country: str,
    sort: int = 1,
    continuation_token: str | None = None,
    timeout: int = 30,
) -> tuple[list[RustReview], str | None]: ...
def fetch_and_parse_search(
    query: str, lang: str, country: str, timeout: int = 30
) -> list[RustSearchResult]: ...
def fetch_and_parse_list(
    category: str | None,
    collection: str,
    lang: str,
    country: str,
    num: int = 100,
    timeout: int = 30,
) -> list[RustSearchResult]: ...

# Batch functions for parallel processing (recommended for multiple requests)
def fetch_and_parse_apps_batch(
    requests: list[tuple[str, str, str]],
) -> list[RustAppInfo]: ...
def fetch_and_parse_list_batch(
    requests: list[tuple[str | None, str, str, str, int]],
) -> list[list[RustSearchResult]]: ...
def fetch_and_parse_search_batch(
    requests: list[tuple[str, str, str]],
) -> list[list[RustSearchResult]]: ...
def fetch_and_parse_reviews_batch(
    requests: list[tuple[str, str, str, int, str | None]],
) -> list[tuple[list[RustReview], str | None]]: ...

# ============================================================================
# APK Analysis Types
# ============================================================================

class RustDexClass:
    class_name: str
    package_name: str
    simple_name: str
    access_flags: int
    superclass: str | None
    interfaces: list[str]
    methods: list[RustDexMethod]
    fields: list[RustDexField]
    references: RustReferencePool
    def is_public(self) -> bool: ...
    def is_final(self) -> bool: ...
    def is_abstract(self) -> bool: ...
    def is_interface(self) -> bool: ...
    def is_enum(self) -> bool: ...
    def method_count(self) -> int: ...
    def field_count(self) -> int: ...
    def to_dict(self) -> dict[str, Any]: ...

class RustDexMethod:
    declaring_class: str
    name: str
    parameters: list[str]
    return_type: str
    access_flags: int
    references: RustReferencePool
    def is_public(self) -> bool: ...
    def is_private(self) -> bool: ...
    def is_protected(self) -> bool: ...
    def is_static(self) -> bool: ...
    def is_final(self) -> bool: ...
    def is_constructor(self) -> bool: ...
    def is_static_initializer(self) -> bool: ...
    def signature(self) -> str: ...
    def to_dict(self) -> dict[str, Any]: ...

class RustDexField:
    name: str
    field_type: str
    declaring_class: str
    access_flags: int

class RustReferencePool:
    strings: list[str]
    types: list[str]
    fields: list[str]
    methods: list[str]
    def __len__(self) -> int: ...
    def contains(self, value: str) -> bool: ...
    def contains_string(self, value: str) -> bool: ...
    def contains_type(self, value: str) -> bool: ...
    def contains_field(self, value: str) -> bool: ...
    def contains_method(self, value: str) -> bool: ...
    def to_dict(self) -> dict[str, Any]: ...

class RustManifestInfo:
    package_name: str
    version_code: str | None
    version_name: str | None
    min_sdk_version: str | None
    target_sdk_version: str | None
    application_label: str | None
    permissions: list[str]
    activities: list[str]
    services: list[str]
    receivers: list[str]
    providers: list[str]
    intent_filters: list[ActivityIntentFilter]
    def get_deeplinks(self) -> list[Any]: ...
    def to_dict(self) -> dict[str, Any]: ...

class IntentFilterData:
    scheme: str | None
    host: str | None
    path: str | None
    path_prefix: str | None
    path_pattern: str | None

class ActivityIntentFilter:
    activity: str
    actions: list[str]
    categories: list[str]
    data: list[IntentFilterData]
    def is_deeplink(self) -> bool: ...

class RustInstruction:
    opcode: str
    dest: int | None
    value: int | None
    string_idx: int | None
    method_idx: int | None
    args: list[int]
    raw: str
    def is_const(self) -> bool: ...
    def is_invoke(self) -> bool: ...
    def get_boolean_value(self) -> bool | None: ...
    def to_dict(self) -> dict[str, Any]: ...

class MethodSignature:
    class_name: str
    method_name: str
    descriptor: str

# ============================================================================
# Entry Point Analysis
# ============================================================================

class ComponentType:
    Activity: str
    Service: str
    BroadcastReceiver: str
    ContentProvider: str

class EntryPoint:
    class_name: str
    component_type: ComponentType
    intent_filters: list[ActivityIntentFilter]
    is_deeplink_handler: bool
    class_found: bool
    def get_deeplink_patterns(self) -> list[str]: ...
    def get_actions(self) -> list[str]: ...
    def handles_action(self, action: str) -> bool: ...

class PyEntryPointAnalyzer:
    def analyze(self) -> list[EntryPoint]: ...
    def get_deeplink_handlers(self) -> list[EntryPoint]: ...
    def get_found_entry_points(self) -> list[EntryPoint]: ...
    def get_stats(self) -> str: ...

def analyze_entry_points_from_apk(apk_path: str) -> PyEntryPointAnalyzer: ...

# ============================================================================
# Call Graph Analysis
# ============================================================================

class MethodCall:
    caller: str
    callee: str
    call_site: str

class CallPath:
    methods: list[str]
    calls: list[MethodCall]
    length: int
    def get_source(self) -> str | None: ...
    def get_target(self) -> str | None: ...
    def contains_method(self, method: str) -> bool: ...

class CallGraph:
    def get_all_methods(self) -> list[str]: ...
    def get_callees(self, method: str) -> list[str]: ...
    def get_callers(self, method: str) -> list[str]: ...
    def find_methods(self, pattern: str) -> list[str]: ...
    def find_paths(
        self, source: str, target: str, max_depth: int = 10
    ) -> list[CallPath]: ...
    def get_stats(self) -> dict[str, int]: ...

class PyCallGraphBuilder:
    def add_class(self, class_: DecompiledClass) -> None: ...
    def build(self) -> CallGraph: ...

def build_call_graph_from_apk(
    apk_path: str, class_filter: list[str] | None = None
) -> CallGraph: ...
def build_call_graph_from_apk_parallel(
    apk_path: str, class_filter: list[str] | None = None
) -> CallGraph: ...

# ============================================================================
# Data Flow Analysis (New Generic API)
# ============================================================================

class Flow:
    entry_point: str
    component_type: str
    sink_method: str
    paths: list[CallPath]
    is_deeplink_handler: bool
    min_path_length: int
    path_count: int

    def get_shortest_path(self) -> CallPath | None: ...
    def get_lifecycle_methods(self) -> list[str]: ...

class DataFlow:
    source: str
    sink: str
    flow_path: list[str]
    confidence: float

class DataFlowAnalyzer:
    def find_flows_to(
        self, sink_patterns: list[str], max_depth: int = 10
    ) -> list[Flow]: ...
    def find_webview_flows(self, max_depth: int = 10) -> list[Flow]: ...
    def find_file_flows(self, max_depth: int = 10) -> list[Flow]: ...
    def find_network_flows(self, max_depth: int = 10) -> list[Flow]: ...
    def find_sql_flows(self, max_depth: int = 10) -> list[Flow]: ...
    def find_deeplink_flows(
        self, sink_patterns: list[str], max_depth: int = 10
    ) -> list[Flow]: ...
    def analyze_data_flows(self, flows: list[Flow]) -> list[DataFlow]: ...
    def get_stats(self) -> dict[str, int]: ...

def create_data_flow_analyzer(apk_path: str) -> DataFlowAnalyzer: ...
def find_flows_from_apk(
    apk_path: str, sink_patterns: list[str], max_depth: int = 10
) -> list[Flow]: ...
def find_webview_flows_from_apk(apk_path: str, max_depth: int = 10) -> list[Flow]: ...
def find_file_flows_from_apk(apk_path: str, max_depth: int = 10) -> list[Flow]: ...
def find_network_flows_from_apk(apk_path: str, max_depth: int = 10) -> list[Flow]: ...

# ============================================================================
# Backward Compatibility (Deprecated - use DataFlowAnalyzer instead)
# ============================================================================

# Type aliases for backward compatibility
WebViewFlow = Flow
WebViewFlowAnalyzer = DataFlowAnalyzer

def analyze_webview_flows_from_apk(
    apk_path: str, max_depth: int = 10
) -> list[Flow]: ...
def create_webview_analyzer_from_apk(apk_path: str) -> DataFlowAnalyzer: ...

# ============================================================================
# APK Extraction Functions
# ============================================================================

def extract_apk_info(apk_path: str) -> tuple[int, bool, bool, list[str]]: ...
def extract_manifest_raw(apk_path: str) -> bytes: ...
def parse_manifest_from_apk(apk_path: str) -> RustManifestInfo: ...
def extract_classes_from_apk(
    apk_path: str, parallel: bool = True
) -> list[RustDexClass]: ...
def search_classes(
    apk_path: str,
    filter: ClassFilter,
    limit: int | None = None,
    parallel: bool = True,
) -> list[RustDexClass]: ...
def search_methods(
    apk_path: str,
    class_filter: ClassFilter,
    method_filter: MethodFilter,
    limit: int | None = None,
    parallel: bool = True,
) -> list[tuple[RustDexClass, RustDexMethod]]: ...

# ============================================================================
# Bytecode Analysis Functions
# ============================================================================

def decode_bytecode(bytecode: bytes) -> list[RustInstruction]: ...
def extract_constants(bytecode: bytes) -> list[str]: ...
def extract_method_calls(bytecode: bytes) -> list[str]: ...
def extract_methods_bytecode(classes: list[RustDexClass]) -> dict[str, bytes]: ...
def get_method_bytecode_from_apk(
    apk_path: str, class_name: str, method_name: str
) -> bytes | None: ...

# ============================================================================
# Method Resolution Functions
# ============================================================================

class MethodResolverPy:
    def resolve_method(
        self, class_name: str, method_name: str, descriptor: str
    ) -> str | None: ...

def create_method_resolver(apk_path: str) -> MethodResolverPy: ...
def resolve_method_from_apk(
    apk_path: str, class_name: str, method_name: str, descriptor: str
) -> str | None: ...

# ============================================================================
# Expression Reconstruction Functions
# ============================================================================

class ReconstructedExpression:
    method: str
    expressions: list[str]

class ExpressionBuilderPy:
    def reconstruct_expressions(
        self, class_name: str, method_name: str
    ) -> ReconstructedExpression | None: ...

def create_expression_builder(apk_path: str) -> ExpressionBuilderPy: ...
def reconstruct_expressions_from_apk(
    apk_path: str, class_name: str, method_name: str
) -> ReconstructedExpression | None: ...

# ============================================================================
# Class Decompilation Functions
# ============================================================================

class DecompiledMethod:
    name: str
    descriptor: str
    access_flags: int
    code: str

class DecompiledClass:
    class_name: str
    access_flags: int
    superclass: str | None
    interfaces: list[str]
    fields: list[str]
    methods: list[DecompiledMethod]

def decompile_class_from_apk(
    apk_path: str, class_name: str
) -> DecompiledClass | None: ...

# ============================================================================
# Resources Functions
# ============================================================================

class PyResolvedResource:
    resource_id: int
    resource_type: str
    resource_name: str
    value: str

class PyResourceResolver:
    def resolve_resource(self, resource_id: int) -> PyResolvedResource | None: ...
    def get_string(self, resource_id: int) -> str | None: ...

def parse_resources_from_apk(apk_path: str) -> PyResourceResolver: ...

# ============================================================================
# DEX Filter Classes
# ============================================================================

class ClassFilter:
    def __init__(
        self,
        packages: list[str] | None = None,
        exclude_packages: list[str] | None = None,
        class_name: str | None = None,
        modifiers: int | None = None,
    ) -> None: ...

class MethodFilter:
    def __init__(
        self,
        method_name: str | None = None,
        param_count: int | None = None,
        param_types: list[str] | None = None,
        return_type: str | None = None,
        modifiers: int | None = None,
    ) -> None: ...

# ============================================================================
# Google Play APK Download (Low-level API)
# ============================================================================

class GpapiClient:
    email: str
    """Google account email address"""

    def __init__(
        self,
        email: str,
        oauth_token: str | None = None,
        aas_token: str | None = None,
        device: str = "px_9a",
        locale: str = "en_US",
        timezone: str = "America/New_York",
    ) -> None: ...
    def login(self) -> None: ...
    def get_aas_token(self) -> str: ...
    def save_credentials(self, path: str) -> None: ...
    @staticmethod
    def from_credentials(path: str) -> GpapiClient: ...
    def download_apk(
        self,
        package_id: str,
        dest_path: str,
        version_code: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> str: ...
    def get_package_details(self, package_id: str) -> str: ...
