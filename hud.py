# hud.py - periodically updates HUD values (CPU estimate, oscillator type)
from js import document, window, console, performance
from pyodide.ffi import to_js
import time, math

def update_hud_stats():
    try:
        # CPU estimate: simple busy-loop sample skew (cheap heuristic)
        t0 = performance.now()
        # do tiny amount of work
        s = 0
        for i in range(1000):
            s += i*i
        t1 = performance.now()
        elapsed = t1 - t0
        cpu_est = min(100, int(elapsed))
        el = document.getElementById('hud-cpu')
        if el:
            el.innerText = f'CPU est (ms sample): {cpu_est}'
        # oscillator type
        wf = document.getElementById('waveform').value
        el2 = document.getElementById('hud-osc')
        if el2:
            el2.innerText = f'Oscillator: {wf}'
    except Exception as e:
        pass
    # schedule next
    window.setTimeout(to_js(lambda: update_hud_stats()), 1000)

update_hud_stats()
