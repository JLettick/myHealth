"""
Agent service for managing AI conversations.

Handles conversation persistence, health context building,
and orchestration of Bedrock API calls.
"""

import logging
from datetime import datetime, date, timezone
from typing import Optional, Dict, Any, List
from uuid import uuid4

from app.config import get_settings, Settings
from app.services.supabase_client import get_supabase_service, SupabaseService
from app.services.bedrock_client import get_bedrock_client, BedrockClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful health and fitness assistant for the myHealth app.
You have access to the user's health data from their Whoop device, nutrition logs, and workout logs.
Provide personalized, actionable advice based on their data.
Be encouraging but honest. If you notice concerning patterns, suggest consulting a healthcare professional.
Keep responses concise and focused.
Do not make up data - only reference the health context provided below.

{health_context}"""


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

    async def build_health_context(self, user_id: str) -> str:
        """Build context string from user's health data."""
        context_parts = []

        # Get Whoop data
        try:
            from app.services.whoop_sync_service import get_whoop_sync_service

            whoop_service = get_whoop_sync_service()
            whoop_summary = await whoop_service.get_dashboard_summary(user_id)
            if whoop_summary.get("is_connected"):
                recovery = whoop_summary.get("latest_recovery_score")
                sleep_hrs = whoop_summary.get("latest_sleep_hours")
                hrv = whoop_summary.get("latest_hrv")
                rhr = whoop_summary.get("latest_resting_hr")
                strain = whoop_summary.get("latest_strain_score")
                workouts = whoop_summary.get("total_workouts_7d", 0)

                context_parts.append(
                    f"""Whoop Data:
- Recovery Score: {f'{recovery:.0f}%' if recovery else 'N/A'}
- Sleep: {f'{sleep_hrs:.1f} hours' if sleep_hrs else 'N/A'}
- HRV: {f'{hrv:.0f} ms' if hrv else 'N/A'}
- Resting HR: {f'{rhr:.0f} bpm' if rhr else 'N/A'}
- Strain Score: {f'{strain:.1f}' if strain else 'N/A'}
- Workouts (7 days): {workouts}"""
                )
        except Exception as e:
            logger.warning(f"Failed to get Whoop data: {e}")

        # Get Nutrition data
        try:
            from app.services.nutrition_service import get_nutrition_service

            nutrition_service = get_nutrition_service()
            nutrition_summary = await nutrition_service.get_daily_summary(
                user_id, date.today()
            )
            if nutrition_summary:
                cals = nutrition_summary.get("total_calories", 0)
                protein = nutrition_summary.get("total_protein_g", 0)
                carbs = nutrition_summary.get("total_carbs_g", 0)
                fat = nutrition_summary.get("total_fat_g", 0)

                context_parts.append(
                    f"""Today's Nutrition:
- Calories: {cals:.0f} kcal
- Protein: {protein:.0f}g
- Carbs: {carbs:.0f}g
- Fat: {fat:.0f}g"""
                )
        except Exception as e:
            logger.warning(f"Failed to get nutrition data: {e}")

        # Get Workout data
        try:
            from app.services.workout_service import get_workout_service

            workout_service = get_workout_service()
            workout_summary = await workout_service.get_daily_summary(
                user_id, date.today()
            )
            if workout_summary and workout_summary.get("total_sessions", 0) > 0:
                sessions = workout_summary.get("total_sessions", 0)
                sets = workout_summary.get("total_sets", 0)
                duration = workout_summary.get("total_duration_minutes", 0)
                volume = workout_summary.get("total_volume_kg")
                distance = workout_summary.get("total_distance_meters")
                exercises = workout_summary.get("exercises", [])

                exercise_list = ", ".join([ex.get("exercise_name", "") for ex in exercises[:5]])

                workout_text = f"""Today's Workouts:
- Sessions: {sessions}
- Total Sets: {sets}
- Duration: {duration} minutes"""

                if volume:
                    workout_text += f"\n- Total Volume: {volume:.0f} kg"
                if distance:
                    workout_text += f"\n- Total Distance: {distance:.0f} m"
                if exercise_list:
                    workout_text += f"\n- Exercises: {exercise_list}"

                context_parts.append(workout_text)
        except Exception as e:
            logger.warning(f"Failed to get workout data: {e}")

        if not context_parts:
            return "No health data available yet. The user should connect their Whoop device, log meals, or track workouts to get personalized insights."

        return "\n\n".join(context_parts)

    async def send_message(
        self,
        user_id: str,
        content: str,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a message and get AI response.

        Args:
            user_id: User's ID
            content: User's message content
            conversation_id: Optional existing conversation ID

        Returns:
            Dict with 'message' (AI response) and 'conversation_id'
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

        # Get conversation history
        history = self._get_messages(conversation_id)

        # Build messages for Bedrock
        messages = [
            {"role": msg["role"], "content": msg["content"]} for msg in history
        ]

        # Build system prompt with health context
        health_context = await self.build_health_context(user_id)
        system_prompt = SYSTEM_PROMPT.format(health_context=health_context)

        # Get AI response
        response_text = await self.bedrock.invoke_model(
            messages=messages,
            system_prompt=system_prompt,
        )

        # Save assistant message
        assistant_message = self._save_message(
            conversation_id, "assistant", response_text
        )

        # Update conversation title if first exchange
        if len(history) == 1:
            title = content[:50] + "..." if len(content) > 50 else content
            self._update_conversation_title(conversation_id, title)

        return {
            "message": assistant_message,
            "conversation_id": conversation_id,
        }

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
