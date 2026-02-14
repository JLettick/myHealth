/**
 * Empty state component for analytics charts.
 */

interface EmptyAnalyticsStateProps {
  message?: string;
}

export function EmptyAnalyticsState({
  message = 'No data available for this period.',
}: EmptyAnalyticsStateProps): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-gray-400">
      <svg
        className="w-16 h-16 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <p className="text-sm">{message}</p>
    </div>
  );
}
