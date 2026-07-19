@echo off
REM ============================================================
REM  Weather Assistant AI — Local Development Server
REM  Starts the ADK web UI at http://127.0.0.1:8000/dev-ui
REM ============================================================

echo.
echo  Starting Weather Assistant AI...
echo  ADK Dev UI will be available at: http://127.0.0.1:8000/dev-ui
echo.

uv run python -m google.adk.cli web . --host 127.0.0.1 --port 8000

pause
