import sounddevice as sd, numpy as np, wave, time

FS = 48000
SEC = 5
CH = 1
TARGET_DBFS = -1.0

print(f"🎙️  Recording start... ({SEC} seconds at {FS} Hz)")
start = time.time()

x = sd.rec(int(SEC * FS), samplerate=FS, channels=CH, dtype='int32')
sd.wait()

end = time.time()
print(f"✅  Recording done in {end - start:.2f} seconds")

# ---- 정규화 ----
xf = x.astype(np.float64) / (2**31)
peak = np.max(np.abs(xf)) + 1e-12
target = 10 ** (TARGET_DBFS / 20)  # 약 0.891
scale = min(target / peak, 200.0)   # 과한 증폭 제한(최대 50배)

print(f"🔊  Normalizing audio... (peak={peak:.6f}, scale×{scale:.2f})")

y = np.clip(xf * scale, -1.0, 1.0)
y32 = (y * (2**31 - 1)).astype(np.int32)

# ---- 파일 저장 ----
out = "1boost.mp3"
with wave.open(out, "wb") as f:
    f.setnchannels(CH)
    f.setsampwidth(4)
    f.setframerate(FS)
    f.writeframes(y32.tobytes())

print(f"💾  Saved normalized audio to '{out}'")

