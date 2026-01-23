/**
 * Frontend logging utility.
 *
 * Provides consistent logging across the application with
 * different log levels and optional context data.
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
  context?: Record<string, unknown>;
}

/**
 * Logger class for frontend logging.
 */
class Logger {
  private isDev = import.meta.env.DEV;

  /**
   * Internal log method.
   */
  private log(
    level: LogLevel,
    message: string,
    context?: Record<string, unknown>
  ): void {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      context,
    };

    if (this.isDev) {
      const consoleMethod = level === 'debug' ? 'log' : level;
      const prefix = `[${level.toUpperCase()}]`;
      if (context) {
        console[consoleMethod](prefix, message, context);
      } else {
        console[consoleMethod](prefix, message);
      }
    }

    // In production, send critical logs to backend
    if (!this.isDev && (level === 'error' || level === 'warn')) {
      this.sendToBackend(entry);
    }
  }

  /**
   * Send log to backend for persistence (production only).
   */
  private sendToBackend(entry: LogEntry): void {
    // Could implement sending logs to a backend endpoint
    // For now, just use navigator.sendBeacon for non-blocking sends
    // navigator.sendBeacon('/api/v1/logs', JSON.stringify(entry));
  }

  /**
   * Log debug message (development only).
   */
  debug(message: string, context?: Record<string, unknown>): void {
    this.log('debug', message, context);
  }

  /**
   * Log info message.
   */
  info(message: string, context?: Record<string, unknown>): void {
    this.log('info', message, context);
  }

  /**
   * Log warning message.
   */
  warn(message: string, context?: Record<string, unknown>): void {
    this.log('warn', message, context);
  }

  /**
   * Log error message.
   */
  error(message: string, context?: Record<string, unknown>): void {
    this.log('error', message, context);
  }
}

export const logger = new Logger();
