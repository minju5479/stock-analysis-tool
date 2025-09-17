"""
전략 인터페이스 정의
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import pandas as pd
from dataclasses import dataclass

@dataclass
class Signal:
    date: pd.Timestamp
    action: str  # BUY/SELL/HOLD
    confidence: float
    reason: str
    stop: float | None
    target: float | None
    size: float | None

class Strategy:
    name: str = "base"

    def __init__(self):
        self._ticker = None
        self._point_in_time_financials = None
    
    def set_ticker(self, ticker: str):
        """전략에서 사용할 종목 코드 설정"""
        self._ticker = ticker
        
    def set_financial_data_source(self, financial_data_source):
        """Point-in-Time 재무데이터 소스 설정"""
        self._point_in_time_financials = financial_data_source

    async def get_financial_data_at_date(self, date: pd.Timestamp) -> Optional[Dict[str, Any]]:
        """특정 날짜의 Point-in-Time 재무데이터 조회"""
        if not self._point_in_time_financials or not self._ticker:
            return None
        
        try:
            return await self._point_in_time_financials.get_financial_data_at_date(
                self._ticker, date.to_pydatetime()
            )
        except Exception:
            return None

    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        raise NotImplementedError

    def latest_signal(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> Signal:
        sigs = self.compute_signals(df, params)
        row = sigs.iloc[-1]
        return Signal(
            date=row.name,
            action=row["action"],
            confidence=row["confidence"],
            reason=row["reason"],
            stop=row.get("stop"),
            target=row.get("target"),
            size=row.get("size"),
        )
