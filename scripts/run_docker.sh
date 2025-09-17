#!/bin/bash

echo " 주식 분석 도구 Docker 이미지 빌드 및 실행"
echo "=========================================="

# 프로젝트 루트 디렉토리로 이동
cd "$(dirname "$0")/.."

# Docker 데몬 상태 확인
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 데몬이 실행되지 않았습니다."
    echo "   Docker Desktop을 시작한 후 다시 시도해주세요."
    echo "   또는 다음 명령어로 Docker Desktop을 시작할 수 있습니다:"
    echo "   open -a Docker"
    exit 1
fi

# docker 디렉토리로 이동
cd docker

# 기존 컨테이너 중지 및 삭제
echo "🧹 기존 컨테이너 정리 중..."
docker-compose down

# 기존 이미지 삭제 (선택사항)
echo "🗑️ 기존 이미지 정리 중..."
docker system prune -f

# 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker-compose build --no-cache

echo "🚀 웹 + API 서버 실행 중..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Docker 컨테이너가 성공적으로 시작되었습니다!"
    echo ""
    echo "=== 서비스 접속 정보 ==="
    echo "🌐 웹 인터페이스: http://localhost:8501"
    echo "🚀 API 서버: http://localhost:8000"
    echo "📚 API 문서: http://localhost:8000/docs"
    echo ""
    echo "=== 유용한 명령어 ==="
    echo "컨테이너 상태 확인: docker ps"
    echo "컨테이너 로그 확인: docker-compose logs"
    echo "컨테이너 중지: docker-compose down"
    echo ""
    echo "🎉 모든 서비스가 준비되었습니다!"
else
    echo ""
    echo "❌ Docker 컨테이너 시작에 실패했습니다."
    echo "   로그를 확인하려면: docker-compose logs"
    exit 1
fi