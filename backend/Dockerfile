FROM python:3.12-slim

WORKDIR /app

# System deps for argon2-cffi / asyncpg builds.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the whole project first: the editable/source build needs the `app` package
# present, and Alembic needs its migrations available at runtime.
COPY . .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

EXPOSE 8000
# Apply migrations, then serve. Network isolation is enforced upstream (Tailscale /
# unpublished port), not by binding to a specific interface.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
