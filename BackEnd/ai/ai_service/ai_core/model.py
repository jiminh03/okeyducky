from langchain_openai import ChatOpenAI
import os


llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    streaming=True,
    base_url=os.getenv("AI_BASE_URL"),
    api_key=os.getenv("LANGCHAIN_API_KEY"),
)
