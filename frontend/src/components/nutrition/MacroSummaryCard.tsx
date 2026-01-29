/**
 * Daily macro summary card component.
 */

import { useNutrition } from '../../contexts/NutritionContext';
import { formatMacros, calculateMacroPercentage } from '../../types/nutrition';

export function MacroSummaryCard() {
  const { dailySummary, goals, isLoading } = useNutrition();

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  const calories = Number(dailySummary?.total_calories || 0);
  const protein = Number(dailySummary?.total_protein_g || 0);
  const carbs = Number(dailySummary?.total_carbs_g || 0);
  const fat = Number(dailySummary?.total_fat_g || 0);

  const macros = [
    {
      label: 'Calories',
      value: calories,
      target: goals?.calories_target,
      unit: 'kcal',
      colorClass: 'text-blue-600',
      bgClass: 'bg-blue-500',
    },
    {
      label: 'Protein',
      value: protein,
      target: goals?.protein_g_target,
      unit: 'g',
      colorClass: 'text-red-600',
      bgClass: 'bg-red-500',
    },
    {
      label: 'Carbs',
      value: carbs,
      target: goals?.carbs_g_target,
      unit: 'g',
      colorClass: 'text-yellow-600',
      bgClass: 'bg-yellow-500',
    },
    {
      label: 'Fat',
      value: fat,
      target: goals?.fat_g_target,
      unit: 'g',
      colorClass: 'text-green-600',
      bgClass: 'bg-green-500',
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Summary</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {macros.map((macro) => {
          const percentage = calculateMacroPercentage(macro.value, macro.target);
          return (
            <div key={macro.label} className="text-center p-3 bg-gray-50 rounded-lg">
              <div className={`text-2xl font-bold ${macro.colorClass}`}>
                {formatMacros(macro.value)}
              </div>
              <div className="text-sm text-gray-500">
                {macro.label}
                {macro.target && (
                  <span className="block text-xs">
                    / {formatMacros(macro.target)} {macro.unit}
                  </span>
                )}
              </div>
              {percentage !== null && (
                <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${macro.bgClass} transition-all`}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
