/**
 * TypeScript types for AI Agent feature.
 */

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages?: ChatMessage[];
}

export interface SendMessageRequest {
  content: string;
  conversation_id?: string;
}

export interface ChatResponse {
  message: ChatMessage;
  conversation_id: string;
}

export interface ConversationListResponse {
  conversations: Conversation[];
}
