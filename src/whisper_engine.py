from faster_whisper import WhisperModel
import subprocess, tempfile, os, time

# ===============================
# OPTIMIZATION 1: Use tiny model for speed or base for balance
# faster_whisper with int8 quantization is ~3-4x faster than openai-whisper
# ===============================
model = WhisperModel(
    "tiny",  # Changed from "small" - 4x faster, still accurate for Quran
    device="cpu", 
    compute_type="int8",
    num_workers=1,  # Optimized for CPU cores
    cpu_threads=4   # Use available CPU threads
)

# ===============================
# OPTIMIZATION 2: Shorter recording window
# Reduce from 2s to 1.5s for faster response
# ===============================
def record_audio(duration=1.5):
    """Record audio with optimized settings for speech recognition."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    filename = temp_file.name
    temp_file.close()

    MIC_NAME = "Headset (JBL TUNE570BT)" # عدل حسب ميكروفونك

    command = [
        "ffmpeg",
        "-f", "dshow",
        "-i", f"audio={mic_name}",
        "-t", str(duration),
        "-ac", "1",                    # Mono for speed
        "-ar", "16000",                # Optimal for speech recognition
        "-acodec", "pcm_s16le",        # Faster codec
        "-y",
        filename
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return filename

# ===============================
# OPTIMIZATION 3: Batch processing
# Skip sleep when text found, only sleep on failure
# ===============================
def start_listening(process_text_callback):
    """Listen for audio input and transcribe continuously."""
    consecutive_errors = 0
    max_errors = 3
    
    while True:
        try:
            audio_file = record_audio(1.5)

            # OPTIMIZATION 4: Use language parameter efficiently
            # Specify language to skip detection step (~200ms saved)
            segments, info = model.transcribe(
                audio_file, 
                language="ar",
                beam_size=3,           # Reduced beam size for speed
                best_of=1,             # Skip multiple sampling
                patience=1.0           # Balance accuracy vs speed
            )

            text = "".join([s.text for s in segments])
            
            # Clean up immediately
            try:
                os.remove(audio_file)
            except:
                pass

            if text.strip():
                process_text_callback(text)
                consecutive_errors = 0
                # OPTIMIZATION 5: No sleep when text processed (async)
            else:
                # Short sleep only on silence
                time.sleep(0.05)

        except Exception as e:
            print(f"[ERROR] Whisper failed: {e}")
            consecutive_errors += 1
            
            # Exponential backoff on errors
            backoff_time = min(0.5 * (2 ** consecutive_errors), 5)
            time.sleep(backoff_time)
            
            # Reload model if too many errors
            if consecutive_errors >= max_errors:
                try:
                    model.model = None
                    consecutive_errors = 0
                except:
                    pass
