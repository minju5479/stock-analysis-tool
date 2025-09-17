"""
차트 생성 관련 API 라우트
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict
import logging
from datetime import datetime

from ...core.data import StockDataFetcher, DataProcessor
from ...core.chart import ChartAnalyzer
from ..schemas.models import ChartData, ErrorResponse
from ...core.utils.exceptions import StockAnalysisError

router = APIRouter(prefix="/charts", tags=["charts"])
logger = logging.getLogger(__name__)

@router.get("/{ticker}/{chart_type}", response_model=ChartData)
async def get_chart(
    ticker: str,
    chart_type: str = Query(..., regex="^(candlestick|price|technical)$"),
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")
):
    """차트를 생성합니다."""
    try:
        fetcher = StockDataFetcher()
        processor = DataProcessor()
        chart_analyzer = ChartAnalyzer()

        # 데이터 조회 및 처리
        hist = await fetcher.get_stock_data(ticker, period)
        processed_data = processor.process_stock_data(hist)

        # 기술적 지표 계산 (차트용 평면 키)
        indicators = chart_analyzer.calculate_technical_indicators(processed_data)

        # 차트 타입에 따라 적절한 차트 생성
        if chart_type == "candlestick":
            fig = chart_analyzer.create_candlestick_chart(processed_data, ticker, indicators)
        elif chart_type == "price":
            fig = chart_analyzer.create_price_chart(processed_data, ticker)
        else:  # technical
            fig = chart_analyzer.create_technical_analysis_chart(processed_data, ticker, indicators)

        # HTML로 변환
        html_content = fig.to_html(include_plotlyjs=True, full_html=False)

        return ChartData(
            ticker=ticker,
            period=period,
            chart_type=chart_type,
            html_content=html_content
        )
    except StockAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating chart for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")
