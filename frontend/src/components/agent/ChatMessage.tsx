/**
 * Chat message bubble component.
 */

import { useState } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types/agent';

interface ChatMessageProps {
  message: ChatMessageType;
}

/**
 * Renders a single chat message with different styles for user vs assistant.
 */
export function ChatMessage({ message }: ChatMessageProps): JSX.Element {
  const isUser = message.role === 'user';
  const hasToolActions =
    !isUser && message.tool_actions && message.tool_actions.length > 0;
  const hasDebugTrace =
    import.meta.env.DEV &&
    !isUser &&
    message.debug_trace &&
    message.debug_trace.length > 0;

  const [debugExpanded, setDebugExpanded] = useState(false);

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-md'
            : 'bg-gray-100 text-gray-900 rounded-bl-md'
        }`}
      >
        {/* Tool action badges */}
        {hasToolActions && (
          <div className="flex flex-wrap gap-1.5 mb-2">
            {message.tool_actions!.map((action, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
              >
                <svg
                  className="w-3 h-3"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                {action.label}
              </span>
            ))}
          </div>
        )}

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

        {/* Debug trace panel (dev only) */}
        {hasDebugTrace && (
          <div className="mt-2 border-t border-gray-200 pt-2">
            <button
              onClick={() => setDebugExpanded(!debugExpanded)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 font-mono"
            >
              <svg
                className={`w-3 h-3 transition-transform ${debugExpanded ? 'rotate-90' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9 5l7 7-7 7"
                />
              </svg>
              Debug ({message.debug_trace!.length} tool call
              {message.debug_trace!.length !== 1 ? 's' : ''})
            </button>

            {debugExpanded && (
              <div className="mt-2 space-y-2 max-h-96 overflow-y-auto">
                {message.debug_trace!.map((trace, idx) => (
                  <div
                    key={idx}
                    className="bg-gray-50 border border-gray-200 rounded-lg p-2 text-xs font-mono"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="bg-gray-700 text-white px-1.5 py-0.5 rounded text-[10px] font-bold">
                        {trace.step}
                      </span>
                      <span className="font-semibold text-indigo-700">
                        {trace.tool_name}
                      </span>
                    </div>

                    {trace.model_text && (
                      <div className="mb-1 text-gray-500 italic text-[11px]">
                        "{trace.model_text}"
                      </div>
                    )}

                    <details className="mb-1">
                      <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                        Input
                      </summary>
                      <pre className="mt-1 p-1.5 bg-white rounded border border-gray-100 overflow-x-auto text-[11px] text-gray-700 whitespace-pre-wrap">
                        {JSON.stringify(trace.tool_input, null, 2)}
                      </pre>
                    </details>

                    <details>
                      <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                        Output
                      </summary>
                      <pre className="mt-1 p-1.5 bg-white rounded border border-gray-100 overflow-x-auto text-[11px] text-gray-700 whitespace-pre-wrap max-h-48 overflow-y-auto">
                        {JSON.stringify(trace.tool_output, null, 2)}
                      </pre>
                    </details>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
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
