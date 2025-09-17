"""
API 응답 모델을 정의하는 모듈
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class StockPrice(BaseModel):
    """주식 가격 정보 모델"""
    ticker: str
    current_price: float
    previous_close: float
    price_change: float
    price_change_percentage: float
    open: float
    high: float
    low: float
    volume: int
    company_name: str = Field(default="N/A")
    currency: str = Field(default="USD")
    timestamp: datetime

class TechnicalIndicators(BaseModel):
    """기술적 지표 모델"""
    ticker: str
    period: str
    moving_averages: Dict[str, float]
    rsi: Dict[str, Any]
    macd: Dict[str, Any]
    bollinger_bands: Dict[str, float]
    volume_analysis: Dict[str, Any]
    stochastic: Optional[Dict[str, Any]]

class FinancialMetrics(BaseModel):
    """재무 지표 모델"""
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    price_to_book: Optional[float]
    price_to_sales: Optional[float]
    debt_to_equity: Optional[float]

class StockAnalysis(BaseModel):
    """종합 주식 분석 모델"""
    ticker: str
    analysis_period: str
    basic_info: Dict[str, Any]
    financial_analysis: FinancialMetrics
    technical_indicators: TechnicalIndicators
    volume_analysis: Dict[str, Any]
    volatility_analysis: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    summary: str

class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ChartData(BaseModel):
    """차트 데이터 모델"""
    ticker: str
    period: str
    chart_type: str
    html_content: str
