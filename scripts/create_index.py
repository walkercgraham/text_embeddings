#!/usr/bin/env python3
"""
Create Azure Search Index with Vector Search Capabilities

Usage:
    python scripts/create_index.py [--delete-existing]

Options:
    --delete-existing    Delete the index if it already exists before creating
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import config, create_index, delete_index, get_index_info


# ============================================================================
# INDEX SCHEMA DEFINITION
# ============================================================================
# Customize this schema for your project by modifying the fields below

INDEX_SCHEMA = {
    "name": config.azure_search_index_name,
    "fields": [
        {
            "name": "contract_item_id",
            "type": "Edm.String",
            "key": True,
            "filterable": True
        },
        {
            "name": "contract_number",
            "type": "Edm.String",
            "filterable": True,
            "searchable": True
        },
        {
            "name": "contract_item_number",
            "type": "Edm.Int32",
            "filterable": True
        },
        {
            "name": "item_text",
            "type": "Edm.String",
            "searchable": True
        },
        {
            "name": "vendor_name",
            "type": "Edm.String",
            "filterable": True,
            "searchable": True
        },
        {
            "name": "unit_price",
            "type": "Edm.Double",
            "filterable": True,
            "sortable": True
        },
        {
            "name": "currency",
            "type": "Edm.String",
            "filterable": True
        },
        {
            "name": "contract_start",
            "type": "Edm.DateTimeOffset",
            "filterable": True,
            "sortable": True
        },
        {
            "name": "contract_end",
            "type": "Edm.DateTimeOffset",
            "filterable": True,
            "sortable": True
        },
        {
            "name": "embedding",
            "type": "Collection(Edm.Single)",
            "dimensions": 1536,  # text-embedding-ada-002 dimension
            "searchable": True,
            "retrievable": True,
            "vectorSearchProfile": "myHnswProfile"
        }
    ],
    "vectorSearch": {
        "algorithms": [
            {
                "name": "myHnsw",
                "kind": "hnsw",
                "hnswParameters": {
                    "metric": "cosine",
                    "m": 12,
                    "efConstruction": 400,
                    "efSearch": 100
                }
            },
            {
                "name": "myExhaustive",
                "kind": "exhaustiveKnn",
                "exhaustiveKnnParameters": {
                    "metric": "cosine"
                }
            }
        ],
        "profiles": [
            {
                "name": "myHnswProfile",
                "algorithm": "myHnsw"
            },
            {
                "name": "myExhaustiveProfile",
                "algorithm": "myExhaustive"
            }
        ]
    }
}


def main():
    """Main function to create the index"""
    parser = argparse.ArgumentParser(
        description="Create Azure Search index with vector search capabilities"
    )
    parser.add_argument(
        "--delete-existing",
        action="store_true",
        help="Delete the index if it already exists"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Azure Search Index Creation")
    print("=" * 60)
    print(f"Index name: {config.azure_search_index_name}")
    print(f"Service: {config.azure_search_service}")
    print()

    # Delete existing index if requested
    if args.delete_existing:
        print("🗑️  Deleting existing index (if present)...")
        delete_index()
        print()

    # Create the index
    print("🔨 Creating index with vector search capabilities...")
    success = create_index(INDEX_SCHEMA)
    print()

    if success:
        # Verify the index was created
        print("✅ Verifying index creation...")
        get_index_info()
        print()
        print("🎉 Index creation complete!")
    else:
        print("❌ Index creation failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
