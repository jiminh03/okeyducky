from loguru import logger

import pyaudio
from openai import OpenAI

import os

from dotenv import load_dotenv



load_dotenv()

client = OpenAI(

    base_url=os.getenv("AI_BASE_URL"),

    api_key=os.getenv("OPENAI_API_KEY")

)
# 2. TTS 설정
MODEL = "gpt-4o-mini-tts"
VOICE = "nova"
TEXT_TO_SPEAK = "안녕하세요. 이것은 FFmpeg가 필요 없는, PyAudio와 PCM을 이용한 스트리밍 테스트입니다."

# 3. PyAudio 설정 (OpenAI PCM 기본값)
FORMAT = pyaudio.paInt16  # 16-bit
CHANNELS = 1               # 1-channel (모노)
RATE = 24000               # 24kHz
CHUNK_SIZE = 1024

logger.info(f"🔊 '{MODEL}' 모델 (PCM) 스트리밍 재생 시작...")

# 리소스를 안전하게 닫기 위해 try...finally 사용
p = None
stream = None

try:
    # 4. PyAudio 초기화 및 스트림 열기
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True)

    # 5. OpenAI에 TTS 요청 (response_format="pcm")
    response = client.audio.speech.create(
        model=MODEL,
        voice=VOICE,
        input=TEXT_TO_SPEAK,
        response_format="pcm" # 핵심: MP3 대신 PCM 요청
    )

    logger.info("   ...오디오 데이터 수신 즉시 재생 중...")

    # 6. PCM 청크를 받아오는 즉시 PyAudio 스트림에 write
    for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
        if chunk:
            stream.write(chunk) # 받은 데이터를 스피커로 바로 전송

    logger.info("🏁 스트리밍 재생 완료.")

except Exception as e:
    logger.info(f"❌ 오류 발생: {e}")
finally:
    # 7. 리소스 정리 (오류가 발생하더라도 항상 실행됨)
    logger.info("   ...리소스 정리 중...")
    if stream:
        stream.stop_stream()
        stream.close()
    if p:
        p.terminate()
    logger.info("✅ 정리 완료.")