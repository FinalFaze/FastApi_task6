#!/bin/sh
set -e

python - <<'PY'
import time
from sqlalchemy import create_engine, text
from app.core import settings

engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True)

for attempt in range(30):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database is ready")
        break
    except Exception as exc:
        print(f"Database is unavailable: {exc}")
        if attempt == 29:
            raise
        time.sleep(2)
PY

alembic upgrade head

exec uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}"
