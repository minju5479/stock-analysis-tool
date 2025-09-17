"""
Statistical Arbitrage 전략
통계적 차익거래 - 가격의 평균 회귀성과 상관관계를 이용한 매매
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from .base import Strategy


class StatisticalArbitrageStrategy(Strategy):
    """통계적 차익거래 전략"""
    
    name = "statistical_arbitrage"
    
    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        """
        통계적 차익거래 신호 생성
        
        Parameters:
            df: OHLCV 데이터
            params:
                - lookback_period: 통계 분석 기간 (기본값: 60)
                - zscore_entry: Z-Score 진입 임계값 (기본값: 2.0)
                - zscore_exit: Z-Score 청산 임계값 (기본값: 0.5)
                - correlation_period: 상관관계 분석 기간 (기본값: 30)
                - mean_reversion_strength: 평균 회귀 강도 (기본값: 0.7)
                - volume_confirmation: 거래량 확인 여부 (기본값: True)
                - warmup: 워밍업 기간 (기본값: 80)
        """
        p = {
            "lookback_period": 60, "zscore_entry": 2.0, "zscore_exit": 0.5,
            "correlation_period": 30, "mean_reversion_strength": 0.7,
            "volume_confirmation": True, "warmup": 80
        }
        if params:
            p.update(params)
        
        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "High", "Low", "Volume"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")
        
        lookback = int(p["lookback_period"])
        zscore_entry = float(p["zscore_entry"])
        zscore_exit = float(p["zscore_exit"])
        correlation_period = int(p["correlation_period"])
        mean_reversion_strength = float(p["mean_reversion_strength"])
        volume_confirmation = bool(p["volume_confirmation"])
        
        # 기본 지표
        s["log_price"] = np.log(s["Close"])
        s["returns"] = s["log_price"].diff().shift(1)
        
        # 1. 평균 회귀성 측정
        
        # 가격의 장기 평균 대비 편차
        s["price_ma"] = s["Close"].rolling(lookback, min_periods=1).mean().shift(1)
        s["price_std"] = s["Close"].rolling(lookback, min_periods=1).std().shift(1)
        s["price_deviation"] = ((s["Close"] - s["price_ma"]) / s["price_std"]).shift(1)
        
        # Z-Score 계산 (정규화된 편차)
        s["zscore"] = s["price_deviation"]
        
        # 2. 평균 회귀 강도 측정 (Hurst Exponent 근사)
        s["mean_reversion_score"] = np.nan
        
        for i in range(lookback, len(s)):
            # 최근 N일 수익률 자기상관 계산
            returns_window = s["returns"].iloc[i-lookback:i].dropna()
            
            if len(returns_window) < 10:
                continue
                
            # 1차 자기상관계수 (음수일수록 평균 회귀적)
            autocorr = returns_window.autocorr(lag=1)
            if pd.notna(autocorr):
                # -1 ~ 1을 0 ~ 1로 변환 (음수일수록 높은 점수)
                s.loc[s.index[i], "mean_reversion_score"] = max(0, -autocorr)
        
        # 3. 변동성 조정
        s["volatility"] = s["returns"].rolling(20, min_periods=1).std().shift(1)
        s["volatility_percentile"] = s["volatility"].rolling(100, min_periods=10).rank(pct=True).shift(1)
        
        # 4. 거래량 패턴
        s["volume_ma"] = s["Volume"].rolling(20, min_periods=1).mean().shift(1)
        s["volume_ratio"] = (s["Volume"] / s["volume_ma"]).shift(1)
        
        # 5. 시장 미시구조 (Bid-Ask Spread 근사)
        s["high_low_spread"] = ((s["High"] - s["Low"]) / s["Close"]).shift(1)
        s["spread_ma"] = s["high_low_spread"].rolling(20, min_periods=1).mean().shift(1)
        s["spread_ratio"] = (s["high_low_spread"] / s["spread_ma"]).shift(1)
        
        # 6. 매매 신호 조건
        
        # 강한 평균 회귀성 확인
        strong_mean_reversion = (s["mean_reversion_score"] > mean_reversion_strength).fillna(False).infer_objects(copy=False)
        
        # Z-Score 기반 진입/청산
        extreme_high = (s["zscore"] > zscore_entry).fillna(False).infer_objects(copy=False)  # 과매수
        extreme_low = (s["zscore"] < -zscore_entry).fillna(False).infer_objects(copy=False)  # 과매도
        
        # 평균 회귀 신호 (중앙값 복귀)
        revert_to_mean_high = (s["zscore"] < zscore_exit) & (s["zscore"].shift(1) > zscore_entry)
        revert_to_mean_high = revert_to_mean_high.fillna(False).infer_objects(copy=False)
        revert_to_mean_low = (s["zscore"] > -zscore_exit) & (s["zscore"].shift(1) < -zscore_entry)
        revert_to_mean_low = revert_to_mean_low.fillna(False).infer_objects(copy=False)
        
        # 낮은 변동성 환경 선호 (예측 가능성 증가)
        low_volatility = (s["volatility_percentile"] < 0.6).fillna(False).infer_objects(copy=False)
        
        # 정상적인 스프레드 (유동성 확인)
        normal_spread = (s["spread_ratio"] < 1.5).fillna(False).infer_objects(copy=False)
        
        # 거래량 확인 (선택적)
        volume_ok = True
        if volume_confirmation:
            volume_ok = (s["volume_ratio"] > 0.8).fillna(False).infer_objects(copy=False)  # 최소 거래량
        
        # 매수 신호: 극도로 과매도 + 평균 회귀 환경
        buy_rule = (extreme_low & strong_mean_reversion & low_volatility & 
                   normal_spread & volume_ok)
        
        # 매도 신호: 극도로 과매수 + 평균 회귀 환경  
        sell_rule = (extreme_high & strong_mean_reversion & low_volatility &
                    normal_spread & volume_ok)
        
        # 청산 신호: 평균 복귀
        close_long = revert_to_mean_low
        close_short = revert_to_mean_high
        
        # 최종 액션 (롱/숏 포지션 고려)
        action = np.where(buy_rule.fillna(False), "BUY",
                 np.where(sell_rule.fillna(False), "SELL",
                         np.where(close_long.fillna(False), "SELL",  # 롱 청산
                                 np.where(close_short.fillna(False), "BUY", "HOLD"))))  # 숏 커버
        
        # 7. 신뢰도 계산 (통계적 유의성)
        
        # Z-Score 극값도
        zscore_strength = np.clip(abs(s["zscore"].fillna(0)) / zscore_entry, 0, 2) / 2
        
        # 평균 회귀 강도
        reversion_strength = s["mean_reversion_score"].fillna(0)
        
        # 시장 상태 (낮은 변동성 + 정상 스프레드)
        market_condition = ((1 - s["volatility_percentile"].fillna(0.5)) + 
                           (2 - s["spread_ratio"].fillna(1)).clip(0, 1)) / 2
        
        confidence = (0.4 * zscore_strength + 0.4 * reversion_strength + 
                     0.2 * market_condition).fillna(0.5)
        confidence = np.clip(confidence, 0, 1)
        
        # 8. 리스크 관리 (통계적 기반)
        
        # 손절: Z-Score가 더 극단으로 갈 때
        extreme_zscore_multiplier = 1.5
        stop = np.where(
            action == "BUY", 
            s["price_ma"] - extreme_zscore_multiplier * zscore_entry * s["price_std"],
            np.where(
                action == "SELL",
                s["price_ma"] + extreme_zscore_multiplier * zscore_entry * s["price_std"],
                np.nan
            )
        )
        
        # 목표: 평균값 회귀
        target = np.where(
            (action == "BUY") | (action == "SELL"),
            s["price_ma"],  # 장기 평균으로 회귀
            np.nan
        )
        
        # 결과 조합
        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = confidence
        out["reason"] = np.where(
            action == "BUY", 
            np.where(buy_rule, "통계적과매도+평균회귀", "숏커버링"),
            np.where(
                action == "SELL",
                np.where(sell_rule, "통계적과매수+평균회귀", "롱청산"),
                "보유"
            )
        )
        out["stop"] = stop
        out["target"] = target
        out["size"] = 1.0
        
        # 워밍업 적용
        warmup = int(p.get("warmup", 80))
        if len(out) <= warmup:
            return out.tail(1) if len(out) > 0 else out
        return out.iloc[warmup:]
