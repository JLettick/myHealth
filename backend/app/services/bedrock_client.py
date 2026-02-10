"""
AWS Bedrock client using the Converse API.

Provides a wrapper around boto3 Bedrock Runtime client for
invoking Claude models with conversation history and tool use.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.config import get_settings, Settings

logger = logging.getLogger(__name__)


class BedrockAPIError(Exception):
    """Raised when Bedrock API call fails."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BedrockClient:
    """Client for AWS Bedrock Runtime Converse API."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._client = None

    @property
    def client(self):
        """Lazy-initialized Bedrock Runtime client."""
        if self._client is None:
            if not self.settings.aws_access_key_id or not self.settings.aws_secret_access_key:
                raise BedrockAPIError(
                    "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.",
                    status_code=503,
                )
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.settings.aws_region,
                aws_access_key_id=self.settings.aws_access_key_id,
                aws_secret_access_key=self.settings.aws_secret_access_key,
            )
        return self._client

    def _consolidate_messages(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Consolidate consecutive same-role messages into Converse API format.

        Claude requires alternating user/assistant roles. This merges
        consecutive messages with the same role and formats content
        as content blocks: [{"text": "..."}].
        """
        if not messages:
            return []

        consolidated = []
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", [])

            # Convert plain string content to content block format
            if isinstance(content, str):
                content = [{"text": content}]

            if consolidated and consolidated[-1]["role"] == role:
                # Merge content blocks with previous message of same role
                consolidated[-1]["content"].extend(content)
            else:
                consolidated.append({"role": role, "content": list(content)})

        return consolidated

    async def converse(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Call Bedrock Converse API with conversation messages and optional tools.

        Args:
            messages: List of message dicts with 'role' and 'content'
                      (content can be string or content blocks)
            system_prompt: System prompt for the model
            tools: Optional list of tool definitions in Converse API format
            max_tokens: Maximum tokens in response

        Returns:
            Dict with 'output' (message dict) and 'stopReason'

        Raises:
            BedrockAPIError: If the API call fails
        """
        try:
            consolidated_messages = self._consolidate_messages(messages)

            kwargs: Dict[str, Any] = {
                "modelId": self.settings.bedrock_model_id,
                "messages": consolidated_messages,
                "system": [{"text": system_prompt}],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": 0.7,
                },
            }

            if tools:
                kwargs["toolConfig"] = {"tools": tools}

            try:
                response = await asyncio.to_thread(self.client.converse, **kwargs)
            except ClientError as e:
                if e.response["Error"]["Code"] == "ThrottlingException":
                    logger.warning("Bedrock throttled, retrying in 1s...")
                    await asyncio.sleep(1)
                    response = await asyncio.to_thread(self.client.converse, **kwargs)
                else:
                    raise

            return {
                "output": response["output"]["message"],
                "stopReason": response["stopReason"],
            }

        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise BedrockAPIError(
                "AWS credentials not configured",
                status_code=503,
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"Bedrock API error: {error_code} - {error_message}")

            if error_code == "ThrottlingException":
                raise BedrockAPIError("Rate limited, please try again later", 429)
            elif error_code == "ValidationException":
                raise BedrockAPIError(f"Invalid request: {error_message}", 400)
            elif error_code == "AccessDeniedException":
                raise BedrockAPIError("Access denied to Bedrock model", 403)
            elif error_code == "ResourceNotFoundException":
                raise BedrockAPIError(
                    f"Model not found: {self.settings.bedrock_model_id}", 404
                )
            else:
                raise BedrockAPIError(f"Bedrock error: {error_message}", 500)

        except BedrockAPIError:
            raise

        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock: {e}")
            raise BedrockAPIError(str(e), 500)


_bedrock_client: Optional[BedrockClient] = None


def get_bedrock_client() -> BedrockClient:
    """Get singleton Bedrock client instance."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
