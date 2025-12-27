# Bloomed Terminal – Usage

## Setup (Windows)
1. `python -m venv .venv && .venv\Scripts\activate`
2. `pip install -r requirements.txt`
3. Set `ANTHROPIC_API_KEY` in `.env` (copy from `.env.example`).

## Run API
`uvicorn app.server:app --host 0.0.0.0 --port 8000`

## Quick tests
- Generate: `python scripts\quick_local.py`
- API ping: `python scripts\client_demo.py`
- Model info: `scripts\curl_model_info.bat`
- Tests: `scripts\run_tests.bat`

## Persona style
Outputs default to a blended “house voice” via a system prompt (see `app/personalities.py`). Provide your own `system` message in `messages` to override.

## Change model
Edit `.env` (copy from `.env.example`) and set `ANTHROPIC_MODEL` to a supported Claude model.
