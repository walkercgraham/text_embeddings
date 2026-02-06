"""
Azure Search Vector Embedding Pipeline - Utility Modules
"""

from .config import config
from .embeddings import get_embedding
from .azure_search import (
    create_index,
    delete_index,
    get_index_info,
    get_index_stats,
    upload_documents,
    text_search,
    vector_search,
    hybrid_search
)
from .data_processing import (
    load_csv,
    format_datetime_for_azure,
    init_embedding_tracking,
    prepare_documents_for_upload
)

# Celonis integration (optional - only available when pycelonis is installed)
try:
    from .celonis_connection import (
        connect_celonis,
        get_data_pool,
        get_data_model,
        list_data_pools,
        list_data_models,
        build_pql_query,
        extract_dataframe,
        load_celonis_data,
    )
    _celonis_available = True
except ImportError:
    _celonis_available = False

__all__ = [
    'config',
    'get_embedding',
    'create_index',
    'delete_index',
    'get_index_info',
    'get_index_stats',
    'upload_documents',
    'text_search',
    'vector_search',
    'hybrid_search',
    'load_csv',
    'format_datetime_for_azure',
    'init_embedding_tracking',
    'prepare_documents_for_upload',
    'save_checkpoint',
    'load_checkpoint',
    'print_embedding_summary',
    'format_datetime_column',
    # Celonis (conditional)
    'connect_celonis',
    'get_data_pool',
    'get_data_model',
    'list_data_pools',
    'list_data_models',
    'build_pql_query',
    'extract_dataframe',
    'load_celonis_data',
]
