# myHealth Project Context

**Last Updated**: January 2026

This document provides context for AI agents working on this project. Read this before making changes.

---

## Project Overview

A full-stack health tracking application with:
- **User Authentication** - Email/password via Supabase Auth
- **Whoop Integration** - OAuth connection to sync fitness data (strain, recovery, sleep, workouts)
- **Nutrition Tracker** - Log meals, track macros, view daily/weekly summaries

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, FastAPI, Pydantic v2 |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Database | Supabase (PostgreSQL with RLS) |
| Auth | Supabase Auth with JWT tokens |

---

## Project Structure

```
myHealth/myHealth/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # Route handlers (auth, users, whoop, nutrition)
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/           # Business logic layer
│   │   ├── core/               # Logging, exceptions, encryption
│   │   ├── middleware/         # CORS, logging middleware
│   │   ├── config.py           # Environment settings (Pydantic Settings)
│   │   └── dependencies.py     # FastAPI dependency injection
│   ├── migrations/             # SQL migrations for Supabase
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API client functions
│   │   ├── components/         # React components (common, layout, auth, whoop, nutrition)
│   │   ├── contexts/           # React contexts (AuthContext, WhoopContext, NutritionContext)
│   │   ├── pages/              # Page components (Home, Login, Signup, Dashboard, Nutrition)
│   │   ├── types/              # TypeScript type definitions
│   │   └── utils/              # Utilities (logger, storage)
│   └── package.json
└── docs/                       # Setup and API documentation
```

---

## Key Files to READ for Context

These files demonstrate the established patterns. Read these before implementing new features.

| File | What It Demonstrates |
|------|---------------------|
| `backend/app/api/v1/endpoints/whoop.py` | Endpoint structure, OAuth flow, error handling |
| `backend/app/schemas/whoop.py` | Pydantic schema patterns, validation |
| `backend/app/services/whoop_service.py` | Service layer pattern, Supabase queries |
| `frontend/src/contexts/WhoopContext.tsx` | React context pattern, state management |
| `frontend/src/api/whoop.ts` | Frontend API client pattern |
| `backend/migrations/002_whoop_tables.sql` | Database migration pattern, RLS policies |

---

## Files to SKIP (Standard Boilerplate)

These files follow standard patterns and don't need reading unless modifying them:

- `backend/app/core/logging_config.py` - Standard JSON logging
- `backend/app/middleware/*.py` - CORS and logging middleware
- `frontend/src/utils/*.ts` - Logger and storage utilities
- `frontend/src/components/common/*.tsx` - Button, Input, LoadingSpinner
- `frontend/src/components/layout/*.tsx` - Header, Footer, Layout
- `docs/*.md` - Only read if updating documentation
- `*.lock`, `node_modules/`, `__pycache__/`, `.env`

---

## Database Tables

All tables use UUID primary keys and have RLS (Row Level Security) enabled.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `profiles` | User profiles (extends auth.users) | id, email, full_name |
| `whoop_connections` | OAuth tokens (encrypted) | user_id, access_token_encrypted, token_expires_at |
| `whoop_cycles` | Daily physiological cycles | user_id, whoop_cycle_id, strain_score |
| `whoop_recovery` | Recovery scores | user_id, recovery_score, hrv_rmssd_milli |
| `whoop_sleep` | Sleep sessions | user_id, sleep_score, total_rem_sleep_milli |
| `whoop_workouts` | Workout activities | user_id, sport_name, strain_score |
| `foods` | Food items (global + user custom) | user_id (NULL=global), name, calories, protein_g |
| `food_entries` | User's meal log | user_id, food_id, entry_date, meal_type |
| `nutrition_goals` | Daily macro targets | user_id, calories_target, protein_g_target |

---

## API Routes

| Prefix | Purpose |
|--------|---------|
| `/api/v1/auth/*` | Authentication (signup, login, logout, refresh, me) |
| `/api/v1/users/*` | User profile (get, update, delete) |
| `/api/v1/whoop/*` | Whoop OAuth and data sync |
| `/api/v1/nutrition/*` | Food logging, entries, summaries, goals |

---

## Current State (January 2026)

| Feature | Status | Notes |
|---------|--------|-------|
| Authentication | ✅ Complete | Email/password, JWT refresh |
| Whoop Integration | ✅ Complete | OAuth, syncs cycles/recovery/sleep/workouts |
| Nutrition Tracker | ✅ Complete | Backend + Frontend complete |
| USDA Integration | ✅ Complete | Search USDA foods, import to user's database |

---

## Known Issues & Gotchas

1. **Pydantic Decimal Serialization**
   - Pydantic's `Decimal` type serializes as string in JSON responses
   - Frontend must wrap with `Number()` before calling `.toFixed()` or doing math
   - Example: `Number(value).toFixed(1)` instead of `value.toFixed(1)`

2. **Whoop API v2**
   - Whoop deprecated v1, now uses v2 endpoints
   - v2 uses UUID strings for IDs (not integers)
   - Database columns are TEXT type, not BIGINT

3. **Whoop OAuth Scopes**
   - Must include `offline` scope to get refresh tokens
   - Without it, tokens can't be refreshed and user must reconnect

4. **Sleep Efficiency Column**
   - Changed from DECIMAL(5,4) to DECIMAL(5,2)
   - Whoop returns percentages (e.g., 85.5) not decimals (0.855)

5. **RLS Policies**
   - All tables have Row Level Security enabled
   - Backend uses `admin_client` (service role key) to bypass RLS
   - This allows backend to query on behalf of any user

6. **Timezone Handling**
   - Never use `toISOString()` for dates - it returns UTC which shows wrong date for users behind UTC
   - Use `getLocalDateString()` from `types/nutrition.ts` instead
   - When parsing date strings, add `T12:00:00` suffix to avoid edge cases: `new Date(dateStr + 'T12:00:00')`

7. **Nutrition Goals API**
   - `GET /nutrition/goals` returns 200 with `null` when no goals are set (not 404)
   - Goals are fetched once on mount, not on every date change (they don't vary by date)
   - NutritionContext has separate `refreshGoals()` and `refresh()` functions

---

## Environment Variables

### Backend (`backend/.env`)
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
WHOOP_CLIENT_ID=xxx
WHOOP_CLIENT_SECRET=xxx
WHOOP_REDIRECT_URI=http://localhost:8000/api/v1/whoop/callback
ENCRYPTION_KEY=xxx  # Fernet key for encrypting OAuth tokens
USDA_API_KEY=xxx    # For USDA FoodData Central API
```

### Frontend (`frontend/.env`)
```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Running the Project

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## USDA Food Database Integration (Complete)

The USDA FoodData Central API is integrated:

**Backend:**
- `backend/app/services/usda_service.py` - USDA API client
- `GET /nutrition/foods/usda/search?q=&data_type=` - Search USDA database with optional filter
- `POST /nutrition/foods/usda/import` - Import food to user's database (sends full USDAFoodItem in body)

**Frontend:**
- AddFoodModal supports both "USDA Database" and "My Foods" search
- USDA foods show data type badge (Branded, Foundation, etc.)
- Filter dropdown for data types: "Basic Foods", "Branded Products", "All Foods"
- User can enter amount in grams or servings (toggle between modes)
- Importing a USDA food automatically saves it to user's database

**Setup:**
1. Get API key from https://fdc.nal.usda.gov/api-key-signup.html
2. Add `USDA_API_KEY=xxx` to `backend/.env`

---

## Git Exclusions for Data Loading

The `.gitignore` excludes these paths to keep data loading isolated:
```
backend/scripts/seed_*.py
backend/data/
*.seed.sql
*.seed.json
```

---

## Testing Checklist

When making changes, verify:

1. **Auth Flow**: Signup → Login → Access protected route → Logout
2. **Whoop Flow**: Connect → Sync → View data on dashboard → Disconnect
3. **Nutrition Flow**: Add food → Log entry → View daily summary → Set goals
4. **API Health**: `curl http://localhost:8000/api/v1/health`
