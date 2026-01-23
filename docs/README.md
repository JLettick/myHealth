# myHealth

A full-stack health tracking web application with user authentication.

## Tech Stack

- **Backend**: Python/FastAPI
- **Frontend**: React/TypeScript/Vite/Tailwind CSS
- **Database**: Supabase (PostgreSQL with built-in auth)
- **Deployment**: Docker/Docker Compose

## Features

- User registration and authentication
- Secure session management with JWT tokens
- Token refresh for seamless user experience
- Protected routes for authenticated users
- Responsive design with Tailwind CSS
- Structured logging for debugging
- Docker containerization for easy deployment

## Project Structure

```
myHealth/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # API endpoints
│   │   ├── core/           # Security, logging, exceptions
│   │   ├── schemas/        # Pydantic models
│   │   ├── services/       # Business logic
│   │   ├── middleware/     # CORS, logging middleware
│   │   ├── config.py       # Configuration
│   │   ├── dependencies.py # Auth dependencies
│   │   └── main.py         # Application entry
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── components/    # React components
│   │   ├── contexts/      # Auth context
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

## License

MIT
