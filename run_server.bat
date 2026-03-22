@echo off
set PYTHONIOENCODING=utf-8
cd /d c:\AI-Tools\POE-Strategies
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
