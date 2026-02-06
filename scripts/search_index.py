#!/usr/bin/env python3
"""
Search Azure Search Index

Test all three search modes: text (BM25), vector (semantic), and hybrid

Usage:
    python scripts/search_index.py --query "search terms" --mode [text|vector|hybrid]
    python scripts/search_index.py --query "CHAIR" --mode text --top 5
    python scripts/search_index.py --query "office furniture" --mode hybrid

Options:
    --query TEXT      The search query (required)
    --mode MODE       Search mode: text, vector, or hybrid (default: hybrid)
    --top N           Number of results to return (default: 3)
    --fields FIELDS   Comma-separated list of fields to return (default: all)
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import config, text_search, vector_search, hybrid_search


def print_results(results, mode):
    """Pretty print search results"""
    if not results or "value" not in results:
        print("❌ No results found")
        return

    documents = results["value"]
    count = results.get("@odata.count", len(documents))

    print(f"\n{'='*80}")
    print(f"Search Results ({mode.upper()} mode)")
    print(f"{'='*80}")
    print(f"Total matches: {count}")
    print(f"Showing: {len(documents)} results\n")

    for i, doc in enumerate(documents, 1):
        score = doc.get("@search.score", "N/A")
        print(f"Result {i} (Score: {score})")
        print("-" * 80)

        # Print all fields except @search fields
        for key, value in doc.items():
            if not key.startswith("@search"):
                # Format the value nicely
                if value is None:
                    value = "N/A"
                elif isinstance(value, (list, dict)):
                    value = json.dumps(value, indent=2)

                print(f"  {key}: {value}")

        print()


def main():
    """Main function to run search"""
    parser = argparse.ArgumentParser(
        description="Search Azure Search index using text, vector, or hybrid search"
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Search query text"
    )
    parser.add_argument(
        "--mode",
        choices=["text", "vector", "hybrid"],
        default="hybrid",
        help="Search mode (default: hybrid)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=3,
        help="Number of results to return (default: 3)"
    )
    parser.add_argument(
        "--fields",
        default=None,
        help="Comma-separated list of fields to return (default: all)"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("Azure Search Query")
    print("=" * 80)
    print(f"Index: {config.azure_search_index_name}")
    print(f"Query: {args.query}")
    print(f"Mode: {args.mode}")
    print(f"Top K: {args.top}")
    print()

    # Suppress SSL warnings
    import warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Execute search based on mode
    try:
        if args.mode == "text":
            print("🔍 Performing text search (BM25)...")
            results = text_search(
                query=args.query,
                top_k=args.top,
                select_fields=args.fields
            )

        elif args.mode == "vector":
            print("🔍 Performing vector search (semantic)...")
            results = vector_search(
                query=args.query,
                top_k=args.top,
                select_fields=args.fields
            )

        elif args.mode == "hybrid":
            print("🔍 Performing hybrid search (text + vector with RRF)...")
            # For hybrid search, need to specify searchable text fields
            # Customize this list based on your index schema
            search_fields = ["item_text", "vendor_name", "contract_number"]

            results = hybrid_search(
                query=args.query,
                top_k=args.top,
                search_fields=search_fields,
                select_fields=args.fields
            )

        # Print results
        print_results(results, args.mode)

    except Exception as e:
        print(f"\n❌ Search failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
