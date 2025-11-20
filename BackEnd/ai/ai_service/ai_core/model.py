from langchain_openai import ChatOpenAI
from openai import HttpxBinaryResponseContent, OpenAI
import os


chat_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    streaming=True,
    base_url=os.getenv("AI_BASE_URL"),
    api_key=os.getenv("LANGCHAIN_API_KEY"),
)

report_llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.7,
    base_url=os.getenv("AI_BASE_URL"),
    api_key=os.getenv("LANGCHAIN_API_KEY"),
)


_client = OpenAI(base_url=os.getenv("AI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini-tts"
VOICE = "sage"

async def request_tts(sentence)->HttpxBinaryResponseContent:
    return _client.audio.speech.create(
        model=MODEL,
        voice=VOICE,
        input=sentence,
        response_format="pcm"
    )