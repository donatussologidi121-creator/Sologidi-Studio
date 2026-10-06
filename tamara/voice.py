"""Tamara's ears and mouth: listen through the microphone, speak through the speakers."""
import collections
import os
import re
import subprocess
import time

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
BLOCK_SECONDS = 0.1
SILENCE_SECONDS = 1.0       # how long you must pause before Tamara decides you finished
MAX_UTTERANCE_SECONDS = 30

WAKE_PATTERN = re.compile(r"\b(tamara|tamera|tamarah|tamarra|tamar|tamra|tomara)\b[,.!?]*", re.I)


class Ears:
    def __init__(self):
        from faster_whisper import WhisperModel

        print("Loading speech recognition (the first run downloads a small model)...")
        self.model = WhisperModel("base.en", device="cpu", compute_type="int8")
        self.threshold = 0.015
        self.calibrate()

    def calibrate(self):
        """Measure the room's background noise so we know what counts as speech."""
        audio = sd.rec(int(0.7 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        noise = float(np.sqrt(np.mean(audio**2)))
        self.threshold = max(0.012, noise * 3.0)

    def listen(self, wait_seconds=None, max_seconds=MAX_UTTERANCE_SECONDS):
        """Record one spoken phrase. Returns audio, or None if nobody spoke within wait_seconds."""
        block = int(SAMPLE_RATE * BLOCK_SECONDS)
        frames, started, quiet_blocks = [], False, 0
        lead_in = collections.deque(maxlen=3)  # keeps the first syllable from being cut off
        quiet_limit = int(SILENCE_SECONDS / BLOCK_SECONDS)
        begin = time.time()
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=block) as stream:
            while True:
                data, _ = stream.read(block)
                level = float(np.sqrt(np.mean(data**2)))
                if level > self.threshold:
                    if not started:
                        frames = list(lead_in)
                    started, quiet_blocks = True, 0
                elif started:
                    quiet_blocks += 1
                if started:
                    frames.append(data.copy())
                    if quiet_blocks >= quiet_limit:
                        break
                    if len(frames) * BLOCK_SECONDS > max_seconds:
                        break
                elif wait_seconds is not None and time.time() - begin > wait_seconds:
                    return None
                else:
                    lead_in.append(data.copy())
        audio = np.concatenate(frames).flatten()
        return audio if len(audio) > SAMPLE_RATE * 0.3 else None

    def transcribe(self, audio):
        if audio is None:
            return ""
        segments, _ = self.model.transcribe(
            audio, language="en", beam_size=1, initial_prompt="Tamara", vad_filter=True
        )
        return " ".join(s.text.strip() for s in segments).strip()


class Mouth:
    def __init__(self):
        self.voice = os.environ.get("TAMARA_VOICE", "Samantha")
        self.rate = os.environ.get("TAMARA_RATE", "185")

    def say(self, text):
        text = re.sub(r"[*_`#>]+", "", text).strip()
        if not text:
            return
        print(f"Tamara: {text}")
        result = subprocess.run(["say", "-v", self.voice, "-r", self.rate, text])
        if result.returncode != 0:  # voice not installed: use the system default
            subprocess.run(["say", text])


def find_wake_word(text):
    """Return the text after 'Tamara', or None if she wasn't addressed."""
    match = WAKE_PATTERN.search(text)
    if not match:
        return None
    rest = (text[: match.start()] + " " + text[match.end():]).strip(" ,.!?")
    rest = re.sub(r"^(hey|hi|hello|okay|ok)\b[ ,.!?]*", "", re.sub(r"\s+", " ", rest), flags=re.I)
    return rest.strip(" ,.!?")
