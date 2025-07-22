#!/bin/bash

echo "===================================="
echo " RAG Lab Elasticsearch 중지 스크립트"
echo "===================================="
echo

echo "Elasticsearch 컨테이너를 중지합니다..."
if docker stop es01 >/dev/null 2>&1; then
    echo "✅ Elasticsearch 컨테이너가 중지되었습니다."
else
    echo "⚠️  실행 중인 es01 컨테이너를 찾을 수 없습니다."
fi

echo
echo "현재 컨테이너 상태:"
docker ps -a | grep es01

echo
echo "스크립트 완료!"