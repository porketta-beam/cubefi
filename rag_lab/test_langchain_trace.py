from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI

# LangChain 자동 추적 테스트
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

print("LangChain 트레이스 테스트 중...")

try:
    response = llm.invoke("안녕하세요! 간단한 테스트 메시지입니다.")
    print(f"응답: {response.content}")
    print("✅ LangSmith에서 이 트레이스를 확인하세요!")
except Exception as e:
    print(f"오류: {e}")