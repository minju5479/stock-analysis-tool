"""
어닝콜 및 가이던스 데이터 수집을 위한 모듈
"""

import requests
import yfinance as yf
from bs4 import BeautifulSoup
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import warnings

# yfinance의 deprecation 경고 억제
warnings.filterwarnings("ignore", category=DeprecationWarning, module="yfinance")

class EarningsAnalyzer:
    """어닝콜 및 가이던스 분석 클래스"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_earnings_calendar(self, ticker: str) -> Dict[str, Any]:
        """어닝 캘린더 정보를 가져옵니다."""
        try:
            stock = yf.Ticker(ticker)
            calendar = stock.calendar
            
            if calendar is not None and not calendar.empty:
                earnings_data = {
                    "upcoming_earnings": [],
                    "recent_earnings": []
                }
                
                for index, row in calendar.iterrows():
                    earning_info = {
                        "date": index.strftime("%Y-%m-%d") if hasattr(index, 'strftime') else str(index),
                        "eps_estimate": row.get('EPS Estimate', 'N/A'),
                        "reported_eps": row.get('Reported EPS', 'N/A'),
                        "surprise": row.get('Surprise(%)', 'N/A')
                    }
                    
                    if index > datetime.now():
                        earnings_data["upcoming_earnings"].append(earning_info)
                    else:
                        earnings_data["recent_earnings"].append(earning_info)
                
                return earnings_data
            
            return {"error": "어닝 캘린더 데이터를 찾을 수 없습니다."}
            
        except Exception as e:
            return {"error": f"어닝 캘린더 조회 오류: {str(e)}"}
    
    def get_earnings_history(self, ticker: str, limit: int = 4) -> List[Dict[str, Any]]:
        """최근 어닝 발표 이력을 가져옵니다."""
        try:
            stock = yf.Ticker(ticker)
            
            # 분기별 재무 데이터 - deprecated API 대신 income_stmt 사용
            quarterly_income = stock.quarterly_income_stmt
            quarterly_financials = stock.quarterly_financials
            
            earnings_history = []
            
            # 내부: 분기 문자열 생성 (YYYY Q1~Q4)
            def _format_quarter(dt_obj) -> str:
                try:
                    ts = pd.Timestamp(dt_obj)
                    q = (int(ts.month) - 1) // 3 + 1
                    return f"{ts.year} Q{q}"
                except Exception:
                    # 포맷 실패 시 날짜 문자열 반환
                    return str(dt_obj)
            
            if quarterly_income is not None and not quarterly_income.empty:
                # Net Income을 earnings로 사용
                net_income_row = quarterly_income.loc[quarterly_income.index.str.contains('Net Income', case=False, na=False)]
                
                if not net_income_row.empty:
                    net_income_data = net_income_row.iloc[0]  # 첫 번째 Net Income 행 사용
                    
                    # Revenue 데이터도 가져오기
                    revenue_row = quarterly_income.loc[quarterly_income.index.str.contains('Total Revenue|Revenue', case=False, na=False)]
                    revenue_data = revenue_row.iloc[0] if not revenue_row.empty else None
                    
            for i, (date, net_income) in enumerate(net_income_data.head(limit).items()):
                        if i >= limit:
                            break
                            
                        revenue = revenue_data[date] if revenue_data is not None else 'N/A'
                        
                        quarter_data = {
                "quarter": _format_quarter(date),
                            "date": date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date),
                            "revenue": revenue if revenue != 'N/A' else 'N/A',
                            "earnings": net_income if pd.notna(net_income) else 'N/A',
                            "eps": self._calculate_eps(net_income if pd.notna(net_income) else 0, stock.info.get('sharesOutstanding', 1))
                        }
                        earnings_history.append(quarter_data)
            
            return earnings_history
            
        except Exception as e:
            return [{"error": f"어닝 이력 조회 오류: {str(e)}"}]
    
    def get_analyst_estimates(self, ticker: str) -> Dict[str, Any]:
        """애널리스트 추정치를 가져옵니다 (yfinance 최신 API 기준)."""
        try:
            stock = yf.Ticker(ticker)

            estimates: Dict[str, Dict[str, Any]] = {
                "current_quarter": {"eps_estimate": "N/A", "revenue_estimate": "N/A"},
                "next_quarter": {"eps_estimate": "N/A", "revenue_estimate": "N/A"},
                "current_year": {"eps_estimate": "N/A", "revenue_estimate": "N/A"},
                "next_year": {"eps_estimate": "N/A", "revenue_estimate": "N/A"},
                "recommendations": {}
            }

            # 1) earnings_estimate / revenue_estimate 활용 (yfinance 0.2.x 권장 경로)
            try:
                eps_df = getattr(stock, "earnings_estimate", None)
                rev_df = getattr(stock, "revenue_estimate", None)

                def find_row(df: Optional[pd.DataFrame], keys: list[str]) -> Optional[pd.Series]:
                    if df is None or not hasattr(df, "empty") or df.empty:
                        return None
                    # 인덱스가 period라 가정: '0q', '+1q', '0y', '+1y'
                    try:
                        # 인덱스를 문자열로 비교
                        idx_str = df.index.astype(str)
                        for k in keys:
                            # 정확히 일치하는 첫 행 반환
                            matches = [i for i, s in enumerate(idx_str) if s.lower() == k.lower()]
                            if matches:
                                return df.iloc[matches[0]]
                    except Exception:
                        return None
                    return None

                row_keys = {
                    "current_quarter": ["0q"],
                    "next_quarter": ["+1q", "1q"],
                    "current_year": ["0y"],
                    "next_year": ["+1y", "1y"],
                }

                for label, keys in row_keys.items():
                    eps_row = find_row(eps_df, keys)
                    rev_row = find_row(rev_df, keys)

                    # EPS 추정치
                    if eps_row is not None:
                        val = eps_row.get("avg", None)
                        if pd.notna(val):
                            estimates[label]["eps_estimate"] = float(val)
                    # 매출 추정치
                    if rev_row is not None:
                        val = rev_row.get("avg", None)
                        if pd.notna(val):
                            estimates[label]["revenue_estimate"] = float(val)
            except Exception:
                # DataFrame 접근 실패 시 다음 단계 진행
                pass

            # 2) 애널리스트 추천 (yfinance 0.2.x 형식)
            try:
                recommendations = getattr(stock, "recommendations", None)
                if recommendations is not None and not recommendations.empty:
                    latest_row = None
                    # period 컬럼이 있으면 0m가 최신
                    if "period" in recommendations.columns:
                        zero_m = recommendations[recommendations["period"].astype(str).str.lower() == "0m"]
                        latest_row = zero_m.iloc[0] if not zero_m.empty else recommendations.iloc[0]
                    else:
                        latest_row = recommendations.iloc[-1]

                    if latest_row is not None:
                        estimates["recommendations"] = {
                            "strong_buy": int(latest_row.get('strongBuy', 0)),
                            "buy": int(latest_row.get('buy', 0)),
                            "hold": int(latest_row.get('hold', 0)),
                            "sell": int(latest_row.get('sell', 0)),
                            "strong_sell": int(latest_row.get('strongSell', 0)),
                            "recommendation_key": "N/A"
                        }
            except Exception:
                pass

            return estimates

        except Exception as e:
            return {"error": f"애널리스트 추정치 조회 오류: {str(e)}"}
    
    def get_guidance_info(self, ticker: str) -> Dict[str, Any]:
        """회사 가이던스 정보를 가져옵니다 (제한적)."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            guidance = {
                "forward_pe": info.get('forwardPE', 'N/A'),
                "forward_eps": info.get('forwardEps', 'N/A'),
                "peg_ratio": info.get('pegRatio', 'N/A'),
                "price_to_book": info.get('priceToBook', 'N/A'),
                "revenue_growth": info.get('revenueGrowth', 'N/A'),
                "earnings_growth": info.get('earningsGrowth', 'N/A'),
                "analyst_target_price": info.get('targetMeanPrice', 'N/A'),
                "recommendation_mean": info.get('recommendationMean', 'N/A'),
                "number_of_analyst_opinions": info.get('numberOfAnalystOpinions', 'N/A')
            }
            
            # 추천 의견 해석
            rec_mean = guidance.get("recommendation_mean")
            if isinstance(rec_mean, (int, float)):
                if rec_mean <= 1.5:
                    guidance["recommendation_text"] = "강력 매수"
                elif rec_mean <= 2.5:
                    guidance["recommendation_text"] = "매수"
                elif rec_mean <= 3.5:
                    guidance["recommendation_text"] = "보유"
                elif rec_mean <= 4.5:
                    guidance["recommendation_text"] = "매도"
                else:
                    guidance["recommendation_text"] = "강력 매도"
            else:
                guidance["recommendation_text"] = "N/A"
            
            return guidance
            
        except Exception as e:
            return {"error": f"가이던스 정보 조회 오류: {str(e)}"}
    
    def _calculate_eps(self, earnings: float, shares_outstanding: int) -> float:
        """EPS를 계산합니다."""
        try:
            if shares_outstanding and earnings:
                return round(earnings / shares_outstanding, 2)
            return 0.0
        except:
            return 0.0
    
    def get_comprehensive_earnings_analysis(self, ticker: str) -> Dict[str, Any]:
        """종합적인 어닝 분석을 수행합니다."""
        try:
            analysis = {
                "ticker": ticker.upper(),
                "analysis_date": datetime.now().isoformat(),
                "earnings_calendar": self.get_earnings_calendar(ticker),
                "earnings_history": self.get_earnings_history(ticker),
                "analyst_estimates": self.get_analyst_estimates(ticker),
                "guidance": self.get_guidance_info(ticker),
                "summary": self._generate_earnings_summary(ticker)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"종합 어닝 분석 오류: {str(e)}"}
    
    def _generate_earnings_summary(self, ticker: str) -> str:
        """어닝 분석 요약을 생성합니다."""
        try:
            guidance = self.get_guidance_info(ticker)
            
            summary_parts = []
            
            # 애널리스트 추천
            rec_text = guidance.get("recommendation_text", "N/A")
            if rec_text != "N/A":
                summary_parts.append(f"애널리스트 추천: {rec_text}")
            
            # 타겟 가격
            target_price = guidance.get("analyst_target_price")
            if target_price and target_price != "N/A":
                summary_parts.append(f"애널리스트 목표가: ${target_price:.2f}")
            
            # Forward P/E
            forward_pe = guidance.get("forward_pe")
            if forward_pe and forward_pe != "N/A":
                summary_parts.append(f"Forward P/E: {forward_pe:.2f}")
            
            # 성장률
            earnings_growth = guidance.get("earnings_growth")
            if earnings_growth and earnings_growth != "N/A":
                growth_pct = earnings_growth * 100
                summary_parts.append(f"예상 순이익 성장률: {growth_pct:.1f}%")
            
            return " | ".join(summary_parts) if summary_parts else "어닝 데이터 분석 중..."
            
        except Exception as e:
            return f"요약 생성 오류: {str(e)}"


# 사용 예시
async def main():
    """테스트 함수"""
    analyzer = EarningsAnalyzer()
    
    # Apple 어닝 분석
    result = analyzer.get_comprehensive_earnings_analysis("AAPL")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
