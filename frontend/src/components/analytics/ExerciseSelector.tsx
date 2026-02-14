/**
 * Searchable exercise dropdown for analytics.
 * Only shows exercises the user has actually logged workouts for.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { getLoggedExercises } from '../../api/analytics';
import type { Exercise } from '../../types/workout';
import type { AnalyticsTab } from '../../types/analytics';

interface ExerciseSelectorProps {
  selectedExerciseId: string | null;
  onSelect: (exercise: Exercise) => void;
  activeTab: AnalyticsTab;
}

export function ExerciseSelector({
  selectedExerciseId,
  onSelect,
  activeTab,
}: ExerciseSelectorProps): JSX.Element {
  const [query, setQuery] = useState('');
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedName, setSelectedName] = useState('');
  const searchIdRef = useRef(0);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();
  const containerRef = useRef<HTMLDivElement>(null);

  const setType = activeTab === 'cardio' ? 'cardio' : activeTab === 'exercise' ? 'strength' : undefined;

  const doSearch = useCallback(
    async (searchQuery: string) => {
      const searchId = ++searchIdRef.current;
      setIsLoading(true);
      try {
        const result = await getLoggedExercises(searchQuery, setType);
        if (searchId === searchIdRef.current) {
          setExercises(result.results);
        }
      } catch {
        // Ignore errors for search
      } finally {
        if (searchId === searchIdRef.current) {
          setIsLoading(false);
        }
      }
    },
    [setType]
  );

  // Initial load when dropdown opens or tab changes
  useEffect(() => {
    if (isOpen) {
      doSearch(query);
    }
  }, [isOpen, setType]); // eslint-disable-line react-hooks/exhaustive-deps

  // Debounced search on query change
  useEffect(() => {
    if (!isOpen) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(query), 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, isOpen, doSearch]);

  // Clear selection when tab changes
  useEffect(() => {
    setSelectedName('');
    setQuery('');
  }, [activeTab]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (exercise: Exercise) => {
    setSelectedName(exercise.name);
    setQuery('');
    setIsOpen(false);
    onSelect(exercise);
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-md">
      <div
        className="flex items-center border border-gray-300 rounded-lg bg-white cursor-pointer"
        onClick={() => setIsOpen(!isOpen)}
      >
        <input
          type="text"
          placeholder={selectedName || 'Select an exercise...'}
          value={isOpen ? query : ''}
          onChange={(e) => {
            setQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          className={`flex-1 px-3 py-2 text-sm rounded-lg focus:outline-none ${
            selectedName && !isOpen ? 'text-gray-900' : 'text-gray-500'
          }`}
        />
        <svg
          className={`w-4 h-4 mr-3 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {isLoading ? (
            <div className="px-3 py-4 text-sm text-gray-500 text-center">Loading...</div>
          ) : exercises.length === 0 ? (
            <div className="px-3 py-4 text-sm text-gray-500 text-center">
              {query ? 'No matching exercises found' : 'No logged exercises yet'}
            </div>
          ) : (
            exercises.map((exercise) => (
              <button
                key={exercise.id}
                onClick={() => handleSelect(exercise)}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-blue-50 transition-colors ${
                  exercise.id === selectedExerciseId ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <div className="font-medium">{exercise.name}</div>
                <div className="text-xs text-gray-400 capitalize">{exercise.category}</div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
