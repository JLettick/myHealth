/**
 * Time range selector with preset buttons and custom date pickers.
 */

import type { TimeRange, TimeRangePreset } from '../../types/analytics';
import { getTimeRangeFromPreset } from '../../types/analytics';

interface TimeRangeSelectorProps {
  value: TimeRange;
  onChange: (range: TimeRange) => void;
}

const PRESETS: { value: TimeRangePreset; label: string }[] = [
  { value: '30d', label: '30D' },
  { value: '90d', label: '90D' },
  { value: '6mo', label: '6M' },
  { value: '1yr', label: '1Y' },
  { value: 'custom', label: 'Custom' },
];

export function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps): JSX.Element {
  const handlePresetClick = (preset: TimeRangePreset) => {
    if (preset === 'custom') {
      onChange({ ...value, preset: 'custom' });
    } else {
      onChange(getTimeRangeFromPreset(preset));
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex rounded-lg border border-gray-300 overflow-hidden">
        {PRESETS.map((preset) => (
          <button
            key={preset.value}
            onClick={() => handlePresetClick(preset.value)}
            className={`px-3 py-1.5 text-sm font-medium transition-colors ${
              value.preset === preset.value
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            } ${preset.value !== '30d' ? 'border-l border-gray-300' : ''}`}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {value.preset === 'custom' && (
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={value.start_date}
            onChange={(e) =>
              onChange({ ...value, start_date: e.target.value })
            }
            className="px-2 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-gray-500 text-sm">to</span>
          <input
            type="date"
            value={value.end_date}
            onChange={(e) =>
              onChange({ ...value, end_date: e.target.value })
            }
            className="px-2 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}
    </div>
  );
}
