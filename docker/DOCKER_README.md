# 🐳 Docker 기반 주식 분석 도구

이 문서는 Docker를 사용하여 주식 분석 도구를 실행하는 방법을 설명합니다.

## 📋 사전 요구사항

- Docker Desktop 설치 및 실행
- Docker Compose (Docker Desktop에 포함됨)

## 🚀 빠른 시작

### 1. Docker Desktop 시작

```bash
# macOS에서 Docker Desktop 시작
open -a Docker

# 또는 Applications 폴더에서 Docker Desktop 실행
```

### 2. 자동 실행 스크립트 사용 (추천)

```bash
# 실행 스크립트 실행
./run_docker.sh
```

스크립트가 다음을 자동으로 수행합니다:
- Docker 데몬 상태 확인
- 이미지 빌드
- 실행 옵션 선택

### 3. 수동 실행

#### 이미지 빌드
```bash
docker build -t stock-analysis-tool .
```

#### 웹 인터페이스 실행
```bash
docker run -p 8501:8501 stock-analysis-tool
```

#### API 서버 실행
```bash
docker run -p 8000:8000 stock-analysis-tool python run_api.py
```

#### Docker Compose로 모든 서비스 실행
```bash
docker-compose up
```

## 🌐 접속 정보

### 웹 인터페이스
- **URL**: http://localhost:8501
- **특징**: 사용자 친화적인 Streamlit 기반 웹 앱
- **기능**: 주식 분석, 차트 생성, 인터랙티브 UI

### API 서버
- **URL**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **기능**: REST API 엔드포인트 제공

## 📊 사용 예제

### 웹 인터페이스 사용
1. 브라우저에서 http://localhost:8501 접속
2. 왼쪽 사이드바에서 주식 선택 또는 직접 입력
3. 분석 기간 선택 (1개월~5년)
4. "🚀 분석 시작" 버튼 클릭

### API 사용
```bash
# 주식 분석
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"ticker": "AAPL", "period": "1y"}'

# 가격 조회
curl "http://localhost:8000/price/AAPL"

# 기술적 지표
curl "http://localhost:8000/technical/AAPL?period=1y"
```

## 🛠️ Docker 명령어

### 컨테이너 관리
```bash
# 실행 중인 컨테이너 확인
docker ps

# 컨테이너 로그 확인
docker logs <container_id>

# 컨테이너 중지
docker stop <container_id>

# 컨테이너 삭제
docker rm <container_id>
```

### 이미지 관리
```bash
# 이미지 목록 확인
docker images

# 이미지 삭제
docker rmi stock-analysis-tool

# 모든 이미지 삭제
docker system prune -a
```

### Docker Compose 명령어
```bash
# 서비스 시작
docker-compose up

# 백그라운드 실행
docker-compose up -d

# 서비스 중지
docker-compose down

# 로그 확인
docker-compose logs

# 특정 서비스 로그 확인
docker-compose logs web
docker-compose logs api
```

## 🔧 환경 변수

Docker 컨테이너에서 사용할 수 있는 환경 변수:

- `PYTHONPATH`: Python 모듈 경로 (기본값: /app)
- `PYTHONUNBUFFERED`: Python 출력 버퍼링 비활성화 (기본값: 1)

## 📁 볼륨 마운트

데이터를 영구적으로 저장하려면 볼륨을 마운트할 수 있습니다:

```bash
# 데이터 디렉토리 마운트
docker run -p 8501:8501 -v $(pwd)/data:/app/data stock-analysis-tool
```

## 🐛 문제 해결

### Docker 데몬이 실행되지 않는 경우
```bash
# Docker Desktop 시작
open -a Docker

# 또는 터미널에서 Docker 데몬 시작 (macOS)
sudo launchctl load /Library/LaunchDaemons/com.docker.docker.plist
```

### 포트가 이미 사용 중인 경우
다른 포트를 사용하세요:
```bash
# 웹 인터페이스를 포트 8502에서 실행
docker run -p 8502:8501 stock-analysis-tool

# API 서버를 포트 8001에서 실행
docker run -p 8001:8000 stock-analysis-tool python run_api.py
```

### 이미지 빌드 실패
```bash
# 캐시 없이 다시 빌드
docker build --no-cache -t stock-analysis-tool .

# Docker 시스템 정리
docker system prune -a
```

## 📝 지원하는 주식

### 🇺🇸 미국 주식
- `AAPL` - Apple Inc.
- `MSFT` - Microsoft Corporation
- `GOOGL` - Alphabet Inc.
- `AMZN` - Amazon.com Inc.
- `TSLA` - Tesla Inc.
- `NVDA` - NVIDIA Corporation
- `META` - Meta Platforms Inc.
- `NFLX` - Netflix Inc.
- `COIN` - Coinbase Global Inc.
- `AMD` - Advanced Micro Devices Inc.

### 🇰🇷 한국 주식
- `005930.KS` - 삼성전자
- `000660.KS` - SK하이닉스
- `035420.KS` - NAVER
- `051910.KS` - LG화학
- `006400.KS` - 삼성SDI
- `035720.KS` - 카카오
- `207940.KS` - 삼성바이오로직스
- `068270.KS` - 셀트리온
- `323410.KS` - 카카오뱅크
- `373220.KS` - LG에너지솔루션

## ⚠️ 주의사항

1. **투자 조언 아님**: 이 도구는 정보 제공 목적으로만 사용되어야 합니다
2. **실시간 데이터**: Yahoo Finance API를 사용하여 실시간 데이터를 제공합니다
3. **인터넷 연결**: 데이터 조회를 위해 인터넷 연결이 필요합니다
4. **API 제한**: 과도한 요청 시 API 제한이 있을 수 있습니다
5. **Docker 리소스**: Docker 컨테이너는 시스템 리소스를 사용합니다

---

**즐거운 주식 분석 되세요! 📈✨** 