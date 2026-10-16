# Deploy and Host Reflex with Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template/r64A10?utm_medium=integration&utm_source=button&utm_campaign=reflex)

[Reflex](https://reflex.dev) is an open-source framework for building full-stack web apps in pure Python. You write the UI and the backend logic in Python, and Reflex compiles the frontend to a fast React app. This template deploys a production-ready Reflex app with Postgres and Redis on Railway.

## About Hosting Reflex

A Reflex app has two parts: a static frontend (HTML, CSS, and JavaScript) and a Python backend that keeps a WebSocket open to every browser session. This template builds the frontend once, when the image is built, so deploys, restarts and new replicas start in seconds without compiling anything. At runtime the **Reflex** service serves everything on one port: Caddy serves the prebuilt frontend and forwards backend routes to the Reflex backend in the same container. **Postgres** stores application data and **Redis** stores session state, each as its own Railway service, so you can add Reflex replicas. Database migrations run once per deploy, before the new version takes traffic.

## Common Use Cases

- Internal tools and admin dashboards built entirely in Python
- Data and AI apps (chat interfaces, model playgrounds, analytics) with a real database
- Customer-facing SaaS products and portals
- Prototypes that need to grow into production apps without a rewrite

## Dependencies for Reflex Hosting

- Python 3.11+ and [Reflex](https://reflex.dev) 0.10
- [Postgres](https://www.postgresql.org) for application data, accessed with [SQLModel](https://sqlmodel.tiangolo.com) and migrated with [Alembic](https://alembic.sqlalchemy.org)
- [Redis](https://redis.io) for shared session state
- [Caddy](https://caddyserver.com) for static file serving and reverse proxying

### Deployment Dependencies

- [Reflex self-hosting guide](https://reflex.dev/docs/hosting/self-hosting/)
- [Reflex database docs](https://reflex.dev/docs/database/overview/)
- [Railway private networking](https://docs.railway.com/networking/private-networking)
- [Railway pre-deploy command](https://docs.railway.com/deployments/pre-deploy-command)

### Implementation Details

```
           Internet (HTTPS, Railway edge)
                        │
        ┌───────────────▼────────────────┐
        │ Reflex service  (port $PORT)    │
        │                                 │
        │  Caddy ── static frontend,      │  built at image build time
        │    │      precompressed, cached │
        │    │ /_event /ping /_health     │
        │    ▼ /_upload                   │
        │  Reflex backend (127.0.0.1)     │  Granian workers
        └───────┬─────────────────┬───────┘
     private net│                 │private net
        ┌───────▼──────┐   ┌──────▼────────┐
        │   Postgres   │   │     Redis     │
        │  (app data)  │   │ (state store) │
        └──────────────┘   └───────────────┘
```

| Service  | Source | Public | Health check | Notes |
|----------|--------|--------|--------------|-------|
| Reflex   | `Dockerfile` | Yes | `/_health` | Pre-deploy runs `alembic upgrade head`. `/_health` returns 503 until Postgres and Redis are reachable, so a deploy goes live only when it can serve traffic. |
| Postgres | Railway Postgres | No | n/a | Persistent volume. Referenced as `${{Postgres.DATABASE_URL}}`. |
| Redis    | Railway Redis | No | n/a | Persistent volume, password protected. Referenced as `${{Redis.REDIS_URL}}`. |

Reflex service variables:

| Variable | Value | Purpose |
|----------|-------|---------|
| `PORT` | `8080` | Public port. Railway routes the domain here. |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | Private Postgres connection. `rxconfig.py` selects the psycopg driver. |
| `REFLEX_REDIS_URL` | `${{Redis.REDIS_URL}}` | Private Redis connection for session state. |
| `GRANIAN_WORKERS` | `2` | Backend worker processes per replica. Raise it for larger instances, or add replicas. |

How the container runs:

- `Dockerfile` runs `reflex export --frontend-only` in a build stage. The runtime image has the prebuilt frontend, the Python environment and Caddy, but no bun or `node_modules`.
- `start.sh` starts Caddy on `$PORT` and `reflex run --env prod --backend-only` on `127.0.0.1:8000`. If either process exits, the container exits and Railway restarts it.
- The page and the backend share one origin, so no `REFLEX_API_URL` or CORS setup is needed.

#### Deploy from a GitHub repo instead of the template

Deploying this repo directly creates only the Reflex service, with no database, no migration step and no health check. Railway does not read service settings from the repo, so without Postgres the app falls back to SQLite, no tables exist, and signing the guestbook fails with "An error occurred". Finish the setup in the project:

1. Add **Database → PostgreSQL** and **Database → Redis**. Name them `Postgres` and `Redis`.
2. On the Reflex service, set the variables from the table above.
3. In the service settings, set the pre-deploy command to `alembic upgrade head` and the health check path to `/_health`.
4. Trigger a new deployment (push a commit or click Deploy). The pre-deploy log shows the migration running, and `/_health` returns `{"status":true,"db":true,"redis":true}`.

For a new project, `.railway/railway.ts` applies all of this in one step (see Infrastructure as Code below).

#### Build your own app

The included guestbook (`app/app.py`, `app/models.py`) shows the full loop: a form writes to Postgres, and the list reloads from it. Replace it with your own pages and models.

1. Change your models in `app/models.py` (any `SQLModel` table defined or imported there is picked up).
2. Generate a migration and review it:

   ```bash
   alembic revision --autogenerate -m "describe the change"
   ```

3. Commit and push. Railway rebuilds the image, the pre-deploy step applies the migration, and the new version goes live once `/_health` passes.

If your app adds backend API routes (for example with `api_transformer`), add their paths to the `@backend` matcher in `Caddyfile`. Changes to pages or styles take effect on the next deploy, because the frontend is built into the image.

#### Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head   # creates reflex.db (SQLite) unless DATABASE_URL is set
reflex run
```

To use Postgres and Redis locally, export the variables from `.env.example` first.

#### Scale

- **More traffic:** add replicas of the Reflex service. Redis holds the session state, so any replica can serve any session, and Railway's edge spreads connections across replicas.
- **Bigger replicas:** raise `GRANIAN_WORKERS` and the service's memory.
- **Uploads:** `rx.upload` writes to the container filesystem by default, which is not shared between replicas. Store uploads in a [Railway Bucket](https://docs.railway.com/storage-buckets) or other object storage.

#### Infrastructure as Code

`.railway/railway.ts` describes the same three services with Railway's [Infrastructure as Code](https://docs.railway.com/infrastructure-as-code). To manage your own project from code, set `REPO` to your fork, then run `cd .railway && npm install && railway config plan`.

### Why Deploy Reflex on Railway?

Railway is a singular platform to deploy your infrastructure stack. Railway will host your infrastructure so you don't have to deal with configuration, while allowing you to vertically and horizontally scale it.

By deploying Reflex on Railway, you are one step closer to supporting a complete full-stack application with minimal burden. Host your servers, databases, AI agents, and more on Railway.
