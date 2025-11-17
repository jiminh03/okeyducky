# output_parsers.py
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser

# 단순 텍스트 파서 객체 생성
str_parser = StrOutputParser()

# JSON 파서 (요약용)
json_parser = JsonOutputParser()