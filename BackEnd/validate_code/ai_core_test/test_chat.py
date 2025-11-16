# main.py
import asyncio
from dotenv import load_dotenv
from ai.ai_service.ai_core.chain import (
    chain_with_history,
)  # memory.py가 수정된 버전 사용

load_dotenv()


async def run_chat_with_parsing():
    session_id = "child_test_002"
    print(f"--- 대화 시작 (Session: {session_id}) ---")
    print("--- 구분자(\\)를 이용한 TTS 청크 분리 테스트 ---")

    while True:
        user_input = input("\n👶 아이: ")
        if user_input.lower() in ["exit", "q"]:
            break

        # TTS용 문장 버퍼
        sentence_buffer = ""
        
        print("🐥 오리(Raw): ", end="", flush=True)  # 디버깅용 라벨

        async for token in chain_with_history.astream(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}}
        ):
            # 1. [디버깅용] 화면에는 있는 그대로 출력 (여기선 '\'가 보입니다)
            print(token, end="", flush=True)
            
            # 2. 버퍼에 토큰 추가
            sentence_buffer += token
            
            # 3. 구분자(\)를 기준으로 문장 분리
            if "\\" in sentence_buffer:
                # split을 하는 순간, parts 리스트의 요소들에는 '\'가 없습니다!
                parts = sentence_buffer.split("\\")
                
                # 완성된 앞 문장들 처리
                for part in parts[:-1]:
                    clean_sentence = part.strip()  # 앞뒤 공백만 제거
                    
                    if clean_sentence:
                        # 4. [TTS 전송용] 여기서는 '\'가 없는 깔끔한 문장만 나옵니다.
                        # 화면 출력과 섞이지 않게 줄바꿈(\n) 후 로그를 찍습니다.
                        print(f"\n   🔊 [TTS 전송]: '{clean_sentence}'")
                        
                        # await tts_service.send(clean_sentence) # 실제 전송
                        
                        # 다시 Raw 출력을 이어가기 위해 라벨 표시 (선택사항)
                        print("🐥 오리(Raw): ", end="", flush=True)

                # 남은 뒷부분(아직 완성 안 된 조각)을 다시 버퍼에 넣음
                # 다음 문장 시작점의 공백 제거 (lstrip)
                sentence_buffer = parts[-1].lstrip()

        # 4. 루프가 끝났는데 버퍼에 남은 게 있다면 처리 (마지막에 \를 깜빡했을 경우 대비)
        if sentence_buffer.strip():
            print(f"\n   🔊 [TTS 전송(나머지)]: '{sentence_buffer.strip()}'")

        print("\n" + "-" * 50)


if __name__ == "__main__":
    asyncio.run(run_chat_with_parsing())
