import os
import tempfile
import sounddevice as sd
import soundfile as sf
import keyboard
from faster_whisper import WhisperModel

def list_input_devices():
    devs = sd.query_devices()
    return [(i, d['name']) for i, d in enumerate(devs) if d['max_input_channels'] > 0]

def pick_device(name_substring: str | None):
    if not name_substring:
        return None
    name_substring = name_substring.lower()
    for i, name in list_input_devices():
        if name_substring in name.lower():
            return i
    return None

def record_until_space_release(path, samplerate=16000, device=None):
    sd.default.samplerate = samplerate
    sd.default.channels = 1
    if device is not None:
        sd.default.device = (device, None)

    print("Hold SPACE to record...")
    keyboard.wait("space")  # wait for press
    print("Recording... (press SPACE again to stop)")
    rec = sd.rec(int(60 * samplerate), dtype="int16")  # max 60s buffer

    keyboard.wait("space")  # wait for press
    sd.stop()

    # Trim to actual length
    frames = sd.get_stream().read_available  # not accurate here, so just trim silence
    audio_data = rec[:len(rec[rec != 0]) or 1]  # quick crude trim
    sf.write(path, rec, samplerate, subtype="PCM_16")
    print("Recording stopped.")

def transcribe_local(wav_path, model_size="small", language=None):
    device = "cuda" if os.environ.get("CUDA_PATH") else "cpu"
    compute_type = "int8_float16" if device == "cuda" else "int8"
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(wav_path, language=language, beam_size=1)
    return "".join(seg.text for seg in segments).strip()

if __name__ == "__main__":
    mic_name = None  # e.g., "USB"
    mic_index = pick_device(mic_name)

    with tempfile.TemporaryDirectory() as td:
        wav_path = os.path.join(td, "clip.wav")
        record_until_space_release(wav_path, device=mic_index)
        print("Transcribing...")
        text = transcribe_local(wav_path, model_size="small", language="en")
        print("\n--- Transcript ---")
        print(text)
