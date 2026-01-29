/**
 * Meal section component showing entries for a specific meal.
 */

import type { MealSummary, MealType } from '../../types/nutrition';
import { MEAL_TYPE_LABELS, MEAL_TYPE_ICONS, formatMacros } from '../../types/nutrition';
import { useNutrition } from '../../contexts/NutritionContext';

interface MealSectionProps {
  meal: MealSummary;
  onAddFood: (mealType: MealType) => void;
}

export function MealSection({ meal, onAddFood }: MealSectionProps) {
  const { removeEntry } = useNutrition();

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-lg font-medium text-gray-900">
          {MEAL_TYPE_ICONS[meal.meal_type]} {MEAL_TYPE_LABELS[meal.meal_type]}
        </h4>
        <div className="text-sm text-gray-500">
          {formatMacros(Number(meal.total_calories))} kcal
        </div>
      </div>

      {meal.entries.length === 0 ? (
        <p className="text-gray-400 text-sm mb-3">No foods logged</p>
      ) : (
        <ul className="space-y-2 mb-3">
          {meal.entries.map((entry) => (
            <li
              key={entry.id}
              className="flex justify-between items-center p-2 bg-gray-50 rounded"
            >
              <div className="flex-1">
                <div className="font-medium text-gray-800">
                  {entry.food?.name || 'Unknown food'}
                </div>
                <div className="text-xs text-gray-500">
                  {entry.servings} serving{Number(entry.servings) !== 1 ? 's' : ''} -{' '}
                  {formatMacros(entry.total_calories)} kcal |{' '}
                  P: {formatMacros(entry.total_protein_g)}g |{' '}
                  C: {formatMacros(entry.total_carbs_g)}g |{' '}
                  F: {formatMacros(entry.total_fat_g)}g
                </div>
              </div>
              <button
                onClick={() => removeEntry(entry.id)}
                className="ml-2 text-red-500 hover:text-red-700 text-sm"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}

      <button
        onClick={() => onAddFood(meal.meal_type)}
        className="w-full py-2 px-4 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        + Add Food
      </button>
    </div>
  );
}
