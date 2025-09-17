"""
추세 분석 모듈
"""

import pandas as pd
from typing import Dict, Any

class TrendAnalyzer:
    """추세 분석 클래스"""
    
    @staticmethod
    def analyze_trend(hist: pd.DataFrame) -> Dict[str, Any]:
        """추세 분석을 수행합니다."""
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
            "trend_strength": TrendAnalyzer._assess_trend_strength(short_trend, medium_trend, long_trend)
        }
    
    @staticmethod
    def _assess_trend_strength(short: float, medium: float, long: float) -> str:
        """추세 강도 평가"""
        if short > 0 and medium > 0 and long > 0:
            return "강한 상승 추세"
        elif short < 0 and medium < 0 and long < 0:
            return "강한 하락 추세"
        elif short > 0 and medium > 0:
            return "상승 추세"
        elif short < 0 and medium < 0:
            return "하락 추세"
        return "혼조세"
