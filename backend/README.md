# TaskLedger Backend

FastAPI + PydanticAI backend for the TaskLedger meeting-to-action agent system.

## Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

4. **Run the server:**
   ```bash
   python main.py
   # Or with uvicorn directly:
   uvicorn main:app --reload
   ```

## API Endpoints

- `GET /` - Root health check
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with dependencies
- `GET /docs` - Interactive API documentation (Swagger)
- `GET /redoc` - Alternative API documentation

## Architecture

```
backend/
├── main.py           # FastAPI app & endpoints
├── config.py         # Environment configuration
├── logger.py         # Structured logging
├── requirements.txt  # Python dependencies
└── .env             # Environment variables (not in git)
```

## Development

Server runs on `http://localhost:8000` with auto-reload enabled.

Access interactive docs at `http://localhost:8000/docs`
