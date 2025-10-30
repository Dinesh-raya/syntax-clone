# PySynthax Full — Developer Mode (Live DSP)

This package runs a PyScript-based synth in developer mode with full diagnostics (HUD, FPS, CPU estimate).

## How to run

### Linux / macOS
Make the script executable and run:
```bash
chmod +x run.sh
./run.sh
```
This will start a local HTTP server at port 8000 and open your browser.

### Windows
Run:
```
run.bat
```
It will open your default browser and start a local server.

Alternatively, serve the folder with Python manually:
```bash
python -m http.server 8000
```
Then open `http://localhost:8000`.

## Notes
- Use Chrome or Edge for best compatibility.
- Click "Unlock Audio" once to enable audio.
- Toggle the HUD overlay with `Shift + D`.
- Live DSP uses WebAudio OscillatorNodes controlled from Python (via PyScript).
