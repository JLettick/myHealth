/**
 * API functions for AI Agent feature.
 */

import apiClient from './client';
import type {
  ChatResponse,
  Conversation,
  ConversationListResponse,
  SendMessageRequest,
} from '../types/agent';

/**
 * Send a message to the AI agent and get a response.
 */
export async function sendMessage(
  request: SendMessageRequest
): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>('/agent/chat', request);
  return response.data;
}

/**
 * Get all conversations for the current user.
 */
export async function getConversations(): Promise<Conversation[]> {
  const response = await apiClient.get<ConversationListResponse>(
    '/agent/conversations'
  );
  return response.data.conversations;
}

/**
 * Get a specific conversation with all messages.
 */
export async function getConversation(id: string): Promise<Conversation> {
  const response = await apiClient.get<Conversation>(
    `/agent/conversations/${id}`
  );
  return response.data;
}

/**
 * Delete a conversation and all its messages.
 */
export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(`/agent/conversations/${id}`);
}
