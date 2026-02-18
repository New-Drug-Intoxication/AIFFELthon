import base64
import io
import re
import sys
from io import StringIO

# Create a persistent namespace that will be shared across all executions
_persistent_namespace = {}
_DEFAULT_NAMESPACE_IMPORTS = {
    "os": "os",
    "pd": "pandas",
    "np": "numpy",
}
_DEFAULT_NAMESPACE_HELPERS = (
    "infer_column",
    "infer_ensembl_gene_id_column",
    "ensure_unique_columns",
    "safe_concat",
    "safe_reindex",
    "preview",
    "summarize_df",
    "summarize_dict",
)

_DEFAULT_DF_HEAD_ROWS = 5
_DEFAULT_DICT_TOP_N = 20
_DEFAULT_LIST_TOP_N = 20
_DEFAULT_MAX_CHARS = 500
MAX_OUTPUT_CHARS = 8000
TRUNCATE_THRESHOLD = 3000

# Global list to store captured plots
_captured_plots = []


def _bootstrap_default_namespace() -> None:
    """Ensure commonly used modules are preloaded into the persistent namespace."""
    global _persistent_namespace

    _persistent_namespace.setdefault("__builtins__", __builtins__)
    for alias, module_name in _DEFAULT_NAMESPACE_IMPORTS.items():
        if alias in _persistent_namespace:
            continue
        try:
            _persistent_namespace[alias] = __import__(module_name)
        except Exception:
            # Optional preload: skip unavailable modules and keep execution alive.
            continue

    for helper_name in _DEFAULT_NAMESPACE_HELPERS:
        helper = globals().get(helper_name)
        if callable(helper):
            _persistent_namespace[helper_name] = helper


def reset_python_repl_namespace(preload_defaults: bool = True) -> None:
    """Reset the shared Python REPL namespace.

    Args:
        preload_defaults: If True, preload commonly used aliases (`pd`, `np`, `os`).
    """
    global _persistent_namespace
    _persistent_namespace = {"__builtins__": __builtins__}
    if preload_defaults:
        _bootstrap_default_namespace()


def _normalize_column_token(name: object) -> str:
    """Normalize a column identifier for robust fuzzy matching."""
    import re

    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def infer_column(df, candidates, *, normalize: bool = True):
    """Infer the best matching DataFrame column from a list of candidate names.

    Args:
        df: Pandas DataFrame-like object.
        candidates: Iterable of candidate column names ordered by preference.
        normalize: If True, compare with normalized tokens (case/punctuation agnostic).

    Returns:
        The matched column name from `df.columns`, or `None` when no match is found.
    """
    columns = list(getattr(df, "columns", []))
    if not columns:
        return None

    # Exact match first
    for cand in candidates:
        if cand in columns:
            return cand

    # Case-insensitive match
    lower_to_column = {str(col).lower(): col for col in columns}
    for cand in candidates:
        matched = lower_to_column.get(str(cand).lower())
        if matched is not None:
            return matched

    if not normalize:
        return None

    normalized_to_column = {}
    for col in columns:
        token = _normalize_column_token(col)
        normalized_to_column.setdefault(token, col)

    for cand in candidates:
        token = _normalize_column_token(cand)
        if token in normalized_to_column:
            return normalized_to_column[token]

    return None


def infer_ensembl_gene_id_column(df):
    """Infer likely Ensembl gene identifier column name from a DataFrame.

    This helper handles common schema variants such as `ensembl_gene_id`,
    `Ensembl Gene ID`, `gene_id`, and fallback detection based on `ENSG...` values.
    """
    candidates = [
        "ensembl_gene_id",
        "ensembl gene id",
        "ensembl_id",
        "gene_ensembl_id",
        "gene_id",
        "ensembl",
        "ensg",
    ]
    matched = infer_column(df, candidates, normalize=True)
    if matched is not None:
        return matched

    # Value-based fallback: find a column with ENSG-like identifiers.
    columns = list(getattr(df, "columns", []))
    for col in columns:
        try:
            series = df[col].dropna().astype(str).head(200)
        except Exception:
            continue
        if not series.empty and series.str.startswith("ENSG").mean() >= 0.5:
            return col

    return None


def ensure_unique_columns(df, sep: str = "__dup"):
    """Return a copy of a DataFrame with guaranteed unique column names."""
    columns = list(getattr(df, "columns", []))
    if not columns:
        return df

    if getattr(df.columns, "is_unique", True):
        return df

    seen = {}
    renamed = []
    for col in columns:
        key = str(col)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 1:
            renamed.append(col)
        else:
            renamed.append(f"{key}{sep}{seen[key] - 1}")

    out = df.copy()
    out.columns = renamed
    return out


def safe_concat(frames, axis: int = 0, ignore_index: bool = True, dedup_columns: bool = True, **kwargs):
    """Safely concatenate DataFrames while optionally deduplicating columns first."""
    import pandas as pd

    prepared = []
    for frame in frames:
        if frame is None:
            continue
        if dedup_columns and hasattr(frame, "columns"):
            prepared.append(ensure_unique_columns(frame))
        else:
            prepared.append(frame)

    if not prepared:
        return pd.DataFrame()

    return pd.concat(prepared, axis=axis, ignore_index=ignore_index, **kwargs)


def safe_reindex(df, *args, dedup_columns: bool = True, dedup_index: bool = True, **kwargs):
    """Safely call DataFrame.reindex after fixing duplicate columns/index when requested."""
    working = df
    if dedup_columns and hasattr(working, "columns") and not working.columns.is_unique:
        working = ensure_unique_columns(working)
    if dedup_index and hasattr(working, "index") and not working.index.is_unique:
        working = working.reset_index(drop=True)
    return working.reindex(*args, **kwargs)


def _truncate_text(text: object, max_chars: int = _DEFAULT_MAX_CHARS) -> str:
    """Convert an object to text and truncate long output for compact summaries."""
    rendered = str(text)
    if len(rendered) <= max_chars:
        return rendered
    omitted = len(rendered) - max_chars
    return f"{rendered[:max_chars]} ... [truncated {omitted} chars]"


def summarize_df(df, *, head_rows: int = _DEFAULT_DF_HEAD_ROWS, max_chars: int = _DEFAULT_MAX_CHARS) -> str:
    """Return a compact summary string for DataFrames."""
    if df is None:
        return "DataFrame summary: <None>"

    try:
        shape = getattr(df, "shape", None)
        columns = list(getattr(df, "columns", []))
        col_preview = columns[:50]
        lines = [
            f"DataFrame summary: shape={shape}",
            f"columns({len(columns)}): {col_preview}",
        ]
        if len(columns) > len(col_preview):
            lines.append(f"... {len(columns) - len(col_preview)} more columns omitted")

        head_obj = df.head(head_rows) if hasattr(df, "head") else df
        lines.append(f"head({head_rows}):")
        lines.append(_truncate_text(head_obj, max_chars=max_chars))
        return "\n".join(lines)
    except Exception as exc:
        return f"DataFrame summary unavailable: {exc}"


def summarize_dict(d, *, top_n: int = _DEFAULT_DICT_TOP_N, max_chars: int = _DEFAULT_MAX_CHARS) -> str:
    """Return a compact key/value summary string for dictionaries."""
    if d is None:
        return "dict summary: <None>"
    if not isinstance(d, dict):
        return _truncate_text(d, max_chars=max_chars)

    items = list(d.items())
    lines = [f"dict summary: total_keys={len(items)}, showing_top={min(top_n, len(items))}"]
    for key, value in items[:top_n]:
        key_text = _truncate_text(key, max_chars=120)
        value_text = _truncate_text(repr(value), max_chars=max_chars)
        lines.append(f"- {key_text}: {value_text}")

    if len(items) > top_n:
        lines.append(f"... {len(items) - top_n} more keys omitted")
    return "\n".join(lines)


def _summarize_sequence(seq, *, top_n: int = _DEFAULT_LIST_TOP_N, max_chars: int = _DEFAULT_MAX_CHARS) -> str:
    """Return a compact summary for list/tuple/set values."""
    seq_list = list(seq)
    lines = [f"{type(seq).__name__} summary: size={len(seq_list)}, showing_top={min(top_n, len(seq_list))}"]
    for idx, value in enumerate(seq_list[:top_n]):
        lines.append(f"- [{idx}] {_truncate_text(repr(value), max_chars=max_chars)}")
    if len(seq_list) > top_n:
        lines.append(f"... {len(seq_list) - top_n} more items omitted")
    return "\n".join(lines)


def preview(
    obj,
    *,
    df_head: int = _DEFAULT_DF_HEAD_ROWS,
    dict_top_n: int = _DEFAULT_DICT_TOP_N,
    list_top_n: int = _DEFAULT_LIST_TOP_N,
    max_chars: int = _DEFAULT_MAX_CHARS,
) -> str:
    """Return a compact preview string for common large objects."""
    if obj is None:
        return "<None>"

    # DataFrame/Series-like: prioritize tabular summary first.
    if hasattr(obj, "columns") and hasattr(obj, "shape") and hasattr(obj, "head"):
        return summarize_df(obj, head_rows=df_head, max_chars=max_chars)

    if isinstance(obj, dict):
        return summarize_dict(obj, top_n=dict_top_n, max_chars=max_chars)

    if isinstance(obj, (list, tuple, set)):
        return _summarize_sequence(obj, top_n=list_top_n, max_chars=max_chars)

    return _truncate_text(obj, max_chars=max_chars)


def _line_signature(line: str) -> str:
    """Build a loose structural signature for a line by masking values."""
    masked = re.sub(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", "D", line)
    masked = re.sub(r"\b[A-Za-z_][\w\-]*\b", "W", masked)
    masked = re.sub(r"\s+", " ", masked).strip()
    return masked


def _format_group(group: list[tuple[str, str]], head: int, tail: int) -> str:
    """Format a run of lines that share the same signature with optional compression."""
    lines = [item[0] for item in group]
    if len(lines) <= head + tail + 1:
        return "\n".join(lines)

    omitted = len(lines) - head - tail
    result = lines[:head]
    result.append(f"  ... ({omitted} more rows with same structure)")
    result.extend(lines[-tail:])
    return "\n".join(result)


def _compress_repeated_lines(lines: list[str], head: int = 5, tail: int = 2) -> str:
    """Compress consecutive lines that share a structural signature."""
    if len(lines) <= head + tail + 3:
        return "\n".join(lines)

    chunks: list[str] = []
    current_group: list[tuple[str, str]] = []

    for line in lines:
        signature = _line_signature(line)
        if current_group and signature == current_group[0][1]:
            current_group.append((line, signature))
            continue

        if current_group:
            chunks.append(_format_group(current_group, head=head, tail=tail))
        current_group = [(line, signature)]

    if current_group:
        chunks.append(_format_group(current_group, head=head, tail=tail))

    return "\n".join(chunks)


def _structural_summarize(text: str) -> str:
    """Apply structure-aware regex-based summarization to very large text."""

    # DataFrame-like reprs: keep header + shape footer, collapse the middle.
    text = re.sub(
        r"((?:.*\n){0,8})(?:.*\n){10,}(\[\d+\s+rows\s+x\s+\d+\s+columns\])",
        lambda m: f"{m.group(1)}  ... (omitted)\n{m.group(2)}",
        text,
        flags=re.IGNORECASE,
    )

    def _shorten_container(match: re.Match[str]) -> str:
        content = match.group(0)
        if len(content) < 500:
            return content
        return f"{content[:300]} ... ({len(content)} chars total)"

    text = re.sub(r"\{[^{}]{500,}\}", _shorten_container, text, flags=re.DOTALL)
    text = re.sub(r"\[[^\[\]]{500,}\]", _shorten_container, text, flags=re.DOTALL)
    return text


def _postprocess_output(raw: str) -> str:
    """Post-process executed stdout so the LLM can consume compact, high-signal context."""
    if not raw:
        return raw

    if len(raw) <= TRUNCATE_THRESHOLD:
        return raw

    lines = raw.split("\n")
    compressed = _compress_repeated_lines(lines)

    if len(compressed) > MAX_OUTPUT_CHARS:
        compressed = _structural_summarize(compressed)

    if len(compressed) > MAX_OUTPUT_CHARS:
        half = MAX_OUTPUT_CHARS // 2
        compressed = (
            compressed[:half]
            + f"\n\n... [{len(raw)} chars total, truncated] ...\n\n"
            + compressed[-half:]
        )

    return compressed


def run_python_repl(command: str) -> str:
    """Executes the provided Python command in a persistent environment and returns the output.
    Variables defined in one execution will be available in subsequent executions.
    """

    def execute_in_repl(command: str) -> str:
        """Helper function to execute the command in the persistent environment."""
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()

        # Use the persistent namespace
        global _persistent_namespace

        try:
            _bootstrap_default_namespace()

            # Apply matplotlib monkey patches before execution
            _apply_matplotlib_patches()

            # Execute the command in the persistent namespace
            exec(command, _persistent_namespace)
            output = mystdout.getvalue()

            # Capture any matplotlib plots that were generated
            # _capture_matplotlib_plots()

        except Exception as e:
            output = f"Error: {str(e)}"
        finally:
            sys.stdout = old_stdout
        return _postprocess_output(output)

    command = command.strip("```").strip()
    return execute_in_repl(command)


reset_python_repl_namespace(preload_defaults=True)


def _capture_matplotlib_plots():
    """Capture any matplotlib plots that might have been generated during execution."""
    global _captured_plots
    try:
        import matplotlib.pyplot as plt

        # Check if there are any active figures
        if plt.get_fignums():
            for fig_num in plt.get_fignums():
                fig = plt.figure(fig_num)

                # Save figure to base64
                buffer = io.BytesIO()
                fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                buffer.seek(0)

                # Convert to base64
                image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
                plot_data = f"data:image/png;base64,{image_data}"

                # Add to captured plots if not already there
                if plot_data not in _captured_plots:
                    _captured_plots.append(plot_data)

                # Close the figure to free memory
                plt.close(fig)

    except ImportError:
        # matplotlib not available
        pass
    except Exception as e:
        print(f"Warning: Could not capture matplotlib plots: {e}")


def _apply_matplotlib_patches():
    """Apply simple monkey patches to matplotlib functions to automatically capture plots."""
    try:
        import matplotlib.pyplot as plt

        # Only patch if matplotlib is available and not already patched
        if hasattr(plt, "_biomni_patched"):
            return

        # Store original functions
        original_show = plt.show
        original_savefig = plt.savefig

        def show_with_capture(*args, **kwargs):
            """Enhanced show function that captures plots before displaying them."""
            # Capture any plots before showing
            _capture_matplotlib_plots()
            # Print a message to indicate plot was generated
            print("Plot generated and displayed")
            # Call the original show function
            return original_show(*args, **kwargs)

        def savefig_with_capture(*args, **kwargs):
            """Enhanced savefig function that captures plots after saving them."""
            # Get the filename from args if provided
            filename = args[0] if args else kwargs.get("fname", "unknown")
            # Call the original savefig function
            result = original_savefig(*args, **kwargs)
            # Capture the plot after saving
            _capture_matplotlib_plots()
            # Print a message to indicate plot was saved
            print(f"Plot saved to: {filename}")
            return result

        # Replace functions with enhanced versions
        plt.show = show_with_capture
        plt.savefig = savefig_with_capture

        # Mark as patched to avoid double-patching
        plt._biomni_patched = True

    except ImportError:
        # matplotlib not available
        pass
    except Exception as e:
        print(f"Warning: Could not apply matplotlib patches: {e}")


def get_captured_plots():
    """Get all captured matplotlib plots."""
    global _captured_plots
    return _captured_plots.copy()


def clear_captured_plots():
    """Clear all captured matplotlib plots."""
    global _captured_plots
    _captured_plots = []


def read_function_source_code(function_name: str) -> str:
    """Read the source code of a function from any module path.

    Parameters
    ----------
        function_name (str): Fully qualified function name (e.g., 'bioagentos.tool.support_tools.write_python_code')

    Returns
    -------
        str: The source code of the function

    """
    import importlib
    import inspect

    # Split the function name into module path and function name
    parts = function_name.split(".")
    module_path = ".".join(parts[:-1])
    func_name = parts[-1]

    try:
        # Import the module
        module = importlib.import_module(module_path)

        # Get the function object from the module
        function = getattr(module, func_name)

        # Get the source code of the function
        source_code = inspect.getsource(function)

        return source_code
    except (ImportError, AttributeError) as e:
        return f"Error: Could not find function '{function_name}'. Details: {str(e)}"


# def request_human_feedback(question, context, reason_for_uncertainty):
#     """
#     Request human feedback on a question.

#     Parameters:
#         question (str): The question that needs human feedback.
#         context (str): Context or details that help the human understand the situation.
#         reason_for_uncertainty (str): Explanation for why the LLM is uncertain about its answer.

#     Returns:
#         str: The feedback provided by the human.
#     """
#     print("Requesting human feedback...")
#     print(f"Question: {question}")
#     print(f"Context: {context}")
#     print(f"Reason for Uncertainty: {reason_for_uncertainty}")

#     # Capture human feedback
#     human_response = input("Please provide your feedback: ")

#     return human_response


def download_synapse_data(
    entity_ids: str | list[str],
    download_location: str = ".",
    follow_link: bool = False,
    recursive: bool = False,
    timeout: int = 300,
    entity_type: str = "dataset",
):
    """Download data from Synapse using entity IDs.

    Uses the synapse CLI to download files, folders, or projects from Synapse.
    Requires SYNAPSE_AUTH_TOKEN environment variable for authentication.
    Automatically installs synapseclient if not available.

    CRITICAL: Always check entity type from query_synapse() search results or user hints and pass the correct entity_type!
    The default entity_type="dataset" may not be appropriate for your entity.

    IMPORTANT: Multiple entity IDs are only supported for entity_type="file".
    For datasets, folders, and projects, only a single entity_id is supported.

    Parameters
    ----------
    entity_ids : str or list of str
        Synapse entity ID(s) to download.
        - For files: Can be a single ID string or list of ID strings
        - For datasets/folders/projects: Must be a single ID string only
    download_location : str, default "."
        Directory where files will be downloaded (current directory by default)
    follow_link : bool, default False
        Whether to follow links to download the linked entity
    recursive : bool, default False
        Whether to recursively download folders and their contents
        ONLY valid for entity_type="folder" - ignored for other types
    timeout : int, default 300
        Timeout in seconds for each download operation
    entity_type : str, default "dataset"
        Type of Synapse entity ("dataset", "file", "folder", "project")
        MUST match the actual entity type from search results or user hints!
        The default "dataset" should only be used for actual datasets.
        Check the 'node_type' field in search results to determine correct type.

    Returns
    -------
    dict
        Dictionary containing download results and any errors

    Notes
    -----
    Requires SYNAPSE_AUTH_TOKEN environment variable with your Synapse personal
    access token for authentication.

    AGENT USAGE GUIDANCE:
    1. Always check the 'node_type' field from query_synapse() search results or user hints
    2. Pass the correct entity_type parameter matching the node_type
    3. Do NOT rely on the default entity_type="dataset" unless confirmed
    4. For multiple downloads, ensure all entities are of type "file"
    5. Only use recursive=True with entity_type="folder"

    Examples
    --------
    # After searching with query_synapse(), check node_type and use appropriate entity_type:

    # If search result shows 'node_type': 'dataset'
    download_synapse_data("syn123456", entity_type="dataset")

    # If search result shows 'node_type': 'file'
    download_synapse_data("syn654321", entity_type="file")

    # If search result shows 'node_type': 'folder'
    download_synapse_data("syn789012", entity_type="folder", recursive=True)

    # Multiple files (only if all are 'node_type': 'file')
    download_synapse_data(["syn111", "syn222"], entity_type="file")
    """
    import os
    import subprocess

    # Check for required authentication token
    synapse_token = os.environ.get("SYNAPSE_AUTH_TOKEN")
    if not synapse_token:
        return {
            "success": False,
            "error": "SYNAPSE_AUTH_TOKEN environment variable is required for downloading",
            "suggestion": "Set SYNAPSE_AUTH_TOKEN with your Synapse personal access token",
        }

    # Check if synapse CLI is available
    try:
        subprocess.run(["synapse", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # Try to install synapseclient
            print("Installing synapseclient...")
            subprocess.run(["pip", "install", "synapseclient"], check=True)
            print("✓ synapseclient installed successfully")
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to install synapseclient: {e}",
                "suggestion": "Please install manually: pip install synapseclient",
            }

    # Ensure entity_ids is a list
    if isinstance(entity_ids, str):
        entity_ids = [entity_ids]

    # Validate that multiple IDs are only used with file entity type
    if len(entity_ids) > 1 and entity_type != "file":
        return {
            "success": False,
            "error": f"Multiple entity IDs are only supported for entity_type='file'. "
            f"For entity_type='{entity_type}', only a single entity_id is supported.",
            "suggestion": "Use a single entity_id string instead of a list, or change entity_type to 'file'",
        }

    # Validate that recursive is only used with folder entity type
    if recursive and entity_type != "folder":
        return {
            "success": False,
            "error": f"recursive=True is only valid for entity_type='folder'. "
            f"For entity_type='{entity_type}', recursive should be False.",
            "suggestion": "Set recursive=False, or change entity_type to 'folder' if appropriate",
        }

    # Create download directory if it doesn't exist
    os.makedirs(download_location, exist_ok=True)

    results = []
    errors = []

    for entity_id in entity_ids:
        try:
            # Build synapse download command with authentication
            if entity_type == "dataset":
                # For datasets, use query syntax to download the actual files
                cmd = [
                    "synapse",
                    "-p",
                    synapse_token,
                    "get",
                    "-q",
                    f"select * from {entity_id}",
                    "--downloadLocation",
                    download_location,
                ]
            else:
                # For files, folders, projects, use direct ID
                cmd = ["synapse", "-p", synapse_token, "get", entity_id, "--downloadLocation", download_location]

            # Add recursive flag only for folders (validation above ensures recursive is only True for folders)
            if entity_type == "folder" and recursive:
                cmd.append("-r")

            if follow_link:
                cmd.append("--followLink")

            # Execute download
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)

            results.append(
                {
                    "entity_id": entity_id,
                    "success": True,
                    "stdout": result.stdout,
                    "download_location": download_location,
                }
            )

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to download {entity_id}: {e.stderr if e.stderr else str(e)}"
            errors.append(error_msg)
            results.append({"entity_id": entity_id, "success": False, "error": error_msg})
        except subprocess.TimeoutExpired:
            error_msg = f"Download timeout for {entity_id} (>{timeout} seconds)"
            errors.append(error_msg)
            results.append({"entity_id": entity_id, "success": False, "error": error_msg})

    # Summary
    successful_downloads = [r for r in results if r["success"]]
    failed_downloads = [r for r in results if not r["success"]]

    return {
        "success": len(failed_downloads) == 0,
        "total_requested": len(entity_ids),
        "successful": len(successful_downloads),
        "failed": len(failed_downloads),
        "download_location": download_location,
        "results": results,
        "errors": errors if errors else None,
    }
