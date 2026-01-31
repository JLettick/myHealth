/**
 * Agent Context for managing AI chat state.
 */

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from 'react';
import type { ChatMessage, Conversation } from '../types/agent';
import {
  sendMessage as sendMessageApi,
  getConversations,
  getConversation,
  deleteConversation as deleteConversationApi,
} from '../api/agent';
import { useAuth } from './AuthContext';
import { logger } from '../utils/logger';

interface AgentContextValue {
  // Current conversation state
  messages: ChatMessage[];
  conversationId: string | null;

  // Conversations list
  conversations: Conversation[];

  // Loading states
  isLoading: boolean;
  isSending: boolean;

  // Error state
  error: string | null;

  // Actions
  sendMessage: (content: string) => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  newConversation: () => void;
  deleteConversation: (id: string) => Promise<void>;
  refreshConversations: () => Promise<void>;
  clearError: () => void;
}

const AgentContext = createContext<AgentContextValue | null>(null);

interface AgentProviderProps {
  children: React.ReactNode;
}

export function AgentProvider({ children }: AgentProviderProps) {
  const { isAuthenticated } = useAuth();

  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Fetch conversations list
  const refreshConversations = useCallback(async () => {
    if (!isAuthenticated) {
      setConversations([]);
      return;
    }

    try {
      const convos = await getConversations();
      setConversations(convos);
    } catch (err) {
      logger.error('Failed to fetch conversations', { error: err });
    }
  }, [isAuthenticated]);

  // Load a specific conversation
  const loadConversation = useCallback(
    async (id: string) => {
      if (!isAuthenticated) return;

      setIsLoading(true);
      setError(null);

      try {
        const conversation = await getConversation(id);
        setConversationId(conversation.id);
        setMessages(conversation.messages || []);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Failed to load conversation';
        setError(message);
        logger.error('Failed to load conversation', { error: err });
      } finally {
        setIsLoading(false);
      }
    },
    [isAuthenticated]
  );

  // Start a new conversation
  const newConversation = useCallback(() => {
    setConversationId(null);
    setMessages([]);
    setError(null);
  }, []);

  // Send a message
  const sendMessage = useCallback(
    async (content: string) => {
      if (!isAuthenticated || !content.trim()) return;

      setIsSending(true);
      setError(null);

      // Optimistically add user message
      const tempUserMessage: ChatMessage = {
        id: `temp-${Date.now()}`,
        role: 'user',
        content: content.trim(),
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMessage]);

      try {
        const response = await sendMessageApi({
          content: content.trim(),
          conversation_id: conversationId || undefined,
        });

        // Update conversation ID if this is a new conversation
        if (!conversationId) {
          setConversationId(response.conversation_id);
          // Refresh conversations list to include the new one
          refreshConversations();
        }

        // Replace temp message with real one and add assistant response
        setMessages((prev) => {
          // Remove the temp user message
          const filtered = prev.filter((m) => m.id !== tempUserMessage.id);
          // Add the user message (reconstructed) and assistant response
          return [
            ...filtered,
            {
              id: `user-${Date.now()}`,
              role: 'user' as const,
              content: content.trim(),
              created_at: tempUserMessage.created_at,
            },
            response.message,
          ];
        });
      } catch (err) {
        // Remove the optimistic message on error
        setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id));

        const message =
          err instanceof Error ? err.message : 'Failed to send message';
        setError(message);
        logger.error('Failed to send message', { error: err });
      } finally {
        setIsSending(false);
      }
    },
    [isAuthenticated, conversationId, refreshConversations]
  );

  // Delete a conversation
  const deleteConversation = useCallback(
    async (id: string) => {
      if (!isAuthenticated) return;

      try {
        await deleteConversationApi(id);

        // Remove from local state
        setConversations((prev) => prev.filter((c) => c.id !== id));

        // If this was the current conversation, clear it
        if (conversationId === id) {
          newConversation();
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : 'Failed to delete conversation';
        setError(message);
        logger.error('Failed to delete conversation', { error: err });
      }
    },
    [isAuthenticated, conversationId, newConversation]
  );

  // Load conversations on mount
  useEffect(() => {
    if (isAuthenticated) {
      refreshConversations();
    } else {
      setConversations([]);
      setMessages([]);
      setConversationId(null);
    }
  }, [isAuthenticated, refreshConversations]);

  const value: AgentContextValue = {
    messages,
    conversationId,
    conversations,
    isLoading,
    isSending,
    error,
    sendMessage,
    loadConversation,
    newConversation,
    deleteConversation,
    refreshConversations,
    clearError,
  };

  return (
    <AgentContext.Provider value={value}>{children}</AgentContext.Provider>
  );
}

/**
 * Hook to access Agent context.
 */
export function useAgent(): AgentContextValue {
  const context = useContext(AgentContext);
  if (!context) {
    throw new Error('useAgent must be used within an AgentProvider');
  }
  return context;
}
