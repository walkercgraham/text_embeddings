"""
Data processing utilities - CSV loading, datetime formatting, and checkpoint management
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable


# Column names for tracking embedding status
STATUS_COL = "embedded_status"   # "pending" | "success" | "failed"
ERROR_COL = "embedded_error"
AT_COL = "embedded_at"


def load_csv(csv_path: str) -> pd.DataFrame:
    """
    Load CSV file into a pandas DataFrame

    Args:
        csv_path: Path to the CSV file

    Returns:
        DataFrame with CSV data
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    print(f"📂 Loading CSV from: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"   Loaded {len(df)} rows")
    return df


def format_datetime_for_azure(dt_str: str) -> str:
    """
    Format datetime string for Azure Search (ISO 8601 with Z timezone)

    Args:
        dt_str: Datetime string in various formats

    Returns:
        Formatted datetime string like "2024-11-01T00:00:00Z"

    Note:
        Azure Search requires Edm.DateTimeOffset format with UTC timezone
    """
    # If it already has timezone info (Z or +hh:mm), keep it
    if dt_str.endswith("Z") or "+" in dt_str[10:] or "-" in dt_str[10:]:
        return dt_str

    # Otherwise, add Z to indicate UTC
    return dt_str + "Z"


def format_datetime_column(df: pd.DataFrame, column: str) -> None:
    """
    Format a datetime column in-place for Azure Search compatibility

    Args:
        df: DataFrame to modify
        column: Name of the datetime column to format

    Note:
        Modifies the DataFrame in-place. Treats naive datetimes as UTC.
    """
    # Parse datetime (handles various string formats)
    dt = pd.to_datetime(df[column], errors="coerce")

    # If values are naive (no timezone), treat them as UTC
    dt = dt.dt.tz_localize("UTC", nonexistent="shift_forward", ambiguous="NaT")

    # Format exactly as Azure likes: 2024-11-01T00:00:00Z
    df[column] = dt.dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def init_embedding_tracking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Initialize tracking columns for embedding status

    Args:
        df: DataFrame to add tracking columns to

    Returns:
        DataFrame with tracking columns added

    Note:
        Adds three columns:
        - embedded_status: "pending" | "success" | "failed"
        - embedded_error: Error message if failed
        - embedded_at: Timestamp of when embedding was completed
    """
    # Add status columns if they don't exist
    if STATUS_COL not in df.columns:
        df[STATUS_COL] = "pending"
    if ERROR_COL not in df.columns:
        df[ERROR_COL] = ""
    if AT_COL not in df.columns:
        df[AT_COL] = pd.NaT

    # Normalize any NaN values
    df[STATUS_COL] = df[STATUS_COL].fillna("pending")
    df[ERROR_COL] = df[ERROR_COL].fillna("")

    return df


def save_checkpoint(df: pd.DataFrame, checkpoint_path: str) -> None:
    """
    Save DataFrame to checkpoint file (Parquet format)

    Args:
        df: DataFrame to save
        checkpoint_path: Path to save checkpoint file
    """
    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(checkpoint_path, index=False)
    print(f"💾 Checkpoint saved: {checkpoint_path}")


def load_checkpoint(checkpoint_path: str) -> Optional[pd.DataFrame]:
    """
    Load DataFrame from checkpoint file if it exists

    Args:
        checkpoint_path: Path to checkpoint file

    Returns:
        DataFrame if checkpoint exists, None otherwise
    """
    path = Path(checkpoint_path)
    if not path.exists():
        return None

    print(f"📂 Loading checkpoint from: {checkpoint_path}")
    df = pd.read_parquet(checkpoint_path)
    print(f"   Loaded {len(df)} rows")

    # Show progress
    if STATUS_COL in df.columns:
        success = (df[STATUS_COL] == "success").sum()
        failed = (df[STATUS_COL] == "failed").sum()
        pending = (df[STATUS_COL] == "pending").sum()
        print(f"   Progress: {success} success, {failed} failed, {pending} pending")

    return df


def prepare_documents_for_upload(
    df: pd.DataFrame,
    field_mapping: Dict[str, str],
    row_filter: Optional[Callable] = None
) -> list:
    """
    Prepare documents from DataFrame for upload to Azure Search

    Args:
        df: Source DataFrame
        field_mapping: Dictionary mapping DataFrame columns to index field names
                      Example: {"Id": "contract_item_id", "ShortText": "item_text"}
        row_filter: Optional function to filter rows (e.g., lambda row: row['embedded_status'] == 'success')

    Returns:
        List of document dictionaries ready for upload
    """
    documents = []

    for idx, row in df.iterrows():
        # Apply filter if provided
        if row_filter and not row_filter(row):
            continue

        # Build document using field mapping
        doc = {}
        for source_col, target_field in field_mapping.items():
            if source_col in row.index:
                value = row[source_col]

                # Convert NaN/NaT to None
                if pd.isna(value):
                    value = None

                doc[target_field] = value

        documents.append(doc)

    return documents


def get_embedding_progress(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get embedding progress statistics

    Args:
        df: DataFrame with embedding tracking columns

    Returns:
        Dictionary with counts of success, failed, and pending rows
    """
    if STATUS_COL not in df.columns:
        return {"total": len(df), "success": 0, "failed": 0, "pending": len(df)}

    return {
        "total": len(df),
        "success": (df[STATUS_COL] == "success").sum(),
        "failed": (df[STATUS_COL] == "failed").sum(),
        "pending": (df[STATUS_COL] == "pending").sum()
    }


def print_embedding_summary(df: pd.DataFrame) -> None:
    """
    Print a summary of embedding progress

    Args:
        df: DataFrame with embedding tracking columns
    """
    stats = get_embedding_progress(df)

    print("\n===== EMBEDDING SUMMARY =====")
    print(f"✅ Success  : {stats['success']}")
    print(f"❌ Failed   : {stats['failed']}")
    print(f"⏳ Pending  : {stats['pending']}")
    print(f"📊 Total    : {stats['total']}")
    print("=============================")
