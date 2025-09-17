"""
주식 데이터 수집을 위한 모듈
"""

import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from ..utils.exceptions import DataNotFoundError, NetworkError

logger = logging.getLogger(__name__)

class StockDataFetcher:
    def __init__(self):
        self.cache = {}  # 간단한 메모리 캐시
    
    async def get_stock_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """주식 데이터를 가져옵니다."""
        try:
            cache_key = f"{ticker}_{period}"
            
            # 캐시된 데이터가 있는지 확인
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"캐시된 데이터를 사용합니다: {ticker}")
                return cached_data
            
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            if hist.empty:
                raise DataNotFoundError(f"티커 {ticker}에 대한 데이터를 찾을 수 없습니다")
            
            # 데이터 캐시에 저장
            self.cache[cache_key] = hist
            
            return hist
            
        except DataNotFoundError:
            raise
        except Exception as e:
            raise NetworkError(f"데이터 조회 실패: {str(e)}")
    
    async def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """주식의 기본 정보를 가져옵니다."""
        try:
            cache_key = f"{ticker}_info"
            
            # 캐시된 데이터가 있는지 확인
            cached_info = self.cache.get(cache_key)
            if cached_info is not None:
                logger.info(f"캐시된 정보를 사용합니다: {ticker}")
                return cached_info
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                raise DataNotFoundError(f"티커 {ticker}에 대한 정보를 찾을 수 없습니다")
            
            # 데이터 캐시에 저장
            self.cache[cache_key] = info
            
            return info
            
        except DataNotFoundError:
            raise
        except Exception as e:
            raise NetworkError(f"정보 조회 실패: {str(e)}")
    
    def clear_cache(self, ticker: Optional[str] = None):
        """캐시를 초기화합니다."""
        if ticker:
            # 특정 티커의 캐시만 삭제
            keys_to_delete = [k for k in self.cache.keys() if k.startswith(f"{ticker}_")]
            for key in keys_to_delete:
                del self.cache[key]
            logger.info(f"{ticker} 캐시가 초기화되었습니다.")
        else:
            # 전체 캐시 삭제
            self.cache.clear()
            logger.info("전체 캐시가 초기화되었습니다.")
