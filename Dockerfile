# jacket-masters — Single-container deploy (Render / Railway / self-hosted)
#
# One container: FastAPI (starlette StaticFiles) serves the static site
# (index.html, css/, js/) AND the two API endpoints (/api/product, /api/newsletter).
# SQLite lives inside the container image, so there is nothing to mount at runtime.
# The DB is seeded at build time so the app is immediately usable.

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# --- runtime deps (Python) ---
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# --- project + seed DB at build time (local dev / Render) ---
COPY . /app

RUN python db/init_db.py --db db/jacket-masters.db --seed

# --- production entry ---
ENV PORT=8000
EXPOSE 8000

# uvicorn binds to $PORT (set by Render / Railway, default 8000)
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}"]
