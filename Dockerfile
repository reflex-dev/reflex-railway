# Reflex app service: one container, one public port ($PORT).
# The frontend is compiled and built here, at image build time, so starting a
# container (deploy, restart, new replica) never compiles or builds anything.
FROM python:3.13-slim AS builder

# uv installs python packages; Reflex uses the bun on PATH to build the frontend.
COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /bin/uv
COPY --from=oven/bun:1 /usr/local/bin/bun /usr/local/bin/bun
ENV UV_COMPILE_BYTECODE=1 UV_NO_CACHE=1 PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install requirements before copying the app so code edits reuse this layer.
COPY requirements.txt .
RUN uv venv && uv pip install -r requirements.txt

COPY . .
# The page and its backend share an origin (Caddy proxies backend routes), so
# no REFLEX_API_URL is needed.
RUN reflex export --frontend-only --no-zip


# Runtime image: python environment, app source, prebuilt frontend and Caddy.
# No bun, node_modules or build tooling.
FROM python:3.13-slim

COPY --from=caddy:2 /usr/bin/caddy /usr/bin/caddy
# The Reflex version is pinned in the image, so skip the PyPI "newer version"
# lookup that would otherwise delay every start.
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PORT=8080 \
    REFLEX_BACKEND_HOST=127.0.0.1 REFLEX_BACKEND_PORT=8000 \
    REFLEX_CHECK_LATEST_VERSION=false

WORKDIR /app
# The app user owns /app so Reflex can write its runtime files there; Caddy
# keeps its state under $HOME, which is also /app.
RUN adduser --disabled-password --gecos "" --home /app reflex && chown reflex /app
COPY --chown=reflex --from=builder /app/.venv .venv
# .web/backend lets the backend start without evaluating static pages.
COPY --chown=reflex --from=builder /app/.web/backend .web/backend
COPY --from=builder /app/.web/build/client /srv
COPY --chown=reflex . .
USER reflex

EXPOSE 8080
# Migrations run once per deploy in Railway's pre-deploy step
# (`alembic upgrade head`), not on every replica start.
CMD ["./start.sh"]
