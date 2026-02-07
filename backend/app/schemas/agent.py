"""
Pydantic schemas for AI agent endpoints.

Defines request/response models for chat conversations.
"""

from datetime import datetime
from typing import Any, Dict, Optional, List, Literal

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    """Request to send a chat message."""

    content: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = Field(
        None, description="Existing conversation ID to continue"
    )


class ToolAction(BaseModel):
    """A tool action performed during an AI response."""

    tool: str = Field(..., description="Tool name that was executed")
    label: str = Field(..., description="Human-readable action description")


class DebugToolCall(BaseModel):
    """Debug trace entry for a single tool call (dev only)."""

    step: int = Field(..., description="Iteration number (1-indexed)")
    tool_name: str = Field(..., description="Tool that was called")
    tool_input: Dict[str, Any] = Field(..., description="Input the model provided")
    tool_output: Dict[str, Any] = Field(..., description="Result returned by tool")
    model_text: Optional[str] = Field(None, description="Text the model produced alongside the tool call")


class ChatMessage(BaseModel):
    """A chat message in a conversation."""

    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    tool_actions: Optional[List[ToolAction]] = Field(
        None, description="Tool actions performed for this response"
    )


class ChatResponse(BaseModel):
    """Response from sending a chat message."""

    message: ChatMessage
    conversation_id: str
    tool_actions: Optional[List[ToolAction]] = Field(
        None, description="Tool actions performed during this response"
    )
    debug_trace: Optional[List[DebugToolCall]] = Field(
        None, description="Debug trace of tool calls (dev only)"
    )


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
