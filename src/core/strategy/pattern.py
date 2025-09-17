"""
패턴 인식 전략: 차트 패턴과 지지/저항 수준 기반
"""
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import numpy as np
from .base import Strategy

class PatternStrategy(Strategy):
    name = "pattern"

    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        p = {"pattern_window": 10, "support_resistance_window": 20, "breakout_threshold": 0.01, "warmup": 50}
        if params:
            p.update(params)

        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "High", "Low", "Volume", "Daily_Return", "Volatility"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")

        pattern_window = int(p["pattern_window"])
        sr_window = int(p["support_resistance_window"])
        breakout_threshold = float(p["breakout_threshold"])
        
        # 지지/저항 수준 계산
        s["resistance"] = s["High"].rolling(sr_window, min_periods=1).max().shift(1)
        s["support"] = s["Low"].rolling(sr_window, min_periods=1).min().shift(1)
        
        # 피벗 포인트 감지 (NaN 값 안전 처리)
        s["is_pivot_high"] = ((s["High"] > s["High"].shift(1)) & 
                             (s["High"] > s["High"].shift(-1)) & 
                             (s["High"] == s["High"].rolling(3, center=True).max())).shift(1).fillna(False).infer_objects(copy=False)
        s["is_pivot_low"] = ((s["Low"] < s["Low"].shift(1)) & 
                            (s["Low"] < s["Low"].shift(-1)) & 
                            (s["Low"] == s["Low"].rolling(3, center=True).min())).shift(1).fillna(False).infer_objects(copy=False)
        
        # 더블 톱/바텀 패턴 감지
        def detect_double_top_bottom(highs, lows, is_pivot_high, is_pivot_low, window=10):
            double_top = pd.Series(False, index=highs.index)
            double_bottom = pd.Series(False, index=lows.index)
            
            for i in range(window, len(highs)):
                # 더블 톱: 두 개의 비슷한 고점
                pivot_mask = is_pivot_high[i-window:i].fillna(False)
                if pivot_mask.any():
                    recent_highs = highs[i-window:i][pivot_mask]
                    if len(recent_highs) >= 2:
                        last_two_highs = recent_highs.tail(2)
                        if len(last_two_highs) == 2:
                            if abs(last_two_highs.iloc[0] - last_two_highs.iloc[1]) / last_two_highs.iloc[0] < 0.02:
                                double_top.iloc[i] = True
                
                # 더블 바텀: 두 개의 비슷한 저점
                pivot_mask_low = is_pivot_low[i-window:i].fillna(False)
                if pivot_mask_low.any():
                    recent_lows = lows[i-window:i][pivot_mask_low]
                    if len(recent_lows) >= 2:
                        last_two_lows = recent_lows.tail(2)
                        if len(last_two_lows) == 2:
                            if abs(last_two_lows.iloc[0] - last_two_lows.iloc[1]) / last_two_lows.iloc[0] < 0.02:
                                double_bottom.iloc[i] = True
                            
            return double_top, double_bottom
        
        s["double_top"], s["double_bottom"] = detect_double_top_bottom(
            s["High"], s["Low"], s["is_pivot_high"], s["is_pivot_low"], pattern_window
        )
        
        # 삼각형 패턴 (고점은 내려오고 저점은 올라오는)
        s["high_trend"] = s["High"].rolling(pattern_window, min_periods=1).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0, raw=True
        ).shift(1)
        s["low_trend"] = s["Low"].rolling(pattern_window, min_periods=1).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0, raw=True
        ).shift(1)
        
        # 삼각형 패턴: 고점 하락, 저점 상승 (NaN 안전 처리)
        triangle_pattern = ((s["high_trend"] < -0.001) & (s["low_trend"] > 0.001))
        triangle_pattern = triangle_pattern.fillna(False).infer_objects(copy=False)
        
        # 브레이크아웃 감지 (NaN 안전 처리)
        resistance_breakout = (s["Close"] > s["resistance"] * (1 + breakout_threshold))
        resistance_breakout = resistance_breakout.fillna(False).infer_objects(copy=False)
        support_breakdown = (s["Close"] < s["support"] * (1 - breakout_threshold))
        support_breakdown = support_breakdown.fillna(False).infer_objects(copy=False)
        
        # 거래량 확인
        s["volume_sma"] = s["Volume"].rolling(10, min_periods=1).mean().shift(1)
        volume_surge = (s["Volume"] > s["volume_sma"] * 1.5).fillna(False).infer_objects(copy=False)
        
        # 패턴 신호 조건 (모든 boolean 시리즈가 NaN 안전)
        # 매수: 더블바텀 후 지지선 돌파 + 거래량, 삼각형에서 저항선 돌파
        buy_pattern = (s["double_bottom"].shift(1).fillna(False).infer_objects(copy=False) & resistance_breakout & volume_surge) | \
                     (triangle_pattern & resistance_breakout & volume_surge)
        
        # 매도: 더블톱 후 저항선 이탈, 지지선 붕괴
        sell_pattern = (s["double_top"].shift(1).fillna(False).infer_objects(copy=False) & support_breakdown) | \
                      (support_breakdown & volume_surge)
        
        # action 배열 생성 (NaN 안전)
        action = np.where(buy_pattern.fillna(False).infer_objects(copy=False), "BUY", 
                 np.where(sell_pattern.fillna(False).infer_objects(copy=False), "SELL", "HOLD"))
        
        # 신뢰도 (패턴 명확성 + 거래량 + 브레이크아웃 강도) - NaN 안전 처리
        pattern_strength = (s["double_top"].fillna(False).infer_objects(copy=False) | s["double_bottom"].fillna(False).infer_objects(copy=False) | triangle_pattern).astype(float)
        
        # 브레이크아웃 강도 계산 (NaN 안전)
        resistance_diff = (s["Close"] - s["resistance"]) / s["resistance"]
        support_diff = (s["support"] - s["Close"]) / s["support"] 
        
        breakout_strength = np.where(resistance_breakout, 
                                   resistance_diff.fillna(0),
                                   np.where(support_breakdown,
                                          support_diff.fillna(0), 0))
        breakout_strength = np.clip(np.array(breakout_strength) / 0.05, 0, 1)  # 5% 브레이크아웃을 100%로 정규화
        
        volume_ratio = (s["Volume"] / s["volume_sma"]).fillna(1.0)
        volume_strength = np.clip((volume_ratio - 1) / 2, 0, 1)
        confidence = (0.4 * pattern_strength + 0.4 * breakout_strength + 0.2 * volume_strength).fillna(0.5)
        
        # 스탑/타겟 (지지/저항 수준 기반) - NaN 안전 처리
        stop = np.where(action == "BUY", s["support"] * 0.99, 
                       np.where(action == "SELL", s["resistance"] * 1.01, np.nan))
        target = np.where(action == "BUY", s["resistance"] * 1.02, 
                         np.where(action == "SELL", s["support"] * 0.98, np.nan))
        
        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = np.clip(confidence, 0, 1)
        out["reason"] = np.where(action == "BUY", "패턴돌파+지지저항+거래량",
                           np.where(action == "SELL", "패턴붕괴+지지이탈", "보유"))
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
