"""
밸류에이션 분석 모듈
"""

from typing import Any, Dict, List, Tuple
import yfinance as yf
import pandas as pd
import numpy as np

class ValuationAnalyzer:
    def __init__(self):
        # 저평가 기준 (업계 평균 대비)
        self.undervalued_criteria = {
            "pe_ratio": 15.0,        # P/E 비율 < 15
            "price_to_book": 1.5,    # P/B 비율 < 1.5  
            "price_to_sales": 2.0,   # P/S 비율 < 2.0
            "price_to_cash_flow": 10.0,  # P/CF 비율 < 10
            "enterprise_value_ebitda": 10.0,  # EV/EBITDA < 10
            "debt_to_equity": 0.5,   # 부채비율 < 0.5
            "current_ratio": 1.5,    # 유동비율 > 1.5
            "roe": 0.10,            # ROE > 10%
            "profit_margin": 0.05    # 순이익률 > 5%
        }

    def analyze(self, financial_info: Dict[str, Any]) -> Dict[str, Any]:
        """밸류에이션 지표를 분석합니다."""
        return {
            "pe_ratio": financial_info.get("trailingPE", "N/A"),
            "forward_pe": financial_info.get("forwardPE", "N/A"),
            "price_to_book": financial_info.get("priceToBook", "N/A"),
            "price_to_sales": financial_info.get("priceToSalesTrailing12Months", "N/A"),
            "price_to_cash_flow": financial_info.get("priceToFreeCashflow", "N/A"),
            "enterprise_value_ebitda": financial_info.get("enterpriseToEbitda", "N/A"),
            "debt_to_equity": financial_info.get("debtToEquity", "N/A"),
            "current_ratio": financial_info.get("currentRatio", "N/A"),
            "return_on_equity": financial_info.get("returnOnEquity", "N/A"),
            "profit_margins": financial_info.get("profitMargins", "N/A")
        }

    def is_undervalued(self, financial_info: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """종목이 저평가되었는지 판단합니다."""
        valuation_metrics = self.analyze(financial_info)
        undervalued_score = 0
        total_criteria = 0
        
        criteria_results = {}
        
        # P/E 비율 체크
        pe_ratio = valuation_metrics.get("pe_ratio")
        if pe_ratio and pe_ratio != "N/A" and isinstance(pe_ratio, (int, float)):
            total_criteria += 1
            if pe_ratio < self.undervalued_criteria["pe_ratio"]:
                undervalued_score += 1
                criteria_results["pe_ratio"] = {"value": pe_ratio, "status": "저평가"}
            else:
                criteria_results["pe_ratio"] = {"value": pe_ratio, "status": "보통"}
        
        # P/B 비율 체크
        pb_ratio = valuation_metrics.get("price_to_book")
        if pb_ratio and pb_ratio != "N/A" and isinstance(pb_ratio, (int, float)):
            total_criteria += 1
            if pb_ratio < self.undervalued_criteria["price_to_book"]:
                undervalued_score += 1
                criteria_results["price_to_book"] = {"value": pb_ratio, "status": "저평가"}
            else:
                criteria_results["price_to_book"] = {"value": pb_ratio, "status": "보통"}
        
        # P/S 비율 체크
        ps_ratio = valuation_metrics.get("price_to_sales")
        if ps_ratio and ps_ratio != "N/A" and isinstance(ps_ratio, (int, float)):
            total_criteria += 1
            if ps_ratio < self.undervalued_criteria["price_to_sales"]:
                undervalued_score += 1
                criteria_results["price_to_sales"] = {"value": ps_ratio, "status": "저평가"}
            else:
                criteria_results["price_to_sales"] = {"value": ps_ratio, "status": "보통"}
        
        # ROE 체크
        roe = valuation_metrics.get("return_on_equity")
        if roe and roe != "N/A" and isinstance(roe, (int, float)):
            total_criteria += 1
            if roe > self.undervalued_criteria["roe"]:
                undervalued_score += 1
                criteria_results["return_on_equity"] = {"value": roe, "status": "양호"}
            else:
                criteria_results["return_on_equity"] = {"value": roe, "status": "부족"}
        
        # 종합 평가
        if total_criteria > 0:
            undervalued_ratio = undervalued_score / total_criteria
            is_undervalued = undervalued_ratio >= 0.6  # 60% 이상 기준 충족시 저평가
            
            return is_undervalued, {
                "undervalued_score": undervalued_score,
                "total_criteria": total_criteria,
                "undervalued_ratio": undervalued_ratio,
                "criteria_results": criteria_results,
                "recommendation": "매수" if is_undervalued else "관망"
            }
        
        return False, {"error": "분석할 수 있는 데이터가 부족합니다"}

    def screen_undervalued_stocks(self, stock_symbols: List[str], progress_callback=None) -> pd.DataFrame:
        """여러 종목의 저평가 여부를 스크리닝합니다."""
        results = []
        total_stocks = len(stock_symbols)
        
        for i, symbol in enumerate(stock_symbols):
            try:
                # 진행률 콜백 호출
                if progress_callback:
                    progress_callback(i + 1, total_stocks, symbol)
                
                # 종목 정보 가져오기
                stock = yf.Ticker(symbol)
                info = stock.info
                
                if not info or 'longName' not in info:
                    continue
                
                # 저평가 분석
                is_undervalued, analysis = self.is_undervalued(info)
                
                if "error" not in analysis:
                    results.append({
                        "symbol": symbol,
                        "name": info.get("longName", symbol),
                        "sector": info.get("sector", "Unknown"),
                        "market_cap": info.get("marketCap", 0),
                        "current_price": info.get("currentPrice", 0),
                        "pe_ratio": info.get("trailingPE", None),
                        "pb_ratio": info.get("priceToBook", None),
                        "ps_ratio": info.get("priceToSalesTrailing12Months", None),
                        "roe": info.get("returnOnEquity", None),
                        "is_undervalued": is_undervalued,
                        "undervalued_score": analysis["undervalued_score"],
                        "total_criteria": analysis["total_criteria"],
                        "undervalued_ratio": analysis["undervalued_ratio"],
                        "recommendation": analysis["recommendation"]
                    })
                    
            except Exception as e:
                print(f"Error analyzing {symbol}: {str(e)}")
                continue
        
        # DataFrame으로 변환하고 저평가 점수순으로 정렬
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values("undervalued_ratio", ascending=False)
            
        return df
