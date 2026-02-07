/**
 * TypeScript types for AI Agent feature.
 */

export interface ToolAction {
  tool: string;
  label: string;
}

export interface DebugToolCall {
  step: number;
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_output: Record<string, unknown>;
  model_text?: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  tool_actions?: ToolAction[];
  debug_trace?: DebugToolCall[];
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
  tool_actions?: ToolAction[];
  debug_trace?: DebugToolCall[];
}

export interface ConversationListResponse {
  conversations: Conversation[];
}
