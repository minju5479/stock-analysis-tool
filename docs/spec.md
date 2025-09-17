# 📋 주식 분석 도구 (Stock Analysis Tool) - 기술 사양서

## 📌 프로젝트 개요

### 프로젝트명
주식 분석 도구 (Stock Analysis Tool)

### 프로젝트 설명
Yahoo Finance API를 기반으로 한 종합 주식 분석 플랫폼으로, 실시간 데이터 분석, 기술적 지표 계산, 재무제표 분석, 인터랙티브 차트 생성을 제공하는 Python 기반 웹 애플리케이션

### 개발 기간
2025.01 ~ 2025.08 (전략 시스템 확장 완료: 2025.08.08)

### 개발 언어 및 프레임워크
- **Backend**: Python 3.9+, FastAPI, Streamlit
- **Data Analysis**: pandas, numpy, yfinance
- **Visualization**: plotly, matplotlib, seaborn
- **Trading Strategy**: 4가지 서로 다른 분석 기법 (룰베이스/모멘텀/평균회귀/패턴인식)
- **Backtesting**: 룩어헤드 바이어스 방지, 현실적 수수료/슬리피지 모델링
- **Containerization**: Docker, docker-compose
- **AI Integration**: MCP (Model Context Protocol)

---

## 🏗️ 아키텍처 설계

### 전체 시스템 아키텍처
```
┌─────────────────────────────────────────────────────────────┐
│                   사용자 인터페이스 계층                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Streamlit     │    FastAPI      │      MCP Server         │
│   Web UI        │    REST API     │    (AI Integration)     │
│   :8501         │    :8000        │                         │
└─────────────────┼─────────────────┼─────────────────────────┘
                  │                 │
┌─────────────────┴─────────────────┴─────────────────────────┐
│                   비즈니스 로직 계층                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Analysis      │     Chart       │     Data Processing     │
│   Engine        │    Generator    │       Module           │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • StockAnalyzer │ • ChartAnalyzer │ • DataFetcher          │
│ • Technical     │ • ChartRenderer │ • DataProcessor        │
│ • Financial     │ • Formatters    │ • CacheManager         │
│ • Volume        │ • Styles        │                        │
│ • Volatility    │                 │                        │
│ • Trend         │                 │                        │
└─────────────────┼─────────────────┼─────────────────────────┘
                  │                 │
┌─────────────────┴─────────────────┴─────────────────────────┐
│                    데이터 접근 계층                           │
├─────────────────────────────────────────────────────────────┤
│              Yahoo Finance API                              │
│            External Data Sources                           │
└─────────────────────────────────────────────────────────────┘
```

### 모듈 구조
```
src/
├── core/                    # 핵심 비즈니스 로직
│   ├── analysis/           # 분석 엔진
│   ├── chart/              # 차트 생성
│   ├── data/               # 데이터 처리
│   └── utils/              # 공용 유틸리티
├── web/                    # 웹 인터페이스
├── api/                    # REST API 서버
└── mcp/                    # MCP 서버
```

---

## 🔧 핵심 컴포넌트 명세

### 1. 데이터 분석 엔진 (src/core/analysis/)

#### StockAnalyzer (stock_analyzer.py)
**역할**: 메인 주식 분석 오케스트레이터
**주요 메서드**:
```python
async def analyze_stock(ticker: str, period: str = "1y") -> Dict[str, Any]
async def get_stock_price(ticker: str) -> Dict[str, Any]
def _generate_summary() -> str
```

**의존성**:
- TechnicalAnalyzer: 기술적 지표 분석
- VolumeAnalyzer: 거래량 분석
- VolatilityAnalyzer: 변동성 분석
- TrendAnalyzer: 추세 분석
- FinancialAnalyzer: 재무제표 분석

#### TechnicalAnalyzer (technical/indicators.py)
**역할**: 30+ 기술적 지표 계산 및 해석
**주요 지표**:
- **추세 지표**: MA(20/50/200), MACD, Parabolic SAR, ADX
- **모멘텀 지표**: RSI, Stochastic, Williams %R, ROC, MFI
- **변동성 지표**: Bollinger Bands, ATR, Standard Deviation
- **거래량 지표**: OBV, A/D Line, Volume Ratio

**핵심 메서드**:
```python
def calculate_moving_averages(close_prices: pd.Series) -> Dict[str, float]
def calculate_rsi(close_prices: pd.Series) -> Dict[str, Any]
def calculate_macd(close_prices: pd.Series) -> Dict[str, Any]
def calculate_bollinger_bands(close_prices: pd.Series) -> Dict[str, float]
```

#### FinancialAnalyzer (financial/analyzer.py)
**역할**: 재무제표 기반 기업 분석
**분석 영역**:
- **수익성**: ROE, ROA, 영업이익률, 순이익률, EBITDA 마진
- **안정성**: 부채비율, 유동비율, 당좌비율, 이자보상배수
- **성장성**: 매출/영업이익/순이익 성장률, EPS 성장률
- **배당**: 배당수익률, 배당성향, 배당 지속성

### 2. 차트 생성 엔진 (src/core/chart/)

#### ChartAnalyzer (analyzer.py)
**역할**: 차트 생성 메인 오케스트레이터
**제공 차트**:
- **캔들스틱 차트**: 4-subplot (가격/거래량/RSI/MACD)
- **가격 차트**: 기본 가격 추이 + 거래량 오버레이
- **기술적 지표 차트**: 2x2 subplot (RSI/MACD/볼린저밴드/스토캐스틱)

**핵심 메서드**:
```python
async def generate_charts(ticker: str, period: str = "1y") -> Dict[str, go.Figure]
def create_candlestick_chart(df: pd.DataFrame, ticker: str, indicators: Dict) -> go.Figure
def create_price_chart(df: pd.DataFrame, ticker: str) -> go.Figure
def create_technical_analysis_chart(df: pd.DataFrame, ticker: str, indicators: Dict) -> go.Figure
```

#### ChartRenderer (renderers.py)
**역할**: 차트 구성 요소 렌더링
**렌더링 컴포넌트**:
- 캔들스틱, 이동평균선, 볼린저 밴드
- 거래량 바, RSI, MACD, 스토캐스틱
- 한글 요일 hover, 색상 스타일링

#### ChartFormatters (formatters.py)
**역할**: 데이터 포맷팅 및 한글 지원
**기능**:
- 한글 요일 표시 (월화수목금토일)
- 가격/거래량/지표 hover 텍스트 포맷팅
- 통화 기호 자동 변환 (KRW/USD)

#### ChartStyles (styles.py)
**역할**: 차트 스타일링 및 레이아웃
**스타일 요소**:
- 색상 팔레트 (상승/하락/지표별)
- 레이아웃 템플릿 (캔들스틱/기술지표/가격)
- 반응형 차트 크기 및 비율

### 3. 웹 인터페이스 (src/web/)

#### WebInterface (web_interface.py)
**역할**: Streamlit 기반 사용자 인터페이스
**주요 기능**:
- 티커 검색 및 자동완성
- 인기 주식 목록 제공
- 실시간 분석 결과 표시
- 인터랙티브 차트 렌더링
- 세션 상태 관리

**UI 구성**:
```python
# 사이드바: 설정 및 주식 선택
# 메인 영역: 분석 결과 및 차트
# 기본 정보 → 기술적 지표(요약/상세 탭) → 재무 분석 → 어닝콜&가이던스 → 차트 분석 순서
# 애널리스트 추정치는 표 형태(EPS/매출)로 표시
```

### 4. REST API 서버 (src/api/)

#### API Server (server.py)
**역할**: FastAPI 기반 REST API 제공
**엔드포인트**:
```python
POST /analyze              # 종합 주식 분석
GET  /price/{ticker}       # 실시간 가격 조회
GET  /technical/{ticker}   # 기술적 지표만 조회
GET  /earnings/{ticker}    # 어닝콜 & 가이던스 분석 (애널리스트 추정치/캘린더/가이던스)
GET  /chart/{ticker}       # 차트 데이터 조회
GET  /health              # 헬스 체크
```

**API 스키마** (schemas/models.py):
```python
class StockAnalysisRequest(BaseModel):
    ticker: str
    period: str = "1y"

class StockAnalysisResponse(BaseModel):
    ticker: str
    basic_info: BasicInfo
    technical_indicators: TechnicalIndicators
    financial_analysis: FinancialAnalysis
```

### 5. MCP 서버 (src/mcp/)

#### Stock Analysis MCP Server (stock_analysis_mcp.py)
**역할**: AI 클라이언트 연동을 위한 MCP 서버
**제공 도구**:
- `analyze_stock`: 종합 주식 분석
- `get_stock_price`: 실시간 가격 조회
- `get_technical_indicators`: 기술적 지표 계산
- `create_chart`: 차트 생성 및 저장

**MCP 통합 방식**:
```python
# Claude Desktop 설정
{
  "mcpServers": {
    "stock-analysis": {
      "command": "python",
      "args": ["/path/to/stock_analysis_mcp.py"],
      "env": {}
    }
  }
}
```

---

## 📊 데이터 모델 명세

### 기본 정보 모델
```python
class BasicInfo:
    current_price: float
    previous_price: float
    price_change: float
    price_change_percentage: float
    company_name: str
    sector: str
    industry: str
    market_cap: Optional[int]
    pe_ratio: Optional[float]
  currency: str
    dividend_yield: Optional[float]
```

### 기술적 지표 모델
```python
class TechnicalIndicators:
    moving_averages: Dict[str, float]  # MA20, MA50, MA200
    rsi: Dict[str, Union[float, str]]  # current, interpretation
    macd: Dict[str, float]             # macd_line, signal_line, histogram
    bollinger_bands: Dict[str, float]  # upper, middle, lower
    stochastic: Dict[str, float]       # k_percent, d_percent
    williams_r: Dict[str, Union[float, str]]
    roc: Dict[str, Union[float, str]]
    mfi: Dict[str, Union[float, str]]
    obv: Dict[str, Union[str, int]]
```
### 어닝콜 & 가이던스 모델
```python
class AnalystEstimates:
  current_quarter: { eps_estimate: float, revenue_estimate: float }
  next_quarter:    { eps_estimate: float, revenue_estimate: float }
  current_year:    { eps_estimate: float, revenue_estimate: float }
  next_year:       { eps_estimate: float, revenue_estimate: float }
  recommendations: { strong_buy: int, buy: int, hold: int, sell: int, strong_sell: int }

class EarningsCalendarItem:
  date: str
  eps_estimate: Optional[float]
  reported_eps: Optional[float]
  surprise: Optional[float]

class EarningsAnalysis:
  earnings_history: List[{ quarter: str, date: str, revenue: float, earnings: float, eps: float }]
  analyst_estimates: AnalystEstimates
  earnings_calendar: { upcoming_earnings: List[EarningsCalendarItem], recent_earnings: List[EarningsCalendarItem] }
  guidance: { forward_pe: float, forward_eps: float, targetMeanPrice: float, recommendationMean: float, numberOfAnalystOpinions: int }
```


### 재무 분석 모델
```python
class FinancialAnalysis:
    profitability: Dict[str, float]    # ROE, ROA, margins
    financial_health: Dict[str, float] # ratios, liquidity
    valuation: Dict[str, float]        # PE, PB, PS ratios
    growth: Dict[str, float]           # revenue, earnings growth
    dividend: Dict[str, float]         # yield, payout ratio
    summary: str                       # AI-generated summary
```

---

## 🚀 배포 및 운영 명세

### Docker 컨테이너화
```dockerfile
# Multi-stage build
FROM python:3.11-slim as base

# 시스템 의존성
RUN apt-get update && apt-get install -y gcc g++ curl

# Python 의존성
COPY requirements-docker.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드
COPY . .
EXPOSE 8501 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1
```

### Docker Compose 구성
```yaml
services:
  web:        # Streamlit 웹 인터페이스 (포트 8501)
  api:        # FastAPI REST API 서버 (포트 8000)
  
volumes:
  data:       # 공유 데이터 볼륨
```

### 환경변수 관리
```bash
PYTHONPATH=/app                # Python 모듈 경로
PYTHONUNBUFFERED=1            # 로그 버퍼링 비활성화
DOCKER_ENV=true               # Docker 환경 플래그
```

---

## 🔒 보안 및 에러 처리

### 예외 처리 계층구조
```python
# 사용자 정의 예외 (utils/exceptions.py)
class StockAnalysisError(Exception)        # 기본 예외
class InvalidTickerError(StockAnalysisError)  # 잘못된 티커
class DataNotFoundError(StockAnalysisError)   # 데이터 없음
class NetworkError(StockAnalysisError)        # 네트워크 오류
class ValidationError(StockAnalysisError)     # 검증 오류
```

### API 보안
- CORS 정책 설정
- 요청 제한 및 검증
- 예외 처리 미들웨어
- 로깅 및 모니터링

---

## 🎯 전략 시스템 아키텍처

### 전략 시스템 설계 원칙
- **확장 가능한 아키텍처**: 새로운 전략을 쉽게 추가할 수 있는 플러그인 구조
- **룩어헤드 바이어스 방지**: 미래 정보를 사용하지 않는 현실적인 백테스트
- **파라미터 투명성**: 모든 전략 파라미터를 사용자가 조정 가능하도록 노출
- **성능 지표 표준화**: 모든 전략에 동일한 성과 평가 기준 적용

### 전략 베이스 클래스
```python
class Strategy:
    """모든 거래 전략의 기본 클래스"""
    name: str
    
    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        주가 데이터를 받아 매수/매도 신호를 생성
        
        Args:
            df: OHLCV + 파생 지표 데이터
            params: 전략별 파라미터
            
        Returns:
            signals: 날짜별 action, confidence, reason, stop, target 포함
        """
        pass
```

### 구현된 전략 명세

#### 1. RuleBasedStrategy (룰베이스 전략)
**파일**: `src/core/strategy/rule_based.py`
**핵심 로직**:
- **매수 조건**: RSI < 임계값 & MACD 골든크로스 & 상승추세
- **매도 조건**: RSI > 임계값 & MACD 데드크로스 & 하락추세
- **파라미터**: `rsi_buy_threshold`, `rsi_sell_threshold`, `risk_reward_ratio`

#### 2. MomentumStrategy (모멘텀 전략)  
**파일**: `src/core/strategy/momentum.py`
**핵심 로직**:
- **모멘텀 계산**: (현재가 - N일전 가격) / N일전 가격
- **매수 조건**: 강한 상승 모멘텀 + 고거래량 또는 고점 돌파 + 거래량 급증
- **매도 조건**: 약한 하락 모멘텀 + 고거래량 또는 저점 이탈 + 거래량 급증
- **파라미터**: `momentum_period`, `breakout_threshold`, `volume_sma`

#### 3. MeanReversionStrategy (평균회귀 전략)
**파일**: `src/core/strategy/mean_reversion.py`  
**핵심 로직**:
- **볼린저밴드**: 중심선(SMA) ± N * 표준편차
- **매수 조건**: RSI 과매도 + 볼린저밴드 하단 근처 + 낮은 변동성
- **매도 조건**: RSI 과매수 + 볼린저밴드 상단 근처
- **파라미터**: `bb_period`, `bb_std`, `rsi_oversold`, `rsi_overbought`

#### 4. PatternStrategy (패턴인식 전략)
**파일**: `src/core/strategy/pattern.py`
**핵심 로직**:
- **패턴 감지**: 더블톱/바텀, 삼각형 패턴
- **지지/저항**: 고점/저점의 롤링 최대/최소값
- **매수 조건**: 더블바텀 후 지지선 돌파 또는 삼각형에서 저항선 돌파 + 거래량
- **매도 조건**: 더블톱 후 저항선 이탈 또는 지지선 붕괴 + 거래량
- **파라미터**: `pattern_window`, `support_resistance_window`, `breakout_threshold`

### 백테스트 엔진

#### BacktestEngine 클래스
**파일**: `src/core/backtest/engine.py`
**핵심 기능**:
```python
def run(self, df: pd.DataFrame, signals: pd.DataFrame, 
        fee_bps: float = 10.0, slippage_bps: float = 10.0) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    백테스트 실행
    
    Args:
        df: 주가 데이터 (OHLCV)
        signals: 전략에서 생성된 신호
        fee_bps: 거래 수수료 (basis points)
        slippage_bps: 슬리피지 (basis points)
        
    Returns:
        trades: 거래 내역 (매수/매도 타이밍, 손익)
        equity: 자산 곡선 (날짜별 포트폴리오 가치)
    """
```

**현실적 모델링**:
- 다음 날 시가에 체결 (당일 종가 기준 신호 생성 → 익일 시가 체결)
- 수수료/슬리피지 차감 (각각 bps 단위로 설정 가능)
- 룩어헤드 바이어스 방지 (미래 정보 사용 금지)

#### 성과 지표 계산
**파일**: `src/core/backtest/metrics.py`
```python
def compute_metrics(equity_curve: pd.DataFrame) -> Dict[str, float]:
    """
    백테스트 성과 지표 계산
    
    Returns:
        - CAGR: 연평균 복합 성장률
        - Volatility: 연간 변동성
        - Sharpe: 샤프 비율
        - MaxDrawdown: 최대 낙폭
    """
```

### 전략 파라미터 시스템

#### 프리셋 관리
```python
presets = {
    "보수적": {"warmup": 100, "rsi_buy": 25, "rsi_sell": 75, "risk_rr": 1.5},
    "중립":   {"warmup": 50,  "rsi_buy": 30, "rsi_sell": 70, "risk_rr": 2.0},
    "공격적": {"warmup": 20,  "rsi_buy": 35, "rsi_sell": 65, "risk_rr": 2.5},
}
```

#### 전략별 파라미터 매핑
- **공통 파라미터**: 워밍업 기간, 수수료, 슬리피지
- **전략별 파라미터**: 각 전략에 특화된 임계값 및 계산 파라미터
- **실시간 반영**: 파라미터 변경 시 즉시 신호/백테스트 재계산

---

## 📈 성능 최적화

### 데이터 처리 최적화
- **pandas** 벡터화 연산 활용
- **numpy** 수치 계산 최적화
- 비동기 처리 (asyncio) 적용
- 메모리 효율적인 데이터 구조

### 캐싱 전략
- 주식 데이터 캐싱 (5분 TTL)
- 계산된 지표 캐싱
- 차트 렌더링 결과 캐싱
 - (선택) 애널리스트 추정치 캐싱: `earnings_estimate`/`revenue_estimate` 조회 비용 절감

### 차트 렌더링 최적화
- plotly 서브플롯 최적화
- 데이터 샘플링 (대용량 데이터셋)
- 레이지 로딩 및 점진적 렌더링

---

## 🧪 테스트 명세

### 단위 테스트
```python
# tests/test_analysis.py
def test_stock_analyzer_basic_info()
def test_technical_indicators_calculation()
def test_financial_analysis_metrics()
def test_chart_generation()
```

### 통합 테스트
- API 엔드포인트 테스트
- 웹 인터페이스 E2E 테스트
- Docker 컨테이너 헬스체크

### 성능 테스트
- 대용량 데이터 처리 시간
- 동시 사용자 요청 처리
- 메모리 사용량 모니터링

---

## 📝 API 문서 자동 생성

### OpenAPI/Swagger 스키마
- FastAPI 자동 문서 생성
- 인터랙티브 API 테스트 인터페이스
- 스키마 기반 클라이언트 생성 지원

### 엔드포인트 문서
```
GET  /docs           # Swagger UI
GET  /redoc          # ReDoc 문서
GET  /openapi.json   # OpenAPI 스키마
```

---

## 🔄 변경 이력 (2025-08-08)
- 애널리스트 추정치 N/A 이슈 해결: `earnings_estimate`/`revenue_estimate` DataFrame 사용으로 전환 (0q, +1q, 0y, +1y)
- 어닝 이력 분기 표기 교정: `YYYY Q1–Q4` 형식
- 웹 UI 개선: 기본 정보 2행 구성, 기술적 지표 요약/상세 탭, 추정치 표 렌더링

---

## 🔄 CI/CD 및 배포

### 개발 워크플로우
1. **개발**: 로컬 환경에서 개발 및 테스트
2. **컨테이너화**: Docker 이미지 빌드
3. **테스트**: 자동화된 테스트 실행
4. **배포**: 프로덕션 환경 배포

### 모니터링 및 로깅
- 시스템 헬스체크
- 애플리케이션 로깅
- 사용자 액세스 로그
- 에러 추적 및 알림

---

## 📋 기술 제약사항 및 한계

### 데이터 소스 제약
- Yahoo Finance API 의존성
- 실시간 데이터 지연 (15-20분)
- API 호출 횟수 제한

### 성능 제약
- 메모리 집약적 차트 렌더링
- 대용량 히스토리 데이터 처리 시간
- 동시 사용자 수 제한

### 기능적 제약
- 한국/미국 주식 시장 중심
- 기본적인 기술적 분석만 제공
- 실시간 알림 기능 미포함

---

## 🔮 향후 개발 계획

### 단기 계획 (1-3개월)
- 추가 기술적 지표 구현
- 포트폴리오 분석 기능
- 알림 시스템 구축

### 중기 계획 (3-6개월)
- 머신러닝 기반 예측 모델
- 다중 시장 지원 확대
- 모바일 반응형 UI

### 장기 계획 (6개월+)
- 실시간 스트리밍 데이터
- 소셜 트레이딩 기능
- 클라우드 배포 및 스케일링

---

## 📚 참고 문서

- [README.md](README.md) - 사용자 가이드
- [MCP 설정 가이드](docs/mcp_setup_guide.md) - AI 연동 설정
- [Docker 배포 가이드](DOCKER_README.md) - 컨테이너 배포
- [API 문서](http://localhost:8000/docs) - REST API 레퍼런스

---

**📋 작성일**: 2025.08.08  
**📝 작성자**: 개발팀  
**🔄 문서 버전**: v1.0.0
