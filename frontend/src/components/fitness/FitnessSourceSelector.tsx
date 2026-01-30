/**
 * Dropdown selector for fitness data source.
 *
 * Allows users to switch between different fitness data providers
 * (Whoop, Garmin, etc.) on the dashboard.
 */

import React from 'react';

export type FitnessSource = 'whoop' | 'garmin';

interface FitnessSourceSelectorProps {
  /** Currently selected source */
  selectedSource: FitnessSource;
  /** Callback when source changes */
  onSourceChange: (source: FitnessSource) => void;
  /** Whether Whoop is connected */
  whoopConnected: boolean;
  /** Whether Garmin is connected */
  garminConnected: boolean;
}

interface SourceOption {
  id: FitnessSource;
  name: string;
  icon: string;
  enabled: boolean;
}

const sourceOptions: SourceOption[] = [
  { id: 'whoop', name: 'Whoop', icon: '💪', enabled: true },
  { id: 'garmin', name: 'Garmin', icon: '⌚', enabled: false }, // Disabled - API not public
];

/**
 * Fitness source selector dropdown component.
 */
export function FitnessSourceSelector({
  selectedSource,
  onSourceChange,
  whoopConnected,
  garminConnected,
}: FitnessSourceSelectorProps): JSX.Element {
  const getConnectionStatus = (source: FitnessSource): boolean => {
    switch (source) {
      case 'whoop':
        return whoopConnected;
      case 'garmin':
        return garminConnected;
      default:
        return false;
    }
  };

  const getSourceName = (source: FitnessSource): string => {
    const option = sourceOptions.find((o) => o.id === source);
    return option?.name || source;
  };

  return (
    <div className="mb-6">
      <label
        htmlFor="fitness-source"
        className="block text-sm font-medium text-gray-700 mb-2"
      >
        Data Source
      </label>
      <div className="relative inline-block">
        <select
          id="fitness-source"
          value={selectedSource}
          onChange={(e) => onSourceChange(e.target.value as FitnessSource)}
          className="block w-full min-w-[200px] pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 rounded-lg shadow-sm bg-white appearance-none cursor-pointer"
        >
          {sourceOptions.filter((opt) => opt.enabled).map((option) => (
            <option key={option.id} value={option.id}>
              {option.icon} {option.name}
              {getConnectionStatus(option.id) ? ' ✓' : ''}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
          <svg
            className="fill-current h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
          >
            <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
          </svg>
        </div>
      </div>
      <p className="mt-2 text-sm text-gray-500">
        {getConnectionStatus(selectedSource) ? (
          <span className="text-green-600">
            Connected to {getSourceName(selectedSource)}
          </span>
        ) : (
          <span>
            Connect your {getSourceName(selectedSource)} account to see data
          </span>
        )}
      </p>
    </div>
  );
}

export default FitnessSourceSelector;
