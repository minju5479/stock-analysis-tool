"""
변동성 분석 모듈
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

class VolatilityAnalyzer:
    """변동성 분석 클래스"""
    
    @staticmethod
    def analyze_volatility(hist: pd.DataFrame) -> Dict[str, Any]:
        """변동성 분석을 수행합니다."""
        returns = hist['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # 연간 변동성
        
        return {
            "annual_volatility": round(volatility * 100, 2),
            "daily_volatility": round(returns.std() * 100, 2),
            "interpretation": VolatilityAnalyzer._interpret_volatility(volatility)
        }
    
    @staticmethod
    def _interpret_volatility(volatility: float) -> str:
        """변동성 해석"""
        if volatility > 0.4:
            return "높은 변동성 (고위험)"
        elif volatility > 0.2:
            return "보통 변동성"
        return "낮은 변동성 (안정적)"
