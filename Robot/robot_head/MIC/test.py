# file: record_wav.py
import sounddevice as sd
import numpy as np
import wave

DEVICE = None      # 장치 자동선택. 특정 카드 쓰려면 인덱스(정수)로 지정
FS = 48000         # 샘플레이트
SEC = 5            # 녹음 길이(초)
CHANNELS = 1

print("Recording...")
audio = sd.rec(int(SEC*FS), samplerate=FS, channels=CHANNELS, dtype='int32', device=DEVICE)
sd.wait()
print("Done. Saving test.wav")

# 32-bit PCM으로 저장
with wave.open("test.wav", "wb") as wf:
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(4)  # 32-bit
    wf.setframerate(FS)
    wf.writeframes(audio.tobytes())

print("Saved to test.wav")

