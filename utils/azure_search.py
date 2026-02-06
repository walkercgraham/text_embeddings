"""
Azure Search operations - index management and search functions
"""

import requests
import json
from typing import Dict, Any, List, Optional
from .config import config
from .embeddings import get_embedding


def _get_headers() -> Dict[str, str]:
    """Get standard headers for Azure Search API requests"""
    return {
        "Content-Type": "application/json",
        "api-key": config.azure_search_admin_key
    }


def delete_index() -> bool:
    """
    Delete the Azure Search index if it exists

    Returns:
        True if deleted successfully or didn't exist, False if error
    """
    url = (
        f"https://{config.azure_search_service}.search.windows.net/"
        f"indexes/{config.azure_search_index_name}"
        f"?api-version={config.azure_search_api_version}"
    )

    response = requests.delete(url, headers=_get_headers())

    if response.status_code in [200, 204]:
        print(f"🗑️  Index '{config.azure_search_index_name}' deleted successfully")
        return True
    elif response.status_code == 404:
        print(f"ℹ️  Index '{config.azure_search_index_name}' not found, nothing to delete")
        return True
    else:
        print(f"❌ Failed to delete index: {response.status_code}, {response.text}")
        return False


def create_index(index_schema: Dict[str, Any]) -> bool:
    """
    Create an Azure Search index with the provided schema

    Args:
        index_schema: The index configuration including fields and vector search settings

    Returns:
        True if created successfully, False otherwise
    """
    url = (
        f"https://{config.azure_search_service}.search.windows.net/"
        f"indexes/{config.azure_search_index_name}"
        f"?api-version={config.azure_search_api_version}"
    )

    response = requests.put(
        url,
        headers=_get_headers(),
        data=json.dumps(index_schema)
    )

    if response.status_code in [201, 204]:
        print(f"✅ Index '{config.azure_search_index_name}' created successfully!")
        return True
    else:
        print(f"❌ Failed to create index: {response.status_code}, {response.text}")
        return False


def get_index_info() -> Optional[Dict[str, Any]]:
    """
    Retrieve information about the current index

    Returns:
        Dictionary with index metadata, or None if failed
    """
    url = (
        f"https://{config.azure_search_service}.search.windows.net/"
        f"indexes/{config.azure_search_index_name}"
        f"?api-version={config.azure_search_api_version}"
    )

    response = requests.get(url, headers=_get_headers())

    if response.status_code == 200:
        index_definition = response.json()
        print(f"✅ Index '{config.azure_search_index_name}' fields:\n")
        for field in index_definition.get("fields", []):
            print(f"   - {field['name']} ({field['type']})")
        return index_definition
    else:
        print(f"❌ Failed to retrieve index: {response.status_code}, {response.text}")
        return None


def get_index_stats() -> Optional[Dict[str, Any]]:
    """
    Get statistics about the index (document count, storage size, etc.)

    Returns:
        Dictionary with index stats, or None if failed
    """
    url = (
        f"https://{config.azure_search_service}.search.windows.net/"
        f"indexes/{config.azure_search_index_name}/stats"
        f"?api-version={config.azure_search_api_version}"
    )

    response = requests.get(url, headers=_get_headers())

    if response.status_code == 200:
        stats = response.json()
        print(f"📊 Index stats:")
        print(f"   - Document count: {stats.get('documentCount', 0)}")
        print(f"   - Storage size: {stats.get('storageSize', 0)} bytes")
        return stats
    else:
        print(f"❌ Failed to retrieve stats: {response.status_code}, {response.text}")
        return None


def upload_documents(documents: List[Dict[str, Any]]) -> bool:
    """
    Upload documents to Azure Search index

    Args:
        documents: List of documents to upload. Each document should include
                  all required fields for the index schema.

    Returns:
        True if upload successful, False otherwise
    """
    url = (
        f"https://{config.azure_search_service}.search.windows.net/"
        f"indexes/{config.azure_search_index_name}/docs/index"
        f"?api-version={config.azure_search_api_version}"
    )

    # Add search action to each document
    for doc in documents:
        doc["@search.action"] = "mergeOrUpload"

    data = {"value": documents}

    response = requests.post(
        url,
        headers=_get_headers(),
        data=json.dumps(data)
    )

    if response.status_code == 200:
        return True
    else:
        print(f"❌ Upload failed: {response.status_code}, {response.text}")
        return False


def text_search(query: str, top_k: int = 3, select_fields: Optional[str] = None) -> Dict[str, Any]:
    """
    Perform text-based search using BM25 (keyword matching)

    Args:
        query: The search query text
        top_k: Number of results to return
        select_fields: Comma-separated list of fields to return (None = all fields)

    Returns:
        Dictionary containing search results
    """
    url = (
        f"https://{config.azure_search_service}.search.windows.net/"
        f"indexes/{config.azure_search_index_name}/docs/search"
        f"?api-version={config.azure_search_api_version}"
    )

    data = {
        "search": query,
        "top": top_k
    }

    if select_fields:
        data["select"] = select_fields

    response = requests.post(
        url,
        headers=_get_headers(),
        data=json.dumps(data)
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Text search failed: {response.status_code}, {response.text}")
        return {}


def vector_search(
    query: str,
    top_k: int = 3,
    vector_field: str = "embedding",
    select_fields: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform vector-based semantic search

    Args:
        query: The search query text (will be embedded automatically)
        top_k: Number of results to return
        vector_field: Name of the vector field in the index
        select_fields: Comma-separated list of fields to return (None = all fields)

    Returns:
        Dictionary containing search results
    """
    # First, embed the query
    query_embedding = get_embedding(query)
    if query_embedding is None:
        print("❌ Failed to embed query for vector search")
        return {}

    url = (
        f"https://{config.azure_search_service}.search.windows.net/"
        f"indexes/{config.azure_search_index_name}/docs/search"
        f"?api-version={config.azure_search_api_version}"
    )

    data = {
        "vectorQueries": [{
            "kind": "vector",
            "vector": query_embedding,
            "k": top_k,
            "fields": vector_field
        }]
    }

    if select_fields:
        data["select"] = select_fields

    response = requests.post(
        url,
        headers=_get_headers(),
        data=json.dumps(data)
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Vector search failed: {response.status_code}, {response.text}")
        return {}


def hybrid_search(
    query: str,
    top_k: int = 10,
    k_vector: int = 200,
    vector_field: str = "embedding",
    search_fields: Optional[List[str]] = None,
    select_fields: Optional[str] = None,
    filters: Optional[str] = None,
    query_type: str = "simple",
    search_mode: str = "any"
) -> Dict[str, Any]:
    """
    Perform hybrid search combining text (BM25) and vector search

    Args:
        query: The search query text
        top_k: Number of final results to return
        k_vector: Number of vector results to retrieve before fusion
        vector_field: Name of the vector field in the index
        search_fields: List of text fields to search (for BM25 leg)
        select_fields: Comma-separated list of fields to return (None = all fields)
        filters: OData filter expression
        query_type: "simple" or "full" query syntax
        search_mode: "any" or "all" for term matching

    Returns:
        Dictionary containing search results with RRF (Reciprocal Rank Fusion) scores
    """
    # Embed the query
    query_embedding = get_embedding(query)
    if query_embedding is None:
        print("❌ Failed to embed query for hybrid search")
        return {}

    # Ensure embedding is a list of floats
    if hasattr(query_embedding, 'tolist'):
        query_embedding = query_embedding.tolist()
    query_embedding = [float(x) for x in query_embedding]

    url = (
        f"https://{config.azure_search_service}.search.windows.net/"
        f"indexes/{config.azure_search_index_name}/docs/search"
        f"?api-version={config.azure_search_api_version}"
    )

    data = {
        # BM25 text search leg
        "search": query,
        "queryType": query_type,
        "searchMode": search_mode,

        # Vector search leg
        "vectorQueries": [{
            "kind": "vector",
            "fields": vector_field,
            "vector": query_embedding,
            "k": k_vector
        }],

        # Results configuration
        "top": top_k,
        "count": True
    }

    if search_fields:
        data["searchFields"] = ",".join(search_fields)

    if select_fields:
        data["select"] = select_fields

    if filters:
        data["filter"] = filters

    response = requests.post(
        url,
        headers=_get_headers(),
        data=json.dumps(data)
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Hybrid search failed: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        return {}
