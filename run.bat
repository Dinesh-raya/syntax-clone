@echo off
REM Run a local HTTP server and open default browser (Windows)
start "" "http://localhost:8000"
python -m http.server 8000
