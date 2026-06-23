# syntax=docker/dockerfile:1

# Stage 1: build the React/Vite frontend. VITE_BACKEND_URL is intentionally
# unset so App.jsx falls back to "" (same-origin) — the backend serves the dist.
FROM node:20-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: runtime. Tag pinned to the backend's playwright==1.55.0 so the
# bundled Chromium (/ms-playwright/chromium-1187) matches the driver. The
# -noble variant ships Python 3.12 (jammy ships 3.10, which fails pyproject's
# requires-python >=3.11). glibc 2.39 still satisfies the github-copilot-sdk
# 1.0.2 manylinux_2_28 wheel.
FROM mcr.microsoft.com/playwright/python:v1.55.0-noble AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

# main.py: _FRONTEND_DIST = Path(main.py).parents[2]/"frontend"/"dist"
# screenshots.py: _STORE_DIR = parents[2]/"screenshots"
# With backend at /app/backend, parents[2] == /app, so dist -> /app/frontend/dist
# and screenshots -> /app/screenshots.
WORKDIR /app/backend

COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install .

COPY --from=frontend /build/frontend/dist /app/frontend/dist

RUN mkdir -p /app/screenshots \
    && chown -R pwuser:pwuser /app

USER pwuser

EXPOSE 8123
ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8123"]
