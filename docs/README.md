# myHealth

A full-stack health tracking web application that aggregates fitness data from multiple sources into one centralized dashboard.

## Tech Stack

- **Backend**: Python/FastAPI
- **Frontend**: React/TypeScript/Vite/Tailwind CSS
- **Database**: Supabase (PostgreSQL with built-in auth)
- **Deployment**: Docker/Docker Compose

## Features

### Core Features
- User registration and authentication
- Secure session management with JWT tokens
- Token refresh for seamless user experience
- Protected routes for authenticated users
- Responsive design with Tailwind CSS
- Structured logging for debugging
- Docker containerization for easy deployment

### Data Sources

#### Whoop Integration
Connect your Whoop account to sync:
- **Recovery**: Daily recovery score, HRV, resting heart rate, SpO2
- **Strain**: Day strain, calories burned, heart rate data
- **Sleep**: Sleep duration, sleep stages, sleep quality score
- **Workouts**: Activity type, strain, heart rate zones, duration

The dashboard displays your latest metrics and 7-day trends.

## Project Structure

```
myHealth/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   │   └── endpoints/
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── health.py
│   │   │       └── whoop.py    # Whoop integration
│   │   ├── core/           # Security, logging, exceptions, encryption
│   │   ├── schemas/        # Pydantic models (auth, user, whoop)
│   │   ├── services/       # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── whoop_client.py     # Whoop API client
│   │   │   ├── whoop_service.py    # OAuth management
│   │   │   └── whoop_sync_service.py
│   │   ├── middleware/     # CORS, logging middleware
│   │   ├── config.py       # Configuration
│   │   ├── dependencies.py # Auth dependencies
│   │   └── main.py         # Application entry
│   ├── migrations/         # SQL migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/           # API client (auth, whoop)
│   │   ├── components/
│   │   │   ├── common/    # Button, Input, etc.
│   │   │   ├── auth/      # LoginForm, ProtectedRoute
│   │   │   ├── layout/    # Header, Footer, Layout
│   │   │   └── whoop/     # Whoop dashboard components
│   │   ├── contexts/      # Auth & Whoop contexts
│   │   ├── pages/         # Page components
│   │   ├── types/         # TypeScript types
│   │   └── utils/         # Utilities
│   ├── Dockerfile
│   └── package.json
│
├── docs/                   # Documentation
├── docker-compose.yml      # Docker orchestration
└── .env.example           # Environment template
```

## Quick Start

See [SETUP.md](./SETUP.md) for detailed setup instructions.

### Development

1. Set up Supabase project and get credentials
2. Copy `.env.example` files and fill in values
3. Start backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
4. Start frontend: `cd frontend && npm install && npm run dev`

### Production (Docker)

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Build and start containers
docker-compose up -d

# View logs
docker-compose logs -f
```

## API Documentation

When running the backend, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

See [API.md](./API.md) for detailed API documentation.

## Security

- Passwords validated for complexity (uppercase, lowercase, digit, special char)
- JWT tokens with short expiration (1 hour)
- Refresh token rotation
- CORS restricted to specific origins
- Row Level Security (RLS) in Supabase
- Input validation with Pydantic
- Non-root Docker containers
- OAuth tokens encrypted at rest (Fernet symmetric encryption)
- CSRF protection for OAuth flows via state parameter

## License

MIT
