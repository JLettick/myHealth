"""
AWS Bedrock client for invoking foundation models.

Provides a wrapper around boto3 Bedrock Runtime client for
invoking Claude models with conversation history.
"""

import json
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
    """Client for AWS Bedrock Runtime API."""

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
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Consolidate consecutive same-role messages.

        Claude requires alternating user/assistant roles. This merges
        consecutive messages with the same role into one.
        """
        if not messages:
            return []

        consolidated = []
        for msg in messages:
            if consolidated and consolidated[-1]["role"] == msg["role"]:
                # Merge with previous message of same role
                consolidated[-1]["content"] += "\n\n" + msg["content"]
            else:
                consolidated.append({"role": msg["role"], "content": msg["content"]})

        return consolidated

    async def invoke_model(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        max_tokens: int = 1024,
    ) -> str:
        """
        Invoke Bedrock model with conversation messages.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System prompt for the model
            max_tokens: Maximum tokens in response

        Returns:
            Model's text response

        Raises:
            BedrockAPIError: If the API call fails
        """
        try:
            # Consolidate consecutive same-role messages
            consolidated_messages = self._consolidate_messages(messages)

            # Format for Claude models on Bedrock
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "system": system_prompt,
                "messages": consolidated_messages,
            }

            response = self.client.invoke_model(
                modelId=self.settings.bedrock_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )

            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"]

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
