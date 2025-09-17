"""
거래량 분석 모듈
"""

import pandas as pd
from typing import Dict, Any

class VolumeAnalyzer:
    """거래량 분석 클래스"""
    
    @staticmethod
    def analyze_volume(hist: pd.DataFrame) -> Dict[str, Any]:
        """거래량 분석을 수행합니다."""
        volume = hist['Volume']
        avg_volume = volume.mean()
        current_volume = volume.iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        return {
            "current_volume": int(current_volume),
            "average_volume": int(avg_volume),
            "volume_ratio": round(volume_ratio, 2),
            "interpretation": VolumeAnalyzer._interpret_volume(volume_ratio)
        }
    
    @staticmethod
    def _interpret_volume(volume_ratio: float) -> str:
        """거래량 해석"""
        if volume_ratio > 2.0:
            return "거래량 급증 (주목할 만한 움직임)"
        elif volume_ratio > 1.5:
            return "거래량 증가"
        elif volume_ratio < 0.5:
            return "거래량 감소"
        return "정상 거래량"
