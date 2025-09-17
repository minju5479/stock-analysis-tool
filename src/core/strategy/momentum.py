"""
모멘텀 전략: 가격 모멘텀과 거래량 분석 기반
"""
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import numpy as np
from .base import Strategy

class MomentumStrategy(Strategy):
    name = "momentum"

    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        p = {"momentum_period": 20, "volume_sma": 10, "breakout_threshold": 0.02, "warmup": 50}
        if params:
            p.update(params)

        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "High", "Low", "Volume", "Daily_Return", "Volatility"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")

        # 가격 모멘텀 (N일 수익률)
        momentum_period = int(p["momentum_period"])
        s["momentum"] = s["Close"].pct_change(momentum_period).shift(1)
        
        # 거래량 분석
        volume_sma = int(p["volume_sma"])
        s["volume_sma"] = s["Volume"].rolling(volume_sma, min_periods=1).mean().shift(1)
        s["volume_ratio"] = (s["Volume"] / s["volume_sma"]).shift(1)
        
        # 가격 변동성 기반 ATR
        s["high_low"] = s["High"] - s["Low"]
        s["high_close"] = abs(s["High"] - s["Close"].shift(1))
        s["low_close"] = abs(s["Low"] - s["Close"].shift(1))
        s["tr"] = s[["high_low", "high_close", "low_close"]].max(axis=1)
        s["atr"] = s["tr"].rolling(14, min_periods=1).mean().shift(1)
        
        # 브레이크아웃 감지 (전고점 대비)
        s["high_20"] = s["High"].rolling(20, min_periods=1).max().shift(1)
        s["low_20"] = s["Low"].rolling(20, min_periods=1).min().shift(1)
        breakout_threshold = float(p["breakout_threshold"])
        
        # 신호 조건 (NaN 안전 처리)
        strong_momentum = (s["momentum"] > breakout_threshold).fillna(False).infer_objects(copy=False)
        weak_momentum = (s["momentum"] < -breakout_threshold).fillna(False).infer_objects(copy=False)
        high_volume = (s["volume_ratio"] > 1.5).fillna(False).infer_objects(copy=False)
        breakout_up = (s["Close"] > s["high_20"]).fillna(False).infer_objects(copy=False)
        breakdown = (s["Close"] < s["low_20"]).fillna(False).infer_objects(copy=False)
        
        # 매수/매도 규칙
        buy_rule = (strong_momentum & high_volume) | (breakout_up & high_volume)
        sell_rule = (weak_momentum & high_volume) | (breakdown & high_volume)
        
        action = np.where(buy_rule.fillna(False), "BUY", 
                 np.where(sell_rule.fillna(False), "SELL", "HOLD"))
        
        # 신뢰도 (모멘텀 강도 + 거래량 + 브레이크아웃) - NaN 안전 처리
        momentum_safe = s["momentum"].fillna(0)
        volume_ratio_safe = s["volume_ratio"].fillna(1)
        
        momentum_strength = np.clip(np.abs(momentum_safe) / 0.05, 0, 1)  # 5% 모멘텀을 100%로 정규화
        volume_strength = np.clip((volume_ratio_safe - 1) / 2, 0, 1)  # 3배 거래량을 100%로 정규화
        confidence = (0.5 * momentum_strength + 0.3 * volume_strength + 0.2).fillna(0.5)
        confidence = np.where(action == "SELL", confidence, confidence)
        
        # 스탑/타겟 (ATR 기반)
        atr_multiplier = 2.0
        stop = np.where(action == "BUY", s["Close"] - atr_multiplier * s["atr"], 
                       np.where(action == "SELL", s["Close"] + atr_multiplier * s["atr"], np.nan))
        target = np.where(action == "BUY", s["Close"] + 3 * atr_multiplier * s["atr"], 
                         np.where(action == "SELL", s["Close"] - 3 * atr_multiplier * s["atr"], np.nan))
        
        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = np.clip(confidence, 0, 1)
        out["reason"] = np.where(action == "BUY", "강한모멘텀+고거래량/브레이크아웃",
                           np.where(action == "SELL", "약한모멘텀+고거래량/브레이크다운", "보유"))
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
