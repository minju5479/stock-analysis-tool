"""
Point-in-Time 재무데이터 수집 및 관리
특정 시점에 실제로 알 수 있었던 재무정보만을 제공
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


class PointInTimeFinancialData:
    """Point-in-Time 재무데이터 관리 클래스"""
    
    def __init__(self):
        self._cache = {}  # ticker -> DataFrame 캐시
        
    async def get_financial_data_at_date(self, ticker: str, target_date: datetime) -> Optional[Dict[str, Any]]:
        """
        특정 날짜에 실제로 알 수 있었던 재무정보를 반환
        
        Args:
            ticker: 종목 코드
            target_date: 기준 날짜
            
        Returns:
            해당 시점에 알 수 있었던 재무정보 딕셔너리
        """
        try:
            # 캐시된 데이터가 있으면 사용
            if ticker in self._cache:
                financial_history = self._cache[ticker]
            else:
                # 재무데이터 수집 및 캐시
                financial_history = await self._fetch_financial_history(ticker)
                self._cache[ticker] = financial_history
            
            if financial_history is None or financial_history.empty:
                return None
            
            # target_date 이전에 발표된 가장 최신 데이터 찾기
            available_data = financial_history[financial_history.index <= target_date]
            
            if available_data.empty:
                return None
            
            # 가장 최신 데이터 반환
            latest_data = available_data.iloc[-1]
            
            return {
                'report_date': latest_data.name,
                'pe_ratio': latest_data.get('pe_ratio'),
                'pb_ratio': latest_data.get('pb_ratio'),
                'ps_ratio': latest_data.get('ps_ratio'),
                'roe': latest_data.get('roe'),
                'roa': latest_data.get('roa'),
                'debt_to_equity': latest_data.get('debt_to_equity'),
                'current_ratio': latest_data.get('current_ratio'),
                'quick_ratio': latest_data.get('quick_ratio'),
                'profit_margin': latest_data.get('profit_margin'),
                'operating_margin': latest_data.get('operating_margin'),
                'revenue_growth': latest_data.get('revenue_growth'),
                'earnings_growth': latest_data.get('earnings_growth'),
                'dividend_yield': latest_data.get('dividend_yield'),
                'book_value_per_share': latest_data.get('book_value_per_share'),
                'earnings_per_share': latest_data.get('earnings_per_share'),
                'free_cash_flow_per_share': latest_data.get('free_cash_flow_per_share')
            }
            
        except Exception as e:
            logger.error(f"재무데이터 조회 중 오류 ({ticker}, {target_date}): {e}")
            return None
    
    async def _fetch_financial_history(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        종목의 과거 재무데이터 이력을 수집
        분기별 발표 일정을 고려하여 Point-in-Time 데이터 생성
        """
        try:
            stock = yf.Ticker(ticker)
            
            # 기본 정보 및 재무제표 수집
            info = stock.info
            quarterly_financials = stock.quarterly_financials
            quarterly_balance_sheet = stock.quarterly_balance_sheet
            quarterly_cashflow = stock.quarterly_cashflow
            
            if quarterly_financials is None or quarterly_financials.empty:
                logger.warning(f"재무데이터를 찾을 수 없음: {ticker}")
                return None
            
            # 분기별 데이터를 시계열로 정리
            financial_timeline = []
            
            # 분기별 컬럼 순회 (최신부터 과거 순서)
            for quarter_date in quarterly_financials.columns:
                try:
                    # 분기 종료일 기준으로 발표일 추정
                    report_date = self._estimate_report_date(quarter_date)
                    
                    # 해당 분기의 재무지표 수집
                    financial_metrics = await self._extract_financial_metrics(
                        stock, info, quarterly_financials, quarterly_balance_sheet, 
                        quarterly_cashflow, quarter_date
                    )
                    
                    if financial_metrics:
                        financial_metrics['quarter_end'] = quarter_date
                        financial_timeline.append({
                            'report_date': report_date,
                            'data': financial_metrics
                        })
                        
                except Exception as e:
                    logger.warning(f"분기 데이터 처리 중 오류 ({ticker}, {quarter_date}): {e}")
                    continue
            
            if not financial_timeline:
                return None
            
            # DataFrame으로 변환 (발표일 기준으로 인덱스 설정)
            df_data = []
            for item in financial_timeline:
                row_data = item['data'].copy()
                row_data['report_date'] = item['report_date']
                df_data.append(row_data)
            
            if not df_data:
                return None
            
            df = pd.DataFrame(df_data)
            df['report_date'] = pd.to_datetime(df['report_date'])
            df = df.set_index('report_date').sort_index()
            
            logger.info(f"재무데이터 수집 완료: {ticker} ({len(df)}개 분기)")
            return df
            
        except Exception as e:
            logger.error(f"재무데이터 수집 중 오류 ({ticker}): {e}")
            return None
    
    def _estimate_report_date(self, quarter_end_date: datetime) -> datetime:
        """
        분기 종료일을 기준으로 실제 발표일 추정
        일반적으로 분기 종료 후 45-60일 후 발표
        """
        try:
            quarter_end = pd.to_datetime(quarter_end_date)
            
            # 분기별 발표일 추정
            if quarter_end.month == 3:  # 1분기
                report_date = datetime(quarter_end.year, 5, 15)
            elif quarter_end.month == 6:  # 2분기  
                report_date = datetime(quarter_end.year, 8, 15)
            elif quarter_end.month == 9:  # 3분기
                report_date = datetime(quarter_end.year, 11, 15)
            elif quarter_end.month == 12:  # 4분기
                report_date = datetime(quarter_end.year + 1, 3, 31)
            else:
                # 기본값: 분기 종료 후 60일
                report_date = quarter_end + timedelta(days=60)
            
            return report_date
            
        except Exception:
            # 예외 발생 시 기본값 반환
            return pd.to_datetime(quarter_end_date) + timedelta(days=60)
    
    async def _extract_financial_metrics(
        self, 
        stock, 
        info: Dict, 
        financials: pd.DataFrame, 
        balance_sheet: pd.DataFrame,
        cashflow: pd.DataFrame, 
        quarter_date
    ) -> Optional[Dict[str, float]]:
        """특정 분기의 재무지표 추출"""
        try:
            metrics = {}
            
            # 현재 주가 정보에서 일부 비율 계산
            current_price = info.get('currentPrice', info.get('regularMarketPrice'))
            shares_outstanding = info.get('sharesOutstanding')
            market_cap = info.get('marketCap')
            
            # 손익계산서에서 추출
            if quarter_date in financials.columns:
                total_revenue = financials.loc['Total Revenue', quarter_date] if 'Total Revenue' in financials.index else None
                net_income = financials.loc['Net Income', quarter_date] if 'Net Income' in financials.index else None
                operating_income = financials.loc['Operating Income', quarter_date] if 'Operating Income' in financials.index else None
                
                # 수익성 지표
                if total_revenue and total_revenue != 0:
                    if net_income:
                        metrics['profit_margin'] = float(net_income / total_revenue)
                    if operating_income:
                        metrics['operating_margin'] = float(operating_income / total_revenue)
                
                # EPS 계산
                if net_income and shares_outstanding:
                    eps = net_income / shares_outstanding
                    metrics['earnings_per_share'] = float(eps)
                    
                    # P/E 비율 계산
                    if current_price and eps != 0:
                        metrics['pe_ratio'] = float(current_price / eps)
            
            # 대차대조표에서 추출  
            if quarter_date in balance_sheet.columns:
                total_assets = balance_sheet.loc['Total Assets', quarter_date] if 'Total Assets' in balance_sheet.index else None
                total_equity = balance_sheet.loc['Total Stockholder Equity', quarter_date] if 'Total Stockholder Equity' in balance_sheet.index else None
                total_debt = balance_sheet.loc['Total Debt', quarter_date] if 'Total Debt' in balance_sheet.index else None
                current_assets = balance_sheet.loc['Current Assets', quarter_date] if 'Current Assets' in balance_sheet.index else None
                current_liabilities = balance_sheet.loc['Current Liabilities', quarter_date] if 'Current Liabilities' in balance_sheet.index else None
                
                # 재무 건전성 지표
                if current_assets and current_liabilities and current_liabilities != 0:
                    metrics['current_ratio'] = float(current_assets / current_liabilities)
                
                if total_debt and total_equity and total_equity != 0:
                    metrics['debt_to_equity'] = float(total_debt / total_equity)
                
                # ROE, ROA 계산
                if net_income:
                    if total_equity and total_equity != 0:
                        metrics['roe'] = float(net_income / total_equity)
                    if total_assets and total_assets != 0:
                        metrics['roa'] = float(net_income / total_assets)
                
                # P/B 비율 계산
                if total_equity and shares_outstanding and current_price:
                    book_value_per_share = total_equity / shares_outstanding
                    metrics['book_value_per_share'] = float(book_value_per_share)
                    if book_value_per_share != 0:
                        metrics['pb_ratio'] = float(current_price / book_value_per_share)
            
            # P/S 비율 계산
            if total_revenue and market_cap:
                # 연간화 (분기 데이터를 4배)
                annual_revenue = total_revenue * 4
                metrics['ps_ratio'] = float(market_cap / annual_revenue)
            
            # 성장률 계산 (연간 기준)
            try:
                prev_year_same_quarter = financials.columns[financials.columns.get_loc(quarter_date) + 4] \
                    if financials.columns.get_loc(quarter_date) + 4 < len(financials.columns) else None
                
                if prev_year_same_quarter and total_revenue:
                    prev_revenue = financials.loc['Total Revenue', prev_year_same_quarter] if 'Total Revenue' in financials.index else None
                    if prev_revenue and prev_revenue != 0:
                        metrics['revenue_growth'] = float((total_revenue - prev_revenue) / prev_revenue)
                
                if prev_year_same_quarter and net_income:
                    prev_income = financials.loc['Net Income', prev_year_same_quarter] if 'Net Income' in financials.index else None
                    if prev_income and prev_income != 0:
                        metrics['earnings_growth'] = float((net_income - prev_income) / prev_income)
            except:
                pass  # 성장률 계산 실패는 무시
            
            # 배당 정보 (연간 데이터 사용)
            dividend_yield = info.get('dividendYield')
            if dividend_yield:
                metrics['dividend_yield'] = float(dividend_yield)
            
            return metrics if metrics else None
            
        except Exception as e:
            logger.warning(f"재무지표 추출 중 오류: {e}")
            return None
    
    def clear_cache(self):
        """캐시 초기화"""
        self._cache.clear()
        logger.info("Point-in-Time 재무데이터 캐시가 초기화되었습니다")


# 전역 인스턴스
point_in_time_financials = PointInTimeFinancialData()
