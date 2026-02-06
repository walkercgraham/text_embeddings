"""
Celonis EMS connection utilities - extract data via PQL queries

Requires pycelonis: pip install --extra-index-url=https://pypi.celonis.cloud/ pycelonis
"""

import pandas as pd
from typing import Any, Dict, List, Optional

try:
    from pycelonis import get_celonis
    from pycelonis.pql import PQL, PQLColumn, PQLFilter, OrderByColumn
    _pycelonis_available = True
except ImportError:
    _pycelonis_available = False


def _check_pycelonis():
    """Raise a clear error if pycelonis is not installed."""
    if not _pycelonis_available:
        raise ImportError(
            "pycelonis is required for Celonis integration.\n"
            "Install with: pip install --extra-index-url=https://pypi.celonis.cloud/ pycelonis"
        )


def connect_celonis(base_url: str = None, api_token: str = None, key_type: str = None):
    """
    Connect to Celonis EMS. Falls back to config values if parameters are not provided.

    Args:
        base_url: Celonis base URL (e.g. "https://team.eu-1.celonis.cloud/")
        api_token: API token for authentication
        key_type: Key type - "APP_KEY" or "USER_KEY"

    Returns:
        Celonis connection object
    """
    _check_pycelonis()

    from .config import config

    url = base_url or config.celonis_base_url
    token = api_token or config.celonis_api_token
    ktype = key_type or config.celonis_key_type

    if not url or not token:
        raise ValueError(
            "Celonis base_url and api_token are required. "
            "Set CELONIS_BASE_URL and CELONIS_API_TOKEN in .env or pass them directly."
        )

    celonis = get_celonis(base_url=url, api_token=token, key_type=ktype)
    print(f"Connected to Celonis: {url}")
    return celonis


def list_data_pools(celonis) -> list:
    """List all available data pools."""
    _check_pycelonis()
    pools = celonis.data_integration.get_data_pools()
    print(f"Found {len(pools)} data pool(s):")
    for p in pools:
        print(f"  - {p.name} (id={p.id})")
    return pools


def get_data_pool(celonis, pool_name: str = None, pool_id: str = None):
    """
    Find a data pool by name or ID. Falls back to config values.

    Args:
        celonis: Celonis connection object
        pool_name: Data pool name to search for
        pool_id: Data pool ID (takes precedence over name)

    Returns:
        DataPool object
    """
    _check_pycelonis()

    from .config import config

    pid = pool_id or config.celonis_data_pool_id
    pname = pool_name or config.celonis_data_pool_name

    pools = celonis.data_integration.get_data_pools()

    if pid:
        pool = pools.find(pid)
    elif pname:
        pool = pools.find(pname)
    else:
        raise ValueError(
            "Provide pool_name or pool_id, or set CELONIS_DATA_POOL_NAME / CELONIS_DATA_POOL_ID in .env"
        )

    print(f"Data pool: {pool.name} (id={pool.id})")
    return pool


def list_data_models(data_pool) -> list:
    """List all data models in a data pool."""
    _check_pycelonis()
    models = data_pool.get_data_models()
    print(f"Found {len(models)} data model(s) in '{data_pool.name}':")
    for m in models:
        print(f"  - {m.name} (id={m.id})")
    return models


def get_data_model(data_pool, model_name: str = None, model_id: str = None):
    """
    Find a data model by name or ID. Falls back to config values.

    Args:
        data_pool: DataPool object
        model_name: Data model name to search for
        model_id: Data model ID (takes precedence over name)

    Returns:
        DataModel object
    """
    _check_pycelonis()

    from .config import config

    mid = model_id or config.celonis_data_model_id
    mname = model_name or config.celonis_data_model_name

    models = data_pool.get_data_models()

    if mid:
        model = models.find(mid)
    elif mname:
        model = models.find(mname)
    else:
        raise ValueError(
            "Provide model_name or model_id, or set CELONIS_DATA_MODEL_NAME / CELONIS_DATA_MODEL_ID in .env"
        )

    print(f"Data model: {model.name} (id={model.id})")
    return model


def build_pql_query(
    columns: List[Dict[str, str]],
    filters: Optional[List[str]] = None,
    order_by: Optional[List[Dict[str, str]]] = None,
    distinct: bool = False,
    limit: Optional[int] = None,
) -> "PQL":
    """
    Build a PQL query from a declarative column specification.

    Args:
        columns: List of dicts with "name" and "query" keys.
                 Example: [{"name": "Id", "query": '"Table"."Column"'}]
        filters: Optional list of PQL filter expressions as strings.
                 Example: ['FILTER "Table"."Status" = \'Active\'']
        order_by: Optional list of dicts with "query" and optional "direction" keys.
                  Example: [{"query": '"Table"."Date"', "direction": "DESC"}]
        distinct: Whether to apply DISTINCT
        limit: Maximum number of rows to return

    Returns:
        PQL query object ready for execution
    """
    _check_pycelonis()

    query = PQL(distinct=distinct, limit=limit)

    for col in columns:
        query += PQLColumn(name=col["name"], query=col["query"])

    if filters:
        for f in filters:
            query += PQLFilter(query=f)

    if order_by:
        for ob in order_by:
            direction = ob.get("direction", "ASC").upper()
            query += OrderByColumn(
                query=ob["query"],
                direction=direction,
            )

    return query


def extract_dataframe(data_model, query) -> pd.DataFrame:
    """
    Execute a PQL query against a data model and return a DataFrame.

    Args:
        data_model: DataModel object
        query: PQL query object (from build_pql_query)

    Returns:
        pandas DataFrame with query results
    """
    _check_pycelonis()

    print("Extracting data from Celonis...")
    df = data_model.export_data_frame(query)
    print(f"Extracted {len(df)} rows, {len(df.columns)} columns")
    return df


def load_celonis_data(
    columns: List[Dict[str, str]],
    base_url: str = None,
    api_token: str = None,
    key_type: str = None,
    pool_name: str = None,
    pool_id: str = None,
    model_name: str = None,
    model_id: str = None,
    filters: Optional[List[str]] = None,
    order_by: Optional[List[Dict[str, str]]] = None,
    distinct: bool = False,
    limit: Optional[int] = None,
) -> pd.DataFrame:
    """
    Convenience function: connect to Celonis, build query, and extract data in one call.

    All connection parameters fall back to .env config if not provided.

    Args:
        columns: List of dicts with "name" and "query" keys.
                 Column "name" values should match your FIELD_MAPPING keys.
        base_url: Celonis base URL
        api_token: API token
        key_type: Key type (APP_KEY or USER_KEY)
        pool_name: Data pool name
        pool_id: Data pool ID
        model_name: Data model name
        model_id: Data model ID
        filters: Optional PQL filter expressions
        order_by: Optional ordering specification
        distinct: Whether to apply DISTINCT
        limit: Maximum rows to return

    Returns:
        pandas DataFrame with extracted data
    """
    celonis = connect_celonis(base_url, api_token, key_type)
    pool = get_data_pool(celonis, pool_name, pool_id)
    model = get_data_model(pool, model_name, model_id)
    query = build_pql_query(columns, filters, order_by, distinct, limit)
    return extract_dataframe(model, query)
