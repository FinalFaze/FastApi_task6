

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .

cp .env.example .env

uvicorn app.main:app --reload
```

Swagger: http://127.0.0.1:8000/docs

Все под `/api/v1`:
- `GET/POST/PUT/DELETE /categories`
- `GET/POST/PUT/DELETE /locations`
- `GET/POST/PUT/DELETE /posts`
- `GET/POST/PUT/DELETE /comments`
- `GET/POST/PUT/DELETE /users`
- `GET /health`
