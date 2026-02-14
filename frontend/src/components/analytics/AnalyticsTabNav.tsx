/**
 * Tab navigation for analytics page.
 */

import type { AnalyticsTab } from '../../types/analytics';

interface AnalyticsTabNavProps {
  activeTab: AnalyticsTab;
  onChange: (tab: AnalyticsTab) => void;
}

const TABS: { value: AnalyticsTab; label: string }[] = [
  { value: 'exercise', label: 'Exercise Progression' },
  { value: 'cardio', label: 'Cardio Performance' },
  { value: 'trends', label: 'Overall Trends' },
];

export function AnalyticsTabNav({ activeTab, onChange }: AnalyticsTabNavProps): JSX.Element {
  return (
    <div className="border-b border-gray-200">
      <nav className="flex -mb-px">
        {TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => onChange(tab.value)}
            className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.value
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
