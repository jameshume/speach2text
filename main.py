import argparse, os, tempfile
import sounddevice as sd
import soundfile as sf
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

def record_wav(path, duration_sec=10, samplerate=16000, device=None):
    sd.default.samplerate = samplerate
    sd.default.channels = 1
    if device is not None:
        sd.default.device = (device, None)
    audio = sd.rec(int(duration_sec * samplerate), dtype='int16')
    sd.wait()
    sf.write(path, audio, samplerate, subtype='PCM_16')

def transcribe_local(wav_path, model_size="small", device_hint="auto", language=None):
    # device_hint: "auto", "cpu", or "cuda"
    device = "cuda" if (device_hint == "cuda") else ("cpu" if device_hint == "cpu" else ("cuda" if os.environ.get("CUDA_PATH") else "cpu"))
    compute_type = "int8_float16" if device == "cuda" else "int8"  # fast defaults
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, info = model.transcribe(wav_path, language=language, beam_size=1)
    text = "".join(seg.text for seg in segments).strip()
    return text

def main():
    ap = argparse.ArgumentParser(description="Record → local Whisper (faster-whisper) → print text")
    ap.add_argument("--duration", type=float, default=10, help="Seconds to record")
    ap.add_argument("--mic", type=str, default=None, help="Substring of USB mic name (optional)")
    ap.add_argument("--model", type=str, default="small", help="Model size: tiny|base|small|medium|large-v3")
    ap.add_argument("--lang", type=str, default=None, help="e.g. en, fr, es; leave empty for auto")
    ap.add_argument("--device", type=str, default="auto", choices=["auto","cpu","cuda"])
    args = ap.parse_args()

    if args.mic:
        idx = pick_device(args.mic)
        if idx is None:
            print("Mic not found. Available input devices:")
            for i, name in list_input_devices():
                print(f"  [{i}] {name}")
            return
    else:
        idx = None

    with tempfile.TemporaryDirectory() as td:
        wav_path = os.path.join(td, "clip.wav")
        print(f"Recording {args.duration} sec…")
        record_wav(wav_path, duration_sec=args.duration, device=idx)
        print("Transcribing locally…")
        text = transcribe_local(wav_path, model_size=args.model, device_hint=args.device, language=args.lang)
        print("\n--- Transcript ---")
        print(text)

if __name__ == "__main__":
    main()
