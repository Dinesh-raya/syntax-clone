# visualizer.py - reads window.pysx_analyser (set by synth.py) and draws to canvas
from js import document, window, console, Uint8Array
from pyodide.ffi import to_js

canvas = document.getElementById("vis")
ctx = canvas.getContext("2d")

def draw(_=None):
    try:
        analyser = getattr(window, "pysx_analyser", None)
        if analyser:
            buf_len = analyser.frequencyBinCount
            data = Uint8Array.new(buf_len)
            analyser.getByteFrequencyData(data)
            width = canvas.width
            height = canvas.height
            ctx.clearRect(0,0,width,height)
            bar_width = width / buf_len * 1.8
            x = 0
            for i in range(buf_len):
                v = data[i] / 255.0
                bar_h = v * height
                r = int(200 * v)
                g = int(120 + 100 * v)
                b = int(255 - 200 * v)
                ctx.fillStyle = f"rgba({r},{g},{b},0.9)"
                ctx.fillRect(x, height-bar_h, bar_width, bar_h)
                x += bar_width + 1
    except Exception as e:
        # ignore until analyser exists
        pass
    window.requestAnimationFrame(to_js(lambda ts: draw(ts)))

draw()
