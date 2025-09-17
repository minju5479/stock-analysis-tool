"""
주식 분석 도구의 데이터 검증을 위한 클래스
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import re
from datetime import datetime, timedelta

class DataValidator:
    @staticmethod
    def validate_ticker(ticker: str) -> bool:
        """티커 심볼의 유효성을 검증합니다."""
        if not ticker:
            return False
        
        # 기본 티커 형식 검증 (알파벳, 숫자, 점만 허용)
        if not re.match(r'^[A-Za-z0-9.]+$', ticker):
            return False
        
        # 한국 주식 티커 형식 검증 (예: 005930.KS)
        if ticker.endswith('.KS') or ticker.endswith('.KQ'):
            code_part = ticker.split('.')[0]
            if not (len(code_part) == 6 and code_part.isdigit()):
                return False
        
        return True

    @staticmethod
    def validate_period(period: str) -> bool:
        """기간 문자열의 유효성을 검증합니다."""
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        return period in valid_periods

    @staticmethod
    def validate_price_data(hist: pd.DataFrame) -> bool:
        """가격 데이터의 유효성을 검증합니다."""
        import logging
        logger = logging.getLogger(__name__)
        
        if hist is None or hist.empty:
            logger.warning("가격 데이터가 비어있거나 None입니다.")
            return False
        
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in hist.columns]
        if missing_columns:
            logger.warning(f"필수 컬럼이 누락되었습니다: {missing_columns}")
            return False
        
        # 데이터 타입 검증
        for col in required_columns:
            if not pd.api.types.is_numeric_dtype(hist[col]):
                return False
        
        # 값 범위 검증
        if (hist[['Open', 'High', 'Low', 'Close']] < 0).any().any():
            logger.warning("가격 데이터에 음수 값이 포함되어 있습니다.")
            return False
        
        if (hist['Volume'] < 0).any():
            logger.warning("거래량 데이터에 음수 값이 포함되어 있습니다.")
            return False
        
        # 논리적 관계 검증
        price_relations = [
            ('High', '>=', 'Low', "고가가 저가보다 낮은 데이터가 있습니다"),
            ('High', '>=', 'Open', "고가가 시가보다 낮은 데이터가 있습니다"),
            ('High', '>=', 'Close', "고가가 종가보다 낮은 데이터가 있습니다"),
            ('Open', '>=', 'Low', "시가가 저가보다 낮은 데이터가 있습니다"),
            ('Close', '>=', 'Low', "종가가 저가보다 낮은 데이터가 있습니다")
        ]
        
        for col1, op, col2, msg in price_relations:
            if not (hist[col1] >= hist[col2]).all():
                logger.warning(msg)
                return False
        
        return True

    @staticmethod
    def validate_financial_data(data: Dict[str, Any]) -> bool:
        """재무 데이터의 유효성을 검증합니다."""
        if not isinstance(data, dict):
            return False
        
        required_fields = ['market_cap', 'pe_ratio', 'dividend_yield']
        if not all(field in data for field in required_fields):
            return False
        
        # 숫자 필드 검증
        numeric_fields = [
            'market_cap', 'pe_ratio', 'dividend_yield', 
            'price_to_book', 'price_to_sales', 'debt_to_equity'
        ]
        
        for field in numeric_fields:
            if field in data and data[field] != 'N/A':
                try:
                    float(data[field])
                except (ValueError, TypeError):
                    return False
        
        return True

    @staticmethod
    def validate_technical_data(data: Dict[str, Any]) -> bool:
        """기술적 지표 데이터의 유효성을 검증합니다."""
        if not isinstance(data, dict):
            return False
        
        # 필수 필드 검증
        required_sections = ['moving_averages', 'rsi', 'macd', 'bollinger_bands']
        if not all(section in data for section in required_sections):
            return False
        
        # 이동평균 검증
        ma = data.get('moving_averages', {})
        if not all(k in ma for k in ['ma_20', 'ma_50', 'ma_200']):
            return False
        
        # RSI 검증
        rsi = data.get('rsi', {})
        if not all(k in rsi for k in ['current', 'interpretation']):
            return False
        if not (0 <= float(rsi['current']) <= 100):
            return False
        
        # MACD 검증
        macd = data.get('macd', {})
        if not all(k in macd for k in ['macd_line', 'signal_line', 'histogram', 'interpretation']):
            return False
        
        # 볼린저 밴드 검증
        bb = data.get('bollinger_bands', {})
        if not all(k in bb for k in ['upper', 'middle', 'lower']):
            return False
        if not (float(bb['lower']) <= float(bb['middle']) <= float(bb['upper'])):
            return False
        
        return True
