"""
Pydantic schemas for AI agent endpoints.

Defines request/response models for chat conversations.
"""

from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """Request to send a chat message."""

    content: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = Field(
        None, description="Existing conversation ID to continue"
    )


class ChatMessage(BaseModel):
    """A chat message in a conversation."""

    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    """Response from sending a chat message."""

    message: ChatMessage
    conversation_id: str


class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""

    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    """Full conversation with messages."""

    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage]


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""

    conversations: List[ConversationSummary]
