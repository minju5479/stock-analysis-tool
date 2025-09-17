"""
재무 건전성 분석 모듈
"""

from typing import Any, Dict

class FinancialHealthAnalyzer:
    def analyze(self, financial_info: Dict[str, Any]) -> Dict[str, Any]:
        """재무 건전성 지표를 분석합니다."""
        return {
            "debt_to_equity": financial_info.get("debtToEquity", "N/A"),
            "current_ratio": financial_info.get("currentRatio", "N/A"),
            "quick_ratio": financial_info.get("quickRatio", "N/A")
        }
