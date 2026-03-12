# Personal Goals Tracking System

A modular Python automation system for personal productivity — tracks opportunities, sends daily focus reminders, and delivers weekly review reports via **Telegram**, backed by **PostgreSQL (Supabase)**.

---

## Features

| Feature                | Description                                            |
|------------------------|--------------------------------------------------------|
| Opportunity logging    | DB-level deduplication via `UNIQUE(url)` + `ON CONFLICT` |
| Daily reminder         | Sent every day at 09:00 via Telegram                   |
| Daily digest           | Sent every evening at 20:00 with today's opportunities |
| Weekly review          | Sent every Friday at 18:00 with stats + productivity score |
| `/today` command       | Daily productivity dashboard                           |
| `/progress` command    | Monthly opportunity stats                              |
| `/dashboard` command   | Weekly snapshot with contact rate                      |
| `/outreach` command    | Outreach pipeline breakdown                            |
| `/health` command      | System health: DB, scheduler, metrics                  |
| Data cleanup           | Auto-deletes opportunities older than 180 days         |
| In-memory caching      | 5-minute TTL cache for analytics queries               |
| Rate limiting          | Per-user sliding-window command throttling              |
| Owner-only auth        | Commands restricted to configured chat ID              |
| Secret redaction       | Sensitive values masked in log output                  |
| CLI utility            | `python cli.py stats|opportunities|outreach|health|cleanup` |

---

## Project Structure

```
project_root/
├── bot/
│   ├── telegram_bot.py    # Bot setup, command handlers, send_message
│   ├── analytics.py       # Opportunity analytics layer
│   ├── reminders.py       # Daily reminder logic
│   ├── reports.py         # Weekly review logic
│   └── digest.py          # Daily digest logic
├── db/
│   ├── database.py        # Connection manager (get_cursor context manager)
│   ├── queries.py         # Thin wrappers delegating to repository
│   ├── repository.py      # Centralised SQL — OpportunityRepository, OutreachRepository
│   └── migrations.sql     # Indexes, unique constraints
├── automation/
│   ├── scheduler.py       # APScheduler setup (reads task registry)
│   └── tasks.py           # Centralised task registry (all scheduled jobs)
├── security/
│   ├── auth.py            # @owner_only decorator
│   ├── rate_limiter.py    # Sliding-window rate limiter
│   ├── api_middleware.py   # Optional FastAPI API-key middleware
│   └── https_enforcement.py # Optional HTTPS middleware
├── utils/
│   ├── logger.py          # Structured logging setup
│   ├── sanitizer.py       # Secret-redacting log filter
│   ├── metrics.py         # In-memory runtime counters
│   ├── cache.py           # TTL in-memory cache + @timed_cache decorator
│   └── retry.py           # @with_retry exponential backoff decorator
├── config.py              # Environment-based configuration + validation
├── main.py                # Single entry point (bot + scheduler)
├── cli.py                 # CLI utility
├── security_check.py      # Dependency vulnerability scanner
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## Prerequisites

- **Python 3.11+**
- **PostgreSQL** database (Supabase or self-hosted) with the following tables:

```sql
CREATE TABLE opportunities (
    id         UUID PRIMARY KEY,
    source     TEXT,
    title      TEXT,
    url        TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    contacted  BOOLEAN DEFAULT FALSE
);

CREATE TABLE outreach_targets (
    id         UUID PRIMARY KEY,
    name       TEXT,
    company    TEXT,
    contact    TEXT,
    status     TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

Then apply the performance migrations:

```bash
psql "$DATABASE_URL" -f db/migrations.sql
```

- A **Telegram bot token** (create one via [@BotFather](https://t.me/BotFather))
- Your **Telegram chat ID** (send a message to your bot, then check `https://api.telegram.org/bot<TOKEN>/getUpdates`)

---

## Setup

### 1. Clone & enter the project

```bash
git clone https://github.com/oleksandrpechak/Personal_goals_tracking_system.git
cd Personal_goals_tracking_system
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your real values
```

### 5. Run the system

```bash
python main.py
```

The bot starts polling Telegram for commands, and the scheduler fires all registered tasks automatically.

---

## Usage

### Telegram Commands

| Command      | Description                          |
|--------------|--------------------------------------|
| `/start`     | Welcome message & help               |
| `/today`     | Daily productivity dashboard         |
| `/progress`  | Monthly opportunity stats            |
| `/dashboard` | Weekly snapshot with contact rate    |
| `/outreach`  | Outreach pipeline breakdown          |
| `/health`    | System health check                  |
| `/help`      | List available commands              |

### CLI

```bash
python cli.py stats          # weekly + monthly stats
python cli.py opportunities  # today's opportunities
python cli.py outreach       # outreach pipeline
python cli.py health         # system health snapshot
python cli.py cleanup        # delete opportunities older than 180 days
```

### Programmatic Opportunity Logging

```python
from db.queries import log_opportunity

log_opportunity(
    title="Senior Backend Engineer at Acme",
    url="https://example.com/job/123",
    source="LinkedIn",
)
```

---

## Scheduled Tasks

All tasks are registered in `automation/tasks.py` and driven by APScheduler:

| Task             | Schedule             | Description                           |
|------------------|----------------------|---------------------------------------|
| daily_reminder   | Every day 09:00      | Focus reminder via Telegram           |
| daily_digest     | Every day 20:00      | Today's opportunities summary         |
| weekly_review    | Friday 18:00         | Weekly stats + productivity score     |
| data_cleanup     | Sunday 03:00         | Delete opportunities older than 180d  |

---

## Environment Variables

| Variable               | Required | Default | Description                        |
|------------------------|----------|---------|------------------------------------|
| `TELEGRAM_BOT_TOKEN`   | ✅       |         | Bot token from BotFather           |
| `TELEGRAM_CHAT_ID`     | ✅       |         | Your personal chat ID              |
| `DATABASE_URL`         | ✅       |         | PostgreSQL connection string       |
| `API_SECRET_KEY`       | ✅       |         | Secret for API middleware          |
| `DEBUG`                | ❌       | `false` | Enable debug mode                  |
| `LOG_LEVEL`            | ❌       | `INFO`  | Logging level                      |
| `DAILY_REMINDER_HOUR`  | ❌       | `9`     | Hour for daily reminder (0-23)     |
| `DAILY_REMINDER_MINUTE`| ❌       | `0`     | Minute for daily reminder          |
| `DAILY_DIGEST_HOUR`    | ❌       | `20`    | Hour for daily digest              |
| `DAILY_DIGEST_MINUTE`  | ❌       | `0`     | Minute for daily digest            |
| `WEEKLY_REVIEW_DAY`    | ❌       | `fri`   | Day of week for weekly review      |
| `WEEKLY_REVIEW_HOUR`   | ❌       | `18`    | Hour for weekly review             |
| `WEEKLY_REVIEW_MINUTE` | ❌       | `0`     | Minute for weekly review           |

---

## Security

Run the dependency vulnerability scanner:

```bash
python security_check.py
```

Requires `pip-audit` (included in `requirements.txt`).

---

## Architecture Decisions

- **Single process** — bot + scheduler run in one `main.py` process (no Celery, Redis, or microservices)
- **Task registry** — all scheduled jobs defined in `automation/tasks.py`
- **Repository pattern** — all SQL centralised in `db/repository.py`
- **In-memory caching** — 5-minute TTL for analytics (no external cache)
- **Parameterised SQL** — all queries use `%s` placeholders (no string interpolation)
- **Secret redaction** — log filter masks tokens and credentials automatically

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
