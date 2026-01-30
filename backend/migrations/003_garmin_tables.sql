-- Garmin Integration Tables
-- Migration: 003_garmin_tables.sql
-- Created: January 2026

-- ============================================================
-- GARMIN CONNECTIONS TABLE
-- Stores OAuth tokens (encrypted) for Garmin Connect
-- ============================================================

CREATE TABLE IF NOT EXISTS garmin_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    garmin_user_id TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMPTZ NOT NULL,
    scopes TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id)
);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_garmin_connections_user_id ON garmin_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_garmin_connections_active ON garmin_connections(user_id, is_active);

-- RLS Policy
ALTER TABLE garmin_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own Garmin connection"
    ON garmin_connections FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own Garmin connection"
    ON garmin_connections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own Garmin connection"
    ON garmin_connections FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own Garmin connection"
    ON garmin_connections FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================
-- GARMIN ACTIVITIES TABLE
-- Stores workout/activity data from Garmin
-- ============================================================

CREATE TABLE IF NOT EXISTS garmin_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    garmin_activity_id TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    activity_name TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER,
    distance_meters DECIMAL(12, 2),
    calories INTEGER,
    average_hr INTEGER,
    max_hr INTEGER,
    average_speed DECIMAL(8, 4),
    max_speed DECIMAL(8, 4),
    elevation_gain_meters DECIMAL(8, 2),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, garmin_activity_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_garmin_activities_user_id ON garmin_activities(user_id);
CREATE INDEX IF NOT EXISTS idx_garmin_activities_start_time ON garmin_activities(start_time);
CREATE INDEX IF NOT EXISTS idx_garmin_activities_user_time ON garmin_activities(user_id, start_time DESC);

-- RLS Policy
ALTER TABLE garmin_activities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own Garmin activities"
    ON garmin_activities FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own Garmin activities"
    ON garmin_activities FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own Garmin activities"
    ON garmin_activities FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own Garmin activities"
    ON garmin_activities FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================
-- GARMIN SLEEP TABLE
-- Stores sleep session data
-- ============================================================

CREATE TABLE IF NOT EXISTS garmin_sleep (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    garmin_sleep_id TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    total_sleep_seconds INTEGER,
    deep_sleep_seconds INTEGER,
    light_sleep_seconds INTEGER,
    rem_sleep_seconds INTEGER,
    awake_seconds INTEGER,
    sleep_score INTEGER,
    sleep_quality TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, garmin_sleep_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_garmin_sleep_user_id ON garmin_sleep(user_id);
CREATE INDEX IF NOT EXISTS idx_garmin_sleep_start_time ON garmin_sleep(start_time);
CREATE INDEX IF NOT EXISTS idx_garmin_sleep_user_time ON garmin_sleep(user_id, start_time DESC);

-- RLS Policy
ALTER TABLE garmin_sleep ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own Garmin sleep"
    ON garmin_sleep FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own Garmin sleep"
    ON garmin_sleep FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own Garmin sleep"
    ON garmin_sleep FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own Garmin sleep"
    ON garmin_sleep FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================
-- GARMIN HEART RATE TABLE
-- Stores daily heart rate metrics
-- ============================================================

CREATE TABLE IF NOT EXISTS garmin_heart_rate (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    resting_hr INTEGER,
    max_hr INTEGER,
    min_hr INTEGER,
    average_hr INTEGER,
    hrv_value DECIMAL(8, 2),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_garmin_heart_rate_user_id ON garmin_heart_rate(user_id);
CREATE INDEX IF NOT EXISTS idx_garmin_heart_rate_date ON garmin_heart_rate(date);
CREATE INDEX IF NOT EXISTS idx_garmin_heart_rate_user_date ON garmin_heart_rate(user_id, date DESC);

-- RLS Policy
ALTER TABLE garmin_heart_rate ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own Garmin heart rate"
    ON garmin_heart_rate FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own Garmin heart rate"
    ON garmin_heart_rate FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own Garmin heart rate"
    ON garmin_heart_rate FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own Garmin heart rate"
    ON garmin_heart_rate FOR DELETE
    USING (auth.uid() = user_id);


-- ============================================================
-- GARMIN DAILY STATS TABLE
-- Stores daily aggregate stats (steps, calories, etc.)
-- ============================================================

CREATE TABLE IF NOT EXISTS garmin_daily_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_steps INTEGER,
    distance_meters DECIMAL(12, 2),
    calories_burned INTEGER,
    active_calories INTEGER,
    active_minutes INTEGER,
    sedentary_minutes INTEGER,
    floors_climbed INTEGER,
    intensity_minutes INTEGER,
    stress_level INTEGER,
    body_battery_high INTEGER,
    body_battery_low INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_garmin_daily_stats_user_id ON garmin_daily_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_garmin_daily_stats_date ON garmin_daily_stats(date);
CREATE INDEX IF NOT EXISTS idx_garmin_daily_stats_user_date ON garmin_daily_stats(user_id, date DESC);

-- RLS Policy
ALTER TABLE garmin_daily_stats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own Garmin daily stats"
    ON garmin_daily_stats FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own Garmin daily stats"
    ON garmin_daily_stats FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own Garmin daily stats"
    ON garmin_daily_stats FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own Garmin daily stats"
    ON garmin_daily_stats FOR DELETE
    USING (auth.uid() = user_id);
