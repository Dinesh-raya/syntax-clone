# PySynthax — PyScript Full Clone

This is a full-featured PyScript-based clone of a synth playground (styled and inspired by thesynthax.space).
It runs completely in the browser with Python (Pyodide) via PyScript.

## Features
- 9 playable pads (oscillator-based voices)
- Waveform selection, master gain, release control
- 4-step sequencer (2 voices)
- Visualizer (real-time frequency bars)
- Sample upload (play on Pad 1)
- Save / Load project (JSON) and localStorage
- MIDI input (if browser supports Web MIDI)

## Run locally
1. Serve the folder over HTTP. Example:

```bash
python -m http.server 8000
```

2. Open `http://localhost:8000` in a modern desktop browser (Chrome/Edge recommended).

> Important: PyScript / Pyodide is large — initial load will take several seconds. For best UX, use a fast connection.

## Notes & next steps
- For production parity with a hand-optimized JS/WebAudio site, consider a JS fallback or hybrid approach (Python for logic + JS for critical audio paths).
- You can customize styles in `styles.css` and extend Python code in `synth.py` / `visualizer.py`.

Enjoy! ⚡
