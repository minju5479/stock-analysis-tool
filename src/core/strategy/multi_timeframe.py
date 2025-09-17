"""
Multi-Timeframe 전략
여러 시간대의 신호를 종합하여 더 신뢰성 높은 매매 결정
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from .base import Strategy


class MultiTimeframeStrategy(Strategy):
    """다중 시간대 전략"""
    
    name = "multi_timeframe"
    
    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        """
        다중 시간대 신호 생성
        
        Parameters:
            df: OHLCV 데이터
            params: 
                - short_ma: 단기 이평선 (기본값: 5)
                - medium_ma: 중기 이평선 (기본값: 20) 
                - long_ma: 장기 이평선 (기본값: 60)
                - volume_period: 거래량 평균 기간 (기본값: 10)
                - atr_period: ATR 기간 (기본값: 14)
                - trend_strength: 트렌드 강도 임계값 (기본값: 0.6)
                - warmup: 워밍업 기간 (기본값: 70)
        """
        p = {
            "short_ma": 5, "medium_ma": 20, "long_ma": 60, "volume_period": 10,
            "atr_period": 14, "trend_strength": 0.6, "warmup": 70
        }
        if params:
            p.update(params)
        
        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "High", "Low", "Volume"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")
        
        # 다중 이동평균선
        short_ma = int(p["short_ma"])
        medium_ma = int(p["medium_ma"])
        long_ma = int(p["long_ma"])
        
        s["sma_short"] = s["Close"].rolling(short_ma, min_periods=1).mean().shift(1)
        s["sma_medium"] = s["Close"].rolling(medium_ma, min_periods=1).mean().shift(1)
        s["sma_long"] = s["Close"].rolling(long_ma, min_periods=1).mean().shift(1)
        
        # 트렌드 방향성
        s["trend_short"] = (s["sma_short"] > s["sma_short"].shift(1)).astype(int).shift(1)
        s["trend_medium"] = (s["sma_medium"] > s["sma_medium"].shift(1)).astype(int).shift(1)
        s["trend_long"] = (s["sma_long"] > s["sma_long"].shift(1)).astype(int).shift(1)
        
        # 트렌드 일치도 (0~1)
        s["trend_alignment"] = ((s["trend_short"] + s["trend_medium"] + s["trend_long"]) / 3).shift(1)
        
        # 가격 위치 (이동평균 대비)
        s["price_vs_short"] = (s["Close"] / s["sma_short"] - 1).shift(1)
        s["price_vs_medium"] = (s["Close"] / s["sma_medium"] - 1).shift(1) 
        s["price_vs_long"] = (s["Close"] / s["sma_long"] - 1).shift(1)
        
        # 이동평균선 배열 상태
        s["ma_bull_setup"] = ((s["sma_short"] > s["sma_medium"]) & 
                             (s["sma_medium"] > s["sma_long"])).shift(1)
        s["ma_bear_setup"] = ((s["sma_short"] < s["sma_medium"]) & 
                             (s["sma_medium"] < s["sma_long"])).shift(1)
        
        # 거래량 확인
        volume_period = int(p["volume_period"])
        s["volume_avg"] = s["Volume"].rolling(volume_period, min_periods=1).mean().shift(1)
        s["volume_ratio"] = (s["Volume"] / s["volume_avg"]).shift(1)
        
        # ATR for 변동성
        atr_period = int(p["atr_period"])
        s["high_low"] = s["High"] - s["Low"]
        s["high_close"] = abs(s["High"] - s["Close"].shift(1))
        s["low_close"] = abs(s["Low"] - s["Close"].shift(1))
        s["tr"] = s[["high_low", "high_close", "low_close"]].max(axis=1)
        s["atr"] = s["tr"].rolling(atr_period, min_periods=1).mean().shift(1)
        
        # 변동성 정규화
        s["volatility_pct"] = (s["atr"] / s["Close"]).shift(1)
        s["volatility_rank"] = s["volatility_pct"].rolling(50, min_periods=1).rank(pct=True).shift(1)
        
        # 매매 신호 조건
        trend_strength = float(p["trend_strength"])
        
        # 강한 상승 트렌드 + 고거래량
        strong_bull_trend = (s["trend_alignment"] > trend_strength).fillna(False).infer_objects(copy=False)
        bull_ma_setup = s["ma_bull_setup"].fillna(False).infer_objects(copy=False)
        price_above_medium = (s["price_vs_medium"] > 0.02).fillna(False).infer_objects(copy=False)  # 2% 이상
        high_volume = (s["volume_ratio"] > 1.3).fillna(False).infer_objects(copy=False)
        
        # 강한 하락 트렌드 + 고거래량  
        strong_bear_trend = (s["trend_alignment"] < (1 - trend_strength)).fillna(False).infer_objects(copy=False)
        bear_ma_setup = s["ma_bear_setup"].fillna(False).infer_objects(copy=False)
        price_below_medium = (s["price_vs_medium"] < -0.02).fillna(False).infer_objects(copy=False)  # -2% 이하
        
        # 매수 신호: 다중 시간대 상승 + MA 정배열 + 거래량
        buy_rule = strong_bull_trend & bull_ma_setup & price_above_medium & high_volume
        
        # 매도 신호: 다중 시간대 하락 + MA 역배열 + 거래량
        sell_rule = strong_bear_trend & bear_ma_setup & price_below_medium & high_volume
        
        action = np.where(buy_rule.fillna(False).infer_objects(copy=False), "BUY",
                 np.where(sell_rule.fillna(False).infer_objects(copy=False), "SELL", "HOLD"))
        
        # 신뢰도 계산 (트렌드 일치도 + MA 배열 + 거래량)
        trend_score = s["trend_alignment"].fillna(0.5)
        ma_score = np.where(s["ma_bull_setup"].fillna(False).infer_objects(copy=False), 1.0,
                           np.where(s["ma_bear_setup"].fillna(False).infer_objects(copy=False), 1.0, 0.3))
        volume_score = np.clip((s["volume_ratio"].fillna(1) - 1) / 2, 0, 1)
        
        confidence = (0.4 * trend_score + 0.3 * ma_score + 0.3 * volume_score).fillna(0.5)
        confidence = np.clip(confidence, 0, 1)
        
        # 손절/목표가 (ATR 기반)
        atr_multiplier = 2.5
        stop = np.where(action == "BUY", s["Close"] - atr_multiplier * s["atr"],
                       np.where(action == "SELL", s["Close"] + atr_multiplier * s["atr"], np.nan))
        target = np.where(action == "BUY", s["Close"] + 3 * atr_multiplier * s["atr"],
                         np.where(action == "SELL", s["Close"] - 3 * atr_multiplier * s["atr"], np.nan))
        
        # 결과 조합
        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = confidence
        out["reason"] = np.where(action == "BUY", "다중시간대상승+MA정배열+고거래량",
                           np.where(action == "SELL", "다중시간대하락+MA역배열+고거래량", "보유"))
        out["stop"] = stop
        out["target"] = target
        out["size"] = 1.0
        
        # 워밍업 적용
        warmup = int(p.get("warmup", 70))
        if len(out) <= warmup:
            return out.tail(1) if len(out) > 0 else out
        return out.iloc[warmup:]
