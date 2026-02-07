"""Tests for Bedrock Converse API client."""

import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError

from app.services.bedrock_client import BedrockClient, BedrockAPIError


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.aws_access_key_id = "test-key"
    settings.aws_secret_access_key = "test-secret"
    settings.aws_region = "us-east-1"
    settings.bedrock_model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    return settings


@pytest.fixture
def client(mock_settings):
    return BedrockClient(settings=mock_settings)


class TestConsolidateMessages:
    def test_empty_messages(self, client):
        assert client._consolidate_messages([]) == []

    def test_string_content_converted_to_blocks(self, client):
        messages = [{"role": "user", "content": "hello"}]
        result = client._consolidate_messages(messages)
        assert result == [{"role": "user", "content": [{"text": "hello"}]}]

    def test_content_blocks_preserved(self, client):
        messages = [{"role": "user", "content": [{"text": "hello"}]}]
        result = client._consolidate_messages(messages)
        assert result == [{"role": "user", "content": [{"text": "hello"}]}]

    def test_consecutive_same_role_merged(self, client):
        messages = [
            {"role": "user", "content": "first"},
            {"role": "user", "content": "second"},
        ]
        result = client._consolidate_messages(messages)
        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == [{"text": "first"}, {"text": "second"}]

    def test_alternating_roles_preserved(self, client):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "user", "content": "bye"},
        ]
        result = client._consolidate_messages(messages)
        assert len(result) == 3
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        assert result[2]["role"] == "user"

    def test_tool_result_content_blocks_preserved(self, client):
        """Content blocks with toolResult should be preserved as-is."""
        tool_result_block = {
            "toolResult": {
                "toolUseId": "123",
                "content": [{"json": {"key": "value"}}],
            }
        }
        messages = [{"role": "user", "content": [tool_result_block]}]
        result = client._consolidate_messages(messages)
        assert result[0]["content"] == [tool_result_block]


class TestConverse:
    @pytest.mark.asyncio
    async def test_converse_basic(self, client):
        mock_boto_client = MagicMock()
        mock_boto_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Hello!"}],
                }
            },
            "stopReason": "end_turn",
        }
        client._client = mock_boto_client

        result = await client.converse(
            messages=[{"role": "user", "content": "hi"}],
            system_prompt="You are helpful.",
        )

        assert result["stopReason"] == "end_turn"
        assert result["output"]["content"][0]["text"] == "Hello!"
        mock_boto_client.converse.assert_called_once()

    @pytest.mark.asyncio
    async def test_converse_with_tools(self, client):
        mock_boto_client = MagicMock()
        mock_boto_client.converse.return_value = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool-1",
                                "name": "get_whoop_summary",
                                "input": {},
                            }
                        }
                    ],
                }
            },
            "stopReason": "tool_use",
        }
        client._client = mock_boto_client

        tools = [{"toolSpec": {"name": "get_whoop_summary", "description": "test"}}]
        result = await client.converse(
            messages=[{"role": "user", "content": "check recovery"}],
            system_prompt="You are helpful.",
            tools=tools,
        )

        assert result["stopReason"] == "tool_use"
        call_kwargs = mock_boto_client.converse.call_args[1]
        assert "toolConfig" in call_kwargs

    @pytest.mark.asyncio
    async def test_converse_no_tools_omits_tool_config(self, client):
        mock_boto_client = MagicMock()
        mock_boto_client.converse.return_value = {
            "output": {"message": {"role": "assistant", "content": [{"text": "hi"}]}},
            "stopReason": "end_turn",
        }
        client._client = mock_boto_client

        await client.converse(
            messages=[{"role": "user", "content": "hi"}],
            system_prompt="test",
        )

        call_kwargs = mock_boto_client.converse.call_args[1]
        assert "toolConfig" not in call_kwargs

    @pytest.mark.asyncio
    async def test_converse_throttling_error(self, client):
        mock_boto_client = MagicMock()
        mock_boto_client.converse.side_effect = ClientError(
            {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}},
            "Converse",
        )
        client._client = mock_boto_client

        with pytest.raises(BedrockAPIError) as exc_info:
            await client.converse(
                messages=[{"role": "user", "content": "hi"}],
                system_prompt="test",
            )
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_converse_no_credentials(self):
        settings = MagicMock()
        settings.aws_access_key_id = ""
        settings.aws_secret_access_key = ""
        client = BedrockClient(settings=settings)

        with pytest.raises(BedrockAPIError) as exc_info:
            await client.converse(
                messages=[{"role": "user", "content": "hi"}],
                system_prompt="test",
            )
        assert exc_info.value.status_code == 503
