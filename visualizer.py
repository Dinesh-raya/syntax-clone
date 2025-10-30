# visualizer.py - draws both waveform and frequency spectrum. reports FPS to HUD
from js import document, window, console, Uint8Array
from pyodide.ffi import to_js
import time

canvas = document.getElementById('vis')
ctx = canvas.getContext('2d')

last_time = None
frames = 0
fps = 0

def draw(_=None):
    global last_time, frames, fps
    analyser = getattr(window, 'pysx_analyser', None)
    if analyser:
        try:
            # waveform (time domain)
            wave_buf = Uint8Array.new(analyser.fftSize)
            analyser.getByteTimeDomainData(wave_buf)
            width = canvas.width
            height = canvas.height
            ctx.fillStyle = 'rgba(2,6,23,0.25)'
            ctx.fillRect(0,0,width,height)
            # waveform path
            ctx.beginPath()
            slice_w = width / wave_buf.length
            x = 0
            for i in range(wave_buf.length):
                v = wave_buf[i] / 128.0
                y = v * height / 2
                if i == 0:
                    ctx.moveTo(x, y)
                else:
                    ctx.lineTo(x, y)
                x += slice_w
            ctx.strokeStyle = 'rgba(124,58,237,0.9)'
            ctx.lineWidth = 2
            ctx.stroke()

            # frequency bars
            freq_buf = Uint8Array.new(analyser.frequencyBinCount)
            analyser.getByteFrequencyData(freq_buf)
            bar_w = width / freq_buf.length * 1.6
            bx = 0
            for i in range(freq_buf.length):
                v = freq_buf[i] / 255.0
                h = v * (height/2)
                ctx.fillStyle = f'rgba({int(200*v)},{int(120+100*v)},{int(255-200*v)},0.85)'
                ctx.fillRect(bx, height - h, bar_w, h)
                bx += bar_w + 1

            # FPS calc
            now = performance.now()
            if last_time is None:
                last_time = now
            frames += 1
            if now - last_time >= 1000:
                fps = frames
                frames = 0
                last_time = now
                # update HUD
                hud_el = document.getElementById('hud-fps')
                if hud_el:
                    hud_el.innerText = f'FPS: {fps}'
        except Exception as e:
            pass
    window.requestAnimationFrame(to_js(lambda ts: draw(ts)))

draw()
