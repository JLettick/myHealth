"""
AI Agent API endpoints.

Provides chat functionality with an AI health assistant
that has context about the user's health data.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.agent import (
    ChatMessageCreate,
    ChatResponse,
    ConversationSummary,
    ConversationDetail,
    ConversationListResponse,
)
from app.services.agent_service import get_agent_service, AgentService
from app.services.bedrock_client import BedrockAPIError

logger = logging.getLogger(__name__)

router = APIRouter()


def get_service() -> AgentService:
    """Dependency for agent service."""
    return get_agent_service()


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatMessageCreate,
    current_user: UserResponse = Depends(get_current_user),
    agent_service: AgentService = Depends(get_service),
):
    """
    Send a message to the AI agent and get a response.

    Creates a new conversation if conversation_id is not provided.
    The AI has context about the user's Whoop and nutrition data.
    """
    try:
        result = await agent_service.send_message(
            user_id=str(current_user.id),
            content=request.content,
            conversation_id=request.conversation_id,
        )
        return ChatResponse(
            message=result["message"],
            conversation_id=result["conversation_id"],
            tool_actions=result.get("tool_actions"),
            debug_trace=result.get("debug_trace"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BedrockAPIError as e:
        logger.error(f"Bedrock error for user {current_user.id}: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Chat error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message",
        )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    current_user: UserResponse = Depends(get_current_user),
    agent_service: AgentService = Depends(get_service),
):
    """List all conversations for the current user."""
    conversations = agent_service.get_conversations(str(current_user.id))
    return ConversationListResponse(
        conversations=[ConversationSummary(**c) for c in conversations]
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
    agent_service: AgentService = Depends(get_service),
):
    """Get a specific conversation with all messages."""
    conversation = agent_service.get_conversation(
        conversation_id, str(current_user.id)
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return ConversationDetail(**conversation)


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversation(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user),
    agent_service: AgentService = Depends(get_service),
):
    """Delete a conversation and all its messages."""
    deleted = agent_service.delete_conversation(conversation_id, str(current_user.id))
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
