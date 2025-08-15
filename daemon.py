import os
import tempfile
import threading
import sounddevice as sd
import soundfile as sf
import keyboard
import tkinter as tk
from tkinter import messagebox
from faster_whisper import WhisperModel
from datetime import datetime

# ------------------------
# Config
# ------------------------
MIC_NAME = None   # e.g., "USB" (substring of device name) or None for default
MODEL_SIZE = "small"
LANGUAGE = "en"
HOTKEY="ctrl+alt+space"

# ------------------------
# Audio helpers
# ------------------------
def list_input_devices():
    devs = sd.query_devices()
    return [(i, d['name']) for i, d in enumerate(devs) if d['max_input_channels'] > 0]

def pick_device(name_substring):
    if not name_substring:
        return None
    name_substring = name_substring.lower()
    for i, name in list_input_devices():
        if name_substring in name.lower():
            return i
    return None

def record_until_key_release(path, hotkey, samplerate=16000, device=None):
    print("Recording")
    sd.default.samplerate = samplerate
    sd.default.channels = 1
    if device is not None:
        sd.default.device = (device, None)

    audio_data = []
    recording_event = threading.Event()

    def _callback(indata, frames, time, status):
        if status:
            print(status)
        if recording_event.is_set():
            audio_data.append(indata.copy())

    # Start stream but don't record until event is set
    with sd.InputStream(callback=_callback):
        recording_event.set()
        # Wait for key release
        print(f"Wait for key {hotkey}")        
        keyboard.wait(hotkey)
        print("Got key")
        recording_event.clear()        

    # Save WAV
    print("Saving WAV")
    import numpy as np
    if audio_data:
        audio_np = np.concatenate(audio_data, axis=0)
        sf.write(path, audio_np, samplerate, subtype="PCM_16")

# ------------------------
# Transcription
# ------------------------
def transcribe_local(wav_path, model_size=MODEL_SIZE, language=LANGUAGE):
    device = "cuda" if os.environ.get("CUDA_PATH") else "cpu"
    compute_type = "int8_float16" if device == "cuda" else "int8"
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(wav_path, language=language, beam_size=1)
    return "".join(seg.text for seg in segments).strip()

# ------------------------
# Tkinter UI
# ------------------------
class RecorderUI:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # hide until needed
        self.root.attributes("-topmost", True)
        self.label = None

    def show_recording(self):
        self.clear_window()
        self.root.deiconify()
        self.root.title("Recording…")
        self.label = tk.Label(self.root, text=f"Recording… Press {HOTKEY} to stop.", font=("Arial", 14))
        self.label.pack(padx=20, pady=20)
        self.root.update()

    def update_status(self, new_text):
        if self.label:
            self.label.config(text=new_text)
            self.root.update()

    def show_transcript(self, transcript, on_ok):
        self.clear_window()
        self.root.title("Transcript")
        text_box = tk.Text(self.root, wrap="word", height=10, width=50)
        text_box.insert("1.0", transcript)
        text_box.config(state="disabled")
        text_box.pack(padx=10, pady=10)

        ok_button = tk.Button(self.root, text="OK", command=on_ok)
        ok_button.pack(pady=(0, 10))

        self.root.update()

    def show_error(self, message):
        messagebox.showerror("Error", message)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

# ------------------------
# Main loop / Daemon logic
# ------------------------
def run_daemon():
    mic_index = pick_device(MIC_NAME)
    root = tk.Tk()
    ui = RecorderUI(root)

    def hotkey_pressed():
        threading.Thread(target=handle_recording, args=(ui, mic_index), daemon=True).start()

    keyboard.add_hotkey(HOTKEY, hotkey_pressed)

    print(f"Daemon running. Press {HOTKEY} to start/stop recording.")
    root.mainloop()

amRecording = False

def handle_recording(ui, mic_index):
    global amRecording
    try:
        if amRecording:
            print("Already recording cannot run")
            return
        amRecording = True
        ui.show_recording()

        with tempfile.TemporaryDirectory() as td:
            wav_path = os.path.join(td, "clip.wav")
            record_until_key_release(wav_path, HOTKEY, device=mic_index)
            ui.update_status("Transcribing audio...")
            transcript = transcribe_local(wav_path)

        def send_to_clockify():
            global amRecording
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open("log.txt", "a") as f:
                    f.write(f"[{timestamp}] {transcript}\n")
                ui.root.withdraw()
            except Exception as e:
                ui.show_error(f"Clockify error: {e}")
            finally:
                amRecording = False

        ui.show_transcript(transcript, send_to_clockify)

    except Exception as e:
        ui.show_error(str(e))
        ui.root.withdraw()
        amRecording = False

        

# ------------------------
# Entry point
# ------------------------
if __name__ == "__main__":
    run_daemon()
