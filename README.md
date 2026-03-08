# NewsWatcher, Nova Edition

Following the news in the modern age is extremely hard, especially when you need to watch for something specific and no single outlet gives you the full picture. With the power of Amazon Nova AI, NewsWatcher lets you create your own personalised newspaper — a live front page that shows exactly what matters to you. There's nothing better than a front page to get the whole picture in seconds: one glance and you know what's happening.

---

## How it works

### 1. Create a task

A **task** is your definition of what's newsworthy. Give it a name and write a prompt in plain English — e.g. *"Find articles about geopolitical tensions in the Middle East"* or *"Track any news related to AI regulation in the EU"*. You can have as many tasks as you like, each with its own lens on the world. Provide examples of relevant on non-relevant subjects. 

### 2. Add sources

Attach **news sources** to each task. NewsWatcher supports two types:

- **RSS feeds** — any standard RSS or Atom URL (news sites, blogs, agency wires)
- **Telegram channels** — real-time monitoring of public Telegram channels

The same source can feed multiple tasks, and each task can pull from as many sources as you need. 

### 3. Let the AI do the reading

NewsWatcher continuously fetches new items from all your sources. Every article and message is passed to **Amazon Nova** (via AWS Bedrock) along with your task prompt. Nova decides whether each item matches — and writes a clean headline and summary for the ones that do.

### 4. Read your front page

Each task gets its own **newspaper front page** — a live, auto-curated layout that looks like a real newspaper. The most important story gets the top spot. Less urgent items are grouped below. The page stays fresh: old stories drop off, duplicates are merged, and the layout is rebalanced as new items arrive.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript, Chakra UI, RTK Query, Vite |
| Backend | FastAPI (async), SQLAlchemy 2, Alembic, fastapi-users |
| Database | PostgreSQL 16 |
| AI | Amazon Nova Lite via AWS Bedrock |
| News fetching | feedparser (RSS), Telethon (Telegram) |
| Scheduling | APScheduler (AsyncIO) |
| Infrastructure | Docker Compose, nginx |
| Package manager | uv (Python), npm (Node) |

---

## Getting started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- An AWS account with Bedrock enabled and access to the `amazon.nova-lite-v1:0` model in your chosen region

### 1. Clone the repo

```bash
git clone <repository-url>
cd watcher-amazon
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

```env
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=newswatcher
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/newswatcher

# Backend
SECRET_KEY=change-me-to-a-random-string-of-at-least-32-chars
BACKEND_CORS_ORIGINS=["http://localhost"]
ENVIRONMENT=development
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Amazon Bedrock (required for AI filtering)
BACKEND_AWS_ACCESS_KEY=your-aws-access-key-id
BACKEND_AWS_SECRET_KEY=your-aws-secret-access-key
BACKEND_AWS_REGION=us-east-1

# Telegram (optional — only needed if you want Telegram channel sources)
BACKEND_TG_API_ID=your-telegram-api-id
BACKEND_TG_API_HASH=your-telegram-api-hash
BACKEND_TG_SESSION_STRING=your-telegram-session-string

# Frontend
VITE_API_URL=http://localhost/api
```

### 3. Start the app

```bash
make dev
```

This builds all containers, runs database migrations, and starts everything. Once it's up:

| Service | URL |
|---|---|
| App | http://localhost |
| API docs (Swagger) | http://localhost/docs |
| Backend API | http://localhost/api |

### 4. Create a user

```bash
make test-user
# Creates: test@example.com / password123
```

Or register directly in the app at `/signup`.

---

## Make commands

### Running the app

```bash
make dev          # Start all services (build if needed)
make down         # Stop all services
make restart      # Restart services
make clean        # Stop and remove containers + volumes
make rebuild      # Clean + full rebuild from scratch
make status       # Show container status
make logs         # Tail all logs
make logs-backend # Tail backend logs only
make logs-frontend# Tail frontend logs only
```

### Database

```bash
make db-shell             # Open PostgreSQL shell
make backend-shell        # Open backend container shell
make migrate-create MSG="describe your change"  # Create a migration
make migrate-upgrade      # Apply pending migrations
make migrate-downgrade    # Rollback last migration
make migrate-history      # Show migration history
make migrate-current      # Show current revision
```

### Testing & linting

```bash
make test                        # Run all tests
make test-unit FILE=tests/foo.py # Run a specific test file
make test-coverage               # Run tests with coverage report
make lint                        # Run ruff linter with autofix
```

> **Note:** Tests require a `newswatcher_test` database. Create it once with:
> ```bash
> make db-shell
> # then in psql:
> CREATE DATABASE newswatcher_test;
> ```

---

## Production

```bash
cp .env.example .env
# Set POSTGRES_PASSWORD, SECRET_KEY, BACKEND_CORS_ORIGINS, ENVIRONMENT=production
docker-compose -f docker-compose.prod.yml up --build -d
```

---

## Project structure

```
watcher-amazon/
├── backend/
│   ├── app/
│   │   ├── ai/               # Amazon Nova client + AI consumer
│   │   ├── api/              # FastAPI route handlers
│   │   ├── core/             # Config, auth, users
│   │   ├── db/               # Database setup & session
│   │   ├── delivery/         # Newspaper processor
│   │   ├── models/           # SQLAlchemy models
│   │   ├── producers/        # RSS + Telegram feed fetchers
│   │   └── schemas/          # Pydantic schemas
│   ├── alembic/              # Database migrations
│   ├── tests/                # pytest test suite
│   └── pyproject.toml        # Python dependencies (uv)
├── frontend/
│   └── src/
│       ├── components/       # Shared UI components
│       ├── features/         # Feature modules (auth, tasks, etc.)
│       └── services/         # RTK Query API client
├── nginx/                    # Reverse proxy config
├── docker/                   # Docker init scripts
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── Makefile
└── .env.example
```

---

## License

MIT
