mod error;
mod http;
mod models;
mod parser;

// DEX and APK analysis modules
mod apk;
mod dex;

// Google Play APK download module
mod download;

use http::{PlayStoreClient, build_list_request_body as build_list_request_body_impl, build_reviews_request_body as build_reviews_request_body_impl};
use models::{RustAppInfo, RustPermission, RustReview, RustSearchResult};
use parser::{
    parse_app_page as parse_app_page_impl,
    parse_review_batch as parse_review_batch_impl,
    parse_search_results as parse_search_results_impl,
    parse_batchexecute_list_response as parse_batchexecute_list_response_impl,
    parse_batchexecute_reviews_response as parse_batchexecute_reviews_response_impl,
    extract_continuation_token as extract_continuation_token_impl
};
use pyo3::prelude::*;
use once_cell::sync::Lazy;
use futures::future::try_join_all;

// Import DEX and APK types
use apk::{ApkExtractor, RustManifestInfo, parse_manifest, IntentFilterData, ActivityIntentFilter, PyResourceResolver, PyResolvedResource, parse_resources_from_apk};
use dex::models::{RustDexClass, RustDexMethod, RustDexField, RustReferencePool};
use dex::filter::{ClassFilter, MethodFilter};
use dex::container::DexContainer;
use dex::bytecode::{RustInstruction, decode_bytecode, extract_constants, extract_method_calls};
use dex::code_extractor::{extract_methods_bytecode, get_method_bytecode_from_apk};
use dex::method_resolver::{MethodSignature, MethodResolverPy, create_method_resolver, resolve_method_from_apk};
use dex::expression_builder::{ReconstructedExpression, ExpressionBuilderPy, create_expression_builder, reconstruct_expressions_from_apk};
use dex::class_decompiler::{DecompiledClass, DecompiledMethod, decompile_class_from_apk};
use dex::entry_point_analyzer::{EntryPoint, ComponentType, PyEntryPointAnalyzer, analyze_entry_points_from_apk};
use dex::call_graph::{CallGraph, CallPath, MethodCall, PyCallGraphBuilder, build_call_graph_from_apk, build_call_graph_from_apk_parallel};
use dex::data_flow_analyzer::{
    Flow, DataFlow, DataFlowAnalyzer,
    create_data_flow_analyzer,
    find_flows_from_apk,
    find_webview_flows_from_apk,
    find_file_flows_from_apk,
    find_network_flows_from_apk,
    analyze_webview_flows_from_apk,
    create_webview_analyzer_from_apk,
};

/// Global tokio runtime for async operations
/// Multi-threaded runtime for better parallel performance
static TOKIO_RUNTIME: Lazy<tokio::runtime::Runtime> = Lazy::new(|| {
    // Use half of available CPUs (min 2, max 8) for tokio runtime
    // This leaves CPU cores for Python threads and other work
    let num_cpus = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4);
    let worker_threads = (num_cpus / 2).clamp(2, 8);

    tokio::runtime::Builder::new_multi_thread()
        .worker_threads(worker_threads)
        .enable_all()
        .thread_name("playfast-tokio")
        .build()
        .expect("Failed to create tokio runtime")
});

/// Global HTTP client (connection pooling)
static HTTP_CLIENT: Lazy<PlayStoreClient> = Lazy::new(|| {
    PlayStoreClient::new(30).expect("Failed to create HTTP client")
});

/// Get the global tokio runtime
fn get_runtime() -> &'static tokio::runtime::Runtime {
    &TOKIO_RUNTIME
}

/// Get the global HTTP client (with connection pooling)
fn get_client() -> &'static PlayStoreClient {
    &HTTP_CLIENT
}

/// Parse app information from HTML (CPU-intensive, GIL-free operation)
///
/// Args:
///     html (str): The HTML content of the app page
///     app_id (str): The app ID (e.g., "com.spotify.music")
///
/// Returns:
///     RustAppInfo: Parsed app information
///
/// Raises:
///     Exception: If parsing fails
#[pyfunction]
fn parse_app_page(html: &str, app_id: &str) -> PyResult<RustAppInfo> {
    parse_app_page_impl(html, app_id).map_err(Into::into)
}

/// Parse batch of reviews from HTML (CPU-intensive, GIL-free operation)
///
/// Args:
///     html (str): The HTML content containing reviews
///
/// Returns:
///     list[RustReview]: List of parsed reviews
///
/// Raises:
///     Exception: If parsing fails
#[pyfunction]
fn parse_review_batch(html: &str) -> PyResult<Vec<RustReview>> {
    parse_review_batch_impl(html).map_err(Into::into)
}

/// Parse search results from HTML
///
/// Args:
///     html (str): The HTML content of search results page
///
/// Returns:
///     list[RustSearchResult]: List of search results
///
/// Raises:
///     Exception: If parsing fails
#[pyfunction]
fn parse_search_results(html: &str) -> PyResult<Vec<RustSearchResult>> {
    parse_search_results_impl(html).map_err(Into::into)
}

/// Extract continuation token for pagination
///
/// Args:
///     html (str): The HTML content
///
/// Returns:
///     str | None: Continuation token if found, None otherwise
#[pyfunction]
fn extract_continuation_token(html: &str) -> Option<String> {
    extract_continuation_token_impl(html)
}

/// Parse batchexecute API response for list/category results (CPU-intensive, GIL-free operation)
///
/// This parses the response from Google Play's batchexecute API endpoint
/// used for category/collection listings.
///
/// Args:
///     response_text (str): The raw text response from batchexecute API
///
/// Returns:
///     list[RustSearchResult]: List of parsed app results
///
/// Raises:
///     Exception: If parsing fails
#[pyfunction]
fn parse_batchexecute_list_response(response_text: &str) -> PyResult<Vec<RustSearchResult>> {
    parse_batchexecute_list_response_impl(response_text).map_err(Into::into)
}

/// Build request body for batchexecute list API
///
/// This function generates the HTTP POST body required for the Google Play
/// batchexecute API. Use this with Python's aiohttp for async HTTP + Rust parsing.
///
/// Args:
///     category (str | None): Category code (e.g., "GAME_ACTION"), None for all apps
///     collection (str): Collection type (e.g., "topselling_free")
///     num (int): Number of results (default: 100, max: 250)
///
/// Returns:
///     str: URL-encoded POST body ready for HTTP request
///
/// Example:
///     >>> body = build_list_request_body("GAME_ACTION", "topselling_free", 200)
///     >>> # Use with aiohttp:
///     >>> async with session.post(url, data=body) as response:
///     ...     text = await response.text()
///     ...     apps = parse_batchexecute_list_response(text)
#[pyfunction]
#[pyo3(signature = (category, collection, num=100))]
fn build_list_request_body(
    category: Option<&str>,
    collection: &str,
    num: u32,
) -> String {
    build_list_request_body_impl(category, collection, num)
}

/// Build request body for batchexecute reviews API
///
/// This function generates the HTTP POST body required for fetching reviews
/// from the Google Play batchexecute API.
///
/// Args:
///     app_id (str): App package ID (e.g., "com.spotify.music")
///     sort (int): Sort order (1=newest, 2=highest rating, 3=most helpful)
///     continuation_token (str | None): Token for pagination (None for first page)
///     lang (str): Language code (e.g., "en")
///     country (str): Country code (e.g., "us")
///
/// Returns:
///     str: URL-encoded POST body ready for HTTP request
///
/// Example:
///     >>> body = build_reviews_request_body("com.spotify.music", 1, None, "en", "us")
///     >>> # Use with aiohttp:
///     >>> async with session.post(url, data=body) as response:
///     ...     text = await response.text()
///     ...     reviews, next_token = parse_batchexecute_reviews_response(text)
#[pyfunction]
fn build_reviews_request_body(
    app_id: &str,
    sort: u8,
    continuation_token: Option<&str>,
    lang: &str,
    country: &str,
) -> String {
    build_reviews_request_body_impl(app_id, sort, continuation_token, lang, country)
}

/// Parse batchexecute API response for reviews
///
/// This parses the response from Google Play's batchexecute API endpoint
/// used for fetching reviews.
///
/// Args:
///     response_text (str): The raw text response from batchexecute API
///
/// Returns:
///     tuple: (list[RustReview], str | None) - Reviews and next continuation token
///
/// Raises:
///     Exception: If parsing fails
#[pyfunction]
fn parse_batchexecute_reviews_response(response_text: &str) -> PyResult<(Vec<RustReview>, Option<String>)> {
    parse_batchexecute_reviews_response_impl(response_text).map_err(Into::into)
}

/// Fetch and parse app information (combined HTTP + parsing, GIL-free)
///
/// This function performs both HTTP request and parsing in Rust,
/// releasing the GIL for true parallel execution.
///
/// Args:
///     app_id (str): The app package ID (e.g., "com.spotify.music")
///     lang (str): Language code (e.g., "en")
///     country (str): Country code (e.g., "us")
///     timeout (int): Request timeout in seconds (default: 30)
///
/// Returns:
///     RustAppInfo: Parsed app information
///
/// Raises:
///     Exception: If request or parsing fails
#[pyfunction]
#[pyo3(signature = (app_id, lang, country, timeout=30))]
fn fetch_and_parse_app(
    app_id: &str,
    lang: &str,
    country: &str,
    timeout: u64,
) -> PyResult<RustAppInfo> {
    let runtime = get_runtime();

    if timeout == 30 {
        let client = get_client();
        runtime.block_on(async {
            client.fetch_and_parse_app(app_id, lang, country).await
        }).map_err(Into::into)
    } else {
        let client = PlayStoreClient::new(timeout)?;
        runtime.block_on(async {
            client.fetch_and_parse_app(app_id, lang, country).await
        }).map_err(Into::into)
    }
}

/// Fetch and parse reviews (combined HTTP + parsing, GIL-free)
///
/// Args:
///     app_id (str): The app package ID
///     lang (str): Language code
///     country (str): Country code
///     sort (int): Sort order (1=newest, 2=highest, 3=most helpful)
///     continuation_token (str | None): Token for pagination
///     timeout (int): Request timeout in seconds (default: 30)
///
/// Returns:
///     tuple: (list[RustReview], str | None) - Reviews and next token
///
/// Raises:
///     Exception: If request or parsing fails
#[pyfunction]
#[pyo3(signature = (app_id, lang, country, sort=1, continuation_token=None, timeout=30))]
fn fetch_and_parse_reviews(
    app_id: &str,
    lang: &str,
    country: &str,
    sort: u8,
    continuation_token: Option<&str>,
    timeout: u64,
) -> PyResult<(Vec<RustReview>, Option<String>)> {
    let runtime = get_runtime();

    if timeout == 30 {
        let client = get_client();
        runtime.block_on(async {
            client.fetch_and_parse_reviews(app_id, lang, country, sort, continuation_token).await
        }).map_err(Into::into)
    } else {
        let client = PlayStoreClient::new(timeout)?;
        runtime.block_on(async {
            client.fetch_and_parse_reviews(app_id, lang, country, sort, continuation_token).await
        }).map_err(Into::into)
    }
}

/// Fetch and parse search results (combined HTTP + parsing, GIL-free)
///
/// Args:
///     query (str): Search query string
///     lang (str): Language code
///     country (str): Country code
///     timeout (int): Request timeout in seconds (default: 30)
///
/// Returns:
///     list[RustSearchResult]: List of search results
///
/// Raises:
///     Exception: If request or parsing fails
#[pyfunction]
#[pyo3(signature = (query, lang, country, timeout=30))]
fn fetch_and_parse_search(
    query: &str,
    lang: &str,
    country: &str,
    timeout: u64,
) -> PyResult<Vec<RustSearchResult>> {
    let runtime = get_runtime();

    if timeout == 30 {
        let client = get_client();
        runtime.block_on(async {
            client.fetch_and_parse_search(query, lang, country).await
        }).map_err(Into::into)
    } else {
        let client = PlayStoreClient::new(timeout)?;
        runtime.block_on(async {
            client.fetch_and_parse_search(query, lang, country).await
        }).map_err(Into::into)
    }
}

/// Fetch and parse list results (combined HTTP + parsing, GIL-free)
///
/// Args:
///     category (str | None): Category code (e.g., "GAME_ACTION"), None for all apps
///     collection (str): Collection type (e.g., "topselling_free")
///     lang (str): Language code
///     country (str): Country code
///     num (int): Number of results (default: 100, max: 250)
///     timeout (int): Request timeout in seconds (default: 30)
///
/// Returns:
///     list[RustSearchResult]: List of apps in the category/collection
///
/// Raises:
///     Exception: If request or parsing fails
#[pyfunction]
#[pyo3(signature = (category, collection, lang, country, num=100, timeout=30))]
fn fetch_and_parse_list(
    category: Option<&str>,
    collection: &str,
    lang: &str,
    country: &str,
    num: u32,
    timeout: u64,
) -> PyResult<Vec<RustSearchResult>> {
    let runtime = get_runtime();

    if timeout == 30 {
        let client = get_client();
        runtime.block_on(async {
            client.fetch_and_parse_list(category, collection, lang, country, num).await
        }).map_err(Into::into)
    } else {
        let client = PlayStoreClient::new(timeout)?;
        runtime.block_on(async {
            client.fetch_and_parse_list(category, collection, lang, country, num).await
        }).map_err(Into::into)
    }
}

/// Batch fetch and parse multiple app pages in parallel (TRUE parallelism in Rust!)
///
/// This function processes multiple app requests concurrently within a single
/// Rust async runtime, avoiding the overhead of multiple `block_on` calls.
///
/// Args:
///     requests (list[tuple]): List of (app_id, lang, country) tuples
///
/// Returns:
///     list[RustAppInfo]: List of parsed app information (same order as input)
///
/// Raises:
///     Exception: If any request fails
///
/// Example:
///     >>> requests = [
///     ...     ("com.spotify.music", "en", "us"),
///     ...     ("com.netflix.mediaclient", "en", "us"),
///     ...     ("com.whatsapp", "en", "us"),
///     ... ]
///     >>> apps = fetch_and_parse_apps_batch(requests)
#[pyfunction]
fn fetch_and_parse_apps_batch(
    requests: Vec<(String, String, String)>,
) -> PyResult<Vec<RustAppInfo>> {
    let client = get_client();
    let runtime = get_runtime();

    runtime.block_on(async {
        let futures: Vec<_> = requests.iter()
            .map(|(app_id, lang, country)| {
                client.fetch_and_parse_app(app_id, lang, country)
            })
            .collect();

        try_join_all(futures).await
    }).map_err(Into::into)
}

/// Batch fetch and parse multiple list requests in parallel
///
/// Args:
///     requests (list[tuple]): List of (category, collection, lang, country, num) tuples
///         where category can be None
///
/// Returns:
///     list[list[RustSearchResult]]: List of result lists (same order as input)
///
/// Raises:
///     Exception: If any request fails
///
/// Example:
///     >>> requests = [
///     ...     (None, "topselling_free", "en", "us", 100),
///     ...     ("GAME_ACTION", "topselling_free", "en", "kr", 100),
///     ... ]
///     >>> results = fetch_and_parse_list_batch(requests)
#[pyfunction]
fn fetch_and_parse_list_batch(
    requests: Vec<(Option<String>, String, String, String, u32)>,
) -> PyResult<Vec<Vec<RustSearchResult>>> {
    let client = get_client();
    let runtime = get_runtime();

    runtime.block_on(async {
        let futures: Vec<_> = requests.iter()
            .map(|(category, collection, lang, country, num)| {
                client.fetch_and_parse_list(
                    category.as_deref(),
                    collection,
                    lang,
                    country,
                    *num
                )
            })
            .collect();

        try_join_all(futures).await
    }).map_err(Into::into)
}

/// Batch fetch and parse multiple search queries in parallel
///
/// Args:
///     requests (list[tuple]): List of (query, lang, country) tuples
///
/// Returns:
///     list[list[RustSearchResult]]: List of search results (same order as input)
///
/// Raises:
///     Exception: If any request fails
#[pyfunction]
fn fetch_and_parse_search_batch(
    requests: Vec<(String, String, String)>,
) -> PyResult<Vec<Vec<RustSearchResult>>> {
    let client = get_client();
    let runtime = get_runtime();

    runtime.block_on(async {
        let futures: Vec<_> = requests.iter()
            .map(|(query, lang, country)| {
                client.fetch_and_parse_search(query, lang, country)
            })
            .collect();

        try_join_all(futures).await
    }).map_err(Into::into)
}

/// Batch fetch and parse multiple review requests in parallel
///
/// Args:
///     requests (list[tuple]): List of (app_id, lang, country, sort, continuation_token) tuples
///
/// Returns:
///     list[tuple]: List of (reviews, next_token) tuples (same order as input)
///
/// Raises:
///     Exception: If any request fails
#[pyfunction]
fn fetch_and_parse_reviews_batch(
    requests: Vec<(String, String, String, u8, Option<String>)>,
) -> PyResult<Vec<(Vec<RustReview>, Option<String>)>> {
    let client = get_client();
    let runtime = get_runtime();

    runtime.block_on(async {
        let futures: Vec<_> = requests.iter()
            .map(|(app_id, lang, country, sort, continuation_token)| {
                client.fetch_and_parse_reviews(
                    app_id,
                    lang,
                    country,
                    *sort,
                    continuation_token.as_deref()
                )
            })
            .collect();

        try_join_all(futures).await
    }).map_err(Into::into)
}

/// Extract APK information including DEX count and manifest presence
///
/// Args:
///     apk_path (str): Path to the APK file
///
/// Returns:
///     dict: Dictionary with keys: dex_count, has_manifest, has_resources, dex_files
///
/// Raises:
///     Exception: If APK cannot be opened or is invalid
#[pyfunction]
fn extract_apk_info(apk_path: &str) -> PyResult<(usize, bool, bool, Vec<String>)> {
    let extractor = ApkExtractor::new(apk_path)
        .map_err(|e| error::PlayfastError::from(e))?;

    let dex_files: Vec<String> = extractor.dex_entries()
        .iter()
        .map(|e| e.name.clone())
        .collect();

    Ok((
        extractor.dex_count(),
        extractor.has_manifest(),
        extractor.has_resources(),
        dex_files,
    ))
}

/// Extract AndroidManifest.xml from APK (returns raw binary XML)
///
/// Args:
///     apk_path (str): Path to the APK file
///
/// Returns:
///     bytes: Raw AndroidManifest.xml binary data
///
/// Raises:
///     Exception: If APK cannot be opened or manifest not found
#[pyfunction]
fn extract_manifest_raw(apk_path: &str) -> PyResult<Vec<u8>> {
    let extractor = ApkExtractor::new(apk_path)
        .map_err(|e| error::PlayfastError::from(e))?;
    extractor.extract_manifest()
        .map_err(|e| error::PlayfastError::from(e).into())
}

/// Parse AndroidManifest.xml from APK
///
/// Args:
///     apk_path (str): Path to the APK file
///
/// Returns:
///     RustManifestInfo: Parsed manifest information including package name,
///                       version, permissions, activities, services, etc.
///
/// Raises:
///     Exception: If APK cannot be opened, manifest not found, or parsing fails
#[pyfunction]
fn parse_manifest_from_apk(apk_path: &str) -> PyResult<RustManifestInfo> {
    let extractor = ApkExtractor::new(apk_path)
        .map_err(|e| error::PlayfastError::from(e))?;
    let manifest_data = extractor.extract_manifest()
        .map_err(|e| error::PlayfastError::from(e))?;
    parse_manifest(&manifest_data)
        .map_err(|e| error::PlayfastError::from(e).into())
}

/// Extract all classes from an APK file
///
/// Args:
///     apk_path (str): Path to the APK file
///     parallel (bool): Use parallel processing (default: True)
///
/// Returns:
///     list[RustDexClass]: List of all classes from all DEX files
///
/// Raises:
///     Exception: If APK cannot be opened or DEX parsing fails
#[pyfunction]
#[pyo3(signature = (apk_path, parallel=true))]
fn extract_classes_from_apk(apk_path: &str, parallel: bool) -> PyResult<Vec<RustDexClass>> {
    let extractor = ApkExtractor::new(apk_path)
        .map_err(|e| error::PlayfastError::from(e))?;

    let dex_entries = extractor.dex_entries().to_vec();
    let container = dex::container::DexContainer::new(dex_entries);

    let classes = if parallel {
        container.extract_all_classes_parallel()
    } else {
        container.extract_all_classes()
    };

    classes.map_err(|e| error::PlayfastError::from(e).into())
}

/// Search for classes matching a filter in an APK
///
/// Args:
///     apk_path (str): Path to the APK file
///     filter (ClassFilter): Filter criteria for class search
///     limit (int | None): Maximum number of results (default: None = no limit)
///     parallel (bool): Use parallel processing (default: True)
///
/// Returns:
///     list[RustDexClass]: List of matching classes
///
/// Raises:
///     Exception: If APK cannot be opened or search fails
#[pyfunction]
#[pyo3(signature = (apk_path, filter, limit=None, parallel=true))]
fn search_classes(
    apk_path: &str,
    filter: &ClassFilter,
    limit: Option<usize>,
    parallel: bool,
) -> PyResult<Vec<RustDexClass>> {
    let extractor = ApkExtractor::new(apk_path)
        .map_err(|e| error::PlayfastError::from(e))?;

    let dex_entries = extractor.dex_entries().to_vec();
    let container = DexContainer::new(dex_entries);

    // Extract all classes
    let all_classes = if parallel {
        container.extract_all_classes_parallel()
    } else {
        container.extract_all_classes()
    };

    let all_classes = all_classes.map_err(|e| error::PlayfastError::from(e))?;

    // Filter classes
    let mut results: Vec<RustDexClass> = all_classes
        .into_iter()
        .filter(|class| filter.matches(class))
        .collect();

    // Apply limit if specified
    if let Some(max) = limit {
        results.truncate(max);
    }

    Ok(results)
}

/// Search for methods matching a filter in specific classes from an APK
///
/// Args:
///     apk_path (str): Path to the APK file
///     class_filter (ClassFilter): Filter for selecting classes
///     method_filter (MethodFilter): Filter for selecting methods
///     limit (int | None): Maximum number of results (default: None = no limit)
///     parallel (bool): Use parallel processing (default: True)
///
/// Returns:
///     list[tuple[RustDexClass, RustDexMethod]]: List of (class, method) tuples
///
/// Raises:
///     Exception: If APK cannot be opened or search fails
#[pyfunction]
#[pyo3(signature = (apk_path, class_filter, method_filter, limit=None, parallel=true))]
fn search_methods(
    apk_path: &str,
    class_filter: &ClassFilter,
    method_filter: &MethodFilter,
    limit: Option<usize>,
    parallel: bool,
) -> PyResult<Vec<(RustDexClass, RustDexMethod)>> {
    let extractor = ApkExtractor::new(apk_path)
        .map_err(|e| error::PlayfastError::from(e))?;

    let dex_entries = extractor.dex_entries().to_vec();
    let container = DexContainer::new(dex_entries);

    // Extract all classes
    let all_classes = if parallel {
        container.extract_all_classes_parallel()
    } else {
        container.extract_all_classes()
    };

    let all_classes = all_classes.map_err(|e| error::PlayfastError::from(e))?;

    // Filter classes and methods
    let mut results: Vec<(RustDexClass, RustDexMethod)> = Vec::new();

    for class in all_classes {
        if !class_filter.matches(&class) {
            continue;
        }

        for method in &class.methods {
            if method_filter.matches(method) {
                results.push((class.clone(), method.clone()));

                // Check limit
                if let Some(max) = limit {
                    if results.len() >= max {
                        return Ok(results);
                    }
                }
            }
        }
    }

    Ok(results)
}

/// Playfast core module - High-performance Google Play scraping
///
/// This module provides low-level Rust functions for advanced users.
/// Most users should use the high-level API from playfast.batch instead.
///
/// All functions release the GIL for true parallel execution.
///
/// Note: `gil_used = false` declares this module is safe to run without the GIL.
/// This only affects Python 3.14t (free-threading). On Python 3.13 and earlier,
/// this attribute is ignored and has no effect.
#[pymodule]
#[pyo3(gil_used = false)]
fn core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Legacy parsing-only functions (for backward compatibility)
    m.add_function(wrap_pyfunction!(parse_app_page, m)?)?;
    m.add_function(wrap_pyfunction!(parse_review_batch, m)?)?;
    m.add_function(wrap_pyfunction!(parse_search_results, m)?)?;
    m.add_function(wrap_pyfunction!(extract_continuation_token, m)?)?;

    // Async HTTP + Rust parsing helper functions
    m.add_function(wrap_pyfunction!(parse_batchexecute_list_response, m)?)?;
    m.add_function(wrap_pyfunction!(build_list_request_body, m)?)?;
    m.add_function(wrap_pyfunction!(parse_batchexecute_reviews_response, m)?)?;
    m.add_function(wrap_pyfunction!(build_reviews_request_body, m)?)?;

    // New combined HTTP+parsing functions (recommended for performance)
    m.add_function(wrap_pyfunction!(fetch_and_parse_app, m)?)?;
    m.add_function(wrap_pyfunction!(fetch_and_parse_reviews, m)?)?;
    m.add_function(wrap_pyfunction!(fetch_and_parse_search, m)?)?;
    m.add_function(wrap_pyfunction!(fetch_and_parse_list, m)?)?;

    // Batch functions for true parallel processing in Rust
    m.add_function(wrap_pyfunction!(fetch_and_parse_apps_batch, m)?)?;
    m.add_function(wrap_pyfunction!(fetch_and_parse_reviews_batch, m)?)?;
    m.add_function(wrap_pyfunction!(fetch_and_parse_search_batch, m)?)?;
    m.add_function(wrap_pyfunction!(fetch_and_parse_list_batch, m)?)?;

    // DEX and APK analysis functions
    m.add_function(wrap_pyfunction!(extract_apk_info, m)?)?;
    m.add_function(wrap_pyfunction!(extract_manifest_raw, m)?)?;
    m.add_function(wrap_pyfunction!(parse_manifest_from_apk, m)?)?;
    m.add_function(wrap_pyfunction!(extract_classes_from_apk, m)?)?;
    m.add_function(wrap_pyfunction!(search_classes, m)?)?;
    m.add_function(wrap_pyfunction!(search_methods, m)?)?;

    // Bytecode analysis functions
    m.add_function(wrap_pyfunction!(decode_bytecode, m)?)?;
    m.add_function(wrap_pyfunction!(extract_constants, m)?)?;
    m.add_function(wrap_pyfunction!(extract_method_calls, m)?)?;
    m.add_function(wrap_pyfunction!(extract_methods_bytecode, m)?)?;
    m.add_function(wrap_pyfunction!(get_method_bytecode_from_apk, m)?)?;

    // Method resolution functions
    m.add_function(wrap_pyfunction!(create_method_resolver, m)?)?;
    m.add_function(wrap_pyfunction!(resolve_method_from_apk, m)?)?;

    // Expression reconstruction functions (Phase 2)
    m.add_function(wrap_pyfunction!(create_expression_builder, m)?)?;
    m.add_function(wrap_pyfunction!(reconstruct_expressions_from_apk, m)?)?;

    // Class-level decompilation
    m.add_function(wrap_pyfunction!(decompile_class_from_apk, m)?)?;

    // Resources.arsc parsing
    m.add_function(wrap_pyfunction!(parse_resources_from_apk, m)?)?;

    // Entry point analysis
    m.add_function(wrap_pyfunction!(analyze_entry_points_from_apk, m)?)?;

    // Call graph analysis
    m.add_function(wrap_pyfunction!(build_call_graph_from_apk, m)?)?;
    m.add_function(wrap_pyfunction!(build_call_graph_from_apk_parallel, m)?)?;

    // Data flow analysis (generic, WebView is a special case)
    m.add_function(wrap_pyfunction!(create_data_flow_analyzer, m)?)?;
    m.add_function(wrap_pyfunction!(find_flows_from_apk, m)?)?;
    m.add_function(wrap_pyfunction!(find_webview_flows_from_apk, m)?)?;
    m.add_function(wrap_pyfunction!(find_file_flows_from_apk, m)?)?;
    m.add_function(wrap_pyfunction!(find_network_flows_from_apk, m)?)?;

    // Backward compatibility (deprecated)
    m.add_function(wrap_pyfunction!(analyze_webview_flows_from_apk, m)?)?;
    m.add_function(wrap_pyfunction!(create_webview_analyzer_from_apk, m)?)?;

    // Add Play Store model classes
    m.add_class::<RustAppInfo>()?;
    m.add_class::<RustReview>()?;
    m.add_class::<RustSearchResult>()?;
    m.add_class::<RustPermission>()?;

    // Add DEX/APK model classes
    m.add_class::<RustDexClass>()?;
    m.add_class::<RustDexMethod>()?;
    m.add_class::<RustDexField>()?;
    m.add_class::<RustReferencePool>()?;
    m.add_class::<RustManifestInfo>()?;
    m.add_class::<IntentFilterData>()?;
    m.add_class::<ActivityIntentFilter>()?;
    m.add_class::<RustInstruction>()?;
    m.add_class::<MethodSignature>()?;
    m.add_class::<MethodResolverPy>()?;
    m.add_class::<ReconstructedExpression>()?;
    m.add_class::<ExpressionBuilderPy>()?;
    m.add_class::<DecompiledClass>()?;
    m.add_class::<DecompiledMethod>()?;
    m.add_class::<PyResourceResolver>()?;
    m.add_class::<PyResolvedResource>()?;
    m.add_class::<EntryPoint>()?;
    m.add_class::<ComponentType>()?;
    m.add_class::<PyEntryPointAnalyzer>()?;
    m.add_class::<CallGraph>()?;
    m.add_class::<CallPath>()?;
    m.add_class::<MethodCall>()?;
    m.add_class::<PyCallGraphBuilder>()?;
    // New generic API
    m.add_class::<Flow>()?;
    m.add_class::<DataFlow>()?;
    m.add_class::<DataFlowAnalyzer>()?;

    // Backward compatibility (WebViewFlow/WebViewFlowAnalyzer are type aliases)

    // Add DEX filter classes
    m.add_class::<ClassFilter>()?;
    m.add_class::<MethodFilter>()?;

    // Add Google Play download client
    m.add_class::<download::GpapiClient>()?;

    Ok(())
}
