"""
성장성 분석 모듈
"""

from typing import Any, Dict

class GrowthAnalyzer:
    def analyze(self, financial_info: Dict[str, Any]) -> Dict[str, Any]:
        """성장성 지표를 분석합니다."""
        return {
            "revenue_growth": financial_info.get("revenueGrowth", "N/A"),
            "earnings_growth": financial_info.get("earningsGrowth", "N/A")
        }
