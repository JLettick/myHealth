/**
 * Chat message bubble component.
 */

import type { ChatMessage as ChatMessageType } from '../../types/agent';

interface ChatMessageProps {
  message: ChatMessageType;
}

/**
 * Renders a single chat message with different styles for user vs assistant.
 */
export function ChatMessage({ message }: ChatMessageProps): JSX.Element {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-md'
            : 'bg-gray-100 text-gray-900 rounded-bl-md'
        }`}
      >
        {/* Message content */}
        <div className="whitespace-pre-wrap break-words text-sm leading-relaxed">
          {message.content}
        </div>

        {/* Timestamp */}
        <div
          className={`text-xs mt-1 ${
            isUser ? 'text-blue-200' : 'text-gray-400'
          }`}
        >
          {formatTime(message.created_at)}
        </div>
      </div>
    </div>
  );
}

/**
 * Format timestamp for display.
 */
function formatTime(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

export default ChatMessage;
