#!/usr/bin/env python3
"""
Stock Analysis MCP Server
주식 티커를 입력받아 종합적인 분석을 제공하는 MCP 서버
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from bs4 import BeautifulSoup

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockAnalysisMCPServer:
    def __init__(self):
        self.server = Server("stock-analysis-mcp")
        self.setup_tools()
    
    def setup_tools(self):
        """MCP 도구들을 설정합니다."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """사용 가능한 도구 목록을 반환합니다."""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="analyze_stock",
                        description="주식 티커를 입력받아 종합적인 분석을 제공합니다",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "ticker": {
                                    "type": "string",
                                    "description": "분석할 주식의 티커 심볼 (예: AAPL, MSFT, 005930.KS)"
                                },
                                "period": {
                                    "type": "string",
                                    "description": "분석 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)",
                                    "default": "1y"
                                }
                            },
                            "required": ["ticker"]
                        }
                    ),
                    Tool(
                        name="get_stock_price",
                        description="주식의 현재 가격 정보를 조회합니다",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "ticker": {
                                    "type": "string",
                                    "description": "조회할 주식의 티커 심볼"
                                }
                            },
                            "required": ["ticker"]
                        }
                    ),
                    Tool(
                        name="get_technical_indicators",
                        description="주식의 기술적 지표를 계산합니다",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "ticker": {
                                    "type": "string",
                                    "description": "분석할 주식의 티커 심볼"
                                },
                                "period": {
                                    "type": "string",
                                    "description": "분석 기간",
                                    "default": "1y"
                                }
                            },
                            "required": ["ticker"]
                        }
                    ),
                    Tool(
                        name="get_financial_info",
                        description="주식의 재무 정보를 조회합니다",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "ticker": {
                                    "type": "string",
                                    "description": "조회할 주식의 티커 심볼"
                                }
                            },
                            "required": ["ticker"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """도구 호출을 처리합니다."""
            try:
                if name == "analyze_stock":
                    result = await self.analyze_stock(arguments)
                elif name == "get_stock_price":
                    result = await self.get_stock_price(arguments)
                elif name == "get_technical_indicators":
                    result = await self.get_technical_indicators(arguments)
                elif name == "get_financial_info":
                    result = await self.get_financial_info(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return CallToolResult(
                    content=[
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                )
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return CallToolResult(
                    content=[
                        {
                            "type": "text",
                            "text": json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)
                        }
                    ]
                )
    
    async def analyze_stock(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """주식 종합 분석을 수행합니다."""
        ticker = arguments.get("ticker", "").upper()
        period = arguments.get("period", "1y")
        
        if not ticker:
            return {"error": "티커가 필요합니다"}
        
        try:
            # 주식 정보 가져오기
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 가격 데이터 가져오기
            hist = stock.history(period=period)
            
            if hist.empty:
                return {"error": f"티커 {ticker}에 대한 데이터를 찾을 수 없습니다"}
            
            # 기본 정보
            current_price = hist['Close'].iloc[-1]
            prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            # 기술적 지표 계산
            technical_indicators = self.calculate_technical_indicators(hist)
            
            # 거래량 분석
            volume_analysis = self.analyze_volume(hist)
            
            # 변동성 분석
            volatility_analysis = self.analyze_volatility(hist)
            
            # 추세 분석
            trend_analysis = self.analyze_trend(hist)
            
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
                "technical_indicators": technical_indicators,
                "volume_analysis": volume_analysis,
                "volatility_analysis": volatility_analysis,
                "trend_analysis": trend_analysis,
                "summary": self.generate_summary(
                    current_price, price_change_pct, technical_indicators, 
                    volume_analysis, volatility_analysis, trend_analysis
                )
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing stock {ticker}: {str(e)}")
            return {"error": f"주식 분석 중 오류가 발생했습니다: {str(e)}"}
    
    async def get_stock_price(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """주식 현재 가격 정보를 조회합니다."""
        ticker = arguments.get("ticker", "").upper()
        
        if not ticker:
            return {"error": "티커가 필요합니다"}
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 최근 가격 데이터
            hist = stock.history(period="5d")
            
            if hist.empty:
                return {"error": f"티커 {ticker}에 대한 데이터를 찾을 수 없습니다"}
            
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
            return {"error": f"가격 조회 중 오류가 발생했습니다: {str(e)}"}
    
    async def get_technical_indicators(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """기술적 지표를 계산합니다."""
        ticker = arguments.get("ticker", "").upper()
        period = arguments.get("period", "1y")
        
        if not ticker:
            return {"error": "티커가 필요합니다"}
        
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                return {"error": f"티커 {ticker}에 대한 데이터를 찾을 수 없습니다"}
            
            technical_indicators = self.calculate_technical_indicators(hist)
            
            return {
                "ticker": ticker,
                "period": period,
                "technical_indicators": technical_indicators
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators for {ticker}: {str(e)}")
            return {"error": f"기술적 지표 계산 중 오류가 발생했습니다: {str(e)}"}
    
    async def get_financial_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """재무 정보를 조회합니다."""
        ticker = arguments.get("ticker", "").upper()
        
        if not ticker:
            return {"error": "티커가 필요합니다"}
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 재무 정보 추출
            financial_info = {
                "market_cap": info.get('marketCap', 'N/A'),
                "enterprise_value": info.get('enterpriseValue', 'N/A'),
                "pe_ratio": info.get('trailingPE', 'N/A'),
                "forward_pe": info.get('forwardPE', 'N/A'),
                "price_to_book": info.get('priceToBook', 'N/A'),
                "price_to_sales": info.get('priceToSalesTrailing12Months', 'N/A'),
                "dividend_yield": info.get('dividendYield', 'N/A'),
                "dividend_rate": info.get('dividendRate', 'N/A'),
                "payout_ratio": info.get('payoutRatio', 'N/A'),
                "debt_to_equity": info.get('debtToEquity', 'N/A'),
                "current_ratio": info.get('currentRatio', 'N/A'),
                "quick_ratio": info.get('quickRatio', 'N/A'),
                "return_on_equity": info.get('returnOnEquity', 'N/A'),
                "return_on_assets": info.get('returnOnAssets', 'N/A'),
                "profit_margins": info.get('profitMargins', 'N/A'),
                "operating_margins": info.get('operatingMargins', 'N/A'),
                "revenue_growth": info.get('revenueGrowth', 'N/A'),
                "earnings_growth": info.get('earningsGrowth', 'N/A'),
                "beta": info.get('beta', 'N/A'),
                "52_week_high": info.get('fiftyTwoWeekHigh', 'N/A'),
                "52_week_low": info.get('fiftyTwoWeekLow', 'N/A'),
                "50_day_average": info.get('fiftyDayAverage', 'N/A'),
                "200_day_average": info.get('twoHundredDayAverage', 'N/A')
            }
            
            return {
                "ticker": ticker,
                "financial_info": financial_info,
                "company_info": {
                    "name": info.get('longName', 'N/A'),
                    "sector": info.get('sector', 'N/A'),
                    "industry": info.get('industry', 'N/A'),
                    "country": info.get('country', 'N/A'),
                    "currency": info.get('currency', 'N/A'),
                    "exchange": info.get('exchange', 'N/A')
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting financial info for {ticker}: {str(e)}")
            return {"error": f"재무 정보 조회 중 오류가 발생했습니다: {str(e)}"}
    
    def calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """기술적 지표를 계산합니다."""
        if hist.empty:
            return {}
        
        close_prices = hist['Close']
        
        # 이동평균
        ma_20 = close_prices.rolling(window=20).mean().iloc[-1]
        ma_50 = close_prices.rolling(window=50).mean().iloc[-1]
        ma_200 = close_prices.rolling(window=200).mean().iloc[-1]
        
        # RSI 계산
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # MACD 계산
        ema_12 = close_prices.ewm(span=12).mean()
        ema_26 = close_prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        macd_histogram = macd - signal
        
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_histogram = macd_histogram.iloc[-1]
        
        # 볼린저 밴드
        bb_20 = close_prices.rolling(window=20).mean()
        bb_std = close_prices.rolling(window=20).std()
        bb_upper = bb_20 + (bb_std * 2)
        bb_lower = bb_20 - (bb_std * 2)
        
        current_bb_upper = bb_upper.iloc[-1]
        current_bb_lower = bb_lower.iloc[-1]
        current_bb_middle = bb_20.iloc[-1]
        
        # 스토캐스틱
        low_14 = hist['Low'].rolling(window=14).min()
        high_14 = hist['High'].rolling(window=14).max()
        k_percent = 100 * ((close_prices - low_14) / (high_14 - low_14))
        d_percent = k_percent.rolling(window=3).mean()
        
        current_k = k_percent.iloc[-1]
        current_d = d_percent.iloc[-1]
        
        return {
            "moving_averages": {
                "ma_20": round(ma_20, 2),
                "ma_50": round(ma_50, 2),
                "ma_200": round(ma_200, 2)
            },
            "rsi": {
                "current": round(current_rsi, 2),
                "interpretation": self.interpret_rsi(current_rsi)
            },
            "macd": {
                "macd_line": round(current_macd, 2),
                "signal_line": round(current_signal, 2),
                "histogram": round(current_histogram, 2),
                "interpretation": self.interpret_macd(current_macd, current_signal)
            },
            "bollinger_bands": {
                "upper": round(current_bb_upper, 2),
                "middle": round(current_bb_middle, 2),
                "lower": round(current_bb_lower, 2),
                "interpretation": self.interpret_bollinger_bands(
                    close_prices.iloc[-1], current_bb_upper, current_bb_lower
                )
            },
            "stochastic": {
                "k_percent": round(current_k, 2),
                "d_percent": round(current_d, 2),
                "interpretation": self.interpret_stochastic(current_k, current_d)
            }
        }
    
    def analyze_volume(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """거래량 분석을 수행합니다."""
        if hist.empty:
            return {}
        
        volume = hist['Volume']
        avg_volume = volume.mean()
        current_volume = volume.iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        return {
            "current_volume": int(current_volume),
            "average_volume": int(avg_volume),
            "volume_ratio": round(volume_ratio, 2),
            "interpretation": self.interpret_volume(volume_ratio)
        }
    
    def analyze_volatility(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """변동성 분석을 수행합니다."""
        if hist.empty:
            return {}
        
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # 연간 변동성
        
        return {
            "annual_volatility": round(volatility * 100, 2),
            "daily_volatility": round(returns.std() * 100, 2),
            "interpretation": self.interpret_volatility(volatility)
        }
    
    def analyze_trend(self, hist: pd.DataFrame) -> Dict[str, Any]:
        """추세 분석을 수행합니다."""
        if hist.empty:
            return {}
        
        close_prices = hist['Close']
        
        # 단기 추세 (5일)
        short_trend = (close_prices.iloc[-1] - close_prices.iloc[-5]) / close_prices.iloc[-5] * 100 if len(close_prices) >= 5 else 0
        
        # 중기 추세 (20일)
        medium_trend = (close_prices.iloc[-1] - close_prices.iloc[-20]) / close_prices.iloc[-20] * 100 if len(close_prices) >= 20 else 0
        
        # 장기 추세 (60일)
        long_trend = (close_prices.iloc[-1] - close_prices.iloc[-60]) / close_prices.iloc[-60] * 100 if len(close_prices) >= 60 else 0
        
        return {
            "short_term_trend": round(short_trend, 2),
            "medium_term_trend": round(medium_trend, 2),
            "long_term_trend": round(long_trend, 2),
            "trend_strength": self.assess_trend_strength(short_trend, medium_trend, long_trend)
        }
    
    def interpret_rsi(self, rsi: float) -> str:
        """RSI 해석"""
        if rsi > 70:
            return "과매수 구간 (매도 신호)"
        elif rsi < 30:
            return "과매도 구간 (매수 신호)"
        else:
            return "중립 구간"
    
    def interpret_macd(self, macd: float, signal: float) -> str:
        """MACD 해석"""
        if macd > signal:
            return "상승 신호 (MACD가 시그널선 위)"
        else:
            return "하락 신호 (MACD가 시그널선 아래)"
    
    def interpret_bollinger_bands(self, price: float, upper: float, lower: float) -> str:
        """볼린저 밴드 해석"""
        if price > upper:
            return "상단 밴드 돌파 (과매수 가능성)"
        elif price < lower:
            return "하단 밴드 돌파 (과매도 가능성)"
        else:
            return "밴드 내 정상 범위"
    
    def interpret_stochastic(self, k: float, d: float) -> str:
        """스토캐스틱 해석"""
        if k > 80 and d > 80:
            return "과매수 구간"
        elif k < 20 and d < 20:
            return "과매도 구간"
        else:
            return "중립 구간"
    
    def interpret_volume(self, volume_ratio: float) -> str:
        """거래량 해석"""
        if volume_ratio > 2.0:
            return "거래량 급증 (주목할 만한 움직임)"
        elif volume_ratio > 1.5:
            return "거래량 증가"
        elif volume_ratio < 0.5:
            return "거래량 감소"
        else:
            return "정상 거래량"
    
    def interpret_volatility(self, volatility: float) -> str:
        """변동성 해석"""
        if volatility > 0.4:
            return "높은 변동성 (고위험)"
        elif volatility > 0.2:
            return "보통 변동성"
        else:
            return "낮은 변동성 (안정적)"
    
    def assess_trend_strength(self, short: float, medium: float, long: float) -> str:
        """추세 강도 평가"""
        if short > 0 and medium > 0 and long > 0:
            return "강한 상승 추세"
        elif short < 0 and medium < 0 and long < 0:
            return "강한 하락 추세"
        elif short > 0 and medium > 0:
            return "상승 추세"
        elif short < 0 and medium < 0:
            return "하락 추세"
        else:
            return "혼조세"
    
    def generate_summary(self, current_price: float, price_change_pct: float, 
                        technical_indicators: Dict, volume_analysis: Dict,
                        volatility_analysis: Dict, trend_analysis: Dict) -> str:
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

async def main():
    """메인 함수"""
    server = StockAnalysisMCPServer()
    
    # stdio 서버로 실행
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="stock-analysis-mcp",
                server_version="1.0.0",
                capabilities=server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 