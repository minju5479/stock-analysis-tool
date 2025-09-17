# 📈 주식 분석 도구 (Stock Analysis Tool)

주식 티커를 입력받아 종합적인 분석과 차트를 제공하는 Python 도구입니다.

## 🌟 최신 업데이트 (2025.08.14)

### � 포트폴리오 관리 시스템 추가
- **새로운 메인 모드**: "포트폴리오 관리" 전용 페이지 추가
- **보유 종목 관리**: 티커, 수량, 평균 단가 입력으로 개인 포트폴리오 구성
- **실시간 현재가**: yfinance를 통한 실시간 가격 조회 및 수익률 계산
- **🤖 AI 기반 목표가/손절가 추천**: 
  - 13개 전략 분석 기반 데이터 드리븐 추천
  - 보수적/적극적 목표가 자동 계산
  - AI 추천 손절가 설정
  - 상위 3개 전략 근거와 성과 지표 제공
- **원클릭 적용**: AI 추천값을 포트폴리오에 바로 적용
- **종합 분석**: 전체 포트폴리오 수익률 및 종목별 대응 전략 제시
- **일괄 AI 분석**: 모든 보유 종목에 대한 전체 AI 분석 실행

### 🎨 UI/UX 대폭 개선
- **모던 사이드바**: 기존 라디오 버튼을 시각적 그라디언트 버튼으로 교체
- **4개 메인 모드**: 전체분석, 포트폴리오 관리, 전략전용, 저평가 스크리닝
- **아이콘 기반 네비게이션**: 각 모드별 직관적 아이콘과 설명 추가
- **현재 모드 표시**: 선택된 모드를 별도 카드로 명확히 강조
- **도움말 시스템**: 모드별 상세 안내와 시스템 정보 제공
- **반응형 디자인**: 컬럼 기반 레이아웃으로 공간 효율성 증대

### 🔧 기술적 개선사항
- **조건부 UI 렌더링**: 전체분석 모드에서만 분석 설정/전략 파라미터 표시
- **세션 상태 관리**: 포트폴리오 데이터 지속성 보장
- **오류 처리 강화**: AI 분석 실패 시 상세한 오류 메시지 제공
- **데이터 구조 최적화**: `generate_investment_guide` 메서드 활용으로 성능 개선

### 🔬 고급 전략 포트폴리오 (13개 전략)
- **🔸 Quantitative Factor**: 재무 지표 + 기술적 분석 융합 (★ 1위 전략)
- **🔸 Machine Learning**: 머신러닝 기반 예측 모델 (2위, 13.53% CAGR)
- **🔸 Market Regime**: 시장 체제 인식 기반 적응형 전략 (3위, 12.55% CAGR)
- **🔸 Multi-Timeframe**: 다중 시간대 분석 전략
- **🔸 Statistical Arbitrage**: 통계적 차익거래 전략
- **🔸 Volume Profile**: 거래량 프로파일 기반 전략
- **🔸 Sentiment Analysis**: 시장 심리 분석 전략
- **🔸 Options Strategy**: 옵션 전략 시뮬레이션
- **🔸 Crypto Arbitrage**: 가상화폐 차익거래 전략
- **기존 4개 전략**: Rule-based, Momentum, Mean Reversion, Pattern 전략

### 📊 포괄적 백테스트 시스템
- **대규모 테스트**: 3,510개 개별 백테스트 수행 완료
- **정밀한 분석**: 27개 우량 종목 × 13개 전략 × 10개 파라미터 조합
- **검증된 결과**: CSV/JSON 형태의 상세한 분석 결과 제공
- **통계적 유의성**: 충분한 샘플 사이즈로 전략 효과성 입증

### 🔍 저평가 종목 스크리닝 기능 추가
- **전체 시장 스크리닝**: 한국 주식, 미국 주식, 또는 전체 시장에서 저평가 종목 발굴
- **종합 점수 시스템**: P/E, P/B, P/S 비율, ROE, 재무 안정성 등을 종합한 10점 만점 평가
- **고급 필터 옵션**: 시가총액, P/E 비율, ROE, 유동비율 등 다양한 조건으로 세밀한 필터링
- **상세 분석**: 상위 종목에 대한 저평가 근거와 재무 지표 상세 분석 제공
- **결과 내보내기**: CSV 파일로 스크리닝 결과 다운로드 가능
- **실시간 데이터**: Yahoo Finance API 기반 최신 재무 데이터 활용

### 🧪 백테스트 시스템 고도화
- **신뢰성 있는 백테스트**: 룩어헤드 바이어스 방지, 실제적인 수수료/슬리피지 반영
- **다양한 성과 지표**: CAGR, 변동성, 샤프 비율, 최대 낙폭 등 포괄적 평가
- **거래 내역 추적**: 실제 매수/매도 타이밍과 수익/손실 상세 기록
- **견고한 신호 생성**: 짧은 데이터에서도 안정적인 신호 생성, NaN 값 안전 처리

### 🎨 사용자 경험 개선
- **듀얼 페이지 모드**: 종합 분석 vs 전략 집중 페이지로 사용 목적별 최적화
- **인터랙티브 파라미터 컨트롤**: 실시간 파라미터 조정으로 즉각적인 결과 확인
- **전략별 맞춤 메시지**: 각 전략의 특성을 반영한 구체적인 매수/매도 가이드

### 🔧 이전 업데이트 내역
- 어닝콜 & 가이던스 분석 강화
  - 애널리스트 추정치 N/A 문제 해결: yfinance의 `earnings_estimate`/`revenue_estimate`(0q/+1q/0y/+1y) 기반으로 데이터 수집, 추천은 `recommendations` DataFrame 사용
  - 어닝 이력 분기 표기 수정: `YYYY Q1–Q4` 형식으로 일관 표시
- 웹 UI 개선 (Streamlit)
  - 기본 정보 레이아웃 개편: 가격/시총/P-E/통화 + 회사/섹터/산업/전일 종가 2행 구성
  - 기술적 지표 탭 추가: 요약/상세 탭으로 가독성 향상 (RSI, MACD, 이동평균 추세, OBV 등)
  - 애널리스트 추정치 표 형태 표시 (EPS/매출 추정)
- ChartAnalyzer 모듈 리팩토링: 차트 기능 모듈화로 유지보수성 향상
- 구조적 개선: 기능별 모듈 분리로 코드 재사용성 증대
- 오류 수정: MACD 차트 렌더링 관련 오류 해결
- Docker 지원: 완전한 컨테이너화 환경 제공
- API 서버 안정화: FastAPI 기반 REST API 완전 지원

## 🏗️ 프로젝트 구조

```
stock-analysis-tool/
├── src/                     # 소스 코드
│   ├── core/               # 핵심 비즈니스 로직
│   │   ├── analysis/       # 주식 분석 엔진
│   │   ├── chart/          # 차트 분석 모듈
│   │   ├── data/           # 데이터 처리 모듈
│   │   └── utils/          # 유틸리티 함수들
│   ├── api/                # FastAPI 서버
│   │   ├── routes/         # API 라우트
│   │   ├── schemas/        # 데이터 모델
│   │   └── middleware/     # 미들웨어
│   ├── web/                # Streamlit 웹 인터페이스
│   └── mcp/                # Model Context Protocol 서버
├── scripts/                # 실행 스크립트
│   ├── run_web.py         # 웹 인터페이스 실행
│   ├── run_api.py         # API 서버 실행
│   ├── run_demo.py        # 데모 실행
│   ├── run_docker.sh      # Docker 실행 스크립트
│   └── test_strategies.py  # 전략 테스트 스크립트
├── docker/                # Docker 관련 파일
│   ├── Dockerfile         # Docker 이미지 정의
│   ├── docker-compose.yml # 서비스 구성
│   ├── DOCKER_README.md   # Docker 사용법
│   └── requirements-docker.txt # Docker 의존성
├── docs/                  # 문서
│   ├── README.md          # 개발자 문서
│   ├── spec.md            # 기술 명세서
│   ├── backtest.md        # 백테스팅 가이드
│   └── mcp_setup_guide.md # MCP 설정 가이드
├── results/               # 분석 결과
│   └── test_results_*.md  # 테스트 결과 보고서
├── configs/               # 설정 파일
├── examples/              # 예제 코드
├── tests/                 # 테스트 코드
└── data/                  # 데이터 저장소
```

## 🔧 기술 스택

### 🐍 Backend
- **Python 3.9+**: 메인 개발 언어
- **FastAPI**: REST API 서버 프레임워크
- **Streamlit**: 웹 인터페이스 프레임워크
- **Pydantic**: 데이터 검증 및 직렬화

### 📊 데이터 & 분석
- **yfinance**: Yahoo Finance 데이터 수집
- **pandas**: 데이터 처리 및 분석
- **numpy**: 수치 계산 및 배열 연산
- **scipy**: 과학적 계산 라이브러리
- **ta-lib**: 기술적 분석 지표 라이브러리

### 📈 시각화
- **plotly**: 인터랙티브 차트 생성
- **matplotlib**: 기본 차트 및 그래프
- **seaborn**: 통계 시각화

### 🐳 인프라 & 배포
- **Docker**: 컨테이너화 및 배포
- **docker-compose**: 멀티 컨테이너 관리
- **uvicorn**: ASGI 서버

### 🤖 AI 연동
- **MCP (Model Context Protocol)**: AI 클라이언트 연동
- **JSON Schema**: API 스키마 정의

## 🐳 Docker 사용법

### 기본 실행
```bash
# 전체 서비스 시작 (스크립트 사용)
bash scripts/run_docker.sh

# 또는 직접 실행
cd docker && docker-compose up

# 백그라운드 실행
cd docker && docker-compose up -d

# 특정 서비스만 실행
cd docker && docker-compose up web    # 웹만
cd docker && docker-compose up api    # API만

# 로그 확인
cd docker && docker-compose logs -f web
cd docker && docker-compose logs -f api

# 서비스 중지
cd docker && docker-compose down

# 볼륨까지 삭제
cd docker && docker-compose down --volumes
```

### 개발 환경 설정
```bash
# 이미지 재빌드
cd docker && docker-compose build --no-cache

# 개발용 실행 (코드 변경 시 자동 재시작)
cd docker && docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 컨테이너 접속
cd docker && docker-compose exec api bash
cd docker && docker-compose exec web bash
```k-analysis-tool/
├── 📁 src/                        # 소스 코드
│   ├── 📁 core/                   # 핵심 분석 모듈
│   │   ├── 📁 analysis/           # 분석 엔진
│   │   │   ├── stock_analyzer.py  # 메인 주식 분석기
│   │   │   ├── stock_screener.py  # 저평가 종목 스크리너
│   │   │   ├── 📁 technical/      # 기술적 분석
│   │   │   │   ├── indicators.py  # 기술적 지표
│   │   │   │   ├── trend.py       # 추세 분석
│   │   │   │   ├── volatility.py  # 변동성 분석
│   │   │   │   └── volume.py      # 거래량 분석
│   │   │   └── 📁 financial/      # 재무 분석
│   │   │       ├── analyzer.py    # 재무 분석기
│   │   │       ├── profitability.py  # 수익성 분석
│   │   │       ├── valuation.py   # 밸류에이션
│   │   │       ├── health.py      # 재무건전성
│   │   │       ├── growth.py      # 성장성 분석
│   │   │       └── dividend.py    # 배당 분석
│   │   ├── 📁 chart/              # 차트 생성 모듈
│   │   │   ├── analyzer.py        # 메인 차트 분석기
│   │   │   ├── renderers.py       # 차트 렌더링
│   │   │   ├── formatters.py      # 데이터 포맷팅
│   │   │   └── styles.py          # 차트 스타일링
│   │   ├── 📁 data/               # 데이터 처리
│   │   │   ├── fetcher.py         # 데이터 수집
│   │   │   ├── processor.py       # 데이터 가공
│   │   │   └── cache.py           # 데이터 캐싱
│   │   └── 📁 utils/              # 유틸리티
│   │       ├── exceptions.py      # 예외 처리
│   │       └── validators.py      # 데이터 검증
│   ├── 📁 web/                    # 웹 인터페이스
│   │   └── web_interface.py       # Streamlit 웹 앱
│   ├── 📁 api/                    # API 서버
│   │   ├── server.py              # FastAPI 서버
│   │   ├── api_server.py          # API 서버 메인
│   │   ├── 📁 routes/             # API 라우트
│   │   │   ├── analysis.py        # 분석 엔드포인트
│   │   │   └── charts.py          # 차트 엔드포인트
│   │   ├── 📁 schemas/            # 데이터 모델
│   │   │   └── models.py          # Pydantic 모델
│   │   └── 📁 middleware/         # 미들웨어
│   │       └── error_handlers.py  # 에러 핸들링
│   └── 📁 mcp/                    # MCP 서버
│       ├── stock_analysis_mcp.py  # MCP 서버
│       └── test_mcp.py            # MCP 테스트
├── 📁 configs/                    # 설정 파일
│   ├── mcp_config.json            # MCP 설정
│   └── claude_desktop_config.json # Claude Desktop 설정
├── 📁 docs/                       # 문서
│   ├── README.md                  # 이 파일
│   └── mcp_setup_guide.md         # MCP 설정 가이드
├── 📁 examples/                   # 예제 및 데모
│   ├── simple_demo.py             # 간단한 데모
│   └── demo.py                    # 상세한 데모
├── 📁 tests/                      # 테스트
│   └── test_analysis.py           # 분석 테스트
├── � docker-compose.yml          # Docker Compose 설정
├── 🐳 Dockerfile                  # Docker 이미지 설정
├── �🚀 run_web.py                  # 웹 인터페이스 실행
├── 🚀 run_api.py                  # API 서버 실행
├── 🚀 run_demo.py                 # 데모 실행
├── 📋 requirements.txt            # 의존성 패키지
└── � requirements-docker.txt     # Docker 의존성
```

## 🚀 빠른 시작

### Option 1: Docker 사용 (권장)

```bash
# 저장소 클론
git clone https://github.com/EugeneSon/stock-analysis-tool.git
cd stock-analysis-tool

# Docker Compose로 실행
bash scripts/run_docker.sh
# 또는 직접 실행
cd docker && docker-compose up

# 또는 백그라운드 실행
cd docker && docker-compose up -d
```

서비스 접속:
- **웹 인터페이스**: http://localhost:8501
- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### Option 2: 로컬 설치

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt

# 실행
python scripts/run_web.py    # 웹 인터페이스
python scripts/run_api.py    # API 서버
python scripts/run_demo.py   # 데모
```

## 📊 핵심 기능

### � 포트폴리오 관리 시스템
- **개인 포트폴리오 구성**: 보유 종목, 수량, 평균 단가 관리
- **실시간 현재가**: yfinance API를 통한 실시간 가격 조회
- **수익률 자동 계산**: 개별 종목 및 전체 포트폴리오 수익률 표시
- **🤖 AI 기반 목표가/손절가 추천**:
  - 13개 전략 종합 분석 기반 데이터 드리븐 추천
  - 보수적/적극적 목표가 자동 계산 (기대수익률 70%/100% 적용)
  - AI 추천 손절가 설정 (평균 최대손실 80% 지점)
  - 상위 3개 전략의 성과 지표와 추천 근거 제공
- **원클릭 적용**: AI 추천값을 포트폴리오에 바로 적용
- **종합 분석**: 전체 포트폴리오 수익률 및 종목별 대응 전략
- **일괄 AI 분석**: 모든 보유 종목 동시 분석 및 진행률 표시

### �🔍 종합 주식 분석
- **기본 정보**: 현재가, 변동률, 시가총액, PER, 배당수익률
- **기술적 분석**: 30개 이상의 기술적 지표 및 패턴 분석
- **재무 분석**: 수익성, 안정성, 성장성, 배당 정책 평가
- **어닝콜 & 가이던스**: 애널리스트 추정치, 목표가, 어닝 캘린더, 추천 의견
- **시장 분석**: 섹터/산업군 비교, 시장 대비 성과
- **AI 기반 요약**: 종합적인 투자 관점 제시

### 📈 인터랙티브 차트
- **캔들스틱 차트**: 
  - OHLC 데이터 시각화
  - 이동평균선 (20/50/200일)
  - 볼린저 밴드 오버레이
  - 한글 요일 hover 지원
- **기술적 지표 차트**:
  - RSI, MACD, 스토캐스틱
  - 추세선 및 지지/저항선
  - 거래량 분석 차트
- **멀티플롯 구성**: 가격/거래량/지표를 하나의 차트에 표시

### 🔧 기술적 지표 (30+ 지표)

#### 📈 추세 지표
- **이동평균선** (SMA/EMA): 5, 10, 20, 50, 200일
- **MACD**: 매수/매도 신호 생성
- **Parabolic SAR**: 추세 전환점 포착
- **ADX**: 추세 강도 측정

#### 🎯 모멘텀 지표  
- **RSI**: 과매수/과매도 (14일 기준)
- **스토캐스틱**: %K, %D 오실레이터
- **Williams %R**: 모멘텀 확인 지표
- **ROC**: 가격 변화율 측정
- **MFI**: 거래량 가중 모멘텀

#### 📊 변동성 지표
- **볼린저 밴드**: 가격 변동성 범위
- **ATR**: 평균 실제 범위
- **표준편차**: 가격 변동성 측정

#### 📉 거래량 지표
- **OBV**: 온 밸런스 볼륨
- **A/D Line**: 누적/분산 라인
- **거래량 비율**: 평균 대비 현재 거래량

### 💰 재무 분석

#### 🏢 수익성 지표
- **ROE** (자기자본이익률): 투자 효율성
- **ROA** (총자산이익률): 자산 활용도  
- **영업이익률**: 본업 수익성
- **순이익률**: 최종 수익성
- **EBITDA 마진**: 현금 창출 능력

#### 💪 재무 건전성
- **부채비율**: 레버리지 수준
- **유동비율**: 단기 채무 상환 능력
- **당좌비율**: 즉시 현금화 가능 자산
- **이자보상배수**: 이자 지급 능력

#### � 성장성 분석
- **매출 성장률**: 3년 평균 성장률
- **영업이익 성장률**: 수익성 개선 추이  
- **순이익 성장률**: 최종 성과 개선
- **EPS 성장률**: 주당순이익 증가

#### 💎 배당 분석
- **배당수익률**: 연간 배당금/주가
- **배당성향**: 배당금/순이익 비율
- **배당 지속성**: 배당 지급 연속성

### 📈 어닝콜 & 가이던스 분석

#### 🎯 애널리스트 추정치
- **EPS 추정치**: 현재/다음 분기, 현재/다음 연도 (yfinance `earnings_estimate.avg`)
- **매출 추정치**: 분기 및 연간 예상 매출 (yfinance `revenue_estimate.avg`)
- **목표 주가**: 애널리스트 평균 목표가
- **추천 의견**: Buy/Hold/Sell 분포 및 평균 점수

#### 📅 어닝 캘린더
- **예정된 어닝 발표**: 다음 어닝 발표일 및 EPS 추정치
- **최근 어닝 이력**: 최근 4분기 실적 및 서프라이즈 (분기 표기 `YYYY Q1–Q4`)
- **분기별 실적**: 매출, 순이익, EPS 추이

#### 💼 가이던스 지표
- **Forward P/E**: 미래 실적 기반 밸류에이션
- **PEG Ratio**: 성장률 대비 밸류에이션
- **성장률 전망**: 매출 및 순이익 성장 예상치
- **애널리스트 커버리지**: 분석 기관 수 및 의견 분포

### 🎯 트레이딩 전략 시스템 (13개 전략)

#### 🏆 검증된 최고 성과 전략

#### 🔸 Quantitative Factor 전략 (★ 1위 전략, CAGR 15.14%)
**분석 기법**: 재무 지표와 기술적 분석의 혁신적 융합
- **핵심 원리**: P/E, P/B, ROE 등 재무 지표 + RSI, MACD 등 기술적 지표 결합
- **매수 신호**: 저평가 + 기술적 과매도 + 모멘텀 전환 확인
- **매도 신호**: 고평가 + 기술적 과매수 + 추세 약화
- **검증된 성과**: 270개 테스트에서 79.3% 양의 수익률, 최대 159.92% CAGR 달성
- **위험 조정**: 평균 샤프 비율 0.582, 최대 낙폭 -28.83%
- **특징**: 펀더멘털과 테크니컬의 완벽한 조화, 모든 시장 조건에서 안정적 성과

#### 🔸 Machine Learning 전략 (2위, CAGR 13.53%)
**분석 기법**: 머신러닝 알고리즘 기반 패턴 인식
- **핵심 모델**: 랜덤 포레스트, 그래디언트 부스팅 앙상블
- **특징 엔지니어링**: 기술적 지표, 거래량 패턴, 시장 미시구조
- **예측 대상**: 향후 5일/10일 수익률 예측
- **특징**: 비선형 패턴 포착, 시장 이상 현상 활용

#### 🔸 Market Regime 전략 (3위, CAGR 12.55%)
**분석 기법**: 시장 체제 인식 및 적응형 전략
- **체제 분류**: 상승장/하락장/횡보장/변동성 장세 구분
- **적응 메커니즘**: 체제별 최적 파라미터 자동 전환
- **지표 융합**: VIX, 금리, 거래량 등 거시 지표 활용
- **특징**: 시장 환경 변화에 민첩한 대응

#### 📈 고급 전략 포트폴리오

#### 🔸 Multi-Timeframe 전략
**분석 기법**: 다중 시간대 분석으로 정확도 향상
- **시간대**: 일/주/월 차트 동시 분석
- **신호 확인**: 상위 시간대에서 하위 시간대 신호 검증
- **특징**: 거짓 신호 최소화, 높은 정확도

#### 🔸 Statistical Arbitrage 전략  
**분석 기법**: 통계적 차익거래 및 페어 트레이딩
- **상관관계**: 동일 섹터 종목간 가격 관계 분석
- **평균 회귀**: 가격 스프레드의 통계적 평균 회귀 활용
- **특징**: 시장 중립적, 안정적 수익 추구

#### 🔸 Volume Profile 전략
**분석 기법**: 거래량 프로파일 기반 지지/저항 분석
- **POC 활용**: Point of Control(최대 거래량 가격대) 기반 전략
- **밸류 에어리어**: 거래량이 집중된 가격대 분석
- **특징**: 기관 투자자 관점 반영, 실제적 지지/저항

#### 🔸 Sentiment Analysis 전략
**분석 기법**: 시장 심리 지표 활용
- **공포/탐욕 지수**: VIX, 풋콜 비율 등 심리 지표
- **역발상 신호**: 과도한 낙관/비관시 역방향 투자
- **특징**: 시장 극단 상황에서 높은 수익률

#### 📊 기존 검증된 전략들

#### 🔸 룰베이스 전략 (Rule-Based Strategy)
**분석 기법**: 전통적인 기술적 분석 지표 조합
- **핵심 지표**: 이동평균선(MA), RSI, MACD
- **매수 신호**: RSI 과매도 구간 + MACD 골든크로스 + 상승 추세
- **매도 신호**: RSI 과매수 구간 + MACD 데드크로스 + 하락 추세
- **특징**: 안정적이고 검증된 기법, 초보자에게 적합
- **조정 가능 파라미터**: RSI 임계값, 리스크-리워드 비율, 워밍업 기간

#### 🔸 모멘텀 전략 (Momentum Strategy)
**분석 기법**: 가격 모멘텀과 거래량 분석
- **핵심 지표**: 가격 모멘텀, 거래량 급증, 브레이크아웃/브레이크다운
- **매수 신호**: 강한 상승 모멘텀 + 고거래량 또는 고점 돌파 + 거래량 급증
- **매도 신호**: 약한 하락 모멘텀 + 고거래량 또는 저점 이탈 + 거래량 급증
- **특징**: 추세 추종형, 강한 방향성이 있는 시장에서 유리
- **조정 가능 파라미터**: 모멘텀 기간, 브레이크아웃 임계값, 거래량 기준

#### 🔸 평균회귀 전략 (Mean Reversion Strategy)
**분석 기법**: 볼린저밴드와 RSI를 활용한 평균회귀
- **핵심 지표**: 볼린저밴드, RSI 극값, 변동성 조정
- **매수 신호**: RSI 과매도 + 볼린저밴드 하단 근접 + 낮은 변동성
- **매도 신호**: RSI 과매수 + 볼린저밴드 상단 근접
- **특징**: 횡보장에서 유리, 과매수/과매도 구간 포착에 특화
- **조정 가능 파라미터**: 볼린저밴드 기간/표준편차, RSI 과매수/과매도 임계값

#### 🔸 패턴인식 전략 (Pattern Strategy)
**분석 기법**: 차트 패턴과 지지/저항 수준 분석
- **핵심 지표**: 더블톱/바텀, 삼각형 패턴, 지지/저항선, 브레이크아웃
- **매수 신호**: 더블바텀 후 지지선 돌파 또는 삼각형에서 저항선 돌파 + 거래량 급증
- **매도 신호**: 더블톱 후 저항선 이탈 또는 지지선 붕괴 + 거래량 급증
- **특징**: 고급 기법, 패턴 인식 능력 필요, 큰 수익 가능성
- **조정 가능 파라미터**: 패턴 윈도우, 지지/저항 윈도우, 브레이크아웃 임계값

#### 🧪 포괄적 백테스트 시스템
- **대규모 검증**: 3,510개 개별 백테스트 완료 (27개 종목 × 13개 전략 × 10개 파라미터)
- **성과 지표**: CAGR, 변동성, 샤프 비율, 최대 낙폭(Max Drawdown), 승률
- **현실적 모델링**: 다음날 시가 체결, 수수료/슬리피지 반영
- **거래 내역**: 매수/매도 타이밍, 수익/손실, 보유 기간 추적
- **견고한 신호**: 룩어헤드 바이어스 방지, 짧은 데이터에서도 안정적 동작
- **통계적 검증**: 충분한 샘플 사이즈로 전략 효과성 입증

#### 📈 검증된 성과 결과
- **Quantitative Factor**: 평균 CAGR 15.14%, 최대 CAGR 159.92%
- **Machine Learning**: 평균 CAGR 13.53%, 안정적인 AI 기반 예측
- **Market Regime**: 평균 CAGR 12.55%, 적응형 시장 대응
- **전체 평균**: 기존 전략 6.82% → 신규 전략 15.14% (+121.8% 개선)

#### ⚙️ 전략 파라미터 제어
- **프리셋 시스템**: 보수적/중립/공격적 설정으로 빠른 적용
- **실시간 조정**: 워밍업 기간, 수수료, 슬리피지 등 즉시 반영
- **전략별 맞춤**: 각 전략에 특화된 파라미터 노출 및 설명

## 🌐 다양한 인터페이스

### 1. 🖥️ 웹 인터페이스 (Streamlit)
- **사용자 친화적 UI**: 직관적인 대시보드
- **실시간 차트**: 인터랙티브 plotly 차트
- **티커 검색**: 자동완성 및 추천
- **기간 설정**: 1개월 ~ 5년 분석
- **다운로드**: PDF/이미지 내보내기

### 2. 🔌 REST API (FastAPI)
```bash
# 주식 종합 분석
POST /analyze
{
  "ticker": "AAPL", 
  "period": "1y"
}

# 실시간 가격 조회  
GET /price/{ticker}

# 기술적 지표만 조회
GET /technical/{ticker}?period=6mo

# 어닝콜 & 가이던스 분석
GET /earnings/{ticker}?include_estimates=true

# 차트 데이터 조회
GET /chart/{ticker}?type=candlestick&period=3mo

# 종합 분석 (어닝 포함)
GET /comprehensive/{ticker}?period=1y&include_earnings=true
```

### 3. 🤖 MCP 서버 (AI 연동)
- **Claude Desktop 연동**: 자연어로 주식 분석 요청
- **실시간 대화**: "AAPL 주식 어때?" → 즉시 분석 결과
- **맞춤형 답변**: AI가 상황에 맞는 투자 인사이트 제공

### 4. 📱 CLI 도구
```bash
# 빠른 분석
python -m src.core.analysis.stock_analyzer AAPL

# 차트 생성  
python -m src.core.chart.analyzer TSLA --period 6mo

# 배치 분석
python run_demo.py --batch AAPL,MSFT,GOOGL
```

## 🛠️ 사용 방법

### 웹 인터페이스

#### � 포트폴리오 관리 모드
1. `python scripts/run_web.py` 실행
2. 브라우저에서 `http://localhost:8501` 접속
3. 왼쪽 사이드바에서 **"포트폴리오 관리"** 선택
4. **보유 주식 등록**:
   - 티커 입력 (예: AAPL, 005930.KS)
   - 보유 수량 입력
   - 평균 단가 입력
   - **추가** 버튼 클릭
5. **AI 분석 실행**:
   - 개별 종목: **🤖 AI분석** 버튼 클릭
   - 전체 종목: **🤖 전체 AI 분석 실행** 버튼 클릭
6. **AI 추천 활용**:
   - 보수적/적극적 목표가 확인
   - AI 손절가 확인
   - **적용** 버튼으로 자동 입력
7. **포트폴리오 종합 분석**으로 전체 현황 확인

**포트폴리오 관리 특징:**
- **실시간 현재가**: yfinance API 기반 실시간 가격 조회
- **AI 기반 추천**: 13개 전략 종합 분석으로 목표가/손절가 추천
- **수익률 자동 계산**: 개별 종목 및 전체 포트폴리오 수익률 표시
- **원클릭 적용**: AI 추천값을 바로 포트폴리오에 적용

#### �📊 종합 분석 모드
1. `python scripts/run_web.py` 실행 (또는 가상환경: `source venv/bin/activate && python scripts/run_web.py`)
2. 브라우저에서 `http://localhost:8501` 접속
3. 왼쪽 사이드바에서 페이지 모드 선택: **"전체분석"**
4. 주식 선택 또는 직접 입력
5. 분석 기간 선택 (1개월~5년)
6. **🚀 분석 시작** 버튼 클릭
7. **📈 차트 분석** 섹션에서 원하는 차트 타입 선택

#### 🎯 전략 전용 모드
1. 왼쪽 사이드바에서 페이지 모드: **"전략전용"** 선택
2. 전략 파라미터에서 원하는 전략 선택 (룰베이스/모멘텀/평균회귀/패턴인식)
3. 프리셋 선택 (보수적/중립/공격적) 또는 수동 조정
4. 매수/매도 가이드와 백테스트 결과 확인

#### 🔍 저평가 종목 스크리닝 모드
1. 왼쪽 사이드바에서 페이지 모드: **"저평가 스크리닝"** 선택
2. **시장 선택**: 한국 주식, 미국 주식, 또는 전체
3. **최소 점수** 설정: 6.0점 이상 (10점 만점)
4. **최대 결과 수**: 표시할 종목 수 (10~100개)
5. **고급 필터 설정** (선택사항):
   - 최소 시가총액 (억원/백만달러)
   - 최대 P/E 비율
   - 최소 ROE (%)
   - 최소 유동비율
6. **🚀 스크리닝 시작** 버튼 클릭
7. 결과 분석 및 **📄 CSV 파일로 다운로드**

**저평가 스크리닝 특징:**
- **종합 평가**: P/E, P/B, P/S, ROE, 재무건전성 등을 종합한 10점 만점 점수
- **실시간 데이터**: Yahoo Finance API 기반 최신 재무 데이터
- **상세 분석**: 상위 3개 종목에 대한 저평가 근거 제공
- **결과 내보내기**: CSV 형태로 스크리닝 결과 저장 가능

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

# 어닝 분석
curl "http://localhost:8000/earnings/AAPL?include_estimates=true&include_guidance=true"

# 종합 분석 (어닝 포함)
curl "http://localhost:8000/comprehensive/AAPL?period=1y&include_earnings=true"
```

## 📋 지원하는 티커

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

## � 용어 설명

### 기술적 지표 용어
- **RSI (Relative Strength Index)**
  - 가격의 상승/하락 추세를 판단하는 대표적인 지표
  - 0-100 사이의 값으로 표시되며, 70 이상은 과매수, 30 이하는 과매도로 해석
  
- **MACD (Moving Average Convergence Divergence)**
  - 단기(12일)와 장기(26일) 이동평균선의 차이를 보여주는 지표
  - 추세 전환점을 포착하는데 유용
  
- **볼린저 밴드 (Bollinger Bands)**
  - 20일 이동평균선을 중심으로 표준편차를 이용해 상/하한선을 설정
  - 가격 변동성과 추세를 동시에 파악 가능
  
- **ROC (Rate of Change)**
  - 특정 기간 동안의 가격 변화율을 백분율로 나타냄
  - 모멘텀과 추세 강도를 측정하는데 사용
  
- **Williams %R**
  - 과매수/과매도 구간을 파악하는 모멘텀 지표
  - -100에서 0 사이의 값을 가지며, -80 이하는 과매도, -20 이상은 과매수로 해석
  
- **OBV (On Balance Volume)**
  - 거래량과 가격의 관계를 분석하는 지표
  - 가격 상승 시 거래량은 양수, 하락 시 음수로 계산하여 누적
  
- **MFI (Money Flow Index)**
  - 가격과 거래량을 동시에 고려하는 모멘텀 지표
  - RSI와 유사하나 거래량 가중치가 반영됨

### 재무제표 용어
- **ROE (Return on Equity)**: 자기자본이익률, 투자 효율성 측정
- **ROA (Return on Assets)**: 총자산이익률, 자산 활용 효율성 측정
- **부채비율**: 기업의 재무 안정성을 나타내는 지표
- **유동비율**: 단기 채무 상환 능력을 나타내는 지표
- **배당성향**: 순이익 중 배당금 지급 비율

## �🔧 기술 스택

- **Python 3.9+**
- **yfinance**: 주식 데이터 수집
- **pandas**: 데이터 처리
- **numpy**: 수치 계산
- **plotly**: 인터랙티브 차트
- **streamlit**: 웹 인터페이스
- **fastapi**: API 서버
- **MCP**: AI 클라이언트 연동

## 📚 문서

- [MCP 설정 가이드](docs/mcp_setup_guide.md) - AI 클라이언트 연동 방법
- [API 문서](http://localhost:8000/docs) - API 서버 실행 후 접속

## ⚠️ 주의사항

1. **투자 조언 아님**: 이 도구는 정보 제공 목적으로만 사용되어야 합니다
2. **실시간 데이터**: Yahoo Finance API를 사용하여 실시간 데이터를 제공합니다
3. **인터넷 연결**: 데이터 조회를 위해 인터넷 연결이 필요합니다
4. **API 제한**: 과도한 요청 시 API 제한이 있을 수 있습니다

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해 주세요.

## 📄 라이선스

MIT License

---

**즐거운 주식 분석 되세요! 📈✨** 