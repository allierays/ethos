"""Embedding service using Azure OpenAI.

Infrastructure module: provides get_embedding() for converting text to vector
embeddings. Nothing calls this yet. Fails gracefully when Azure OpenAI is
unavailable or misconfigured.
"""

from __future__ import annotations

import logging
import os

from openai import AsyncAzureOpenAI

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSION = 1536


async def get_embedding(text: str) -> list[float]:
    """Convert text to a 1536-dimension embedding vector via Azure OpenAI.

    Returns an empty list when:
    - text is empty or whitespace-only
    - Azure OpenAI env vars are missing
    - the Azure API call fails for any reason
    """
    if not text or not text.strip():
        return []

    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    if not endpoint or not api_key or not deployment:
        logger.warning(
            "Azure OpenAI not configured. Set AZURE_OPENAI_ENDPOINT, "
            "AZURE_OPENAI_API_KEY, and AZURE_OPENAI_EMBEDDING_DEPLOYMENT."
        )
        return []

    try:
        client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-01",
        )
        response = await client.embeddings.create(
            model=deployment,
            input=text,
        )
        return response.data[0].embedding
    except Exception as exc:
        logger.warning("Azure OpenAI embedding failed: %s", exc)
        return []
