/**
 * TypeScript types for Nutrition/Macro tracking.
 */

// =============================================================================
// Food Types
// =============================================================================

export interface Food {
  id: string;
  user_id: string | null;
  name: string;
  brand: string | null;
  serving_size: number;
  serving_unit: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number | null;
  sugar_g: number | null;
  sodium_mg: number | null;
  is_verified: boolean;
  barcode: string | null;
  created_at: string;
}

export interface FoodCreate {
  name: string;
  brand?: string;
  serving_size: number;
  serving_unit: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
  sugar_g?: number;
  sodium_mg?: number;
  barcode?: string;
}

export type FoodUpdate = Partial<FoodCreate>;

// =============================================================================
// Food Entry Types
// =============================================================================

export type MealType = 'breakfast' | 'lunch' | 'dinner' | 'snack';

export interface FoodEntry {
  id: string;
  user_id: string;
  food_id: string;
  entry_date: string;
  meal_type: MealType;
  servings: number;
  notes: string | null;
  logged_at: string;
  created_at: string;
  food?: Food;
  total_calories?: number;
  total_protein_g?: number;
  total_carbs_g?: number;
  total_fat_g?: number;
}

export interface FoodEntryCreate {
  food_id: string;
  entry_date: string;
  meal_type: MealType;
  servings: number;
  notes?: string;
}

export type FoodEntryUpdate = Partial<FoodEntryCreate>;

// =============================================================================
// Summary Types
// =============================================================================

export interface MealSummary {
  meal_type: MealType;
  entries: FoodEntry[];
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
}

export interface DailySummary {
  date: string;
  meals: MealSummary[];
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  total_fiber_g: number;
  calories_target: number | null;
  protein_g_target: number | null;
  carbs_g_target: number | null;
  fat_g_target: number | null;
}

export interface WeeklySummary {
  start_date: string;
  end_date: string;
  daily_summaries: DailySummary[];
  avg_calories: number;
  avg_protein_g: number;
  avg_carbs_g: number;
  avg_fat_g: number;
}

// =============================================================================
// Goals Types
// =============================================================================

export interface NutritionGoals {
  id: string;
  user_id: string;
  calories_target: number | null;
  protein_g_target: number | null;
  carbs_g_target: number | null;
  fat_g_target: number | null;
  fiber_g_target: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface NutritionGoalsCreate {
  calories_target?: number;
  protein_g_target?: number;
  carbs_g_target?: number;
  fat_g_target?: number;
  fiber_g_target?: number;
}

// =============================================================================
// List Response Types
// =============================================================================

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
}

export type FoodListResponse = PaginatedResponse<Food>;

export interface FoodSearchResponse {
  results: Food[];
  total: number;
  query: string;
}

// =============================================================================
// USDA Food Types
// =============================================================================

export interface USDAFoodItem {
  fdc_id: string;
  name: string;
  brand: string | null;
  data_type: string;
  serving_size: number;
  serving_unit: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number | null;
}

export interface USDASearchResponse {
  results: USDAFoodItem[];
  total: number;
  query: string;
  page: number;
  page_size: number;
}

// =============================================================================
// Utility Constants
// =============================================================================

export const MEAL_TYPE_LABELS: Record<MealType, string> = {
  breakfast: 'Breakfast',
  lunch: 'Lunch',
  dinner: 'Dinner',
  snack: 'Snack',
};

export const MEAL_TYPE_ICONS: Record<MealType, string> = {
  breakfast: '🌅',
  lunch: '☀️',
  dinner: '🌙',
  snack: '🍎',
};

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Get today's date as YYYY-MM-DD string in local timezone.
 * Using toISOString() returns UTC which can show wrong date for users
 * in timezones behind UTC.
 */
export function getLocalDateString(date: Date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function formatMacros(value: number | null | undefined): string {
  if (value === null || value === undefined) return '--';
  return Math.round(Number(value)).toString();
}

export function calculateMacroPercentage(
  current: number,
  target: number | null
): number | null {
  if (!target || target === 0) return null;
  return Math.round((current / target) * 100);
}
