# synth.py - main synth logic for the PyScript Synthax clone
from js import document, window, console, Uint8Array, Blob, URL, navigator
from pyodide.ffi import to_js
import json

# === state ===
audio_ctx = None
master = None
analyser = None
master_gain_node = None

VOICE_POOL_SIZE = 10
voice_pool = []
sample_buffer = None

seq = [[False]*4, [False]*4]
seq_running = False
seq_timer = None
seq_pos = 0

def el(id): return document.getElementById(id)

def ensure_audio():
    global audio_ctx, master, analyser, master_gain_node, voice_pool
    if audio_ctx is None:
        AudioContext = window.AudioContext if hasattr(window, "AudioContext") else window.webkitAudioContext
        audio_ctx = AudioContext.new()
        master_gain_node = audio_ctx.createGain()
        master_gain_node.gain.value = float(el("gain").value)
        master_gain_node.connect(audio_ctx.destination)
        analyser = audio_ctx.createAnalyser()
        analyser.fftSize = 512
        master_gain_node.connect(analyser)
        # expose analyser for visualizer module
        window.pysx_analyser = analyser
        master = master_gain_node
        for i in range(VOICE_POOL_SIZE):
            voice_pool.append({"osc": None, "gain": None, "in_use": False})
        console.log("Audio context initialized (synth.py)")

def unlock_audio(ev=None):
    ensure_audio()
    if audio_ctx.state == "suspended":
        p = audio_ctx.resume()
        p.then(lambda *_: console.log("Audio resumed")).catch(lambda e: console.log("Audio resume failed", e))

el("unlock").addEventListener("click", to_js(lambda ev: unlock_audio(ev)))

def update_master_gain(ev=None):
    ensure_audio()
    val = float(el("gain").value)
    master_gain_node.gain.value = val

el("gain").addEventListener("input", to_js(lambda ev: update_master_gain(ev)))

def get_release():
    try:
        return float(el("release").value)
    except:
        return 0.6

def get_waveform():
    return el("waveform").value

def get_free_voice():
    ensure_audio()
    for v in voice_pool:
        if not v["in_use"]:
            v["in_use"] = True
            if v["gain"] is None:
                v["gain"] = audio_ctx.createGain()
                v["gain"].gain.value = 0.0
                v["gain"].connect(master)
            return v
    v = voice_pool[0]
    return v

def release_voice(v):
    v["in_use"] = False

def note_to_freq(note_index):
    base = 220.0
    return base * (2 ** (note_index / 12.0))

def play_osc(note_index, dur=0.6):
    ensure_audio()
    v = get_free_voice()
    try:
        osc = audio_ctx.createOscillator()
        osc.type = get_waveform()
    except Exception:
        osc = audio_ctx.createOscillator()
        osc.type = "sine"
    freq = note_to_freq(note_index)
    osc.frequency.setValueAtTime(freq, audio_ctx.currentTime)
    g = v["gain"]
    g.gain.cancelScheduledValues(audio_ctx.currentTime)
    g.gain.setValueAtTime(0.0001, audio_ctx.currentTime)
    g.gain.linearRampToValueAtTime(0.8, audio_ctx.currentTime + 0.01)
    release_time = audio_ctx.currentTime + dur
    g.gain.exponentialRampToValueAtTime(0.001, release_time + 0.02)

    osc.connect(g)
    osc.start()
    # schedule stop
    window.setTimeout(to_js(lambda: (osc.stop(), release_voice(v))), int((dur+0.06)*1000))

def play_sample(when=0):
    global sample_buffer
    if not sample_buffer:
        return
    src = audio_ctx.createBufferSource()
    src.buffer = sample_buffer
    g = audio_ctx.createGain()
    g.gain.value = 1.0
    src.connect(g)
    g.connect(master)
    src.start()

def pad_click(ev):
    ensure_audio()
    eln = ev.currentTarget
    ni = int(eln.getAttribute("data-note"))
    if sample_buffer and ni == 0:
        play_sample()
    else:
        play_osc(ni, dur=get_release())

pads = document.querySelectorAll(".pad")
for i in range(pads.length):
    pads.item(i).addEventListener("click", to_js(lambda ev, i=i: pad_click(ev)))

# sequencer
seq_timer = None
seq_pos = 0
def seq_step():
    global seq_pos, seq_timer
    for voice in (0,1):
        if seq[voice][seq_pos]:
            if sample_buffer and voice == 0:
                play_sample()
            else:
                base_note = voice * 3
                play_osc(base_note + seq_pos, dur=get_release())
    seq_pos = (seq_pos + 1) % 4
    bpm = int(el("bpm").value)
    interval = (60.0 / max(30,bpm)) * 1000
    seq_timer = window.setTimeout(to_js(seq_step), int(interval))

def seq_start(ev=None):
    global seq_timer, seq_pos
    if seq_timer:
        return
    ensure_audio()
    seq_pos = 0
    seq_step()
    el("seq-start").disabled = True
    el("seq-stop").disabled = False

def seq_stop(ev=None):
    global seq_timer
    if seq_timer:
        window.clearTimeout(seq_timer)
    seq_timer = None
    el("seq-start").disabled = False
    el("seq-stop").disabled = True

def seq_clear(ev=None):
    for v in range(len(seq)):
        for s in range(len(seq[v])):
            seq[v][s] = False
    render_seq()

el("seq-start").addEventListener("click", to_js(lambda e: seq_start(e)))
el("seq-stop").addEventListener("click", to_js(lambda e: seq_stop(e)))
el("seq-clear").addEventListener("click", to_js(lambda e: seq_clear(e)))
el("seq-stop").disabled = True

def toggle_step(voice, step_idx, ev=None):
    seq[voice][step_idx] = not seq[voice][step_idx]
    render_seq()

def render_seq():
    for v in range(2):
        container = el(f"seq-{v}")
        container.innerHTML = ""
        for i in range(4):
            d = document.createElement("div")
            d.className = "step" + (" on" if seq[v][i] else "")
            d.innerText = str(i+1)
            def make_click(v=v, i=i):
                return to_js(lambda ev: toggle_step(v, i, ev))
            d.addEventListener("click", make_click())
            container.appendChild(d)

render_seq()

# sample upload
def handle_file_upload(ev):
    f = ev.target.files.item(0)
    if not f:
        return
    fr = window.FileReader.new()
    def onload(e):
        # decode audio data
        def on_decoded(buf):
            global sample_buffer
            sample_buffer = buf
            console.log("Sample decoded and ready")
        def on_err(err):
            console.log("Decode error", err)
        audio_ctx.decodeAudioData(fr.result).then(on_decoded).catch(on_err)
    fr.onload = onload
    fr.readAsArrayBuffer(f)

el("sample-file").addEventListener("change", to_js(lambda ev: handle_file_upload(ev)))
el("use-sample").addEventListener("click", to_js(lambda e: console.log('Use sample: pad 1 will play sample if loaded')))

# save/load project
def build_manifest():
    return {
        "seq": seq,
        "bpm": int(el("bpm").value),
        "waveform": get_waveform(),
        "gain": float(el("gain").value),
        "release": get_release()
    }

def download_project(ev=None):
    manifest = build_manifest()
    text = json.dumps(manifest)
    blob = Blob.new([text], {"type":"application/json"})
    url = URL.createObjectURL(blob)
    a = document.createElement("a")
    a.href = url
    a.download = "pysynthax-project.json"
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)

el("download-project").addEventListener("click", to_js(lambda e: download_project(e)))

def upload_project_file(ev):
    f = ev.target.files.item(0)
    if not f:
        return
    fr = window.FileReader.new()
    def onload(e):
        try:
            manifest = json.loads(fr.result)
            apply_manifest(manifest)
            console.log("Project loaded from file")
        except Exception as ex:
            console.log("Failed to parse project file", ex)
    fr.onload = onload
    fr.readAsText(f)

el("upload-project").addEventListener("change", to_js(lambda ev: upload_project_file(ev)))

def apply_manifest(man):
    global seq
    if "seq" in man:
        seq[:] = man["seq"]
        render_seq()
    if "bpm" in man:
        el("bpm").value = man["bpm"]
    if "waveform" in man:
        el("waveform").value = man["waveform"]
    if "gain" in man:
        el("gain").value = str(man["gain"])
        update_master_gain()
    if "release" in man:
        el("release").value = str(man["release"])

def save_local(ev=None):
    manifest = build_manifest()
    window.localStorage.setItem("pysx_project", json.dumps(manifest))
    console.log("Saved to localStorage")

def load_local(ev=None):
    v = window.localStorage.getItem("pysx_project")
    if v:
        try:
            manifest = json.loads(v)
            apply_manifest(manifest)
            console.log("Loaded from localStorage")
        except Exception as e:
            console.log("Failed to load local project", e)
    else:
        console.log("No saved project found")

el("save-local").addEventListener("click", to_js(lambda e: save_local(e)))
el("load-from-local").addEventListener("click", to_js(lambda e: load_local(e)))

# MIDI
def midi_connect(ev=None):
    if not hasattr(navigator, "requestMIDIAccess"):
        console.log("Web MIDI not available")
        return
    def on_midi(midi):
        console.log("MIDI ready", midi)
        for inp in midi.inputs.values():
            def on_msg(event):
                data = event.data
                status = data[0] & 0xf0
                note = data[1]
                vel = data[2] if len(data) > 2 else 0
                if status == 0x90 and vel > 0:
                    pad = (note - 60) % 9
                    if sample_buffer and pad == 0:
                        play_sample()
                    else:
                        play_osc(pad, dur=get_release())
            inp.onmidimessage = to_js(on_msg)
    def on_err(e):
        console.log("MIDI error", e)
    navigator.requestMIDIAccess().then(on_midi).catch(on_err)

el("midi-connect").addEventListener("click", to_js(lambda e: midi_connect(e)))

console.log("synth.py loaded")
