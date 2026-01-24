-- Whoop Integration Tables Migration
-- Run this in Supabase SQL Editor
-- Migration: 002_whoop_tables
-- Description: Creates tables for Whoop fitness data integration

-- ============================================================================
-- 1. WHOOP CONNECTIONS TABLE
-- Stores OAuth tokens for connected Whoop accounts
-- ============================================================================

CREATE TABLE IF NOT EXISTS whoop_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    whoop_user_id TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    scopes TEXT[] NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_whoop_connections_user_id ON whoop_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_whoop_connections_whoop_user_id ON whoop_connections(whoop_user_id);

-- ============================================================================
-- 2. WHOOP CYCLES TABLE
-- Daily physiological cycles (strain, heart rate, etc.)
-- ============================================================================

CREATE TABLE IF NOT EXISTS whoop_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    whoop_cycle_id BIGINT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    strain_score DECIMAL(5, 2),
    kilojoules DECIMAL(10, 2),
    average_heart_rate INTEGER,
    max_heart_rate INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, whoop_cycle_id)
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_whoop_cycles_user_id ON whoop_cycles(user_id);
CREATE INDEX IF NOT EXISTS idx_whoop_cycles_start_time ON whoop_cycles(user_id, start_time DESC);

-- ============================================================================
-- 3. WHOOP RECOVERY TABLE
-- Recovery scores and related metrics
-- ============================================================================

CREATE TABLE IF NOT EXISTS whoop_recovery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    whoop_cycle_id BIGINT NOT NULL,
    recovery_score DECIMAL(5, 2),
    resting_heart_rate DECIMAL(5, 2),
    hrv_rmssd_milli DECIMAL(8, 3),
    spo2_percentage DECIMAL(5, 2),
    skin_temp_celsius DECIMAL(5, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, whoop_cycle_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_whoop_recovery_user_id ON whoop_recovery(user_id);
CREATE INDEX IF NOT EXISTS idx_whoop_recovery_cycle_id ON whoop_recovery(user_id, whoop_cycle_id);

-- ============================================================================
-- 4. WHOOP SLEEP TABLE
-- Sleep sessions and sleep stage data
-- ============================================================================

CREATE TABLE IF NOT EXISTS whoop_sleep (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    whoop_sleep_id BIGINT NOT NULL,
    whoop_cycle_id BIGINT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    is_nap BOOLEAN DEFAULT false,
    sleep_score DECIMAL(5, 2),
    total_in_bed_milli BIGINT,
    total_awake_milli BIGINT,
    total_light_sleep_milli BIGINT,
    total_slow_wave_sleep_milli BIGINT,
    total_rem_sleep_milli BIGINT,
    sleep_efficiency DECIMAL(5, 4),
    respiratory_rate DECIMAL(5, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, whoop_sleep_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_whoop_sleep_user_id ON whoop_sleep(user_id);
CREATE INDEX IF NOT EXISTS idx_whoop_sleep_start_time ON whoop_sleep(user_id, start_time DESC);

-- ============================================================================
-- 5. WHOOP WORKOUTS TABLE
-- Workout/activity sessions
-- ============================================================================

CREATE TABLE IF NOT EXISTS whoop_workouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    whoop_workout_id BIGINT NOT NULL,
    whoop_cycle_id BIGINT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    sport_id INTEGER NOT NULL,
    sport_name TEXT,
    strain_score DECIMAL(5, 2),
    kilojoules DECIMAL(10, 2),
    average_heart_rate INTEGER,
    max_heart_rate INTEGER,
    distance_meter DECIMAL(10, 2),
    altitude_gain_meter DECIMAL(8, 2),
    altitude_change_meter DECIMAL(8, 2),
    zone_zero_milli BIGINT,
    zone_one_milli BIGINT,
    zone_two_milli BIGINT,
    zone_three_milli BIGINT,
    zone_four_milli BIGINT,
    zone_five_milli BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, whoop_workout_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_whoop_workouts_user_id ON whoop_workouts(user_id);
CREATE INDEX IF NOT EXISTS idx_whoop_workouts_start_time ON whoop_workouts(user_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_whoop_workouts_sport_id ON whoop_workouts(sport_id);

-- ============================================================================
-- 6. ROW LEVEL SECURITY POLICIES
-- Ensure users can only access their own data
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE whoop_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE whoop_cycles ENABLE ROW LEVEL SECURITY;
ALTER TABLE whoop_recovery ENABLE ROW LEVEL SECURITY;
ALTER TABLE whoop_sleep ENABLE ROW LEVEL SECURITY;
ALTER TABLE whoop_workouts ENABLE ROW LEVEL SECURITY;

-- whoop_connections policies
CREATE POLICY "Users can view own whoop connections"
    ON whoop_connections FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own whoop connections"
    ON whoop_connections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own whoop connections"
    ON whoop_connections FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own whoop connections"
    ON whoop_connections FOR DELETE
    USING (auth.uid() = user_id);

-- whoop_cycles policies
CREATE POLICY "Users can view own whoop cycles"
    ON whoop_cycles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own whoop cycles"
    ON whoop_cycles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own whoop cycles"
    ON whoop_cycles FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own whoop cycles"
    ON whoop_cycles FOR DELETE
    USING (auth.uid() = user_id);

-- whoop_recovery policies
CREATE POLICY "Users can view own whoop recovery"
    ON whoop_recovery FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own whoop recovery"
    ON whoop_recovery FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own whoop recovery"
    ON whoop_recovery FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own whoop recovery"
    ON whoop_recovery FOR DELETE
    USING (auth.uid() = user_id);

-- whoop_sleep policies
CREATE POLICY "Users can view own whoop sleep"
    ON whoop_sleep FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own whoop sleep"
    ON whoop_sleep FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own whoop sleep"
    ON whoop_sleep FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own whoop sleep"
    ON whoop_sleep FOR DELETE
    USING (auth.uid() = user_id);

-- whoop_workouts policies
CREATE POLICY "Users can view own whoop workouts"
    ON whoop_workouts FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own whoop workouts"
    ON whoop_workouts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own whoop workouts"
    ON whoop_workouts FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own whoop workouts"
    ON whoop_workouts FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 7. UPDATED_AT TRIGGER FUNCTION
-- Automatically update the updated_at column
-- ============================================================================

CREATE OR REPLACE FUNCTION update_whoop_connections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_whoop_connections_updated_at
    BEFORE UPDATE ON whoop_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_whoop_connections_updated_at();

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Tables created:
--   - whoop_connections: OAuth token storage
--   - whoop_cycles: Daily physiological cycles
--   - whoop_recovery: Recovery scores
--   - whoop_sleep: Sleep sessions
--   - whoop_workouts: Workout activities
--
-- All tables have:
--   - UUID primary keys
--   - Foreign key to auth.users with CASCADE delete
--   - Row Level Security enabled
--   - Appropriate indexes for query performance
-- ============================================================================
