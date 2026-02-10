/**
 * Modal for searching and adding food to a meal.
 * Supports searching local foods and USDA FoodData Central database.
 */

import { useState, useCallback, useRef } from 'react';
import type { Food, MealType, FoodEntryCreate, USDAFoodItem } from '../../types/nutrition';
import { searchFoods, searchUSDAFoods, importUSDAFood } from '../../api/nutrition';
import { useNutrition } from '../../contexts/NutritionContext';
import { MEAL_TYPE_LABELS } from '../../types/nutrition';

type SearchSource = 'local' | 'usda';
type InputMode = 'servings' | 'grams';
type USDADataType = 'Foundation,SR Legacy' | 'Branded' | 'Foundation,SR Legacy,Branded';

const DATA_TYPE_OPTIONS: { value: USDADataType; label: string }[] = [
  { value: 'Foundation,SR Legacy', label: 'Basic Foods' },
  { value: 'Branded', label: 'Branded Products' },
  { value: 'Foundation,SR Legacy,Branded', label: 'All Foods' },
];

interface AddFoodModalProps {
  isOpen: boolean;
  mealType: MealType;
  onClose: () => void;
}

export function AddFoodModal({ isOpen, mealType, onClose }: AddFoodModalProps) {
  const { selectedDate, addEntry } = useNutrition();
  const [query, setQuery] = useState('');
  const [searchSource, setSearchSource] = useState<SearchSource>('usda');
  const [dataType, setDataType] = useState<USDADataType>('Foundation,SR Legacy');
  const [localResults, setLocalResults] = useState<Food[]>([]);
  const [usdaResults, setUsdaResults] = useState<USDAFoodItem[]>([]);
  const [selectedFood, setSelectedFood] = useState<Food | null>(null);
  const [selectedUSDAFood, setSelectedUSDAFood] = useState<USDAFoodItem | null>(null);
  const [inputMode, setInputMode] = useState<InputMode>('grams');
  const [servings, setServings] = useState(1);
  const [grams, setGrams] = useState(100);
  const [isSearching, setIsSearching] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track search request identity to discard stale responses
  const searchIdRef = useRef(0);

  const handleSearch = useCallback(async () => {
    if (query.length < 2) return;

    const currentSearchId = ++searchIdRef.current;
    setIsSearching(true);
    setError(null);
    try {
      if (searchSource === 'local') {
        const response = await searchFoods(query);
        if (searchIdRef.current !== currentSearchId) return;
        setLocalResults(response.results);
        setUsdaResults([]);
      } else {
        const response = await searchUSDAFoods(query, 1, 20, dataType);
        if (searchIdRef.current !== currentSearchId) return;
        setUsdaResults(response.results);
        setLocalResults([]);
      }
    } catch (err) {
      if (searchIdRef.current !== currentSearchId) return;
      console.error('Search failed:', err);
      setError('Search failed. Please try again.');
    } finally {
      if (searchIdRef.current === currentSearchId) {
        setIsSearching(false);
      }
    }
  }, [query, searchSource, dataType]);

  const handleSelectUSDAFood = useCallback((food: USDAFoodItem) => {
    setSelectedUSDAFood(food);
    setSelectedFood(null);
    // Set default grams to the food's serving size
    setGrams(Number(food.serving_size));
    setServings(1);
  }, []);

  const handleSelectLocalFood = useCallback((food: Food) => {
    setSelectedFood(food);
    setSelectedUSDAFood(null);
    // Set default grams to the food's serving size
    setGrams(Number(food.serving_size));
    setServings(1);
  }, []);

  // Calculate effective servings based on input mode
  const getEffectiveServings = useCallback(() => {
    const currentFood = selectedFood || selectedUSDAFood;
    if (!currentFood) return 1;

    if (inputMode === 'servings') {
      return servings;
    } else {
      // Grams mode: calculate servings from grams
      const servingSize = Number(currentFood.serving_size);
      return servingSize > 0 ? grams / servingSize : 1;
    }
  }, [inputMode, servings, grams, selectedFood, selectedUSDAFood]);

  const handleAdd = useCallback(async () => {
    setIsAdding(true);
    setError(null);

    try {
      let foodToAdd: Food;

      // If USDA food is selected, import it first
      if (selectedUSDAFood) {
        foodToAdd = await importUSDAFood(selectedUSDAFood);
      } else if (selectedFood) {
        foodToAdd = selectedFood;
      } else {
        return;
      }

      const effectiveServings = getEffectiveServings();

      const entry: FoodEntryCreate = {
        food_id: foodToAdd.id,
        entry_date: selectedDate,
        meal_type: mealType,
        servings: effectiveServings,
      };
      await addEntry(entry);

      // Reset and close
      resetState();
      onClose();
    } catch (err) {
      console.error('Failed to add entry:', err);
      setError('Failed to add food. Please try again.');
    } finally {
      setIsAdding(false);
    }
  }, [selectedFood, selectedUSDAFood, selectedDate, mealType, getEffectiveServings, addEntry, onClose]);

  const resetState = () => {
    setQuery('');
    setLocalResults([]);
    setUsdaResults([]);
    setSelectedFood(null);
    setSelectedUSDAFood(null);
    setServings(1);
    setGrams(100);
    setInputMode('grams');
    setError(null);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleBack = () => {
    setSelectedFood(null);
    setSelectedUSDAFood(null);
    setServings(1);
    setGrams(100);
  };

  const handleSourceChange = (source: SearchSource) => {
    setSearchSource(source);
    setLocalResults([]);
    setUsdaResults([]);
    setSelectedFood(null);
    setSelectedUSDAFood(null);
  };

  if (!isOpen) return null;

  const currentFood = selectedFood || selectedUSDAFood;
  const hasResults = localResults.length > 0 || usdaResults.length > 0;
  const effectiveServings = getEffectiveServings();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[80vh] overflow-y-auto">
        <h2 className="text-xl font-bold mb-4">
          Add Food to {MEAL_TYPE_LABELS[mealType]}
        </h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}

        {!currentFood ? (
          <>
            {/* Search Source Toggle */}
            <div className="flex mb-4 border rounded-md overflow-hidden">
              <button
                onClick={() => handleSourceChange('usda')}
                className={`flex-1 py-2 px-3 text-sm font-medium transition-colors ${
                  searchSource === 'usda'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                USDA Database
              </button>
              <button
                onClick={() => handleSourceChange('local')}
                className={`flex-1 py-2 px-3 text-sm font-medium transition-colors ${
                  searchSource === 'local'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                My Foods
              </button>
            </div>

            {/* USDA Data Type Filter */}
            {searchSource === 'usda' && (
              <div className="mb-4">
                <select
                  value={dataType}
                  onChange={(e) => setDataType(e.target.value as USDADataType)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {DATA_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Search Input */}
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder={searchSource === 'usda' ? 'Search USDA foods...' : 'Search my foods...'}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleSearch}
                disabled={isSearching || query.length < 2}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isSearching ? '...' : 'Search'}
              </button>
            </div>

            {/* No Results Message */}
            {!hasResults && query.length >= 2 && !isSearching && (
              <p className="text-gray-500 text-sm mb-4">
                {searchSource === 'usda'
                  ? 'No USDA foods found. Try a different search or switch to "Branded Products".'
                  : 'No foods found. Try searching the USDA database or create a custom food.'}
              </p>
            )}

            {/* Local Results */}
            {searchSource === 'local' && localResults.length > 0 && (
              <ul className="space-y-2 max-h-60 overflow-y-auto">
                {localResults.map((food) => (
                  <li
                    key={food.id}
                    className="p-3 border rounded cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSelectLocalFood(food)}
                  >
                    <div className="font-medium">{food.name}</div>
                    {food.brand && (
                      <div className="text-sm text-gray-500">{food.brand}</div>
                    )}
                    <div className="text-xs text-gray-400">
                      {Number(food.serving_size)}{food.serving_unit} - {Number(food.calories)} kcal
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {/* USDA Results */}
            {searchSource === 'usda' && usdaResults.length > 0 && (
              <ul className="space-y-2 max-h-60 overflow-y-auto">
                {usdaResults.map((food) => (
                  <li
                    key={food.fdc_id}
                    className="p-3 border rounded cursor-pointer hover:bg-gray-50"
                    onClick={() => handleSelectUSDAFood(food)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="font-medium flex-1">{food.name}</div>
                      <span className={`text-xs px-2 py-0.5 rounded-full whitespace-nowrap ${
                        food.data_type === 'Branded'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-green-100 text-green-700'
                      }`}>
                        {food.data_type}
                      </span>
                    </div>
                    {food.brand && (
                      <div className="text-sm text-gray-500">{food.brand}</div>
                    )}
                    <div className="text-xs text-gray-400">
                      {Number(food.serving_size)}{food.serving_unit} - {Number(food.calories)} kcal
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <div>
            {/* Selected Food Details */}
            <div className="mb-4 p-3 bg-gray-50 rounded">
              <div className="flex items-start justify-between gap-2">
                <div className="font-medium">{currentFood.name}</div>
                {selectedUSDAFood && (
                  <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">
                    USDA
                  </span>
                )}
              </div>
              {'brand' in currentFood && currentFood.brand && (
                <div className="text-sm text-gray-500">{currentFood.brand}</div>
              )}
              <div className="text-sm text-gray-500">
                Per {Number(currentFood.serving_size)}{currentFood.serving_unit}:
              </div>
              <div className="text-sm mt-1">
                {Number(currentFood.calories)} kcal | P: {Number(currentFood.protein_g)}g |
                C: {Number(currentFood.carbs_g)}g | F: {Number(currentFood.fat_g)}g
              </div>
            </div>

            {/* Input Mode Toggle */}
            <div className="flex mb-3 border rounded-md overflow-hidden">
              <button
                onClick={() => setInputMode('grams')}
                className={`flex-1 py-2 px-3 text-sm font-medium transition-colors ${
                  inputMode === 'grams'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Grams
              </button>
              <button
                onClick={() => setInputMode('servings')}
                className={`flex-1 py-2 px-3 text-sm font-medium transition-colors ${
                  inputMode === 'servings'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Servings
              </button>
            </div>

            {/* Amount Input */}
            <div className="mb-4">
              {inputMode === 'grams' ? (
                <>
                  <label className="block text-sm font-medium mb-1">
                    Amount (grams)
                  </label>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={grams}
                    onChange={(e) => setGrams(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    = {effectiveServings.toFixed(2)} servings
                  </p>
                </>
              ) : (
                <>
                  <label className="block text-sm font-medium mb-1">
                    Servings ({Number(currentFood.serving_size)}{currentFood.serving_unit} each)
                  </label>
                  <input
                    type="number"
                    min="0.25"
                    step="0.25"
                    value={servings}
                    onChange={(e) => setServings(parseFloat(e.target.value) || 1)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    = {Math.round(servings * Number(currentFood.serving_size))}g
                  </p>
                </>
              )}
            </div>

            {/* Total Macros */}
            <div className="mb-4 p-3 bg-blue-50 rounded">
              <div className="font-medium">Total:</div>
              <div className="text-sm">
                {Math.round(Number(currentFood.calories) * effectiveServings)} kcal |
                P: {Math.round(Number(currentFood.protein_g) * effectiveServings)}g |
                C: {Math.round(Number(currentFood.carbs_g) * effectiveServings)}g |
                F: {Math.round(Number(currentFood.fat_g) * effectiveServings)}g
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <button
                onClick={handleBack}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Back
              </button>
              <button
                onClick={handleAdd}
                disabled={isAdding}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isAdding ? 'Adding...' : `Add to ${MEAL_TYPE_LABELS[mealType]}`}
              </button>
            </div>
          </div>
        )}

        <button
          onClick={handleClose}
          className="w-full mt-4 py-2 px-4 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
