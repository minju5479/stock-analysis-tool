"""
백테스트 성과 지표 계산
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict

def compute_metrics(results_or_equity, data: pd.DataFrame = None, freq: int = 252) -> Dict[str, float]:
    """백테스트 결과로부터 성과 지표를 계산합니다.
    
    Args:
        results_or_equity: 백테스트 결과 딕셔너리 또는 equity DataFrame (하위호환성)
        data: 원본 데이터 (사용하지 않음)
        freq: 연간화 빈도 (기본값: 252)
    
    Returns:
        성과 지표 딕셔너리
    """
    
    # 하위호환성: DataFrame이 전달된 경우 기존 방식 사용
    if isinstance(results_or_equity, pd.DataFrame):
        return compute_metrics_legacy(results_or_equity, freq)
    
    # 새로운 방식: results 딕셔너리 처리
    try:
        results = results_or_equity
        equity_curve = results.get('equity_curve', [])
        trades = results.get('trades', [])
        
        if not equity_curve:
            return {
                "cagr": 0.0,
                "volatility": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "total_trades": 0
            }
        
        # equity 시계열 생성
        try:
            if isinstance(equity_curve[0], dict):
                if 'equity' in equity_curve[0]:
                    equity_values = [item['equity'] for item in equity_curve]
                elif 'portfolio_value' in equity_curve[0]:
                    equity_values = [item['portfolio_value'] for item in equity_curve]
                else:
                    equity_values = [list(item.values())[1] for item in equity_curve if len(item.values()) > 1]
            else:
                equity_values = equity_curve
            
            eq = pd.Series(equity_values)
        except Exception as e:
            print(f"Equity 데이터 파싱 중 오류: {e}")
            return {
                "cagr": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0,
                "max_drawdown": 0.0, "win_rate": 0.0, "total_trades": 0
            }
        
        # CAGR 계산
        periods = len(equity_values)
        if periods > 1 and equity_values[0] > 0:
            years = periods / freq
            if years > 0:
                cagr = ((equity_values[-1] / equity_values[0]) ** (1 / years) - 1) * 100
            else:
                cagr = 0.0
        else:
            cagr = 0.0
        
        # 변동성 및 샤프 비율 계산
        if len(eq) > 1:
            returns = eq.pct_change().fillna(0)
            volatility = returns.std() * np.sqrt(freq) * 100
            sharpe_ratio = returns.mean() / (returns.std() + 1e-9) * np.sqrt(freq) if returns.std() > 0 else 0
            
            # 최대 낙폭 계산
            cummax = eq.cummax()
            drawdown = (eq / cummax - 1) * 100
            max_drawdown = drawdown.min()
        else:
            volatility = 0.0
            sharpe_ratio = 0.0
            max_drawdown = 0.0
        
        # 승률 계산
        if trades:
            # 모든 액션 타입 확인
            action_types = set(t.get('action', 'UNKNOWN') for t in trades)
            print(f"발견된 액션 타입들: {action_types}")
            
            buy_trades = [t for t in trades if t.get('action') == 'BUY']
            sell_trades = [t for t in trades if t.get('action') == 'SELL']
            
            # 다른 가능한 액션 이름들도 확인
            if len(buy_trades) == 0 or len(sell_trades) == 0:
                buy_trades_alt = [t for t in trades if t.get('action', '').upper() in ['BUY', 'LONG', 'ENTER', '1']]
                sell_trades_alt = [t for t in trades if t.get('action', '').upper() in ['SELL', 'SHORT', 'EXIT', '-1', '0']]
                print(f"대안 검색 - 매수형: {len(buy_trades_alt)}, 매도형: {len(sell_trades_alt)}")
                if len(buy_trades_alt) > 0 or len(sell_trades_alt) > 0:
                    buy_trades = buy_trades_alt
                    sell_trades = sell_trades_alt
            
            # 디버깅 정보 출력
            print(f"거래 데이터 분석 - 총 거래: {len(trades)}, 매수: {len(buy_trades)}, 매도: {len(sell_trades)}")
            if len(trades) > 0:
                print(f"첫 번째 거래: {trades[0]}")
                print(f"마지막 거래: {trades[-1]}")
            
            winning_trades = 0
            total_trade_pairs = 0
            
            # 시간순으로 거래 정렬
            all_trades = sorted(trades, key=lambda x: x.get('date', ''))
            
            # 매수-매도 쌍 찾기 (실제 거래 순서 기준)
            position = 0
            buy_price = 0
            
            for trade in all_trades:
                action = trade.get('action', '').upper()
                price = trade.get('price', 0)
                
                # 매수 액션 확인 (다양한 형태 지원)
                if action in ['BUY', 'LONG', 'ENTER', '1'] and position == 0:
                    buy_price = price
                    position = 1
                # 매도 액션 확인 (다양한 형태 지원)  
                elif action in ['SELL', 'SHORT', 'EXIT', '-1', '0'] and position == 1:
                    if price > buy_price:
                        winning_trades += 1
                    total_trade_pairs += 1
                    position = 0
                    print(f"거래 완료 - 매수: {buy_price:.2f}, 매도: {price:.2f}, 수익: {((price/buy_price - 1)*100):.2f}%")
            
            win_rate = (winning_trades / total_trade_pairs * 100) if total_trade_pairs > 0 else 0
            print(f"승률 계산 결과 - 승리 거래: {winning_trades}/{total_trade_pairs}, 승률: {win_rate:.1f}%")
        else:
            win_rate = 0.0
        
        return {
            "cagr": float(cagr),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "win_rate": float(win_rate),
            "total_trades": int(len(trades))
        }
        
    except Exception as e:
        print(f"성과 지표 계산 중 오류: {e}")
        return {
            "cagr": 0.0, "volatility": 0.0, "sharpe_ratio": 0.0,
            "max_drawdown": 0.0, "win_rate": 0.0, "total_trades": 0
        }


def compute_metrics_legacy(equity: pd.DataFrame, freq: int = 252) -> Dict[str, float]:
    """기존 방식의 성과 지표 계산 (하위 호환성)"""
    eq = equity["equity"].astype(float)
    rets = eq.pct_change().fillna(0)
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (freq / len(eq)) - 1 if len(eq) > 1 else 0.0
    vol = rets.std() * np.sqrt(freq)
    sharpe = rets.mean() / (rets.std() + 1e-9) * np.sqrt(freq)
    cummax = eq.cummax()
    dd = (eq / cummax - 1)
    maxdd = dd.min()
    return {
        "CAGR": float(cagr),
        "Volatility": float(vol),
        "Sharpe": float(sharpe),
        "MaxDrawdown": float(maxdd),
    }
