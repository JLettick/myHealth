/**
 * Nutrition tracking page component (protected).
 */

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNutrition } from '../contexts/NutritionContext';
import type { MealType, MealSummary } from '../types/nutrition';
import {
  MacroSummaryCard,
  MealSection,
  AddFoodModal,
  DateSelector,
} from '../components/nutrition';

export function NutritionPage(): JSX.Element {
  const { isAuthenticated } = useAuth();
  const { dailySummary, selectedDate, setSelectedDate, isLoading, error, refresh, refreshGoals } =
    useNutrition();

  // Load nutrition data and goals on mount
  const hasLoadedRef = useRef(false);
  useEffect(() => {
    if (isAuthenticated && !hasLoadedRef.current) {
      hasLoadedRef.current = true;
      refresh();
      refreshGoals();
    }
  }, [isAuthenticated]); // eslint-disable-line react-hooks/exhaustive-deps

  const [addFoodModal, setAddFoodModal] = useState<{
    isOpen: boolean;
    mealType: MealType;
  }>({ isOpen: false, mealType: 'breakfast' });

  const openAddFood = (mealType: MealType) => {
    setAddFoodModal({ isOpen: true, mealType });
  };

  const closeAddFood = () => {
    setAddFoodModal({ isOpen: false, mealType: 'breakfast' });
  };

  // Create default meal summaries
  const getMealSummary = (mealType: MealType): MealSummary => {
    const found = dailySummary?.meals.find((m) => m.meal_type === mealType);
    return (
      found || {
        meal_type: mealType,
        entries: [],
        total_calories: 0,
        total_protein_g: 0,
        total_carbs_g: 0,
        total_fat_g: 0,
      }
    );
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Nutrition Tracker</h1>
        <p className="text-gray-600 mt-2">
          Track your meals and monitor your macros.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">{error}</div>
      )}

      {/* Date Selector */}
      <div className="mb-6">
        <DateSelector value={selectedDate} onChange={setSelectedDate} />
      </div>

      {/* Daily Macro Summary */}
      <div className="mb-8">
        <MacroSummaryCard />
      </div>

      {/* Meal Sections */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow p-4 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="h-20 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {(['breakfast', 'lunch', 'dinner', 'snack'] as MealType[]).map(
            (mealType) => (
              <MealSection
                key={mealType}
                meal={getMealSummary(mealType)}
                onAddFood={openAddFood}
              />
            )
          )}
        </div>
      )}

      {/* Add Food Modal */}
      <AddFoodModal
        isOpen={addFoodModal.isOpen}
        mealType={addFoodModal.mealType}
        onClose={closeAddFood}
      />
    </div>
  );
}
