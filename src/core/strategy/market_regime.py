"""
Market Regime 전략
시장 상황(횡보, 상승, 하락, 고변동성)에 따른 적응형 매매 전략
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from .base import Strategy


class MarketRegimeStrategy(Strategy):
    """시장 국면 분석 전략"""
    
    name = "market_regime"
    
    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        """
        시장 국면에 따른 적응형 신호 생성
        
        Parameters:
            df: OHLCV 데이터
            params:
                - regime_period: 국면 분석 기간 (기본값: 30)
                - trend_threshold: 트렌드 임계값 (기본값: 0.02)
                - volatility_period: 변동성 계산 기간 (기본값: 20)
                - volume_period: 거래량 분석 기간 (기본값: 15)
                - regime_strength: 국면 강도 임계값 (기본값: 0.7)
                - warmup: 워밍업 기간 (기본값: 50)
        """
        p = {
            "regime_period": 30, "trend_threshold": 0.02, "volatility_period": 20,
            "volume_period": 15, "regime_strength": 0.7, "warmup": 50
        }
        if params:
            p.update(params)
        
        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "High", "Low", "Volume"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")
        
        regime_period = int(p["regime_period"])
        trend_threshold = float(p["trend_threshold"])
        volatility_period = int(p["volatility_period"])
        volume_period = int(p["volume_period"])
        regime_strength = float(p["regime_strength"])
        
        # 기본 지표 계산
        s["daily_return"] = s["Close"].pct_change().shift(1)
        
        # 1. 트렌드 강도 (방향성)
        s["returns_ma"] = s["daily_return"].rolling(regime_period, min_periods=1).mean().shift(1)
        s["price_change"] = (s["Close"] / s["Close"].shift(regime_period) - 1).shift(1)
        
        # 2. 변동성 (불확실성)
        s["volatility"] = s["daily_return"].rolling(volatility_period, min_periods=1).std().shift(1)
        s["volatility_ma"] = s["volatility"].rolling(regime_period, min_periods=1).mean().shift(1)
        s["volatility_percentile"] = s["volatility"].rolling(100, min_periods=10).rank(pct=True).shift(1)
        
        # 3. 거래량 패턴 (참여도)
        s["volume_ma"] = s["Volume"].rolling(volume_period, min_periods=1).mean().shift(1)
        s["volume_trend"] = (s["volume_ma"] / s["volume_ma"].shift(regime_period) - 1).shift(1)
        
        # 4. 가격 모멘텀 일관성
        s["momentum_consistency"] = s["daily_return"].rolling(regime_period, min_periods=1).apply(
            lambda x: (x > 0).sum() / len(x) if len(x) > 0 else 0.5, raw=True
        ).shift(1)
        
        # 5. 시장 국면 분류
        # 상승 트렌드: 일관된 양의 수익률 + 낮은-중간 변동성
        uptrend = (
            (s["price_change"] > trend_threshold) &
            (s["momentum_consistency"] > 0.6) &
            (s["volatility_percentile"] < 0.7)
        ).fillna(False)
        
        # 하락 트렌드: 일관된 음의 수익률 + 높은 변동성
        downtrend = (
            (s["price_change"] < -trend_threshold) &
            (s["momentum_consistency"] < 0.4) &
            (s["volatility_percentile"] > 0.3)
        ).fillna(False)
        
        # 횡보: 낮은 방향성 + 낮은 변동성
        sideways = (
            (abs(s["price_change"]) < trend_threshold) &
            (s["volatility_percentile"] < 0.5) &
            (s["momentum_consistency"].between(0.4, 0.6))
        ).fillna(False)
        
        # 고변동성: 높은 변동성 (방향 무관)
        high_volatility = (s["volatility_percentile"] > 0.8).fillna(False).infer_objects(copy=False)
        
        # 국면별 신호 강도
        s["regime_uptrend"] = uptrend.astype(float)
        s["regime_downtrend"] = downtrend.astype(float) 
        s["regime_sideways"] = sideways.astype(float)
        s["regime_high_vol"] = high_volatility.astype(float)
        
        # 6. 국면별 매매 전략
        
        # RSI for 국면별 조정
        delta = s["Close"].diff()
        gain = delta.clip(lower=0).rolling(14, min_periods=1).mean()
        loss = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        s["rsi"] = (100 - (100 / (1 + rs))).shift(1)
        
        # 볼린저 밴드
        s["bb_sma"] = s["Close"].rolling(20, min_periods=1).mean().shift(1)
        s["bb_std"] = s["Close"].rolling(20, min_periods=1).std().shift(1)
        s["bb_upper"] = s["bb_sma"] + 2 * s["bb_std"]
        s["bb_lower"] = s["bb_sma"] - 2 * s["bb_std"]
        s["bb_position"] = ((s["Close"] - s["bb_lower"]) / (s["bb_upper"] - s["bb_lower"])).shift(1)
        
        # 국면별 매매 로직
        
        # 상승 트렌드: 추세 추종
        uptrend_buy = uptrend & (s["rsi"] < 70) & (s["bb_position"] > 0.2)
        uptrend_sell = uptrend & (s["rsi"] > 80) & (s["bb_position"] > 0.9)
        
        # 하락 트렌드: 반전 대기 또는 공매도
        downtrend_buy = downtrend & (s["rsi"] < 25) & (s["bb_position"] < 0.1)
        downtrend_sell = downtrend & (s["rsi"] > 60) & (s["bb_position"] > 0.5)
        
        # 횡보: 평균 회귀
        sideways_buy = sideways & (s["rsi"] < 35) & (s["bb_position"] < 0.3)
        sideways_sell = sideways & (s["rsi"] > 65) & (s["bb_position"] > 0.7)
        
        # 고변동성: 보수적 접근
        high_vol_buy = high_volatility & (s["rsi"] < 30) & (s["bb_position"] < 0.2) & uptrend
        high_vol_sell = high_volatility & (s["rsi"] > 70) & (s["bb_position"] > 0.8)
        
        # 거래량 확인
        high_volume = (s["Volume"] > s["volume_ma"] * 1.2).shift(1)
        high_volume = high_volume.fillna(False).infer_objects(copy=False)
        
        # 최종 매매 신호 (거래량 동반 필요)
        buy_rule = (uptrend_buy | downtrend_buy | sideways_buy | high_vol_buy) & high_volume
        sell_rule = (uptrend_sell | downtrend_sell | sideways_sell | high_vol_sell) & high_volume
        
        action = np.where(buy_rule.fillna(False), "BUY",
                 np.where(sell_rule.fillna(False), "SELL", "HOLD"))
        
        # 신뢰도 계산 (국면 명확성 + RSI 극값 + 거래량)
        regime_clarity = (
            s["regime_uptrend"] + s["regime_downtrend"] + 
            s["regime_sideways"] + s["regime_high_vol"]
        ).fillna(0)
        
        rsi_extreme = np.where(
            s["rsi"].fillna(50) < 30, (30 - s["rsi"].fillna(50)) / 30,
            np.where(s["rsi"].fillna(50) > 70, (s["rsi"].fillna(50) - 70) / 30, 0)
        )
        
        volume_score = np.clip((s["Volume"] / s["volume_ma"] - 1).fillna(0), 0, 1)
        
        confidence = (0.4 * regime_clarity + 0.3 * rsi_extreme + 0.3 * volume_score).fillna(0.5)
        confidence = np.clip(confidence, 0, 1)
        
        # 국면별 손절/목표가 조정
        atr_period = 14
        s["high_low"] = s["High"] - s["Low"]
        s["high_close"] = abs(s["High"] - s["Close"].shift(1))
        s["low_close"] = abs(s["Low"] - s["Close"].shift(1))
        s["tr"] = s[["high_low", "high_close", "low_close"]].max(axis=1)
        s["atr"] = s["tr"].rolling(atr_period, min_periods=1).mean().shift(1)
        
        # 국면별 리스크 조정
        risk_multiplier = np.where(
            s["regime_high_vol"], 1.5,  # 고변동성: 보수적
            np.where(s["regime_uptrend"], 2.0,  # 상승: 공격적
                    np.where(s["regime_downtrend"], 1.8,  # 하락: 신중
                            1.2))  # 횡보: 일반적
        )
        
        stop = np.where(action == "BUY", s["Close"] - risk_multiplier * s["atr"],
                       np.where(action == "SELL", s["Close"] + risk_multiplier * s["atr"], np.nan))
        target = np.where(action == "BUY", s["Close"] + 2.5 * risk_multiplier * s["atr"],
                         np.where(action == "SELL", s["Close"] - 2.5 * risk_multiplier * s["atr"], np.nan))
        
        # 결과 조합
        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = confidence
        out["reason"] = np.where(
            action == "BUY", 
            np.where(uptrend, "상승트렌드추종", 
                    np.where(downtrend, "하락반전대기",
                            np.where(sideways, "횡보평균회귀", "고변동성보수매수"))),
            np.where(
                action == "SELL",
                np.where(uptrend, "상승과열매도",
                        np.where(downtrend, "하락추세매도", 
                                np.where(sideways, "횡보평균회귀매도", "고변동성매도"))),
                "보유"
            )
        )
        out["stop"] = stop
        out["target"] = target
        out["size"] = 1.0
        
        # 워밍업 적용
        warmup = int(p.get("warmup", 50))
        if len(out) <= warmup:
            return out.tail(1) if len(out) > 0 else out
        return out.iloc[warmup:]
