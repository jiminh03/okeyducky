import io
import os
from openai import OpenAI

# 1. API Key를 변수에 저장
# 여기에 사용자님의 실제 OpenAI API Key를 입력하세요.
# (예: 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
YOUR_API_KEY = "S13P32A408-95dabe99-17eb-4307-b9d0-c1b83edc8c23"

# 2. 클라이언트 초기화 시 'api_key' 인수를 사용하여 설정
# 환경 변수 설정을 건너뛰고 바로 키를 사용합니다.
client = OpenAI(api_key=YOUR_API_KEY)


# --- (이하 STT 코드는 동일하게 작동합니다) ---

# 3. 오디오 데이터를 '바이너리 바이트' 형태로 메모리에 로드
# 예시: 'audio_source.wav' 파일을 디스크에서 읽어 메모리에 바이트로 저장
# with open("audio_source.wav", "rb") as f:
#     raw_audio_bytes = f.read()
    
# 임시 오디오 바이트 데이터 (실제 데이터로 대체해야 합니다)
raw_audio_bytes = b'\x52\x49\x46\x46\x24\x00\x00\x00\x57\x41\x56\x45\x66\x6d\x74\x20\x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00\x64\x61\x74\x61\x00\x00\x00\x00'


# 4. io.BytesIO를 사용해 '파일 객체'처럼 생성
audio_stream = io.BytesIO(raw_audio_bytes)
audio_stream.name = "my_audio_data.wav" # 오디오의 실제 형식과 일치해야 합니다.


# 5. Whisper API 호출
try:
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_stream, # 메모리 스트림 객체를 파일처럼 전달
        response_format="text"
    )
    print("변환된 텍스트:")
    print(transcription)

except Exception as e:
    print(f"STT 오류 발생: {e}")
