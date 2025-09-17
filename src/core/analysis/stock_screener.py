"""
저평가 종목 스크리닝 모듈
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime
import time


class UndervaluedStockScreener:
    """저평가 종목을 찾는 스크리너 클래스"""
    
    def __init__(self):
        # 한국 주요 종목 리스트 (예시)
        self.korean_stocks = [
            # 대형주
            "005930.KS",  # 삼성전자
            "000660.KS",  # SK하이닉스
            "035420.KS",  # NAVER
            "005380.KS",  # 현대차
            "006400.KS",  # 삼성SDI
            "035720.KS",  # 카카오
            "051910.KS",  # LG화학
            "096770.KS",  # SK이노베이션
            "003550.KS",  # LG
            "017670.KS",  # SK텔레콤
            
            # 중형주
            "028260.KS",  # 삼성물산
            "009150.KS",  # 삼성전기
            "012330.KS",  # 현대모비스
            "066570.KS",  # LG전자
            "034730.KS",  # SK
            "323410.KS",  # 카카오뱅크
            "086790.KS",  # 하나금융지주
            "316140.KS",  # 우리금융지주
            "105560.KS",  # KB금융
            "138040.KS",  # 메리츠금융지주
        ]
        
        # 미국 주요 종목 리스트 (예시)
        self.us_stocks = [
            # 대형 기술주
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            
            # 금융주  
            "JPM", "BAC", "WFC", "GS", "MS", "C", "USB", "PNC",
            
            # 소비재
            "PG", "KO", "PEP", "WMT", "HD", "MCD", "NKE", "SBUX",
            
            # 헬스케어
            "JNJ", "PFE", "UNH", "ABT", "MRK", "TMO", "DHR", "BMY",
            
            # 산업재
            "BA", "CAT", "GE", "MMM", "HON", "UPS", "RTX", "LMT"
        ]
        
        # 저평가 기준
        self.undervalued_criteria = {
            "pe_ratio_max": 15.0,        # P/E 비율 < 15
            "price_to_book_max": 1.5,    # P/B 비율 < 1.5  
            "price_to_sales_max": 2.0,   # P/S 비율 < 2.0
            "debt_to_equity_max": 0.5,   # 부채비율 < 0.5
            "current_ratio_min": 1.5,    # 유동비율 > 1.5
            "roe_min": 0.10,             # ROE > 10%
            "profit_margin_min": 0.05,   # 순이익률 > 5%
            "revenue_growth_min": 0.05   # 매출성장률 > 5%
        }

    def get_stock_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """개별 종목의 기본 정보를 가져옵니다."""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            if not info or 'longName' not in info:
                return None
                
            return {
                "symbol": symbol,
                "name": info.get("longName", symbol),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "market_cap": info.get("marketCap", 0),
                "current_price": info.get("currentPrice", 0),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "price_to_cash_flow": info.get("priceToFreeCashflow"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "return_on_equity": info.get("returnOnEquity"),
                "profit_margins": info.get("profitMargins"),
                "revenue_growth": info.get("revenueGrowth"),
                "operating_margins": info.get("operatingMargins"),
                "gross_margins": info.get("grossMargins"),
                "book_value": info.get("bookValue"),
                "price_to_earnings_growth": info.get("pegRatio"),
                "enterprise_value": info.get("enterpriseValue"),
                "enterprise_to_revenue": info.get("enterpriseToRevenue"),
                "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "dividend_yield": info.get("dividendYield"),
                "payout_ratio": info.get("payoutRatio")
            }
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def calculate_undervalued_score(self, fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        """저평가 점수를 계산합니다."""
        score = 0
        max_score = 0
        criteria_results = {}
        
        # P/E 비율 체크
        pe_ratio = fundamentals.get("pe_ratio")
        if pe_ratio and isinstance(pe_ratio, (int, float)) and pe_ratio > 0:
            max_score += 1
            if pe_ratio < self.undervalued_criteria["pe_ratio_max"]:
                score += 1
                criteria_results["pe_ratio"] = {"value": pe_ratio, "status": "저평가", "weight": 1}
            else:
                criteria_results["pe_ratio"] = {"value": pe_ratio, "status": "보통", "weight": 1}
        
        # P/B 비율 체크
        pb_ratio = fundamentals.get("price_to_book")
        if pb_ratio and isinstance(pb_ratio, (int, float)) and pb_ratio > 0:
            max_score += 1
            if pb_ratio < self.undervalued_criteria["price_to_book_max"]:
                score += 1
                criteria_results["price_to_book"] = {"value": pb_ratio, "status": "저평가", "weight": 1}
            else:
                criteria_results["price_to_book"] = {"value": pb_ratio, "status": "보통", "weight": 1}
        
        # P/S 비율 체크
        ps_ratio = fundamentals.get("price_to_sales")
        if ps_ratio and isinstance(ps_ratio, (int, float)) and ps_ratio > 0:
            max_score += 1
            if ps_ratio < self.undervalued_criteria["price_to_sales_max"]:
                score += 1
                criteria_results["price_to_sales"] = {"value": ps_ratio, "status": "저평가", "weight": 1}
            else:
                criteria_results["price_to_sales"] = {"value": ps_ratio, "status": "보통", "weight": 1}
        
        # ROE 체크
        roe = fundamentals.get("return_on_equity")
        if roe and isinstance(roe, (int, float)):
            max_score += 1
            if roe > self.undervalued_criteria["roe_min"]:
                score += 1
                criteria_results["return_on_equity"] = {"value": roe, "status": "양호", "weight": 1}
            else:
                criteria_results["return_on_equity"] = {"value": roe, "status": "부족", "weight": 1}
        
        # 순이익률 체크
        profit_margin = fundamentals.get("profit_margins")
        if profit_margin and isinstance(profit_margin, (int, float)):
            max_score += 1
            if profit_margin > self.undervalued_criteria["profit_margin_min"]:
                score += 1
                criteria_results["profit_margins"] = {"value": profit_margin, "status": "양호", "weight": 1}
            else:
                criteria_results["profit_margins"] = {"value": profit_margin, "status": "부족", "weight": 1}
        
        # 부채비율 체크
        debt_to_equity = fundamentals.get("debt_to_equity")
        if debt_to_equity and isinstance(debt_to_equity, (int, float)):
            max_score += 1
            if debt_to_equity < self.undervalued_criteria["debt_to_equity_max"]:
                score += 1
                criteria_results["debt_to_equity"] = {"value": debt_to_equity, "status": "양호", "weight": 1}
            else:
                criteria_results["debt_to_equity"] = {"value": debt_to_equity, "status": "주의", "weight": 1}
        
        # 유동비율 체크
        current_ratio = fundamentals.get("current_ratio")
        if current_ratio and isinstance(current_ratio, (int, float)):
            max_score += 1
            if current_ratio > self.undervalued_criteria["current_ratio_min"]:
                score += 1
                criteria_results["current_ratio"] = {"value": current_ratio, "status": "양호", "weight": 1}
            else:
                criteria_results["current_ratio"] = {"value": current_ratio, "status": "부족", "weight": 1}
        
        # 점수 계산
        undervalued_ratio = score / max_score if max_score > 0 else 0
        
        # 추천등급 결정
        if undervalued_ratio >= 0.75:
            recommendation = "강력매수"
        elif undervalued_ratio >= 0.60:
            recommendation = "매수"
        elif undervalued_ratio >= 0.40:
            recommendation = "보유"
        else:
            recommendation = "관망"
        
        return {
            "undervalued_score": score,
            "max_score": max_score,
            "undervalued_ratio": undervalued_ratio,
            "criteria_results": criteria_results,
            "recommendation": recommendation
        }

    def screen_stocks(self, 
                     stock_list: List[str] = None, 
                     market: str = "mixed",
                     min_market_cap: float = 0,
                     progress_callback: Callable = None) -> pd.DataFrame:
        """저평가 종목을 스크리닝합니다."""
        
        # 종목 리스트 결정
        if stock_list:
            symbols = stock_list
        elif market == "korean":
            symbols = self.korean_stocks
        elif market == "us":
            symbols = self.us_stocks
        else:  # mixed
            symbols = self.korean_stocks + self.us_stocks
        
        results = []
        total_stocks = len(symbols)
        
        print(f"📊 총 {total_stocks}개 종목 분석 시작...")
        
        for i, symbol in enumerate(symbols):
            try:
                # 진행률 업데이트
                if progress_callback:
                    progress_callback(i + 1, total_stocks, symbol)
                else:
                    print(f"분석 중: {symbol} ({i+1}/{total_stocks})")
                
                # 기본 정보 가져오기
                fundamentals = self.get_stock_fundamentals(symbol)
                if not fundamentals:
                    continue
                
                # 시가총액 필터
                market_cap = fundamentals.get("market_cap", 0)
                if market_cap < min_market_cap:
                    continue
                
                # 저평가 점수 계산
                valuation_analysis = self.calculate_undervalued_score(fundamentals)
                
                # 결과에 추가
                result = {**fundamentals, **valuation_analysis}
                results.append(result)
                
                # API 제한을 위한 딜레이
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {str(e)}")
                continue
        
        # DataFrame 생성 및 정렬
        if not results:
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        
        # 저평가 비율이 높은 순으로 정렬
        df = df.sort_values("undervalued_ratio", ascending=False)
        
        # 인덱스 리셋
        df.reset_index(drop=True, inplace=True)
        
        print(f"✅ 분석 완료! 총 {len(df)}개 종목 분석됨")
        
        return df

    def get_top_undervalued(self, 
                           df: pd.DataFrame, 
                           top_n: int = 10, 
                           min_score_ratio: float = 0.5) -> pd.DataFrame:
        """상위 저평가 종목을 반환합니다."""
        
        # 최소 점수 비율 이상인 종목만 필터링
        filtered_df = df[df["undervalued_ratio"] >= min_score_ratio].copy()
        
        # 상위 N개 선택
        return filtered_df.head(top_n)

    def export_results(self, df: pd.DataFrame, filename: str = None) -> str:
        """결과를 파일로 내보냅니다."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"undervalued_stocks_{timestamp}.csv"
        
        filepath = f"results/{filename}"
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        print(f"📁 결과가 {filepath}에 저장되었습니다.")
        return filepath

    def print_summary(self, df: pd.DataFrame, top_n: int = 10):
        """분석 결과 요약을 출력합니다."""
        if df.empty:
            print("분석된 데이터가 없습니다.")
            return
        
        print(f"\n📈 저평가 종목 분석 결과 (상위 {min(top_n, len(df))}개)")
        print("=" * 80)
        
        top_stocks = self.get_top_undervalued(df, top_n)
        
        for idx, row in top_stocks.iterrows():
            print(f"\n{idx + 1}. {row['name']} ({row['symbol']})")
            print(f"   섹터: {row['sector']}")
            print(f"   현재가: ${row['current_price']:.2f}" if row['current_price'] else "   현재가: N/A")
            print(f"   저평가 점수: {row['undervalued_score']}/{row['max_score']} ({row['undervalued_ratio']:.1%})")
            print(f"   추천: {row['recommendation']}")
            
            # 주요 지표
            if row.get('pe_ratio'):
                print(f"   P/E: {row['pe_ratio']:.2f}")
            if row.get('price_to_book'):
                print(f"   P/B: {row['price_to_book']:.2f}")
            if row.get('return_on_equity'):
                print(f"   ROE: {row['return_on_equity']:.1%}")
        
        print(f"\n📊 분석 통계:")
        print(f"   - 총 분석 종목: {len(df)}개")
        print(f"   - 저평가 종목 (60% 이상): {len(df[df['undervalued_ratio'] >= 0.6])}개")
        print(f"   - 강력매수 추천: {len(df[df['recommendation'] == '강력매수'])}개")
        print(f"   - 매수 추천: {len(df[df['recommendation'] == '매수'])}개")

    def screen_korean_stocks(self, min_score: float = 6.0, max_results: int = 20, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """한국 주식 저평가 종목 스크리닝"""
        results = []
        
        for symbol in self.korean_stocks:
            try:
                fundamentals = self.get_stock_fundamentals(symbol)
                if not fundamentals:
                    continue
                    
                # 필터 적용 (None 값 안전 처리)
                if filters:
                    # 시가총액 필터
                    market_cap = fundamentals.get('market_cap', 0) or 0
                    if filters.get('min_market_cap', 0) > market_cap:
                        continue
                    
                    # P/E 비율 필터
                    pe_ratio = fundamentals.get('pe_ratio') or 0
                    if pe_ratio > 0 and filters.get('max_pe_ratio', 100) < pe_ratio:
                        continue
                    
                    # ROE 필터
                    roe = fundamentals.get('return_on_equity') or 0
                    if filters.get('min_roe', -1) > roe:
                        continue
                    
                    # 유동비율 필터
                    current_ratio = fundamentals.get('current_ratio') or 0
                    if filters.get('min_current_ratio', 0) > current_ratio:
                        continue
                
                valuation = self.calculate_undervalued_score(fundamentals)
                
                # 10점 만점으로 환산한 점수 계산
                score_out_of_10 = (valuation['undervalued_ratio'] * 10) if valuation['max_score'] > 0 else 0
                
                if score_out_of_10 >= min_score:
                    result = {
                        'ticker': symbol,
                        'company_name': fundamentals.get('name', symbol),
                        'sector': fundamentals.get('sector', 'Unknown'),
                        'current_price': fundamentals.get('current_price', 0) or 0,
                        'market_cap': fundamentals.get('market_cap', 0) or 0,
                        'pe_ratio': fundamentals.get('pe_ratio', 0) or 0,
                        'pb_ratio': fundamentals.get('price_to_book', 0) or 0,
                        'ps_ratio': fundamentals.get('price_to_sales', 0) or 0,
                        'roe': fundamentals.get('return_on_equity', 0) or 0,
                        'debt_ratio': fundamentals.get('debt_to_equity', 0) or 0,
                        'current_ratio': fundamentals.get('current_ratio', 0) or 0,
                        'high_52w': fundamentals.get('52_week_high', 0) or 0,
                        'low_52w': fundamentals.get('52_week_low', 0) or 0,
                        'undervalued_score': score_out_of_10
                    }
                    results.append(result)
                
                # API 제한을 위한 딜레이
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                continue
        
        # 점수 순으로 정렬
        results.sort(key=lambda x: x['undervalued_score'], reverse=True)
        return results[:max_results]
    
    def screen_us_stocks(self, min_score: float = 6.0, max_results: int = 20, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """미국 주식 저평가 종목 스크리닝"""
        results = []
        
        for symbol in self.us_stocks:
            try:
                fundamentals = self.get_stock_fundamentals(symbol)
                if not fundamentals:
                    continue
                    
                # 필터 적용 (None 값 안전 처리)
                if filters:
                    # 시가총액 필터
                    market_cap = fundamentals.get('market_cap', 0) or 0
                    if filters.get('min_market_cap', 0) > market_cap:
                        continue
                    
                    # P/E 비율 필터
                    pe_ratio = fundamentals.get('pe_ratio') or 0
                    if pe_ratio > 0 and filters.get('max_pe_ratio', 100) < pe_ratio:
                        continue
                    
                    # ROE 필터
                    roe = fundamentals.get('return_on_equity') or 0
                    if filters.get('min_roe', -1) > roe:
                        continue
                    
                    # 유동비율 필터
                    current_ratio = fundamentals.get('current_ratio') or 0
                    if filters.get('min_current_ratio', 0) > current_ratio:
                        continue
                
                valuation = self.calculate_undervalued_score(fundamentals)
                
                # 10점 만점으로 환산한 점수 계산
                score_out_of_10 = (valuation['undervalued_ratio'] * 10) if valuation['max_score'] > 0 else 0
                
                if score_out_of_10 >= min_score:
                    result = {
                        'ticker': symbol,
                        'company_name': fundamentals.get('name', symbol),
                        'sector': fundamentals.get('sector', 'Unknown'),
                        'current_price': fundamentals.get('current_price', 0) or 0,
                        'market_cap': fundamentals.get('market_cap', 0) or 0,
                        'pe_ratio': fundamentals.get('pe_ratio', 0) or 0,
                        'pb_ratio': fundamentals.get('price_to_book', 0) or 0,
                        'ps_ratio': fundamentals.get('price_to_sales', 0) or 0,
                        'roe': fundamentals.get('return_on_equity', 0) or 0,
                        'debt_ratio': fundamentals.get('debt_to_equity', 0) or 0,
                        'current_ratio': fundamentals.get('current_ratio', 0) or 0,
                        'high_52w': fundamentals.get('52_week_high', 0) or 0,
                        'low_52w': fundamentals.get('52_week_low', 0) or 0,
                        'undervalued_score': score_out_of_10
                    }
                    results.append(result)
                
                # API 제한을 위한 딜레이
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                continue
        
        # 점수 순으로 정렬
        results.sort(key=lambda x: x['undervalued_score'], reverse=True)
        return results[:max_results]
