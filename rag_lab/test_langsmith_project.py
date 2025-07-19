from dotenv import load_dotenv
load_dotenv()

from langsmith import Client

client = Client()

try:
    # 프로젝트 생성 시도
    project = client.create_project(
        project_name='rag_lab_project', 
        description='RAG monitoring project'
    )
    print(f"프로젝트 생성 완료: {project}")
except Exception as e:
    print(f"프로젝트 생성 결과: {e}")

# 기존 프로젝트 목록 확인
try:
    projects = client.list_projects()
    print("\n현재 프로젝트 목록:")
    for project in projects:
        print(f"- {project.name} (ID: {project.id})")
except Exception as e:
    print(f"프로젝트 목록 조회 실패: {e}")