# Setup Guide

This guide walks you through setting up the myHealth application for development and production.

## Prerequisites

- Python 3.10+
- Node.js 20+
- Docker and Docker Compose (for containerized deployment)
- Supabase account and project

## 1. Supabase Setup

### Create Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Wait for the project to be provisioned

### Get API Keys

From your Supabase dashboard (Settings > API):
- **Project URL**: `https://your-project-ref.supabase.co`
- **Anon Key**: Public key for client-side use
- **Service Role Key**: Private key for server-side use (keep secret!)

### Configure Authentication

1. Go to Authentication > Settings
2. Set Site URL: `http://localhost:5173` (development) or your production URL
3. Add redirect URLs for OAuth if using social auth

### Run Database Migration

Run this SQL in the Supabase SQL Editor (SQL Editor > New Query):

```sql
-- Create profiles table that extends auth.users
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id);

-- Policy: Users can insert their own profile (on signup)
CREATE POLICY "Users can insert own profile"
    ON public.profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updated_at
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
```

### Run Whoop Tables Migration

If you want to integrate with Whoop, run this SQL to create the necessary tables:

```sql
-- See backend/migrations/002_whoop_tables.sql for the full migration
-- This creates:
--   - whoop_connections: OAuth token storage
--   - whoop_cycles: Daily physiological data
--   - whoop_recovery: Recovery scores
--   - whoop_sleep: Sleep sessions
--   - whoop_workouts: Workout activities
-- Plus RLS policies for all tables
```

Run the migration file: `backend/migrations/002_whoop_tables.sql`

### Run Nutrition Tables Migration

For the nutrition/macro tracking feature, run this SQL:

```sql
-- See backend/migrations/003_nutrition_tables.sql for the full migration
-- This creates:
--   - foods: Food items with nutritional info (global + user custom)
--   - food_entries: User's meal log entries
--   - nutrition_goals: User's daily macro targets
-- Plus RLS policies for all tables
```

Run the migration file: `backend/migrations/003_nutrition_tables.sql`

## 1.5. Whoop Developer Setup (Optional)

To connect your Whoop account and pull fitness data:

### Register Your App

1. Go to [developer.whoop.com](https://developer.whoop.com)
2. Create a new application
3. Set the redirect URI to: `http://localhost:8000/api/v1/whoop/callback`
4. Note your Client ID and Client Secret

### Generate Encryption Key

Whoop OAuth tokens are encrypted at rest. Generate a Fernet encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Add to Environment

Add these variables to your `backend/.env`:

```env
WHOOP_CLIENT_ID=your-client-id
WHOOP_CLIENT_SECRET=your-client-secret
WHOOP_REDIRECT_URI=http://localhost:8000/api/v1/whoop/callback
ENCRYPTION_KEY=your-fernet-key-from-above
```

## 1.6. USDA Food Database Setup (Optional)

To enable searching the USDA FoodData Central database for foods:

### Get API Key

1. Go to [fdc.nal.usda.gov/api-key-signup.html](https://fdc.nal.usda.gov/api-key-signup.html)
2. Fill out the form to request a free API key
3. You'll receive the key via email

### Add to Environment

Add this variable to your `backend/.env`:

```env
USDA_API_KEY=your-usda-api-key
```

The USDA integration provides:
- Search across Foundation, SR Legacy (basic foods) and Branded products
- Automatic import of USDA foods into your personal database
- Nutritional data including calories, protein, carbs, fat, and fiber

## 1.7. AWS Bedrock Setup (AI Health Assistant)

The AI Health Assistant uses AWS Bedrock with Claude models. Follow these steps:

### Create IAM User

1. Go to AWS Console → IAM → Users → Create user
2. Name it something like `bedrock-user`
3. Select **Attach policies directly**
4. Create and attach this custom policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "aws-marketplace:ViewSubscriptions",
                "aws-marketplace:Subscribe"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/*",
                "arn:aws:bedrock:*:*:inference-profile/*"
            ]
        }
    ]
}
```

5. Create access keys: Security credentials → Create access key → Application running outside AWS

### Submit Anthropic Use Case Form

1. Go to AWS Console → Amazon Bedrock → Model catalog
2. Search for "Claude" and select a model (e.g., Claude 3.5 Haiku)
3. Click "Open in playground" or try to invoke
4. Complete the Anthropic use case form when prompted
5. Access is typically granted immediately after form submission

### Add to Environment

Add these variables to your `backend/.env`:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-haiku-20241022-v1:0
```

**Important**: Use the inference profile model ID (note the `us.` prefix) for Claude 3.5 models.

### Run Agent Tables Migration

Run the migration file `backend/migrations/004_agent_tables.sql` in Supabase SQL Editor:

```sql
-- See backend/migrations/004_agent_tables.sql for the full migration
-- This creates:
--   - agent_conversations: Chat conversations
--   - agent_messages: Individual messages
-- Plus RLS policies for all tables
```

---

## 2. Development Setup

### Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your Supabase credentials
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your-anon-key
# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
# SECRET_KEY=generate-a-random-secret-key

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

### Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env
# VITE_API_URL=/api/v1   (same-origin; Vite proxy forwards to localhost:8000)

# Start development server
npm run dev
```

The app will be available at http://localhost:5173

## 3. Production Deployment (Docker)

### Configure Environment

```bash
# In project root
cp .env.example .env

# Edit .env with production values
nano .env
```

Required environment variables:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SECRET_KEY=your-secure-random-secret-key
```

### Build and Run

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services

- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 4. Testing

### Backend

```bash
cd backend
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Frontend

```bash
cd frontend

# Run tests (if configured)
npm test

# Type check
npm run typecheck

# Lint
npm run lint
```

## 5. Troubleshooting

### Common Issues

**CORS Errors**
- Ensure `CORS_ORIGINS` in backend `.env` includes your frontend URL
- Check that the frontend is making requests to the correct API URL

**Token Errors**
- Refresh tokens are stored as httpOnly cookies — they are not visible in JavaScript or localStorage
- To debug: Check DevTools → Application → Cookies for the `refresh_token` cookie on `/api/v1/auth` path
- Access tokens are in memory only and lost on page refresh (re-acquired via `/auth/refresh` cookie)
- Check that Supabase credentials are correct
- Verify the backend can reach Supabase (network/firewall)

**Database Errors**
- Ensure the SQL migration ran successfully
- Check RLS policies are configured correctly
- Verify the service role key has admin access

**AI Assistant Errors**
- `AccessDeniedException`: Check IAM policy includes both `foundation-model/*` and `inference-profile/*` resources
- `ResourceNotFoundException` / Use case form required: Submit Anthropic use case form in Bedrock console
- `ValidationException` about inference profiles: Use model ID with `us.` prefix (e.g., `us.anthropic.claude-3-5-haiku-20241022-v1:0`)
- No health data in AI responses: Ensure Whoop is connected and has synced data

### Logs

**Backend Logs**
```bash
# Development
uvicorn app.main:app --reload --log-level debug

# Docker
docker-compose logs -f backend
```

**Frontend Logs**
- Check browser developer console (F12)
- Network tab shows API requests/responses
