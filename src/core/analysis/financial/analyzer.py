"""
재무 분석 통합 모듈
"""

import logging
from typing import Any, Dict
from .profitability import ProfitabilityAnalyzer
from .valuation import ValuationAnalyzer
from .health import FinancialHealthAnalyzer
from .growth import GrowthAnalyzer
from .dividend import DividendAnalyzer

logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    def __init__(self):
        self.profitability_analyzer = ProfitabilityAnalyzer()
        self.valuation_analyzer = ValuationAnalyzer()
        self.health_analyzer = FinancialHealthAnalyzer()
        self.growth_analyzer = GrowthAnalyzer()
        self.dividend_analyzer = DividendAnalyzer()
    
    def analyze_financial_metrics(self, financial_info: Dict[str, Any]) -> Dict[str, Any]:
        """재무 지표를 분석합니다."""
        analysis = {}
        
        # 각 영역별 분석 수행
        analysis["profitability"] = self.profitability_analyzer.analyze(financial_info)
        analysis["valuation"] = self.valuation_analyzer.analyze(financial_info)
        analysis["financial_health"] = self.health_analyzer.analyze(financial_info)
        analysis["growth"] = self.growth_analyzer.analyze(financial_info)
        analysis["dividend"] = self.dividend_analyzer.analyze(financial_info)
        
        # 종합 평가
        analysis["summary"] = self.generate_financial_summary(analysis)
        
        return analysis

    def generate_financial_summary(self, analysis: Dict[str, Any]) -> str:
        """재무 분석 요약을 생성합니다."""
        summary_parts = []
        
        # 수익성 평가
        profit_margin = analysis["profitability"].get("profit_margin", "N/A")
        if profit_margin != "N/A" and isinstance(profit_margin, (int, float)):
            if profit_margin > 0.2:
                summary_parts.append("높은 수익성을 보이고 있습니다")
            elif profit_margin > 0.1:
                summary_parts.append("양호한 수익성을 보이고 있습니다")
            elif profit_margin > 0:
                summary_parts.append("낮은 수익성을 보이고 있습니다")
        
        # 재무 건전성 평가
        debt_to_equity = analysis["financial_health"].get("debt_to_equity", "N/A")
        if debt_to_equity != "N/A" and isinstance(debt_to_equity, (int, float)):
            if debt_to_equity < 1:
                summary_parts.append("재무구조가 안정적입니다")
            elif debt_to_equity < 2:
                summary_parts.append("재무구조가 보통 수준입니다")
            else:
                summary_parts.append("부채비율이 높은 편입니다")
        
        # 성장성 평가
        revenue_growth = analysis["growth"].get("revenue_growth", "N/A")
        if revenue_growth != "N/A" and isinstance(revenue_growth, (int, float)):
            if revenue_growth > 0.2:
                summary_parts.append("높은 매출 성장을 보이고 있습니다")
            elif revenue_growth > 0:
                summary_parts.append("안정적인 매출 성장을 보이고 있습니다")
            else:
                summary_parts.append("매출이 감소 추세입니다")
        
        return " ".join(summary_parts) if summary_parts else "충분한 재무 데이터가 없습니다"
