/**
 * Date selector component for navigating between days.
 */

import { getLocalDateString } from '../../types/workout';

interface DateSelectorProps {
  value: string;
  onChange: (date: string) => void;
}

export function DateSelector({ value, onChange }: DateSelectorProps) {
  const goToPrevDay = () => {
    const current = new Date(value + 'T12:00:00');
    current.setDate(current.getDate() - 1);
    onChange(getLocalDateString(current));
  };

  const goToNextDay = () => {
    const current = new Date(value + 'T12:00:00');
    current.setDate(current.getDate() + 1);
    onChange(getLocalDateString(current));
  };

  const goToToday = () => {
    onChange(getLocalDateString());
  };

  const formatDisplayDate = (dateStr: string): string => {
    const date = new Date(dateStr + 'T12:00:00');
    const today = getLocalDateString();
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = getLocalDateString(yesterday);

    if (dateStr === today) {
      return 'Today';
    } else if (dateStr === yesterdayStr) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      });
    }
  };

  const isToday = value === getLocalDateString();

  return (
    <div className="flex items-center justify-center gap-4">
      <button
        onClick={goToPrevDay}
        className="p-2 rounded-full hover:bg-gray-100"
        aria-label="Previous day"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <div className="flex items-center gap-2">
        <input
          type="date"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <span className="text-gray-600 font-medium min-w-[100px] text-center">
          {formatDisplayDate(value)}
        </span>
      </div>

      <button
        onClick={goToNextDay}
        disabled={isToday}
        className="p-2 rounded-full hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="Next day"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {!isToday && (
        <button
          onClick={goToToday}
          className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800"
        >
          Today
        </button>
      )}
    </div>
  );
}
