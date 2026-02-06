#!/usr/bin/env python3
"""
Embed data and upload to Azure Search Index

This script:
1. Loads data from CSV or Celonis EMS
2. Generates embeddings for each row
3. Uploads documents to Azure Search
4. Saves checkpoints for resume functionality

Usage:
    python scripts/embed_and_upload.py [--batch-size 5000] [--resume] [--max-rows N] [--source csv|celonis]

Options:
    --batch-size N       Number of rows to process per batch (default: 5000)
    --resume             Resume from checkpoint file if it exists
    --max-rows N         Process only first N rows (useful for testing)
    --source csv|celonis Data source to use (default: from .env or csv)
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    config,
    load_csv,
    format_datetime_column,
    init_embedding_tracking,
    save_checkpoint,
    load_checkpoint,
    get_embedding,
    upload_documents,
    print_embedding_summary
)


# ============================================================================
# FIELD MAPPING CONFIGURATION
# ============================================================================
# Map CSV columns to Azure Search index fields
# Customize this for your project's data structure

FIELD_MAPPING = {
    # CSV Column Name : Index Field Name
    "Id": "contract_item_id",
    "SystemContractNumber": "contract_number",
    "SystemContractItemNumber": "contract_item_number",
    "ShortText": "item_text",
    "Name": "vendor_name",
    "NetUnitPrice": "unit_price",
    "Currency": "currency",
    "ValidityPeriodStartDate": "contract_start",
    "ValidityPeriodEndDate": "contract_end"
}

# Which CSV column to embed (generate vector from)
TEXT_COLUMN_TO_EMBED = "ShortText"

# Datetime columns that need formatting for Azure
DATETIME_COLUMNS = ["ValidityPeriodStartDate", "ValidityPeriodEndDate"]

# ============================================================================
# CELONIS PQL COLUMNS (used when --source celonis)
# ============================================================================
# Each dict has "name" (matching FIELD_MAPPING keys above) and "query" (PQL expression).
# Customize the PQL queries for your Celonis data model.
CELONIS_PQL_COLUMNS = [
    {"name": "Id",                          "query": '"o_celonis_ContractItem"."ID"'},
    {"name": "SystemContractNumber",        "query": '"o_celonis_ContractItem"."SystemContractNumber"'},
    {"name": "SystemContractItemNumber",    "query": '"o_celonis_ContractItem"."SystemContractItemNumber"'},
    {"name": "ShortText",                   "query": '"o_celonis_ContractItem"."ShortText"'},
    {"name": "Name",                        "query": '"o_celonis_ContractItem"."Name"'},
    {"name": "NetUnitPrice",                "query": '"o_celonis_ContractItem"."NetUnitPrice"'},
    {"name": "Currency",                    "query": '"o_celonis_ContractItem"."Currency"'},
    {"name": "ValidityPeriodStartDate",     "query": '"o_celonis_ContractItem"."ValidityPeriodStartDate"'},
    {"name": "ValidityPeriodEndDate",       "query": '"o_celonis_ContractItem"."ValidityPeriodEndDate"'},
]


def process_batch(df, start_idx, batch_size, checkpoint_path, checkpoint_every=250):
    """
    Process a batch of rows: embed and upload

    Args:
        df: DataFrame with data
        start_idx: Starting row index for this batch
        batch_size: Number of rows to process
        checkpoint_path: Path to save checkpoints
        checkpoint_every: Save checkpoint every N rows
    """
    # Filter to pending rows
    pending = df[df["embedded_status"] != "success"]

    if len(pending) == 0:
        print("✅ All rows already processed!")
        return

    # Limit to batch size
    batch = pending.head(batch_size)
    total_rows = len(batch)

    print(f"\n🚀 Processing batch of {total_rows} rows...")

    success_count = 0
    fail_count = 0

    for i, (idx, row) in enumerate(batch.iterrows(), 1):
        doc_id = row.get("Id", f"row_{idx}")

        print(f"\n→ [{i}/{total_rows}] Processing {doc_id}...", end=" ")

        # 1. Generate embedding
        text_to_embed = row[TEXT_COLUMN_TO_EMBED]
        embedding = get_embedding(text_to_embed)

        if embedding is None:
            print("❌ Embedding failed")
            df.at[idx, "embedded_status"] = "failed"
            df.at[idx, "embedded_error"] = "Embedding generation failed"
            df.at[idx, "embedded_at"] = datetime.now(timezone.utc)
            fail_count += 1
            continue

        # 2. Prepare document for upload
        document = {}
        for csv_col, index_field in FIELD_MAPPING.items():
            if csv_col in row.index:
                value = row[csv_col]
                # Handle NaN/NaT values
                if pd.isna(value):
                    value = None
                document[index_field] = value

        # Add the embedding
        document["embedding"] = embedding

        # 3. Upload to Azure Search
        try:
            success = upload_documents([document])
            if success:
                print("✅")
                df.at[idx, "embedded_status"] = "success"
                df.at[idx, "embedded_error"] = ""
                df.at[idx, "embedded_at"] = datetime.now(timezone.utc)
                success_count += 1
            else:
                print("❌ Upload failed")
                df.at[idx, "embedded_status"] = "failed"
                df.at[idx, "embedded_error"] = "Upload to Azure Search failed"
                df.at[idx, "embedded_at"] = datetime.now(timezone.utc)
                fail_count += 1

        except Exception as e:
            print(f"❌ Error: {e}")
            df.at[idx, "embedded_status"] = "failed"
            df.at[idx, "embedded_error"] = str(e)[:2000]
            df.at[idx, "embedded_at"] = datetime.now(timezone.utc)
            fail_count += 1

        # Save checkpoint periodically
        processed = success_count + fail_count
        if checkpoint_path and (processed % checkpoint_every == 0):
            save_checkpoint(df, checkpoint_path)
            print(f"💾 Checkpoint saved ({processed} processed)")

        # Rate limiting
        time.sleep(config.sleep_between_requests)

    # Final checkpoint save
    if checkpoint_path:
        save_checkpoint(df, checkpoint_path)

    print(f"\n📊 Batch complete: {success_count} success, {fail_count} failed")


def main():
    """Main function to run the embedding and upload pipeline"""
    parser = argparse.ArgumentParser(
        description="Embed data and upload to Azure Search"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=config.batch_size,
        help="Number of rows to process per batch"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint file if it exists"
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Process only first N rows (for testing)"
    )
    parser.add_argument(
        "--source",
        choices=["csv", "celonis"],
        default=config.data_source,
        help="Data source: csv or celonis (default: from .env or csv)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Azure Search Vector Embedding Pipeline")
    print("=" * 60)
    print(f"Index: {config.azure_search_index_name}")
    print(f"Source: {args.source}")
    print(f"Batch size: {args.batch_size}")
    print()

    # Load data (from checkpoint if resuming, otherwise from source)
    if args.resume:
        df = load_checkpoint(config.checkpoint_file_path)
        if df is not None:
            print("✅ Resumed from checkpoint\n")
        else:
            print("ℹ️  No checkpoint found, loading from source...\n")
            df = None

    else:
        df = None

    if df is None:
        if args.source == "celonis":
            from utils import load_celonis_data
            config.validate_celonis()
            print("📡 Loading data from Celonis EMS...\n")
            df = load_celonis_data(
                columns=CELONIS_PQL_COLUMNS,
                limit=args.max_rows,
            )
        else:
            df = load_csv(config.csv_file_path)

    # Limit rows for testing if requested
    if args.max_rows:
        print(f"⚙️  Test mode: limiting to first {args.max_rows} rows\n")
        df = df.head(args.max_rows)

    # Format datetime columns for Azure
    print("📅 Formatting datetime columns...")
    for col in DATETIME_COLUMNS:
        if col in df.columns:
            format_datetime_column(df, col)
    print()

    # Initialize tracking columns
    df = init_embedding_tracking(df)

    # Show current progress
    print_embedding_summary(df)
    print()

    # Process in batches
    batch_num = 1
    while True:
        remaining = (df["embedded_status"] != "success").sum()

        if remaining == 0:
            print("\n🎉 All rows embedded successfully!")
            break

        print(f"\n{'='*60}")
        print(f"Batch {batch_num} - {remaining} rows remaining")
        print('='*60)

        process_batch(
            df,
            start_idx=0,
            batch_size=args.batch_size,
            checkpoint_path=config.checkpoint_file_path
        )

        batch_num += 1

        # Check if we're done
        remaining_after = (df["embedded_status"] != "success").sum()
        if remaining_after == 0:
            print("\n🎉 All rows embedded successfully!")
            break

        # Sleep between batches
        if remaining_after > 0:
            print(f"\n⏸️  Sleeping {config.sleep_between_batches}s before next batch...")
            time.sleep(config.sleep_between_batches)

    # Final summary
    print()
    print_embedding_summary(df)
    print()
    print(f"💾 Final checkpoint saved to: {config.checkpoint_file_path}")


if __name__ == "__main__":
    # Suppress SSL warnings when using IP-based endpoint
    import warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Import pandas here since it's used in process_batch
    import pandas as pd

    main()
