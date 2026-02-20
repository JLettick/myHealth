"""
Agent service for managing AI conversations with tool use.

Handles conversation persistence, agentic tool-use loop,
and orchestration of Bedrock Converse API calls.
"""

import logging
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, List
from uuid import uuid4

from app.config import get_settings, Settings
from app.services.supabase_client import get_supabase_service, SupabaseService
from app.services.bedrock_client import get_bedrock_client, BedrockClient
from app.services.agent_tools import (
    TOOL_DEFINITIONS,
    execute_tool,
    get_tool_action_label,
)

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 25
MAX_CONVERSATION_HISTORY = 50

SYSTEM_PROMPT = """You are a helpful health and fitness assistant for the myHealth app.
You can read and write the user's health data using the tools provided.

Today's date is {today}.

## Available Tools

### Reading Data (Single Day)
- **get_nutrition_summary** — Get meals, macros, and goals for a date
- **search_foods** — Search the user's food database by name
- **search_usda_foods** — Search USDA FoodData Central for foods not in the user's DB
- **get_workout_summary** — Get workout sessions, sets, and volume for a date
- **search_exercises** — Search exercises by name or category
- **get_whoop_summary** — Get Whoop recovery, sleep, HRV, and strain metrics

### Analysis Tools (Multi-Day Trends)
- **get_nutrition_trends** — Analyze nutrition over a date range (up to 30 days): daily data, averages, goal adherence
- **get_workout_progression** — Analyze a specific exercise's progression (up to 90 days): weight/volume changes or pace/distance improvements
- **get_workout_trends** — Analyze weekly workout consistency (up to 12 weeks): sessions, volume, duration vs goals
- **get_recovery_trends** — Analyze Whoop recovery and sleep trends (up to 30 days): scores, HRV, sleep quality, trend direction

### Writing Data
- **log_food_entry** — Log a meal (requires food_id from search_foods or create_food)
- **create_food** — Create a custom food with macros
- **log_workout** — Log a workout session with sets
- **create_exercise** — Create a custom exercise

## Meal Logging Workflow
1. Search for the food using search_foods — results have an `id` field (this is the food_id)
2. If found, use log_food_entry with that food_id
3. If NOT found, search search_usda_foods for nutrition data
4. Use create_food with the name and macros from the USDA result — this returns a new food with an `id`
5. Use log_food_entry with the new food's id as food_id
IMPORTANT: USDA results do NOT have a food_id. You must ALWAYS create_food first before logging. Never pass a USDA numeric ID to log_food_entry.

## Workout Logging Workflow
1. Search for the exercise using search_exercises
2. If not found, use create_exercise
3. Use log_workout with exercise_id, set_type, and relevant data (reps/weight or duration/distance)

## Analysis & Recommendations Workflow
When the user asks about trends, progress, or wants recommendations:
- **Nutrition questions** ("How's my diet?", "Am I hitting my macros?") → use `get_nutrition_trends`
- **Exercise progress** ("How's my bench press going?", "Am I getting faster?") → use `get_workout_progression`
- **Training consistency** ("Am I training enough?", "How's my workout volume?") → use `get_workout_trends`
- **Recovery/sleep** ("How's my recovery?", "Am I sleeping well?") → use `get_recovery_trends`
- **Comprehensive review** ("Give me a health update", "How am I doing overall?") → call multiple analysis tools

## Unit Conversions
- Pounds to kg: divide by 2.205
- Miles to meters: multiply by 1609.34
- Kilometers to meters: multiply by 1000

## Recommendation Guidelines
- Base recommendations on actual data, not assumptions — always fetch data first
- Be specific and actionable (e.g. "Try adding 100g of chicken breast to lunch" not "eat more protein")
- Note when data is insufficient for reliable analysis (e.g. fewer than 3-4 data points)
- Highlight positives before suggesting improvements
- Key patterns to look for:
  - Macro deficits: consistently under protein/calorie targets
  - Progressive overload: are weights/volume increasing over time, or plateauing?
  - HRV decline with high training volume may indicate overtraining
  - Sleep quality correlation with recovery scores
  - Protein intake correlation with recovery
- Always suggest consulting a healthcare professional for medical concerns

## Guidelines
- Be concise and encouraging
- Use tools to fetch data on demand rather than guessing
- When logging meals, infer the meal_type from context (time of day, user's words)
- When the user mentions food quantities, estimate servings based on standard serving sizes
- If you notice concerning health patterns, suggest consulting a healthcare professional
- Confirm what you logged so the user can verify accuracy"""


class AgentService:
    """Service for managing AI agent conversations."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        supabase: Optional[SupabaseService] = None,
        bedrock: Optional[BedrockClient] = None,
    ):
        self.settings = settings or get_settings()
        self.supabase = supabase or get_supabase_service()
        self.bedrock = bedrock or get_bedrock_client()

    async def send_message(
        self,
        user_id: str,
        content: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a message and get AI response via agentic tool-use loop.

        Args:
            user_id: User's ID
            content: User's message content
            conversation_id: Optional existing conversation ID

        Returns:
            Dict with 'message' (AI response), 'conversation_id', and 'tool_actions'
        """
        # Create or get conversation
        if conversation_id:
            conversation = self._get_conversation(conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found")
        else:
            conversation_id = self._create_conversation(user_id)

        # Save user message
        self._save_message(conversation_id, "user", content)

        # Load conversation history from DB and format for Converse API
        history = self._get_messages(conversation_id)
        messages = [
            {"role": msg["role"], "content": [{"text": msg["content"]}]}
            for msg in history
        ]

        # Sliding window: keep only the most recent messages to avoid
        # quadratic token cost growth and context window overflow
        if len(messages) > MAX_CONVERSATION_HISTORY:
            messages = messages[-MAX_CONVERSATION_HISTORY:]
            # Bedrock Converse API requires the first message to be role "user"
            if messages and messages[0]["role"] == "assistant":
                messages = messages[1:]

        # Build system prompt
        system_prompt = SYSTEM_PROMPT.format(today=date.today().isoformat())

        # Agentic loop
        tool_actions: List[Dict[str, str]] = []
        debug_trace: List[Dict[str, Any]] = []

        for iteration in range(MAX_TOOL_ITERATIONS):
            response = await self.bedrock.converse(
                messages=messages,
                system_prompt=system_prompt,
                tools=TOOL_DEFINITIONS,
            )

            assistant_message = response["output"]
            stop_reason = response["stopReason"]

            if stop_reason == "end_turn":
                # Extract text from the final response
                response_text = self._extract_text(assistant_message)
                break

            elif stop_reason == "tool_use":
                # Append the assistant's message (with toolUse blocks) to the conversation
                messages.append(assistant_message)

                # Extract any text the model produced alongside tool calls
                model_text = self._extract_text(assistant_message)
                if "sorry" in model_text.lower() and len(model_text) < 60:
                    model_text = None  # Was the fallback text, not real model output

                # Process each tool use block
                tool_result_blocks = []
                for content_block in assistant_message.get("content", []):
                    if "toolUse" in content_block:
                        tool_use = content_block["toolUse"]
                        tool_name = tool_use["name"]
                        tool_input = tool_use.get("input", {})
                        tool_use_id = tool_use["toolUseId"]

                        # Execute the tool
                        result = await execute_tool(tool_name, tool_input, user_id)

                        # Track action for UI display
                        tool_actions.append({
                            "tool": tool_name,
                            "label": get_tool_action_label(tool_name),
                        })

                        # Track debug trace
                        debug_trace.append({
                            "step": iteration + 1,
                            "tool_name": tool_name,
                            "tool_input": tool_input,
                            "tool_output": result,
                            "model_text": model_text,
                        })

                        # Build toolResult block
                        tool_result_blocks.append({
                            "toolResult": {
                                "toolUseId": tool_use_id,
                                "content": [{"json": result}],
                            }
                        })

                # Append user message with tool results
                messages.append({
                    "role": "user",
                    "content": tool_result_blocks,
                })

            else:
                # Unexpected stop reason — extract whatever text exists
                response_text = self._extract_text(assistant_message)
                logger.warning(f"Unexpected stop reason: {stop_reason}")
                break
        else:
            # Max iterations reached — make one final call without tools
            # so the model can produce a proper summary response
            logger.warning(
                f"Agent loop hit max iterations ({MAX_TOOL_ITERATIONS})"
            )
            messages.append(assistant_message)
            messages.append({
                "role": "user",
                "content": [{"text": "You've reached the maximum number of tool calls. Please provide a complete summary of what you accomplished and what remains."}],
            })
            try:
                final_response = await self.bedrock.converse(
                    messages=messages,
                    system_prompt=system_prompt,
                )
                response_text = self._extract_text(final_response["output"])
            except Exception as e:
                logger.error(f"Failed to get final summary: {e}")
                response_text = self._extract_text(assistant_message)

        # Save assistant message to DB
        saved_message = self._save_message(
            conversation_id, "assistant", response_text
        )

        # Update conversation title if first exchange
        if len(history) == 1:
            title = content[:50] + "..." if len(content) > 50 else content
            self._update_conversation_title(conversation_id, title)

        result = {
            "message": saved_message,
            "conversation_id": conversation_id,
            "tool_actions": tool_actions,
        }

        # Only include debug trace in development
        if self.settings.is_development and debug_trace:
            result["debug_trace"] = debug_trace

        return result

    def _extract_text(self, message: Dict[str, Any]) -> str:
        """Extract text content from a Converse API message."""
        texts = []
        for block in message.get("content", []):
            if "text" in block:
                texts.append(block["text"])
        return "\n".join(texts) if texts else "I'm sorry, I wasn't able to generate a response."

    def get_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user."""
        try:
            result = (
                self.supabase.admin_client.table("agent_conversations")
                .select("id, title, created_at, updated_at")
                .eq("user_id", user_id)
                .order("updated_at", desc=True)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.warning(f"Failed to get conversations: {e}")
            return []

    def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a conversation with its messages."""
        conversation = self._get_conversation(conversation_id, user_id)
        if not conversation:
            return None

        messages = self._get_messages(conversation_id)
        conversation["messages"] = messages
        return conversation

    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation."""
        try:
            result = (
                self.supabase.admin_client.table("agent_conversations")
                .delete()
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .execute()
            )
            return len(result.data) > 0
        except Exception as e:
            logger.warning(f"Failed to delete conversation: {e}")
            return False

    def _create_conversation(self, user_id: str) -> str:
        """Create a new conversation."""
        conversation_id = str(uuid4())
        self.supabase.admin_client.table("agent_conversations").insert(
            {
                "id": conversation_id,
                "user_id": user_id,
            }
        ).execute()
        return conversation_id

    def _get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID."""
        try:
            result = (
                self.supabase.admin_client.table("agent_conversations")
                .select("*")
                .eq("id", conversation_id)
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.warning(f"Failed to get conversation: {e}")
            return None

    def _update_conversation_title(self, conversation_id: str, title: str) -> None:
        """Update conversation title."""
        self.supabase.admin_client.table("agent_conversations").update(
            {
                "title": title,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", conversation_id).execute()

    def _save_message(
        self, conversation_id: str, role: str, content: str
    ) -> Dict[str, Any]:
        """Save a message to the conversation."""
        message_id = str(uuid4())
        created_at = datetime.now(timezone.utc)

        self.supabase.admin_client.table("agent_messages").insert(
            {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": created_at.isoformat(),
            }
        ).execute()

        # Update conversation updated_at
        self.supabase.admin_client.table("agent_conversations").update(
            {
                "updated_at": created_at.isoformat(),
            }
        ).eq("id", conversation_id).execute()

        return {
            "id": message_id,
            "role": role,
            "content": content,
            "created_at": created_at.isoformat(),
        }

    def _get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation."""
        try:
            result = (
                self.supabase.admin_client.table("agent_messages")
                .select("id, role, content, created_at")
                .eq("conversation_id", conversation_id)
                .order("created_at", desc=False)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.warning(f"Failed to get messages: {e}")
            return []


_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get singleton agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
