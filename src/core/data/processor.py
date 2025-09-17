"""
주식 데이터 전처리를 위한 모듈
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    @staticmethod
    def preprocess_price_data(df: pd.DataFrame) -> pd.DataFrame:
        """가격 데이터를 전처리합니다."""
        try:
            # 결측치 처리 (새로운 방식 사용)
            df = df.ffill().bfill()
            
            # 이상치 처리 (IQR 방법)
            for col in ['Open', 'High', 'Low', 'Close']:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # 이상치를 경계값으로 대체
                df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
            
            # 거래량 음수 처리
            df['Volume'] = df['Volume'].clip(lower=0)
            
            return df
            
        except Exception as e:
            logger.error(f"데이터 전처리 중 오류 발생: {str(e)}")
            raise
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
        """수익률을 계산합니다."""
        try:
            # 일간 수익률
            df['Daily_Return'] = df['Close'].pct_change()
            
            # 누적 수익률
            df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
            
            # 변동성
            df['Volatility'] = df['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
            
            return df
            
        except Exception as e:
            logger.error(f"수익률 계산 중 오류 발생: {str(e)}")
            raise
    
    @staticmethod
    def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
        """시간 관련 특성을 추가합니다."""
        try:
            # 연도, 월, 요일 추출
            df['Year'] = df.index.year
            df['Month'] = df.index.month
            df['Weekday'] = df.index.weekday
            
            # 월말, 월초 여부
            df['Is_Month_End'] = df.index.is_month_end.astype(int)
            df['Is_Month_Start'] = df.index.is_month_start.astype(int)
            
            # 분기
            df['Quarter'] = df.index.quarter
            
            return df
            
        except Exception as e:
            logger.error(f"시간 특성 추가 중 오류 발생: {str(e)}")
            raise
    
    def process_stock_data(self, df: pd.DataFrame, include_features: bool = True) -> pd.DataFrame:
        """모든 데이터 처리 단계를 수행합니다."""
        try:
            # 기본 전처리
            df = self.preprocess_price_data(df)
            
            # 수익률 계산
            df = self.calculate_returns(df)
            
            # 시간 특성 추가 (선택적)
            if include_features:
                df = self.add_time_features(df)
            
            return df
            
        except Exception as e:
            logger.error(f"데이터 처리 중 오류 발생: {str(e)}")
            raise
