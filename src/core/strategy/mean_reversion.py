"""
평균회귀 전략: 볼린저밴드와 RSI를 활용한 과매수/과매도 반전 전략
"""
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import numpy as np
from .base import Strategy

class MeanReversionStrategy(Strategy):
    name = "mean_reversion"

    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        p = {"bb_period": 20, "bb_std": 2, "rsi_period": 14, "rsi_oversold": 25, "rsi_overbought": 75, "warmup": 50}
        if params:
            p.update(params)

        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "Daily_Return", "Volatility"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")

        # 볼린저 밴드
        bb_period = int(p["bb_period"])
        bb_std = float(p["bb_std"])
        s["bb_sma"] = s["Close"].rolling(bb_period, min_periods=1).mean().shift(1)
        s["bb_std"] = s["Close"].rolling(bb_period, min_periods=1).std().shift(1)
        s["bb_upper"] = s["bb_sma"] + bb_std * s["bb_std"]
        s["bb_lower"] = s["bb_sma"] - bb_std * s["bb_std"]
        s["bb_position"] = ((s["Close"] - s["bb_lower"]) / (s["bb_upper"] - s["bb_lower"])).shift(1)
        
        # RSI
        rsi_period = int(p["rsi_period"])
        delta = s["Close"].diff()
        gain = delta.clip(lower=0).rolling(rsi_period, min_periods=1).mean()
        loss = (-delta.clip(upper=0)).rolling(rsi_period, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        s["rsi"] = (100 - (100 / (1 + rs))).shift(1)
        
        # 가격 위치 (최근 N일 범위 내)
        s["price_percentile"] = s["Close"].rolling(20, min_periods=1).rank(pct=True).shift(1)
        
        # 변동성 조정 (낮은 변동성에서 평균회귀 더 효과적)
        s["volatility_20"] = s["Daily_Return"].rolling(20, min_periods=1).std().shift(1)
        s["volatility_percentile"] = s["volatility_20"].rolling(50, min_periods=1).rank(pct=True).shift(1)
        low_volatility = s["volatility_percentile"] < 0.3
        
        # 평균회귀 신호 조건
        rsi_oversold = float(p["rsi_oversold"])
        rsi_overbought = float(p["rsi_overbought"])
        
        # 과매도 (매수 신호): RSI 낮음 + 볼린저밴드 하단 근처 + 낮은 변동성 (NaN 안전 처리)
        oversold_rsi = (s["rsi"] < rsi_oversold).fillna(False).infer_objects(copy=False)
        near_bb_lower = (s["bb_position"] < 0.2).fillna(False).infer_objects(copy=False)
        price_low = (s["price_percentile"] < 0.3).fillna(False).infer_objects(copy=False)
        
        # 과매수 (매도 신호): RSI 높음 + 볼린저밴드 상단 근처 (NaN 안전 처리)
        overbought_rsi = (s["rsi"] > rsi_overbought).fillna(False).infer_objects(copy=False)
        near_bb_upper = (s["bb_position"] > 0.8).fillna(False).infer_objects(copy=False)
        price_high = (s["price_percentile"] > 0.7).fillna(False).infer_objects(copy=False)
        
        buy_rule = oversold_rsi & near_bb_lower & low_volatility
        sell_rule = overbought_rsi & near_bb_upper
        
        action = np.where(buy_rule.fillna(False), "BUY", 
                 np.where(sell_rule.fillna(False), "SELL", "HOLD"))
        
        # 신뢰도 (RSI 극값 + 볼린저밴드 위치 + 변동성) - NaN 안전 처리
        rsi_safe = s["rsi"].fillna(50)  # RSI NaN을 중립값 50으로 처리
        rsi_extremity = np.where(rsi_safe < 50, (50 - rsi_safe) / 25, (rsi_safe - 50) / 25)  # 0~1
        
        bb_pos_safe = s["bb_position"].fillna(0.5)  # 볼린저밴드 위치 NaN을 중립값 0.5로 처리
        bb_extremity = np.where(bb_pos_safe < 0.5, (0.5 - bb_pos_safe) / 0.5, (bb_pos_safe - 0.5) / 0.5)
        
        volatility_factor = 1 - s["volatility_percentile"].fillna(0.5)
        
        confidence = (0.4 * rsi_extremity + 0.4 * bb_extremity + 0.2 * volatility_factor).fillna(0.5)
        confidence = np.clip(confidence, 0, 1)
        
        # 스탑/타겟 (볼린저밴드 기준)
        stop = np.where(action == "BUY", s["bb_lower"] * 0.98, 
                       np.where(action == "SELL", s["bb_upper"] * 1.02, np.nan))
        target = np.where(action == "BUY", s["bb_sma"], 
                         np.where(action == "SELL", s["bb_sma"], np.nan))
        
        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = confidence
        out["reason"] = np.where(action == "BUY", "과매도+밴드하단+저변동성",
                           np.where(action == "SELL", "과매수+밴드상단", "보유"))
        out["stop"] = stop
        out["target"] = target
        out["size"] = 1.0

        # 워밍업 적용
        res = out
        warmup = int(p.get("warmup", 50))
        if len(res) == 0:
            return res
        if len(res) <= warmup:
            return res.tail(1)
        return res.iloc[warmup:]
