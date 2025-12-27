@echo off
setlocal

if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate

pip install -r requirements.txt

set "HOST=0.0.0.0"
set "PORT=8000"
uvicorn app.server:app --host %HOST% --port %PORT% --reload
