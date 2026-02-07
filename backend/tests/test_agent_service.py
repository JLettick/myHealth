"""Tests for agent service agentic loop."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.agent_service import AgentService


@pytest.fixture
def mock_supabase():
    supabase = MagicMock()
    admin = MagicMock()
    supabase.admin_client = admin

    # Mock conversation table operations
    def make_chain(data=None):
        chain = MagicMock()
        chain.select.return_value = chain
        chain.insert.return_value = chain
        chain.update.return_value = chain
        chain.delete.return_value = chain
        chain.eq.return_value = chain
        chain.order.return_value = chain
        chain.limit.return_value = chain
        result = MagicMock()
        result.data = data or []
        chain.execute.return_value = result
        return chain

    admin.table.side_effect = lambda name: make_chain(
        [{"id": "conv-1", "user_id": "test-user", "title": None}]
        if name == "agent_conversations"
        else []
    )

    return supabase


@pytest.fixture
def mock_bedrock():
    return MagicMock()


@pytest.fixture
def service(mock_supabase, mock_bedrock):
    return AgentService(
        settings=MagicMock(),
        supabase=mock_supabase,
        bedrock=mock_bedrock,
    )


class TestExtractText:
    def test_single_text_block(self, service):
        message = {"content": [{"text": "Hello!"}]}
        assert service._extract_text(message) == "Hello!"

    def test_multiple_text_blocks(self, service):
        message = {"content": [{"text": "Hello"}, {"text": "World"}]}
        assert service._extract_text(message) == "Hello\nWorld"

    def test_mixed_content_blocks(self, service):
        message = {
            "content": [
                {"toolUse": {"name": "test", "input": {}, "toolUseId": "1"}},
                {"text": "Here's the result."},
            ]
        }
        assert service._extract_text(message) == "Here's the result."

    def test_no_text_blocks(self, service):
        message = {
            "content": [
                {"toolUse": {"name": "test", "input": {}, "toolUseId": "1"}}
            ]
        }
        result = service._extract_text(message)
        assert "sorry" in result.lower()

    def test_empty_content(self, service):
        message = {"content": []}
        result = service._extract_text(message)
        assert "sorry" in result.lower()


class TestSendMessageAgenticLoop:
    @pytest.mark.asyncio
    async def test_simple_text_response(self, service, mock_bedrock, user_id):
        """Test a simple response with no tool use."""
        mock_bedrock.converse = AsyncMock(
            return_value={
                "output": {
                    "role": "assistant",
                    "content": [{"text": "Your recovery looks great!"}],
                },
                "stopReason": "end_turn",
            }
        )

        # Mock DB operations for new conversation
        service._create_conversation = MagicMock(return_value="conv-new")
        service._save_message = MagicMock(
            return_value={
                "id": "msg-1",
                "role": "assistant",
                "content": "Your recovery looks great!",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        service._get_messages = MagicMock(
            return_value=[
                {"id": "msg-0", "role": "user", "content": "How is my recovery?", "created_at": "2026-01-01T00:00:00"}
            ]
        )

        result = await service.send_message(user_id, "How is my recovery?")

        assert result["conversation_id"] == "conv-new"
        assert result["message"]["content"] == "Your recovery looks great!"
        assert result["tool_actions"] == []
        mock_bedrock.converse.assert_called_once()

    @pytest.mark.asyncio
    async def test_single_tool_use_then_response(self, service, mock_bedrock, user_id):
        """Test: model calls one tool, then responds with text."""
        call_count = 0

        async def mock_converse(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "output": {
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
                    },
                    "stopReason": "tool_use",
                }
            else:
                return {
                    "output": {
                        "role": "assistant",
                        "content": [{"text": "Your recovery is 85%."}],
                    },
                    "stopReason": "end_turn",
                }

        mock_bedrock.converse = mock_converse

        service._create_conversation = MagicMock(return_value="conv-new")
        service._save_message = MagicMock(
            return_value={
                "id": "msg-1",
                "role": "assistant",
                "content": "Your recovery is 85%.",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        service._get_messages = MagicMock(
            return_value=[
                {"id": "msg-0", "role": "user", "content": "How is my recovery?", "created_at": "2026-01-01T00:00:00"}
            ]
        )

        with patch(
            "app.services.agent_service.execute_tool",
            new_callable=AsyncMock,
            return_value={"is_connected": True, "latest_recovery_score": 85.0},
        ):
            result = await service.send_message(user_id, "How is my recovery?")

        assert len(result["tool_actions"]) == 1
        assert result["tool_actions"][0]["tool"] == "get_whoop_summary"
        assert result["message"]["content"] == "Your recovery is 85%."

    @pytest.mark.asyncio
    async def test_multi_tool_use(self, service, mock_bedrock, user_id):
        """Test: model calls search_foods, then log_food_entry, then responds."""
        call_count = 0

        async def mock_converse(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "output": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-1",
                                    "name": "search_foods",
                                    "input": {"query": "chicken"},
                                }
                            }
                        ],
                    },
                    "stopReason": "tool_use",
                }
            elif call_count == 2:
                return {
                    "output": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-2",
                                    "name": "log_food_entry",
                                    "input": {
                                        "food_id": "food-1",
                                        "meal_type": "lunch",
                                    },
                                }
                            }
                        ],
                    },
                    "stopReason": "tool_use",
                }
            else:
                return {
                    "output": {
                        "role": "assistant",
                        "content": [{"text": "Logged chicken for lunch!"}],
                    },
                    "stopReason": "end_turn",
                }

        mock_bedrock.converse = mock_converse

        service._create_conversation = MagicMock(return_value="conv-new")
        service._save_message = MagicMock(
            return_value={
                "id": "msg-1",
                "role": "assistant",
                "content": "Logged chicken for lunch!",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        service._get_messages = MagicMock(
            return_value=[
                {"id": "msg-0", "role": "user", "content": "I had chicken for lunch", "created_at": "2026-01-01T00:00:00"}
            ]
        )

        with patch(
            "app.services.agent_service.execute_tool",
            new_callable=AsyncMock,
            side_effect=[
                {"foods": [{"id": "food-1", "name": "Chicken"}], "total": 1},
                {"id": "entry-1", "total_calories": 200},
            ],
        ):
            result = await service.send_message(user_id, "I had chicken for lunch")

        assert len(result["tool_actions"]) == 2
        assert result["tool_actions"][0]["tool"] == "search_foods"
        assert result["tool_actions"][1]["tool"] == "log_food_entry"

    @pytest.mark.asyncio
    async def test_existing_conversation(self, service, mock_bedrock, user_id):
        """Test continuing an existing conversation."""
        mock_bedrock.converse = AsyncMock(
            return_value={
                "output": {
                    "role": "assistant",
                    "content": [{"text": "Sure, here's more info."}],
                },
                "stopReason": "end_turn",
            }
        )

        service._get_conversation = MagicMock(
            return_value={"id": "conv-existing", "user_id": user_id}
        )
        service._save_message = MagicMock(
            return_value={
                "id": "msg-2",
                "role": "assistant",
                "content": "Sure, here's more info.",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        service._get_messages = MagicMock(
            return_value=[
                {"id": "msg-0", "role": "user", "content": "Hello", "created_at": "2026-01-01T00:00:00"},
                {"id": "msg-1", "role": "assistant", "content": "Hi!", "created_at": "2026-01-01T00:00:01"},
                {"id": "msg-2", "role": "user", "content": "Tell me more", "created_at": "2026-01-01T00:00:02"},
            ]
        )

        result = await service.send_message(
            user_id, "Tell me more", conversation_id="conv-existing"
        )

        assert result["conversation_id"] == "conv-existing"
        service._get_conversation.assert_called_once_with("conv-existing", user_id)

    @pytest.mark.asyncio
    async def test_conversation_not_found(self, service, user_id):
        """Test error when conversation doesn't exist."""
        service._get_conversation = MagicMock(return_value=None)

        with pytest.raises(ValueError, match="Conversation not found"):
            await service.send_message(
                user_id, "hello", conversation_id="bad-id"
            )

    @pytest.mark.asyncio
    async def test_max_iterations_safety(self, service, mock_bedrock, user_id):
        """Test that the loop stops after MAX_TOOL_ITERATIONS."""
        # Always return tool_use to trigger infinite loop
        mock_bedrock.converse = AsyncMock(
            return_value={
                "output": {
                    "role": "assistant",
                    "content": [
                        {"text": "Let me check..."},
                        {
                            "toolUse": {
                                "toolUseId": "tool-n",
                                "name": "get_whoop_summary",
                                "input": {},
                            }
                        },
                    ],
                },
                "stopReason": "tool_use",
            }
        )

        service._create_conversation = MagicMock(return_value="conv-new")
        service._save_message = MagicMock(
            return_value={
                "id": "msg-1",
                "role": "assistant",
                "content": "Let me check...",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        service._get_messages = MagicMock(
            return_value=[
                {"id": "msg-0", "role": "user", "content": "test", "created_at": "2026-01-01T00:00:00"}
            ]
        )

        with patch(
            "app.services.agent_service.execute_tool",
            new_callable=AsyncMock,
            return_value={"data": "test"},
        ) as mock_exec:
            result = await service.send_message(user_id, "test")

        # Should have been called exactly MAX_TOOL_ITERATIONS times
        assert mock_exec.call_count == 15
        # Should still return a response
        assert result["message"]["content"] is not None
