import asyncio
import re  # 정규표현식 모듈 임포트
from dotenv import load_dotenv
from ai.ai_service.ai_core.chain import (
    chat_chain_with_history,
)  # memory.py가 수정된 버전 사용

load_dotenv()


async def run_chat_with_parsing():
    child_id = "child_test_002"
    print(f"--- 대화 시작 (Session: {child_id}) ---")
    print("--- 구분자(\\) 및 감정 태그 파싱 테스트 ---")

    while True:
        user_input = input("\n👶 아이: ")
        if user_input.lower() in ["exit", "q"]:
            break

        sentence_buffer = ""
        print("🐥 오리(Raw): ", end="", flush=True)

        async for token in chat_chain_with_history.astream(
            {"input": user_input},
            config={"configurable": {"session_id": child_id}}
        ):
            print(token, end="", flush=True)
            sentence_buffer += token
            
            if "\\" in sentence_buffer:
                parts = sentence_buffer.split("\\")
                
                for part in parts[:-1]:
                    clean_sentence = part.strip()
                    if clean_sentence:
                        match = re.match(r"^\((.*?)\)\s*(.*)", clean_sentence, re.DOTALL)
                        
                        if match:
                            emotion = match.group(1)
                            tts_text = match.group(2).strip()
                        else:
                            emotion = None # 태그가 없는 경우
                            tts_text = clean_sentence
                        
                        if tts_text:
                            # --- [수정된 부분] ---
                            if emotion:
                                # 감정이 있으면, 감정 라인이 \n을 담당
                                print(f"\n   😠 [감정]: '{emotion}'")
                                # TTS 라인은 \n 없이 바로 출력
                                print(f"   🔊 [TTS 전송]: '{tts_text}'")
                            else:
                                # 감정이 없으면, TTS 라인이 \n을 담당
                                print(f"\n   🔊 [TTS 전송]: '{tts_text}'")
                            # --- [여기까지] ---
                            
                            print("🐥 오리(Raw): ", end="", flush=True)

                sentence_buffer = parts[-1].lstrip()

        # 4. 루프 종료 후 남은 버퍼 처리 (여기도 수정)
        final_part = sentence_buffer.strip()
        if final_part:
            match = re.match(r"^\((.*?)\)\s*(.*)", final_part, re.DOTALL)
            
            if match:
                emotion = match.group(1)
                tts_text = match.group(2).strip()
            else:
                emotion = None # 일관성을 위해 '평온' 대신 None으로
                tts_text = final_part
            
            if tts_text:
                # --- [수정된 부분] ---
                if emotion:
                    print(f"\n   😠 [감정(나머지)]: '{emotion}'")
                    print(f"   🔊 [TTS 전송(나머지)]: '{tts_text}'")
                else:
                    print(f"\n   🔊 [TTS 전송(나머지)]: '{tts_text}'")
                # --- [여기까지] ---

        print("\n" + "-" * 50)


if __name__ == "__main__":
    asyncio.run(run_chat_with_parsing())