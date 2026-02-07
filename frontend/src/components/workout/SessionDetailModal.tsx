/**
 * Modal for viewing and editing a workout session with its sets.
 */

import { useState } from 'react';
import { useWorkout } from '../../contexts/WorkoutContext';
import type {
  WorkoutSession,
  WorkoutSet,
  WorkoutSetCreate,
  SetType,
  Exercise,
  ExerciseCategory,
} from '../../types/workout';
import {
  WORKOUT_TYPE_LABELS,
  SET_TYPE_LABELS,
  EXERCISE_CATEGORY_LABELS,
  formatWeight,
  formatDistance,
  formatDuration,
} from '../../types/workout';

interface SessionDetailModalProps {
  session: WorkoutSession;
  onClose: () => void;
}

export function SessionDetailModal({
  session,
  onClose,
}: SessionDetailModalProps) {
  const { exercises, addSet, removeSet, removeSession, createExercise } =
    useWorkout();

  const [isAddingSet, setIsAddingSet] = useState(false);
  const [selectedExercise, setSelectedExercise] = useState<Exercise | null>(null);
  const [exerciseSearch, setExerciseSearch] = useState('');
  const [setType, setSetType] = useState<SetType>('strength');
  const [weightUnit, setWeightUnit] = useState<'kg' | 'lbs'>('kg');
  const [setFormData, setSetFormData] = useState({
    reps: '',
    weight: '', // Store the display value in the selected unit
    rpe: '',
    is_warmup: false,
    duration_seconds: '',
    distance_meters: '',
    notes: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Custom exercise creation state
  const [isCreatingExercise, setIsCreatingExercise] = useState(false);
  const [newExerciseData, setNewExerciseData] = useState({
    name: '',
    category: 'strength' as ExerciseCategory,
    equipment: '',
  });

  const filteredExercises = exercises.filter((ex) =>
    ex.name.toLowerCase().includes(exerciseSearch.toLowerCase())
  );

  const handleAddSet = async () => {
    if (!selectedExercise) return;

    setIsSubmitting(true);
    try {
      const newSet: WorkoutSetCreate = {
        exercise_id: selectedExercise.id,
        set_type: setType,
        set_order: session.sets.length + 1,
      };

      if (setType === 'strength') {
        if (setFormData.reps) newSet.reps = parseInt(setFormData.reps);
        if (setFormData.weight) {
          const weightValue = parseFloat(setFormData.weight);
          // Convert lbs to kg if needed (1 lb = 0.453592 kg)
          newSet.weight_kg = weightUnit === 'lbs'
            ? weightValue * 0.453592
            : weightValue;
        }
        if (setFormData.rpe) newSet.rpe = parseFloat(setFormData.rpe);
        newSet.is_warmup = setFormData.is_warmup;
      } else {
        if (setFormData.duration_seconds)
          newSet.duration_seconds = parseInt(setFormData.duration_seconds);
        if (setFormData.distance_meters)
          newSet.distance_meters = parseFloat(setFormData.distance_meters);
      }

      if (setFormData.notes) newSet.notes = setFormData.notes;

      await addSet(session.id, newSet);
      // Keep exercise selected for quick follow-up sets, just clear the form values
      clearFormValues();
    } finally {
      setIsSubmitting(false);
    }
  };

  // Clear only form values, keep exercise selected for quick follow-up sets
  const clearFormValues = () => {
    setSetFormData({
      reps: '',
      weight: '',
      rpe: '',
      is_warmup: false,
      duration_seconds: '',
      distance_meters: '',
      notes: '',
    });
  };

  // Full reset - clears everything including selected exercise
  const resetSetForm = () => {
    setIsAddingSet(false);
    setSelectedExercise(null);
    setExerciseSearch('');
    setIsCreatingExercise(false);
    setNewExerciseData({ name: '', category: 'strength', equipment: '' });
    clearFormValues();
  };

  // Duplicate a set - pre-fill form with existing set's values
  const handleDuplicateSet = (set: WorkoutSet) => {
    // Find the exercise in our exercises list
    const exercise = exercises.find((ex) => ex.id === set.exercise_id) || set.exercise;

    setIsAddingSet(true);
    setSelectedExercise(exercise || null);
    setSetType(set.set_type);

    if (set.set_type === 'strength') {
      // Convert weight from kg to display unit if needed
      let displayWeight = '';
      if (set.weight_kg) {
        displayWeight = weightUnit === 'lbs'
          ? (set.weight_kg / 0.453592).toFixed(0) // Convert kg to lbs
          : set.weight_kg.toString();
      }

      setSetFormData({
        reps: set.reps?.toString() || '',
        weight: displayWeight,
        rpe: set.rpe?.toString() || '',
        is_warmup: set.is_warmup || false,
        duration_seconds: '',
        distance_meters: '',
        notes: set.notes || '',
      });
    } else {
      setSetFormData({
        reps: '',
        weight: '',
        rpe: '',
        is_warmup: false,
        duration_seconds: set.duration_seconds?.toString() || '',
        distance_meters: set.distance_meters?.toString() || '',
        notes: set.notes || '',
      });
    }
  };

  const handleCreateExercise = async () => {
    if (!newExerciseData.name.trim()) return;

    setIsSubmitting(true);
    try {
      const exercise = await createExercise({
        name: newExerciseData.name.trim(),
        category: newExerciseData.category,
        equipment: newExerciseData.equipment.trim() || undefined,
      });

      if (exercise) {
        setSelectedExercise(exercise);
        setIsCreatingExercise(false);
        setNewExerciseData({ name: '', category: 'strength', equipment: '' });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteSet = async (setId: string) => {
    if (window.confirm('Delete this set?')) {
      await removeSet(setId);
    }
  };

  const handleDeleteSession = async () => {
    if (window.confirm('Delete this entire workout session?')) {
      await removeSession(session.id);
      onClose();
    }
  };

  const renderSetItem = (set: WorkoutSet) => {
    const exercise = set.exercise;

    return (
      <li
        key={set.id}
        className="flex items-center justify-between py-3 px-4 hover:bg-gray-50"
      >
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900">
              {exercise?.name || 'Unknown Exercise'}
            </span>
            {set.is_warmup && (
              <span className="px-2 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded">
                Warmup
              </span>
            )}
          </div>
          <div className="text-sm text-gray-500 mt-1">
            {set.set_type === 'strength' ? (
              <>
                {set.reps && `${set.reps} reps`}
                {set.weight_kg && ` @ ${formatWeight(set.weight_kg)}`}
                {set.rpe && ` (RPE ${set.rpe})`}
              </>
            ) : (
              <>
                {set.duration_seconds && formatDuration(set.duration_seconds)}
                {set.distance_meters && ` - ${formatDistance(set.distance_meters)}`}
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleDuplicateSet(set)}
            className="p-1 text-gray-400 hover:text-blue-500"
            title="Duplicate set"
          >
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
                d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </button>
          <button
            onClick={() => handleDeleteSet(set.id)}
            className="p-1 text-gray-400 hover:text-red-500"
            title="Delete set"
          >
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
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      </li>
    );
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black/50 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white rounded-xl shadow-xl w-full max-w-2xl z-10 max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {session.name || WORKOUT_TYPE_LABELS[session.workout_type]}
              </h2>
              <p className="text-sm text-gray-500">
                {WORKOUT_TYPE_LABELS[session.workout_type]} - {session.total_sets}{' '}
                sets
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleDeleteSession}
                className="p-2 text-red-400 hover:text-red-600"
                title="Delete session"
              >
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
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
              <button
                onClick={onClose}
                className="p-1 text-gray-400 hover:text-gray-600"
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Sets List */}
          <div className="flex-1 overflow-y-auto">
            {session.sets.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No exercises logged yet. Add your first set below.
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">{session.sets.map(renderSetItem)}</ul>
            )}
          </div>

          {/* Add Set Form */}
          <div className="border-t border-gray-200 p-4">
            {!isAddingSet ? (
              <button
                onClick={() => setIsAddingSet(true)}
                className="w-full py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-blue-500 hover:text-blue-500 transition-colors flex items-center justify-center gap-2"
              >
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
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Add Set
              </button>
            ) : (
              <div className="space-y-4">
                {/* Set Type Selection */}
                <div className="flex gap-2">
                  {(['strength', 'cardio'] as SetType[]).map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setSetType(type)}
                      className={`flex-1 py-2 text-sm font-medium rounded-lg border transition-colors ${
                        setType === type
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {SET_TYPE_LABELS[type]}
                    </button>
                  ))}
                </div>

                {/* Exercise Selection */}
                {!selectedExercise ? (
                  isCreatingExercise ? (
                    <div className="space-y-3 p-3 border border-gray-200 rounded-lg bg-gray-50">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-gray-900">Create Custom Exercise</span>
                        <button
                          type="button"
                          onClick={() => setIsCreatingExercise(false)}
                          className="text-sm text-gray-500 hover:text-gray-700"
                        >
                          Cancel
                        </button>
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Name *</label>
                        <input
                          type="text"
                          value={newExerciseData.name}
                          onChange={(e) =>
                            setNewExerciseData({ ...newExerciseData, name: e.target.value })
                          }
                          placeholder="e.g., Cable Crossover"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Category</label>
                        <select
                          value={newExerciseData.category}
                          onChange={(e) =>
                            setNewExerciseData({
                              ...newExerciseData,
                              category: e.target.value as ExerciseCategory,
                            })
                          }
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        >
                          {(Object.keys(EXERCISE_CATEGORY_LABELS) as ExerciseCategory[]).map(
                            (cat) => (
                              <option key={cat} value={cat}>
                                {EXERCISE_CATEGORY_LABELS[cat]}
                              </option>
                            )
                          )}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Equipment (optional)</label>
                        <input
                          type="text"
                          value={newExerciseData.equipment}
                          onChange={(e) =>
                            setNewExerciseData({ ...newExerciseData, equipment: e.target.value })
                          }
                          placeholder="e.g., cable, dumbbell"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={handleCreateExercise}
                        disabled={!newExerciseData.name.trim() || isSubmitting}
                        className="w-full py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50"
                      >
                        {isSubmitting ? 'Creating...' : 'Create Exercise'}
                      </button>
                    </div>
                  ) : (
                    <div>
                      <input
                        type="text"
                        placeholder="Search exercises..."
                        value={exerciseSearch}
                        onChange={(e) => setExerciseSearch(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {exerciseSearch && (
                        <div className="mt-2 max-h-40 overflow-y-auto border border-gray-200 rounded-lg">
                          {filteredExercises.length === 0 ? (
                            <div className="p-3 text-center">
                              <p className="text-gray-500 text-sm mb-2">
                                No exercises found for "{exerciseSearch}"
                              </p>
                              <button
                                type="button"
                                onClick={() => {
                                  setNewExerciseData({
                                    ...newExerciseData,
                                    name: exerciseSearch,
                                  });
                                  setIsCreatingExercise(true);
                                  setExerciseSearch('');
                                }}
                                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                              >
                                + Create "{exerciseSearch}" as custom exercise
                              </button>
                            </div>
                          ) : (
                            <ul className="divide-y divide-gray-100">
                              {filteredExercises.slice(0, 10).map((ex) => (
                                <li key={ex.id}>
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setSelectedExercise(ex);
                                      setExerciseSearch('');
                                    }}
                                    className="w-full px-3 py-2 text-left hover:bg-gray-50"
                                  >
                                    <span className="font-medium">{ex.name}</span>
                                    {ex.equipment && (
                                      <span className="ml-2 text-sm text-gray-500">
                                        ({ex.equipment})
                                      </span>
                                    )}
                                  </button>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}
                      <button
                        type="button"
                        onClick={() => setIsCreatingExercise(true)}
                        className="mt-2 text-sm text-blue-600 hover:text-blue-800"
                      >
                        + Create custom exercise
                      </button>
                    </div>
                  )
                ) : (
                  <div className="flex items-center justify-between bg-blue-50 rounded-lg px-3 py-2">
                    <span className="font-medium text-blue-700">
                      {selectedExercise.name}
                    </span>
                    <button
                      type="button"
                      onClick={() => setSelectedExercise(null)}
                      className="text-blue-500 hover:text-blue-700"
                    >
                      Change
                    </button>
                  </div>
                )}

                {/* Set Details Form */}
                {selectedExercise && (
                  <>
                    {setType === 'strength' ? (
                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">
                            Reps
                          </label>
                          <input
                            type="number"
                            value={setFormData.reps}
                            onChange={(e) =>
                              setSetFormData({ ...setFormData, reps: e.target.value })
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <label className="text-xs text-gray-500">
                              Weight
                            </label>
                            <div className="flex rounded-md overflow-hidden border border-gray-300">
                              <button
                                type="button"
                                onClick={() => setWeightUnit('kg')}
                                className={`px-2 py-0.5 text-xs font-medium transition-colors ${
                                  weightUnit === 'kg'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-white text-gray-600 hover:bg-gray-50'
                                }`}
                              >
                                kg
                              </button>
                              <button
                                type="button"
                                onClick={() => setWeightUnit('lbs')}
                                className={`px-2 py-0.5 text-xs font-medium transition-colors ${
                                  weightUnit === 'lbs'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-white text-gray-600 hover:bg-gray-50'
                                }`}
                              >
                                lbs
                              </button>
                            </div>
                          </div>
                          <input
                            type="number"
                            step={weightUnit === 'kg' ? '0.5' : '1'}
                            value={setFormData.weight}
                            onChange={(e) =>
                              setSetFormData({
                                ...setFormData,
                                weight: e.target.value,
                              })
                            }
                            placeholder={weightUnit === 'kg' ? '0.0' : '0'}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">
                            RPE (1-10)
                          </label>
                          <input
                            type="number"
                            min="1"
                            max="10"
                            step="0.5"
                            value={setFormData.rpe}
                            onChange={(e) =>
                              setSetFormData({ ...setFormData, rpe: e.target.value })
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                        <div className="col-span-3">
                          <label className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={setFormData.is_warmup}
                              onChange={(e) =>
                                setSetFormData({
                                  ...setFormData,
                                  is_warmup: e.target.checked,
                                })
                              }
                              className="rounded"
                            />
                            Warmup set
                          </label>
                        </div>
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">
                            Duration (seconds)
                          </label>
                          <input
                            type="number"
                            value={setFormData.duration_seconds}
                            onChange={(e) =>
                              setSetFormData({
                                ...setFormData,
                                duration_seconds: e.target.value,
                              })
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">
                            Distance (meters)
                          </label>
                          <input
                            type="number"
                            value={setFormData.distance_meters}
                            onChange={(e) =>
                              setSetFormData({
                                ...setFormData,
                                distance_meters: e.target.value,
                              })
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                          />
                        </div>
                      </div>
                    )}

                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={resetSetForm}
                        className="px-4 py-2 text-gray-600 hover:text-gray-800"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={handleAddSet}
                        disabled={isSubmitting}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                      >
                        {isSubmitting ? 'Adding...' : 'Add Set'}
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
