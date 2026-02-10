/**
 * Chat input component with send button and optional voice input.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

/**
 * Text input for sending chat messages.
 * Supports Enter to send, Shift+Enter for newline, and voice input via microphone.
 */
export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Ask about your health data...',
}: ChatInputProps): JSX.Element {
  const [content, setContent] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const prevTranscriptRef = useRef<string>('');
  const {
    isListening,
    isSupported,
    error: speechError,
    transcript,
    startListening,
    stopListening,
    resetTranscript,
  } = useSpeechRecognition();

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, [content]);

  // Sync speech transcript into the textarea content by appending only the delta
  useEffect(() => {
    if (!isListening) {
      prevTranscriptRef.current = transcript;
      return;
    }
    const prev = prevTranscriptRef.current;
    if (transcript.length > prev.length && transcript.startsWith(prev)) {
      const delta = transcript.slice(prev.length);
      setContent((current) => current + delta);
    } else if (transcript !== prev) {
      // Transcript was reset or changed entirely (e.g. new recognition session)
      setContent(transcript);
    }
    prevTranscriptRef.current = transcript;
  }, [transcript, isListening]);

  const handleSubmit = useCallback(() => {
    const trimmed = content.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setContent('');
      resetTranscript();
      prevTranscriptRef.current = '';
      stopListening();
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  }, [content, disabled, onSend, resetTranscript, stopListening]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit]
  );

  const handleMicToggle = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  return (
    <div>
      <div className="flex items-end gap-2 p-4 border-t border-gray-200 bg-white">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
        {isSupported && (
          <button
            onClick={handleMicToggle}
            disabled={disabled}
            title={isListening ? 'Stop listening' : 'Start voice input'}
            className={`p-3 rounded-xl transition-colors ${
              isListening
                ? 'bg-red-500 text-white animate-pulse-mic'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z"
              />
            </svg>
          </button>
        )}
        <button
          onClick={handleSubmit}
          disabled={disabled || !content.trim()}
          className="px-4 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {disabled ? (
            <span className="flex items-center gap-2">
              <svg
                className="animate-spin h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </span>
          ) : (
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          )}
        </button>
      </div>
      {speechError && (
        <div className="px-4 pb-2 bg-red-50 text-red-600 text-xs">
          {speechError}
        </div>
      )}
    </div>
  );
}

export default ChatInput;
