/**
 * Nutrition API functions for the frontend.
 */

import apiClient from './client';
import type {
  Food,
  FoodCreate,
  FoodUpdate,
  FoodListResponse,
  FoodSearchResponse,
  FoodEntry,
  FoodEntryCreate,
  FoodEntryUpdate,
  DailySummary,
  WeeklySummary,
  NutritionGoals,
  NutritionGoalsCreate,
  USDAFoodItem,
  USDASearchResponse,
} from '../types/nutrition';
import { logger } from '../utils/logger';

// =============================================================================
// FOODS API
// =============================================================================

export async function createFood(food: FoodCreate): Promise<Food> {
  logger.info('Creating custom food', { name: food.name });
  const response = await apiClient.post<Food>('/nutrition/foods', food);
  return response.data;
}

export async function searchFoods(
  query: string,
  page: number = 1,
  pageSize: number = 20
): Promise<FoodSearchResponse> {
  logger.debug('Searching foods', { query, page });
  const params = new URLSearchParams({
    q: query,
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  const response = await apiClient.get<FoodSearchResponse>(
    `/nutrition/foods/search?${params}`
  );
  return response.data;
}

export async function getMyFoods(
  page: number = 1,
  pageSize: number = 20
): Promise<FoodListResponse> {
  logger.debug('Getting my foods', { page });
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  const response = await apiClient.get<FoodListResponse>(
    `/nutrition/foods/my?${params}`
  );
  return response.data;
}

export async function getFood(foodId: string): Promise<Food> {
  const response = await apiClient.get<Food>(`/nutrition/foods/${foodId}`);
  return response.data;
}

export async function updateFood(foodId: string, food: FoodUpdate): Promise<Food> {
  logger.info('Updating food', { foodId });
  const response = await apiClient.put<Food>(`/nutrition/foods/${foodId}`, food);
  return response.data;
}

export async function deleteFood(foodId: string): Promise<void> {
  logger.info('Deleting food', { foodId });
  await apiClient.delete(`/nutrition/foods/${foodId}`);
}

// =============================================================================
// FOOD ENTRIES API
// =============================================================================

export async function createEntry(entry: FoodEntryCreate): Promise<FoodEntry> {
  logger.info('Creating food entry');
  const response = await apiClient.post<FoodEntry>('/nutrition/entries', entry);
  return response.data;
}

export async function getEntry(entryId: string): Promise<FoodEntry> {
  const response = await apiClient.get<FoodEntry>(`/nutrition/entries/${entryId}`);
  return response.data;
}

export async function updateEntry(
  entryId: string,
  entry: FoodEntryUpdate
): Promise<FoodEntry> {
  logger.info('Updating food entry', { entryId });
  const response = await apiClient.put<FoodEntry>(
    `/nutrition/entries/${entryId}`,
    entry
  );
  return response.data;
}

export async function deleteEntry(entryId: string): Promise<void> {
  logger.info('Deleting food entry', { entryId });
  await apiClient.delete(`/nutrition/entries/${entryId}`);
}

// =============================================================================
// SUMMARIES API
// =============================================================================

export async function getDailySummary(date?: string): Promise<DailySummary> {
  logger.debug('Getting daily summary', { date });
  const params = date ? `?summary_date=${date}` : '';
  const response = await apiClient.get<DailySummary>(
    `/nutrition/summary/daily${params}`
  );
  return response.data;
}

export async function getWeeklySummary(startDate?: string): Promise<WeeklySummary> {
  logger.debug('Getting weekly summary', { startDate });
  const params = startDate ? `?start_date=${startDate}` : '';
  const response = await apiClient.get<WeeklySummary>(
    `/nutrition/summary/weekly${params}`
  );
  return response.data;
}

// =============================================================================
// GOALS API
// =============================================================================

export async function getGoals(): Promise<NutritionGoals | null> {
  logger.debug('Getting nutrition goals');
  const response = await apiClient.get<NutritionGoals | null>('/nutrition/goals');
  return response.data;
}

export async function setGoals(goals: NutritionGoalsCreate): Promise<NutritionGoals> {
  logger.info('Setting nutrition goals');
  const response = await apiClient.put<NutritionGoals>('/nutrition/goals', goals);
  return response.data;
}

// =============================================================================
// USDA FOOD DATABASE API
// =============================================================================

export async function searchUSDAFoods(
  query: string,
  page: number = 1,
  pageSize: number = 20,
  dataType: string = 'Foundation,SR Legacy'
): Promise<USDASearchResponse> {
  logger.debug('Searching USDA foods', { query, page, dataType });
  const params = new URLSearchParams({
    q: query,
    page: page.toString(),
    page_size: pageSize.toString(),
    data_type: dataType,
  });
  const response = await apiClient.get<USDASearchResponse>(
    `/nutrition/foods/usda/search?${params}`
  );
  return response.data;
}

export async function importUSDAFood(usdaFood: USDAFoodItem): Promise<Food> {
  logger.info('Importing USDA food', { fdc_id: usdaFood.fdc_id });
  const response = await apiClient.post<Food>(
    '/nutrition/foods/usda/import',
    usdaFood
  );
  return response.data;
}
