"""
Embedding functions - generates vector embeddings using Azure OpenAI
"""

import requests
from typing import List, Optional
from .config import config


def get_embedding(text: str) -> Optional[List[float]]:
    """
    Fetches text embeddings from Azure OpenAI API.

    Args:
        text: The text to be embedded

    Returns:
        The embedding vector (list of floats) if successful, None if failed

    Note:
        This function uses an IP-based endpoint with a custom Host header
        to work around network restrictions. SSL verification is disabled
        due to IP usage.
    """
    headers = {
        "Content-Type": "application/json",
        "api-key": config.azure_openai_embedding_key,
    }

    # Add Host header if configured (needed when using IP address)
    if config.azure_openai_embedding_host_header:
        headers["Host"] = config.azure_openai_embedding_host_header

    data = {
        "input": text
    }

    url = (
        f"{config.azure_openai_embedding_endpoint}/openai/deployments/"
        f"{config.azure_openai_embedding_deployment}/embeddings"
        f"?api-version={config.azure_openai_embedding_api_version}"
    )

    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            verify=False  # Ignore SSL certificate issues when using IP address
        )

        response.raise_for_status()
        embedding = response.json()["data"][0]["embedding"]
        return embedding

    except requests.exceptions.RequestException as e:
        print(f"❌ Embedding request failed: {e}")
        return None
