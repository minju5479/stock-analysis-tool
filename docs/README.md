# 주식 분석 MCP 서버

주식 티커를 입력받아 종합적인 분석을 제공하는 Model Context Protocol (MCP) 서버입니다.

## 기능

### 1. 종합 주식 분석 (`analyze_stock`)
- 주식 티커와 분석 기간을 입력받아 종합적인 분석 제공
- 기본 정보, 기술적 지표, 거래량 분석, 변동성 분석, 추세 분석 포함
- 자동으로 분석 요약 생성

### 2. 실시간 가격 조회 (`get_stock_price`)
- 주식의 현재 가격 정보 조회
- 전일 대비 변화율, 거래량 등 포함

### 3. 기술적 지표 분석 (`get_technical_indicators`)
- RSI, MACD, 볼린저 밴드, 스토캐스틱 등 기술적 지표 계산
- 각 지표에 대한 해석 제공

### 4. 재무 정보 조회 (`get_financial_info`)
- P/E 비율, 배당수익률, 부채비율 등 재무 정보 제공
- 기업 기본 정보 포함

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. MCP 서버 실행
```bash
python stock_analysis_mcp.py
```

### 3. MCP 클라이언트 설정
`mcp_config.json` 파일을 MCP 클라이언트의 설정 디렉토리에 복사하거나, 클라이언트 설정에 다음을 추가:

```json
{
  "mcpServers": {
    "stock-analysis": {
      "command": "python",
      "args": ["stock_analysis_mcp.py"],
      "env": {}
    }
  }
}
```

## 사용 예시

### 종합 분석
```json
{
  "name": "analyze_stock",
  "arguments": {
    "ticker": "AAPL",
    "period": "1y"
  }
}
```

### 가격 조회
```json
{
  "name": "get_stock_price",
  "arguments": {
    "ticker": "MSFT"
  }
}
```

### 기술적 지표
```json
{
  "name": "get_technical_indicators",
  "arguments": {
    "ticker": "005930.KS",
    "period": "6mo"
  }
}
```

### 재무 정보
```json
{
  "name": "get_financial_info",
  "arguments": {
    "ticker": "GOOGL"
  }
}
```

## 지원하는 티커 형식

- 미국 주식: `AAPL`, `MSFT`, `GOOGL`, `TSLA` 등
- 한국 주식: `005930.KS` (삼성전자), `000660.KS` (SK하이닉스) 등
- 기타 국가 주식: 해당 국가의 티커 형식 지원

## 분석 기간 옵션

- `1d`: 1일
- `5d`: 5일
- `1mo`: 1개월
- `3mo`: 3개월
- `6mo`: 6개월
- `1y`: 1년
- `2y`: 2년
- `5y`: 5년
- `10y`: 10년
- `ytd`: 연초부터 현재까지
- `max`: 최대 기간

## 기술적 지표 설명

### RSI (Relative Strength Index)
- 0-100 범위의 모멘텀 지표
- 70 이상: 과매수 구간
- 30 이하: 과매도 구간

### MACD (Moving Average Convergence Divergence)
- 추세 추종 지표
- MACD 선이 시그널 선 위: 상승 신호
- MACD 선이 시그널 선 아래: 하락 신호

### 볼린저 밴드
- 변동성 기반 지표
- 상단/하단 밴드 돌파 시 과매수/과매도 신호

### 스토캐스틱
- 모멘텀 지표
- K%와 D% 모두 80 이상: 과매수
- K%와 D% 모두 20 이하: 과매도

## 주의사항

1. 이 도구는 투자 조언이 아닌 정보 제공 목적으로만 사용되어야 합니다.
2. 실제 투자 결정은 전문가와 상담 후 이루어져야 합니다.
3. 과거 데이터를 기반으로 한 분석이므로 미래 성과를 보장하지 않습니다.
4. 인터넷 연결이 필요하며, Yahoo Finance API를 사용합니다.

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 이슈로 등록해 주세요. 