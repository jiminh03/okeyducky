# [수정] 최상단에 dotenv 로드 추가
from dotenv import load_dotenv
import os

# 1. 가장 먼저 .env 파일을 로드합니다.
load_dotenv()

# (디버깅용) 포트가 잘 로드되었는지 확인
print(f"DEBUG: DB_PORT = {os.getenv('DB_PORT')}")

# 2. 그 다음에 다른 모듈들을 임포트합니다.
import asyncio
import json
import sys  # [신규] OS 확인용
from datetime import date, datetime, timedelta

# LangChain 관련 임포트
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# DB 관련 임포트
from common.modules.db_instance import db
from common.models.dialogue_model import DailyReport, DialogueLog, Speaker

# ... (DUMMY_DATA_PROMPT는 기존과 동일) ...
DUMMY_DATA_PROMPT = """
당신은 AI 개발 테스트를 위한 더미 데이터 생성기입니다.
아래의 JSON 스키마에 맞춰서, {target_date} 하루 동안의 '아이와 오리 로봇의 대화 리포트' 더미 데이터를 생성해 주세요.

[요구사항]
1. **date**: "{target_date}"
2. **daily_summary**: 하루 동안의 대화 내용을 종합적으로 요약 (300자 이상). 날짜({target_date})에 어울리는 계절감이나 요일 특성을 반영하면 더 좋습니다.
3. **analysis_summary**: 아동 심리 전문가 관점의 분석 리포트 (500자 이상, 서술형)
4. **dialogue_logs**: 최소 15개 이상의 대화 로그 리스트.
   - `speaker`: "child", "robot", "parent" 중 하나
   - `message`: 자연스러운 한국어 대화 내용 (일상, 놀이, 감정 표현 등)
   - `timestamp`: "{target_date}THH:MM:SS" 형식 (시간 순서대로 정렬, 하루 일과 반영)

[출력 형식]
반드시 유효한 JSON 형식으로만 응답해 주세요. (마크다운 코드 블록 제외)
"""

async def generate_and_save_dummy_data_range(start_date_str: str, end_date_str: str, child_id: int = 1):
    print(f"--- [Start] 더미 데이터 생성 시작 ({start_date_str} ~ {end_date_str}) ---")
    
    # 1. LLM 설정
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.8,
        base_url=os.getenv("AI_BASE_URL"),
        api_key=os.getenv("LANGCHAIN_API_KEY"),
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", DUMMY_DATA_PROMPT),
        ("human", "더미 데이터 1세트를 생성해줘.")
    ])
    
    chain = prompt | llm | JsonOutputParser()
    
    # 2. 날짜 범위 계산
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    # DB 연결 초기화
    await db.create_db_and_tables()
    
    # [수정] 세션 메이커를 가져옵니다.
    async_session_maker = db.get_session_maker()

    current_date = start_date
    while current_date <= end_date:
        target_date_str = current_date.strftime("%Y-%m-%d")
        print(f"\n>>> [{target_date_str}] 데이터 생성 중...")

        try:
            # 3. LLM 호출
            dummy_data = await chain.ainvoke({"target_date": target_date_str})
            print(f"   - AI 생성 완료 ({len(dummy_data.get('dialogue_logs', []))} logs)")
            
            # 4. DB 저장
            # [수정] async_session_maker()를 호출하여 세션을 생성합니다.
            async with async_session_maker() as session:
                try:
                    # 날짜 변환
                    report_date = datetime.strptime(dummy_data["date"], "%Y-%m-%d").date()
                    
                    # 4-1. DailyReport 생성
                    new_report = DailyReport(
                        child_id=child_id,
                        date=report_date,
                        daily_summary=dummy_data["daily_summary"],
                        analysis_summary=dummy_data["analysis_summary"]
                    )
                    session.add(new_report)
                    await session.flush() 
                    
                    # 4-2. DialogueLog 생성
                    logs = []
                    for log in dummy_data["dialogue_logs"]:
                        ts = datetime.strptime(log["timestamp"], "%Y-%m-%dT%H:%M:%S")
                        
                        speaker_str = log["speaker"].lower()
                        if speaker_str == "child": speaker = Speaker.CHILD
                        elif speaker_str == "robot": speaker = Speaker.ROBOT
                        elif speaker_str == "parent": speaker = Speaker.PARENT
                        else: speaker = Speaker.ROBOT
                        
                        new_log = DialogueLog(
                            report_id=new_report.report_id,
                            speaker=speaker,
                            message=log["message"],
                            timestamp=ts
                        )
                        logs.append(new_log)
                    
                    session.add_all(logs)
                    await session.commit()
                    print(f"   - ✅ DB 저장 완료 (Report ID: {new_report.report_id})")
                    
                except Exception as e:
                    await session.rollback()
                    print(f"   - 🚨 DB 저장 실패: {e}")

        except Exception as e:
            print(f"   - 🚨 AI 생성 또는 처리 실패: {e}")
        
        current_date += timedelta(days=1)
        # API 속도 제한 방지를 위해 약간 대기
        await asyncio.sleep(1)

    print("\n--- [End] 모든 작업 완료 ---")

if __name__ == "__main__":
    # [수정] Windows 환경에서 asyncio 이벤트 루프 정책 변경
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 2025년 11월 1일부터 18일까지 생성
    asyncio.run(generate_and_save_dummy_data_range("2025-11-01", "2025-11-18", child_id=1))