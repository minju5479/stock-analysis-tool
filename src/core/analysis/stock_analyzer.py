"""
주식 분석 도구의 메인 분석기 모듈
"""

import asyncio
import logging
from typing import Dict, Any
import yfinance as yf
import pandas as pd
from datetime import datetime

from .technical.indicators import TechnicalAnalyzer
from .technical.volume import VolumeAnalyzer
from .technical.volatility import VolatilityAnalyzer
from .technical.trend import TrendAnalyzer
from .financial.analyzer import FinancialAnalyzer
from .financial.earnings import EarningsAnalyzer
from ..utils.exceptions import (
    StockAnalysisError, InvalidTickerError, DataNotFoundError,
    ValidationError, NetworkError, EmptyDataError
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockAnalyzer:
    """주식 분석기 클래스"""
    
    def __init__(self):
        self.technical_analyzer = TechnicalAnalyzer()
        self.volume_analyzer = VolumeAnalyzer()
        self.volatility_analyzer = VolatilityAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.financial_analyzer = FinancialAnalyzer()
        self.earnings_analyzer = EarningsAnalyzer()

    async def analyze_stock(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        """주식 종합 분석을 수행합니다."""
        try:
            if not ticker:
                raise ValidationError("티커가 필요합니다")
            
            ticker = ticker.upper()
            
            try:
                # 주식 데이터 가져오기
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period=period)
            except Exception as e:
                raise NetworkError(f"데이터를 가져오는 중 네트워크 오류 발생: {str(e)}")
            
            if hist.empty:
                raise DataNotFoundError(f"티커 {ticker}에 대한 데이터를 찾을 수 없습니다")
            
            # 기본 정보
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            # 각종 분석 수행
            technical_indicators = self.technical_analyzer.analyze_technical_indicators(hist)
            volume_analysis = self.volume_analyzer.analyze_volume(hist)
            volatility_analysis = self.volatility_analyzer.analyze_volatility(hist)
            trend_analysis = self.trend_analyzer.analyze_trend(hist)
            
            # 재무 분석 수행
            financial_analysis = self.financial_analyzer.analyze_financial_metrics(info)
            
            # 어닝콜 및 가이던스 분석 수행
            earnings_analysis = self.earnings_analyzer.get_comprehensive_earnings_analysis(ticker)
            
            result = {
                "ticker": ticker,
                "analysis_period": period,
                "basic_info": {
                    "current_price": round(current_price, 2),
                    "previous_price": round(prev_price, 2),
                    "price_change": round(price_change, 2),
                    "price_change_percentage": round(price_change_pct, 2),
                    "company_name": info.get('longName', 'N/A'),
                    "sector": info.get('sector', 'N/A'),
                    "industry": info.get('industry', 'N/A'),
                    "market_cap": info.get('marketCap', 'N/A'),
                    "pe_ratio": info.get('trailingPE', 'N/A'),
                    "dividend_yield": info.get('dividendYield', 'N/A')
                },
                "financial_analysis": financial_analysis,
                "earnings_analysis": earnings_analysis,
                "technical_indicators": technical_indicators,
                "volume_analysis": volume_analysis,
                "volatility_analysis": volatility_analysis,
                "trend_analysis": trend_analysis,
                "summary": self._generate_summary(
                    price_change_pct, technical_indicators,
                    volume_analysis, trend_analysis
                )
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing stock {ticker}: {str(e)}")
            if isinstance(e, StockAnalysisError):
                return {"error": str(e)}
            logger.exception("Unexpected error during stock analysis")
            return {"error": "내부 서버 오류가 발생했습니다"}

    async def get_stock_price(self, ticker: str) -> Dict[str, Any]:
        """주식 현재 가격 정보를 조회합니다."""
        try:
            if not ticker:
                raise ValidationError("티커가 필요합니다")
                
            ticker = ticker.upper()
            
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="5d")
            except Exception as e:
                raise NetworkError(f"데이터를 가져오는 중 네트워크 오류 발생: {str(e)}")
            
            if hist.empty:
                raise DataNotFoundError(f"티커 {ticker}에 대한 데이터를 찾을 수 없습니다")
            
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            return {
                "ticker": ticker,
                "current_price": round(current_price, 2),
                "previous_close": round(prev_price, 2),
                "price_change": round(price_change, 2),
                "price_change_percentage": round(price_change_pct, 2),
                "open": round(hist['Open'].iloc[-1], 2),
                "high": round(hist['High'].iloc[-1], 2),
                "low": round(hist['Low'].iloc[-1], 2),
                "volume": int(hist['Volume'].iloc[-1]),
                "company_name": info.get('longName', 'N/A'),
                "currency": info.get('currency', 'USD'),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting stock price for {ticker}: {str(e)}")
            if isinstance(e, StockAnalysisError):
                return {"error": str(e)}
            logger.exception("Unexpected error during stock price retrieval")
            return {"error": "내부 서버 오류가 발생했습니다"}

    def _generate_summary(self, price_change_pct: float, technical_indicators: Dict,
                        volume_analysis: Dict, trend_analysis: Dict) -> str:
        """분석 요약을 생성합니다."""
        summary_parts = []
        
        # 가격 변화
        if price_change_pct > 0:
            summary_parts.append(f"주가가 {abs(price_change_pct):.2f}% 상승했습니다.")
        else:
            summary_parts.append(f"주가가 {abs(price_change_pct):.2f}% 하락했습니다.")
        
        # RSI 해석
        rsi = technical_indicators.get('rsi', {}).get('current', 50)
        if rsi > 70:
            summary_parts.append("RSI가 과매수 구간에 있어 주의가 필요합니다.")
        elif rsi < 30:
            summary_parts.append("RSI가 과매도 구간에 있어 매수 기회일 수 있습니다.")
        
        # 추세 해석
        trend_strength = trend_analysis.get('trend_strength', '')
        summary_parts.append(f"전반적인 추세는 {trend_strength}입니다.")
        
        # 거래량 해석
        volume_ratio = volume_analysis.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            summary_parts.append("거래량이 증가하여 현재 움직임에 신뢰성이 있습니다.")
        elif volume_ratio < 0.5:
            summary_parts.append("거래량이 감소하여 현재 움직임의 신뢰성에 주의가 필요합니다.")
        
        return " ".join(summary_parts)
