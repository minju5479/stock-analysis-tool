"""
간단 백테스트 엔진 (EOD 체결)
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

class BacktestEngine:
    
    def __init__(self, strategy=None):
        """백테스트 엔진 초기화
        
        Args:
            strategy: 사용할 전략 객체 (선택사항)
        """
        self.strategy = strategy
    
    def run_backtest(self, data: pd.DataFrame, initial_capital: float = 100000) -> Dict[str, Any]:
        """전략을 사용하여 백테스트 실행
        
        Args:
            data: 주식 데이터 (OHLCV)
            initial_capital: 초기 자본
            
        Returns:
            백테스트 결과 딕셔너리
        """
        if self.strategy is None:
            raise ValueError("전략이 설정되지 않았습니다")
        
        try:
            # 전략으로부터 신호 생성
            signals_result = self.strategy.compute_signals(data)
            
            if signals_result is None or signals_result.empty:
                return {"trades": [], "equity_curve": [], "final_capital": initial_capital, "initial_capital": initial_capital}
            
            # compute_signals의 결과에서 action 컬럼 추출
            if 'action' in signals_result.columns:
                signal_df = signals_result[['action']].copy()
            else:
                # action 컬럼이 없으면 기본 HOLD로 설정
                signal_df = pd.DataFrame(index=data.index)
                signal_df['action'] = 'HOLD'
            
            # 백테스트 실행
            trades_df, equity_df = self.run(data, signal_df, initial_capital, fee_bps=10.0, slippage_bps=5.0)
            
            # 결과 포맷팅
            trades = trades_df.to_dict('records') if not trades_df.empty else []
            equity_curve = equity_df.to_dict('records') if not equity_df.empty else []
            final_capital = equity_df['equity'].iloc[-1] if not equity_df.empty else initial_capital
            
            return {
                "trades": trades,
                "equity_curve": equity_curve,
                "final_capital": final_capital,
                "initial_capital": initial_capital
            }
            
        except Exception as e:
            print(f"백테스트 실행 중 오류: {e}")
            return {"trades": [], "equity_curve": [], "final_capital": initial_capital, "initial_capital": initial_capital}
    
    def run(self, df: pd.DataFrame, signals: pd.DataFrame, initial_capital: float = 100000, fee_bps: float = 10.0, slippage_bps: float = 10.0) -> Tuple[pd.DataFrame, pd.DataFrame]:
        if df.empty or signals.empty:
            raise ValueError("데이터/시그널이 비어있습니다")

        data = df.copy()
        sig = signals.copy()

        # 체결 룰: 신호 발생 다음 날 시가에 체결
        data["signal"] = sig["action"].reindex(data.index).fillna("HOLD")
        data["signal_shift"] = data["signal"].shift(1).fillna("HOLD")

        pos = 0  # 1: 롱, -1: 숏, 0: 없음 (여기서는 롱/현금만 사용)
        cash = initial_capital
        shares = 0.0
        equity = []
        trades = []

        for i in range(1, len(data)):
            today = data.index[i]
            prev = data.index[i-1]
            open_px = data["Open"].iloc[i]
            close_prev = data["Close"].iloc[i-1]
            action = data["signal_shift"].iloc[i]

            if action == "BUY" and pos == 0:
                # 매수 체결
                fee = open_px * (fee_bps + slippage_bps) / 10000.0
                shares = cash / (open_px + fee)
                cash = 0.0
                pos = 1
                trades.append({"date": today, "action": "BUY", "price": open_px, "shares": shares})
            elif action == "SELL" and pos == 1:
                # 청산 체결
                fee = open_px * (fee_bps + slippage_bps) / 10000.0
                cash = shares * (open_px - fee)
                trades.append({"date": today, "action": "SELL", "price": open_px, "shares": shares})
                shares = 0.0
                pos = 0

            # 자산가치(종가 기준 평가)
            eq = cash + shares * data["Close"].iloc[i]
            equity.append({"date": today, "equity": eq})

        equity_df = pd.DataFrame(equity).set_index("date")
        trades_df = pd.DataFrame(trades)
        return trades_df, equity_df
