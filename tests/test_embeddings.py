"""Tests for ethos/embeddings.py — Azure OpenAI embedding service."""

from unittest.mock import AsyncMock, patch


from ethos_academy.embeddings import get_embedding


class TestGetEmbedding:
    """Tests for the get_embedding() async function."""

    async def test_empty_text_returns_empty_list(self):
        """Empty text input returns [] without calling the API."""
        result = await get_embedding("")
        assert result == []

    async def test_whitespace_only_returns_empty_list(self):
        """Whitespace-only input returns [] without calling the API."""
        result = await get_embedding("   ")
        assert result == []

    @patch.dict(
        "os.environ",
        {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-3-small",
        },
    )
    async def test_returns_embedding_from_azure(self):
        """Valid text with configured env vars returns 1536-dimension float list."""
        fake_embedding = [0.1] * 1536
        mock_response = AsyncMock()
        mock_response.data = [AsyncMock(embedding=fake_embedding)]

        with patch("ethos_academy.embeddings.AsyncAzureOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await get_embedding("Hello world")

            assert len(result) == 1536
            assert all(isinstance(v, float) for v in result)
            mock_client.embeddings.create.assert_awaited_once()

    @patch.dict("os.environ", {}, clear=True)
    async def test_missing_env_vars_returns_empty_list(self):
        """Missing Azure env vars returns [] and logs a warning."""
        result = await get_embedding("Hello world")
        assert result == []

    @patch.dict(
        "os.environ",
        {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-3-small",
        },
    )
    async def test_api_error_returns_empty_list(self):
        """Azure API error returns [] and logs a warning."""
        with patch("ethos_academy.embeddings.AsyncAzureOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(
                side_effect=Exception("Azure API unavailable")
            )
            mock_client_cls.return_value = mock_client

            result = await get_embedding("Hello world")
            assert result == []

    @patch.dict(
        "os.environ",
        {
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_API_KEY": "test-key",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "my-deployment",
        },
    )
    async def test_uses_deployment_from_env(self):
        """get_embedding() uses the deployment name from AZURE_OPENAI_EMBEDDING_DEPLOYMENT."""
        fake_embedding = [0.5] * 1536
        mock_response = AsyncMock()
        mock_response.data = [AsyncMock(embedding=fake_embedding)]

        with patch("ethos_academy.embeddings.AsyncAzureOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            await get_embedding("test text")

            call_kwargs = mock_client.embeddings.create.call_args
            assert call_kwargs.kwargs["model"] == "my-deployment"
