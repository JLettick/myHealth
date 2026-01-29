-- ============================================================================
-- Nutrition Tracking Tables Migration
-- Migration: 003_nutrition_tables
-- Description: Creates tables for nutrition/macro tracking feature
-- ============================================================================

-- ============================================================================
-- 1. FOODS TABLE
-- Stores food items with nutritional information
-- user_id NULL = global/shared food, non-null = user's custom food
-- ============================================================================

CREATE TABLE IF NOT EXISTS foods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    brand TEXT,
    serving_size DECIMAL(10, 2) NOT NULL,
    serving_unit TEXT NOT NULL DEFAULT 'g',
    calories DECIMAL(10, 2) NOT NULL,
    protein_g DECIMAL(10, 2) NOT NULL DEFAULT 0,
    carbs_g DECIMAL(10, 2) NOT NULL DEFAULT 0,
    fat_g DECIMAL(10, 2) NOT NULL DEFAULT 0,
    fiber_g DECIMAL(10, 2) DEFAULT 0,
    sugar_g DECIMAL(10, 2) DEFAULT 0,
    sodium_mg DECIMAL(10, 2) DEFAULT 0,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    barcode TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for foods
CREATE INDEX IF NOT EXISTS idx_foods_user_id ON foods(user_id);
CREATE INDEX IF NOT EXISTS idx_foods_name ON foods(name);
CREATE INDEX IF NOT EXISTS idx_foods_barcode ON foods(barcode) WHERE barcode IS NOT NULL;

-- ============================================================================
-- 2. FOOD_ENTRIES TABLE
-- Stores user's food log entries (what they ate, when, how much)
-- ============================================================================

CREATE TABLE IF NOT EXISTS food_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    food_id UUID NOT NULL REFERENCES foods(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL,
    meal_type TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    servings DECIMAL(10, 2) NOT NULL DEFAULT 1,
    notes TEXT,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for food_entries
CREATE INDEX IF NOT EXISTS idx_food_entries_user_id ON food_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_food_entries_date ON food_entries(user_id, entry_date DESC);
CREATE INDEX IF NOT EXISTS idx_food_entries_meal ON food_entries(user_id, entry_date, meal_type);

-- ============================================================================
-- 3. NUTRITION_GOALS TABLE
-- Stores user's daily macro goals/targets
-- ============================================================================

CREATE TABLE IF NOT EXISTS nutrition_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    calories_target DECIMAL(10, 2),
    protein_g_target DECIMAL(10, 2),
    carbs_g_target DECIMAL(10, 2),
    fat_g_target DECIMAL(10, 2),
    fiber_g_target DECIMAL(10, 2),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_nutrition_goals_user_id ON nutrition_goals(user_id);

-- ============================================================================
-- 4. ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE foods ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_goals ENABLE ROW LEVEL SECURITY;

-- Foods policies (users can see global foods OR their own custom foods)
CREATE POLICY "Users can view global and own foods"
    ON foods FOR SELECT
    USING (user_id IS NULL OR auth.uid() = user_id);

CREATE POLICY "Users can insert own foods"
    ON foods FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own foods"
    ON foods FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own foods"
    ON foods FOR DELETE
    USING (auth.uid() = user_id);

-- Food entries policies (users can only access their own entries)
CREATE POLICY "Users can view own food entries"
    ON food_entries FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own food entries"
    ON food_entries FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own food entries"
    ON food_entries FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own food entries"
    ON food_entries FOR DELETE
    USING (auth.uid() = user_id);

-- Nutrition goals policies
CREATE POLICY "Users can view own nutrition goals"
    ON nutrition_goals FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own nutrition goals"
    ON nutrition_goals FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own nutrition goals"
    ON nutrition_goals FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own nutrition goals"
    ON nutrition_goals FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 5. UPDATED_AT TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_nutrition_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_foods_updated_at
    BEFORE UPDATE ON foods
    FOR EACH ROW
    EXECUTE FUNCTION update_nutrition_updated_at();

CREATE TRIGGER trigger_food_entries_updated_at
    BEFORE UPDATE ON food_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_nutrition_updated_at();

CREATE TRIGGER trigger_nutrition_goals_updated_at
    BEFORE UPDATE ON nutrition_goals
    FOR EACH ROW
    EXECUTE FUNCTION update_nutrition_updated_at();
