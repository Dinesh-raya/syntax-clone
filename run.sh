#!/bin/bash
# Run a local HTTP server and open browser (macOS / Linux)
python3 -m http.server 8000 &
SERVER_PID=$!
sleep 0.8
if command -v xdg-open >/dev/null; then
  xdg-open http://localhost:8000
elif command -v open >/dev/null; then
  open http://localhost:8000
else
  echo "Open http://localhost:8000 in your browser"
fi
wait $SERVER_PID
