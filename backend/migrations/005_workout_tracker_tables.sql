-- ============================================================================
-- Workout Tracker Tables Migration
-- Migration: 005_workout_tracker_tables
-- Description: Creates tables for manual workout logging feature
-- ============================================================================

-- ============================================================================
-- 1. EXERCISES TABLE
-- Master list of exercises (global + user custom)
-- user_id NULL = global/verified exercise, non-null = user's custom exercise
-- ============================================================================

CREATE TABLE IF NOT EXISTS exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('strength', 'cardio', 'flexibility', 'sports', 'other')),
    muscle_groups TEXT[] DEFAULT '{}',
    equipment TEXT,
    description TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for exercises
CREATE INDEX IF NOT EXISTS idx_exercises_user_id ON exercises(user_id);
CREATE INDEX IF NOT EXISTS idx_exercises_name ON exercises(name);
CREATE INDEX IF NOT EXISTS idx_exercises_category ON exercises(category);

-- ============================================================================
-- 2. WORKOUT_SESSIONS TABLE
-- Container for a single workout (e.g., "Leg Day", "Morning Run")
-- ============================================================================

CREATE TABLE IF NOT EXISTS workout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    whoop_workout_id UUID,
    session_date DATE NOT NULL,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    workout_type TEXT NOT NULL CHECK (workout_type IN ('strength', 'cardio', 'mixed', 'flexibility', 'sports', 'other')),
    name TEXT,
    notes TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for workout_sessions
CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id ON workout_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_date ON workout_sessions(user_id, session_date DESC);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_type ON workout_sessions(user_id, workout_type);

-- ============================================================================
-- 3. WORKOUT_SETS TABLE
-- Individual entries within a session (polymorphic for strength/cardio)
-- ============================================================================

CREATE TABLE IF NOT EXISTS workout_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES exercises(id) ON DELETE RESTRICT,
    set_type TEXT NOT NULL CHECK (set_type IN ('strength', 'cardio')),
    set_order INTEGER NOT NULL DEFAULT 1,

    -- Strength fields (nullable for cardio)
    reps INTEGER CHECK (reps > 0),
    weight_kg DECIMAL(10, 2) CHECK (weight_kg >= 0),
    rpe DECIMAL(3, 1) CHECK (rpe >= 1 AND rpe <= 10),
    is_warmup BOOLEAN DEFAULT false,
    is_failure BOOLEAN DEFAULT false,

    -- Cardio fields (nullable for strength)
    duration_seconds INTEGER CHECK (duration_seconds > 0),
    distance_meters DECIMAL(10, 2) CHECK (distance_meters >= 0),
    pace_seconds_per_km INTEGER,
    calories_burned INTEGER,
    avg_heart_rate INTEGER,
    max_heart_rate INTEGER,
    elevation_gain_meters DECIMAL(8, 2),

    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for workout_sets
CREATE INDEX IF NOT EXISTS idx_workout_sets_user_id ON workout_sets(user_id);
CREATE INDEX IF NOT EXISTS idx_workout_sets_session_id ON workout_sets(session_id);
CREATE INDEX IF NOT EXISTS idx_workout_sets_exercise_id ON workout_sets(exercise_id);

-- ============================================================================
-- 4. WORKOUT_GOALS TABLE
-- Optional user targets for workout frequency
-- ============================================================================

CREATE TABLE IF NOT EXISTS workout_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    workouts_per_week_target INTEGER,
    minutes_per_week_target INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_workout_goals_user_id ON workout_goals(user_id);

-- ============================================================================
-- 5. ROW LEVEL SECURITY POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_goals ENABLE ROW LEVEL SECURITY;

-- Exercises policies (users can see global exercises OR their own custom)
CREATE POLICY "Users can view global and own exercises"
    ON exercises FOR SELECT
    USING (user_id IS NULL OR auth.uid() = user_id);

CREATE POLICY "Users can insert own exercises"
    ON exercises FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own exercises"
    ON exercises FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own exercises"
    ON exercises FOR DELETE
    USING (auth.uid() = user_id);

-- Workout sessions policies
CREATE POLICY "Users can view own workout sessions"
    ON workout_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own workout sessions"
    ON workout_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workout sessions"
    ON workout_sessions FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own workout sessions"
    ON workout_sessions FOR DELETE
    USING (auth.uid() = user_id);

-- Workout sets policies
CREATE POLICY "Users can view own workout sets"
    ON workout_sets FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own workout sets"
    ON workout_sets FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workout sets"
    ON workout_sets FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own workout sets"
    ON workout_sets FOR DELETE
    USING (auth.uid() = user_id);

-- Workout goals policies
CREATE POLICY "Users can view own workout goals"
    ON workout_goals FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own workout goals"
    ON workout_goals FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own workout goals"
    ON workout_goals FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own workout goals"
    ON workout_goals FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 6. UPDATED_AT TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_workout_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_exercises_updated_at
    BEFORE UPDATE ON exercises
    FOR EACH ROW
    EXECUTE FUNCTION update_workout_updated_at();

CREATE TRIGGER trigger_workout_sessions_updated_at
    BEFORE UPDATE ON workout_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_workout_updated_at();

CREATE TRIGGER trigger_workout_sets_updated_at
    BEFORE UPDATE ON workout_sets
    FOR EACH ROW
    EXECUTE FUNCTION update_workout_updated_at();

CREATE TRIGGER trigger_workout_goals_updated_at
    BEFORE UPDATE ON workout_goals
    FOR EACH ROW
    EXECUTE FUNCTION update_workout_updated_at();

-- ============================================================================
-- 7. SEED DATA - Common Exercises
-- ============================================================================

INSERT INTO exercises (name, category, muscle_groups, equipment, is_verified) VALUES
-- Strength - Compound
('Bench Press', 'strength', ARRAY['chest', 'triceps', 'shoulders'], 'barbell', true),
('Squat', 'strength', ARRAY['quads', 'glutes', 'hamstrings'], 'barbell', true),
('Deadlift', 'strength', ARRAY['back', 'hamstrings', 'glutes'], 'barbell', true),
('Overhead Press', 'strength', ARRAY['shoulders', 'triceps'], 'barbell', true),
('Pull-ups', 'strength', ARRAY['back', 'biceps'], 'bodyweight', true),
('Barbell Row', 'strength', ARRAY['back', 'biceps'], 'barbell', true),
('Dumbbell Bench Press', 'strength', ARRAY['chest', 'triceps', 'shoulders'], 'dumbbell', true),
('Dumbbell Row', 'strength', ARRAY['back', 'biceps'], 'dumbbell', true),
('Lunges', 'strength', ARRAY['quads', 'glutes', 'hamstrings'], 'bodyweight', true),
('Romanian Deadlift', 'strength', ARRAY['hamstrings', 'glutes', 'back'], 'barbell', true),
('Front Squat', 'strength', ARRAY['quads', 'core'], 'barbell', true),
('Incline Bench Press', 'strength', ARRAY['chest', 'shoulders', 'triceps'], 'barbell', true),
('Dips', 'strength', ARRAY['chest', 'triceps', 'shoulders'], 'bodyweight', true),
('Chin-ups', 'strength', ARRAY['back', 'biceps'], 'bodyweight', true),

-- Strength - Isolation
('Bicep Curl', 'strength', ARRAY['biceps'], 'dumbbell', true),
('Tricep Extension', 'strength', ARRAY['triceps'], 'cable', true),
('Tricep Pushdown', 'strength', ARRAY['triceps'], 'cable', true),
('Leg Curl', 'strength', ARRAY['hamstrings'], 'machine', true),
('Leg Extension', 'strength', ARRAY['quads'], 'machine', true),
('Lateral Raise', 'strength', ARRAY['shoulders'], 'dumbbell', true),
('Face Pull', 'strength', ARRAY['shoulders', 'back'], 'cable', true),
('Leg Press', 'strength', ARRAY['quads', 'glutes'], 'machine', true),
('Calf Raise', 'strength', ARRAY['calves'], 'machine', true),
('Hammer Curl', 'strength', ARRAY['biceps', 'forearms'], 'dumbbell', true),
('Skull Crusher', 'strength', ARRAY['triceps'], 'barbell', true),
('Cable Fly', 'strength', ARRAY['chest'], 'cable', true),
('Lat Pulldown', 'strength', ARRAY['back', 'biceps'], 'cable', true),
('Seated Cable Row', 'strength', ARRAY['back', 'biceps'], 'cable', true),
('Preacher Curl', 'strength', ARRAY['biceps'], 'barbell', true),
('Rear Delt Fly', 'strength', ARRAY['shoulders'], 'dumbbell', true),

-- Core
('Plank', 'strength', ARRAY['core'], 'bodyweight', true),
('Crunch', 'strength', ARRAY['core'], 'bodyweight', true),
('Russian Twist', 'strength', ARRAY['core'], 'bodyweight', true),
('Leg Raise', 'strength', ARRAY['core'], 'bodyweight', true),
('Ab Rollout', 'strength', ARRAY['core'], 'ab_wheel', true),
('Cable Crunch', 'strength', ARRAY['core'], 'cable', true),

-- Cardio
('Running', 'cardio', ARRAY['full_body'], null, true),
('Cycling', 'cardio', ARRAY['quads', 'hamstrings'], null, true),
('Rowing', 'cardio', ARRAY['back', 'core'], 'cardio_machine', true),
('Swimming', 'cardio', ARRAY['full_body'], null, true),
('Walking', 'cardio', ARRAY['full_body'], null, true),
('Elliptical', 'cardio', ARRAY['full_body'], 'cardio_machine', true),
('Stair Climber', 'cardio', ARRAY['quads', 'glutes'], 'cardio_machine', true),
('Jump Rope', 'cardio', ARRAY['full_body'], 'jump_rope', true),
('HIIT', 'cardio', ARRAY['full_body'], null, true),
('Sprints', 'cardio', ARRAY['full_body'], null, true),

-- Flexibility
('Stretching', 'flexibility', ARRAY['full_body'], null, true),
('Yoga', 'flexibility', ARRAY['full_body'], null, true),
('Foam Rolling', 'flexibility', ARRAY['full_body'], 'foam_roller', true),

-- Sports
('Basketball', 'sports', ARRAY['full_body'], null, true),
('Soccer', 'sports', ARRAY['full_body'], null, true),
('Tennis', 'sports', ARRAY['full_body'], null, true),
('Golf', 'sports', ARRAY['core', 'shoulders'], null, true),
('Boxing', 'sports', ARRAY['full_body'], null, true),
('Martial Arts', 'sports', ARRAY['full_body'], null, true),
('Rock Climbing', 'sports', ARRAY['back', 'forearms', 'core'], null, true)
ON CONFLICT DO NOTHING;
