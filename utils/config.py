"""
Configuration management - loads and validates environment variables from .env file
"""

import os
from pathlib import Path
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    _dotenv_available = True
except ImportError:
    _dotenv_available = False


class Config:
    """
    Configuration class that loads settings from .env file
    and provides easy access to all Azure credentials and settings
    """

    def __init__(self):
        self._load_env()
        self._validate()

    def _load_env(self):
        """Load environment variables from .env file"""
        if _dotenv_available:
            # Look for .env in project root
            env_path = Path(__file__).parent.parent / '.env'
            if env_path.exists():
                load_dotenv(env_path)
            else:
                print(f"⚠️  Warning: .env file not found at {env_path}")
                print("    Please copy .env.example to .env and fill in your credentials")
        else:
            print("⚠️  Warning: python-dotenv not installed. Using system environment variables only.")
            print("    Install with: pip install python-dotenv")

    def _validate(self):
        """Validate that required environment variables are set"""
        required = [
            'AZURE_SEARCH_SERVICE',
            'AZURE_SEARCH_ADMIN_KEY',
            'AZURE_SEARCH_INDEX_NAME',
            'AZURE_OPENAI_EMBEDDING_ENDPOINT',
            'AZURE_OPENAI_EMBEDDING_KEY',
            'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
        ]

        missing = [key for key in required if not os.getenv(key)]

        if missing:
            raise ValueError(
                f"❌ Missing required environment variables: {', '.join(missing)}\n"
                f"   Please set them in your .env file"
            )

    @property
    def azure_search_service(self) -> str:
        """Azure AI Search service name"""
        return os.getenv('AZURE_SEARCH_SERVICE', '')

    @property
    def azure_search_admin_key(self) -> str:
        """Azure AI Search admin API key"""
        return os.getenv('AZURE_SEARCH_ADMIN_KEY', '')

    @property
    def azure_search_index_name(self) -> str:
        """Azure AI Search index name"""
        return os.getenv('AZURE_SEARCH_INDEX_NAME', '')

    @property
    def azure_search_api_version(self) -> str:
        """Azure AI Search API version"""
        return os.getenv('AZURE_SEARCH_API_VERSION', '2023-10-01-preview')

    @property
    def azure_openai_embedding_endpoint(self) -> str:
        """Azure OpenAI embedding endpoint (can be IP address)"""
        return os.getenv('AZURE_OPENAI_EMBEDDING_ENDPOINT', '')

    @property
    def azure_openai_embedding_host_header(self) -> str:
        """Host header for Azure OpenAI (needed when using IP address)"""
        return os.getenv('AZURE_OPENAI_EMBEDDING_HOST_HEADER', '')

    @property
    def azure_openai_embedding_key(self) -> str:
        """Azure OpenAI API key for embeddings"""
        return os.getenv('AZURE_OPENAI_EMBEDDING_KEY', '')

    @property
    def azure_openai_embedding_deployment(self) -> str:
        """Azure OpenAI embedding deployment name"""
        return os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', '')

    @property
    def azure_openai_embedding_api_version(self) -> str:
        """Azure OpenAI API version"""
        return os.getenv('AZURE_OPENAI_EMBEDDING_API_VERSION', '2023-05-15')

    @property
    def csv_file_path(self) -> str:
        """Path to CSV data file"""
        return os.getenv('CSV_FILE_PATH', 'data/contract_items_reduced.csv')

    @property
    def checkpoint_file_path(self) -> str:
        """Path to checkpoint file for resume functionality"""
        return os.getenv('CHECKPOINT_FILE_PATH', 'data/checkpoint.parquet')

    @property
    def batch_size(self) -> int:
        """Number of rows to process in each batch"""
        return int(os.getenv('BATCH_SIZE', '5000'))

    @property
    def sleep_between_batches(self) -> float:
        """Seconds to sleep between batches"""
        return float(os.getenv('SLEEP_BETWEEN_BATCHES', '5.0'))

    @property
    def sleep_between_requests(self) -> float:
        """Seconds to sleep between individual API requests"""
        return float(os.getenv('SLEEP_BETWEEN_REQUESTS', '0.25'))

    # ---- Celonis Configuration (optional) ----

    @property
    def data_source(self) -> str:
        """Data source type: 'csv' or 'celonis'"""
        return os.getenv('DATA_SOURCE', 'csv').lower()

    @property
    def celonis_base_url(self) -> str:
        """Celonis EMS base URL"""
        return os.getenv('CELONIS_BASE_URL', '')

    @property
    def celonis_api_token(self) -> str:
        """Celonis API token"""
        return os.getenv('CELONIS_API_TOKEN', '')

    @property
    def celonis_key_type(self) -> str:
        """Celonis key type (APP_KEY or USER_KEY)"""
        return os.getenv('CELONIS_KEY_TYPE', 'APP_KEY')

    @property
    def celonis_data_pool_name(self) -> str:
        """Celonis data pool name"""
        return os.getenv('CELONIS_DATA_POOL_NAME', '')

    @property
    def celonis_data_pool_id(self) -> str:
        """Celonis data pool ID"""
        return os.getenv('CELONIS_DATA_POOL_ID', '')

    @property
    def celonis_data_model_name(self) -> str:
        """Celonis data model name"""
        return os.getenv('CELONIS_DATA_MODEL_NAME', '')

    @property
    def celonis_data_model_id(self) -> str:
        """Celonis data model ID"""
        return os.getenv('CELONIS_DATA_MODEL_ID', '')

    def validate_celonis(self):
        """Validate Celonis configuration (call on-demand, not in __init__)"""
        required = ['CELONIS_BASE_URL', 'CELONIS_API_TOKEN']
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(
                f"Missing required Celonis environment variables: {', '.join(missing)}\n"
                f"   Please set them in your .env file"
            )

        # Need at least pool name or ID
        if not self.celonis_data_pool_name and not self.celonis_data_pool_id:
            raise ValueError(
                "Set either CELONIS_DATA_POOL_NAME or CELONIS_DATA_POOL_ID in .env"
            )

        # Need at least model name or ID
        if not self.celonis_data_model_name and not self.celonis_data_model_id:
            raise ValueError(
                "Set either CELONIS_DATA_MODEL_NAME or CELONIS_DATA_MODEL_ID in .env"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Return all config values as a dictionary (for debugging)"""
        d = {
            'data_source': self.data_source,
            'azure_search_service': self.azure_search_service,
            'azure_search_index_name': self.azure_search_index_name,
            'azure_search_api_version': self.azure_search_api_version,
            'azure_openai_embedding_endpoint': self.azure_openai_embedding_endpoint,
            'azure_openai_embedding_deployment': self.azure_openai_embedding_deployment,
            'csv_file_path': self.csv_file_path,
            'checkpoint_file_path': self.checkpoint_file_path,
            'batch_size': self.batch_size,
            'sleep_between_batches': self.sleep_between_batches,
            'sleep_between_requests': self.sleep_between_requests
        }
        # Include Celonis config if relevant (omit token for security)
        if self.data_source == 'celonis' or self.celonis_base_url:
            d.update({
                'celonis_base_url': self.celonis_base_url,
                'celonis_key_type': self.celonis_key_type,
                'celonis_data_pool_name': self.celonis_data_pool_name,
                'celonis_data_pool_id': self.celonis_data_pool_id,
                'celonis_data_model_name': self.celonis_data_model_name,
                'celonis_data_model_id': self.celonis_data_model_id,
            })
        return d


# Create a singleton instance
config = Config()
