#!/usr/bin/env python3
"""
주식 분석 API 서버
FastAPI를 사용한 REST API 서버
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import uvicorn
import sys
import os

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.analysis.stock_analyzer import StockAnalyzer

# FastAPI 앱 생성
app = FastAPI(
    title="주식 분석 API",
    description="주식 티커를 입력받아 종합적인 분석을 제공하는 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# StockAnalyzer 인스턴스 생성
analyzer = StockAnalyzer()

# Pydantic 모델들
class StockAnalysisRequest(BaseModel):
    ticker: str
    period: str = "1y"

class StockPriceRequest(BaseModel):
    ticker: str

class TechnicalIndicatorsRequest(BaseModel):
    ticker: str
    period: str = "1y"

class FinancialInfoRequest(BaseModel):
    ticker: str

class StockAnalysisResponse(BaseModel):
    ticker: str
    analysis_period: str
    basic_info: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    volume_analysis: Dict[str, Any]
    volatility_analysis: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    summary: str

class StockPriceResponse(BaseModel):
    ticker: str
    current_price: float
    previous_close: float
    price_change: float
    price_change_percentage: float
    open: float
    high: float
    low: float
    volume: int
    company_name: str
    currency: str
    timestamp: str

class ErrorResponse(BaseModel):
    error: str
    message: str

# API 엔드포인트들

@app.get("/", tags=["Root"])
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "주식 분석 API에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "analyze_stock": "/analyze",
            "get_price": "/price/{ticker}",
            "technical_indicators": "/technical/{ticker}",
            "financial_info": "/financial/{ticker}",
            "health": "/health"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "stock-analysis-api"}

@app.post("/analyze", response_model=StockAnalysisResponse, tags=["Analysis"])
async def analyze_stock(request: StockAnalysisRequest):
    """
    주식 종합 분석을 수행합니다.
    
    - **ticker**: 분석할 주식의 티커 심볼 (예: AAPL, MSFT, 005930.KS)
    - **period**: 분석 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
    """
    try:
        result = await analyzer.analyze_stock(request.ticker, request.period)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")

@app.get("/price/{ticker}", response_model=StockPriceResponse, tags=["Price"])
async def get_stock_price(ticker: str):
    """
    주식의 현재 가격 정보를 조회합니다.
    
    - **ticker**: 조회할 주식의 티커 심볼
    """
    try:
        result = await analyzer.get_stock_price(ticker)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가격 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/technical/{ticker}", tags=["Technical"])
async def get_technical_indicators(
    ticker: str,
    period: str = Query("1y", description="분석 기간")
):
    """
    주식의 기술적 지표를 계산합니다.
    
    - **ticker**: 분석할 주식의 티커 심볼
    - **period**: 분석 기간
    """
    try:
        result = await analyzer.get_technical_indicators(ticker, period)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기술적 지표 계산 중 오류가 발생했습니다: {str(e)}")

@app.get("/financial/{ticker}", tags=["Financial"])
async def get_financial_info(ticker: str):
    """
    주식의 재무 정보를 조회합니다.
    
    - **ticker**: 조회할 주식의 티커 심볼
    """
    try:
        result = await analyzer.get_financial_info(ticker)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"재무 정보 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/batch/analyze", tags=["Batch"])
async def batch_analyze(
    tickers: str = Query(..., description="분석할 티커들 (쉼표로 구분)"),
    period: str = Query("1y", description="분석 기간")
):
    """
    여러 주식을 한 번에 분석합니다.
    
    - **tickers**: 분석할 티커들 (쉼표로 구분, 예: AAPL,MSFT,GOOGL)
    - **period**: 분석 기간
    """
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        results = {}
        
        for ticker in ticker_list:
            if ticker:
                result = await analyzer.analyze_stock(ticker, period)
                results[ticker] = result
        
        return {
            "period": period,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"배치 분석 중 오류가 발생했습니다: {str(e)}")

@app.get("/popular", tags=["Popular"])
async def get_popular_stocks():
    """인기 주식 목록을 반환합니다."""
    return {
        "미국 주식": {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc.",
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "NVDA": "NVIDIA Corporation",
            "META": "Meta Platforms Inc.",
            "NFLX": "Netflix Inc.",
            "COIN": "Coinbase Global Inc.",
            "AMD": "Advanced Micro Devices Inc."
        },
        "한국 주식": {
            "005930.KS": "삼성전자",
            "000660.KS": "SK하이닉스",
            "035420.KS": "NAVER",
            "051910.KS": "LG화학",
            "006400.KS": "삼성SDI",
            "035720.KS": "카카오",
            "207940.KS": "삼성바이오로직스",
            "068270.KS": "셀트리온",
            "323410.KS": "카카오뱅크",
            "373220.KS": "LG에너지솔루션"
        }
    }

@app.get("/search/{query}", tags=["Search"])
async def search_stocks(query: str):
    """
    주식 검색 기능 (간단한 구현)
    
    - **query**: 검색할 키워드
    """
    try:
        # 간단한 검색 구현 (실제로는 더 정교한 검색이 필요)
        popular_stocks = {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation",
            "GOOGL": "Alphabet Inc.",
            "AMZN": "Amazon.com Inc.",
            "TSLA": "Tesla Inc.",
            "005930.KS": "삼성전자",
            "000660.KS": "SK하이닉스"
        }
        
        results = {}
        query_upper = query.upper()
        
        for ticker, name in popular_stocks.items():
            if query_upper in ticker or query_upper in name.upper():
                results[ticker] = name
        
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

# 에러 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": exc.detail, "status_code": exc.status_code}

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return {"error": "내부 서버 오류", "message": str(exc)}

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 