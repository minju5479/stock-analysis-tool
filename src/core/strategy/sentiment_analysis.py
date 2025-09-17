"""
Sentiment Analysis Strategy
뉴스/소셜미디어 감정 분석 기반 주가 예측 (시뮬레이션)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from .base import Strategy


class SentimentAnalysisStrategy(Strategy):
    """감정 분석 전략 (뉴스/소셜미디어 감정 시뮬레이션)"""
    
    name = "sentiment_analysis"
    
    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        """
        감정 분석 기반 신호 생성 (뉴스/소셜미디어 감정 시뮬레이션)
        
        Parameters:
            df: OHLCV 데이터
            params:
                - sentiment_period: 감정 분석 기간 (기본값: 5)
                - price_sentiment_lag: 가격-감정 지연 (기본값: 1)
                - sentiment_threshold: 감정 임계값 (기본값: 0.3)
                - volume_weight: 거래량 가중치 (기본값: 0.3)
                - trend_weight: 트렌드 가중치 (기본값: 0.4)
                - momentum_period: 모멘텀 기간 (기본값: 10)
                - volatility_adjustment: 변동성 조정 (기본값: True)
                - warmup: 워밍업 기간 (기본값: 50)
        """
        p = {
            "sentiment_period": 5, "price_sentiment_lag": 1, "sentiment_threshold": 0.3,
            "volume_weight": 0.3, "trend_weight": 0.4, "momentum_period": 10,
            "volatility_adjustment": True, "warmup": 50
        }
        if params:
            p.update(params)
        
        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "High", "Low", "Volume"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")
        
        sentiment_period = int(p["sentiment_period"])
        price_sentiment_lag = int(p["price_sentiment_lag"])
        sentiment_threshold = float(p["sentiment_threshold"])
        volume_weight = float(p["volume_weight"])
        trend_weight = float(p["trend_weight"])
        momentum_period = int(p["momentum_period"])
        
        # 1. 가격 기반 시뮬레이션 감정 지표 생성
        
        # 가격 변화율
        s["returns"] = s["Close"].pct_change()
        s["log_returns"] = np.log(s["Close"] / s["Close"].shift(1))
        
        # 뉴스 감정 시뮬레이션 (가격 변화 패턴 기반)
        
        # 급격한 가격 변화 = 뉴스 이벤트 시뮬레이션
        s["price_shock"] = abs(s["returns"]) > s["returns"].rolling(20, min_periods=5).std() * 2
        s["positive_shock"] = (s["returns"] > s["returns"].rolling(20, min_periods=5).std() * 2)
        s["negative_shock"] = (s["returns"] < -s["returns"].rolling(20, min_periods=5).std() * 2)
        
        # 뉴스 감정 스코어 (실제로는 외부 뉴스 API 사용)
        # 여기서는 가격 패턴으로 시뮬레이션
        news_sentiment_base = np.where(
            s["positive_shock"], np.random.normal(0.7, 0.2, len(s)),  # 긍정적 뉴스
            np.where(s["negative_shock"], np.random.normal(-0.7, 0.2, len(s)),  # 부정적 뉴스
                    np.random.normal(0, 0.3, len(s)))  # 중립적
        )
        
        # 감정 지속성 (뉴스는 며칠간 영향)
        s["news_sentiment_raw"] = news_sentiment_base
        s["news_sentiment"] = s["news_sentiment_raw"].rolling(sentiment_period, min_periods=1).mean()
        
        # 2. 소셜미디어 감정 시뮬레이션
        
        # 거래량 기반 소셜미디어 관심도
        s["volume_ma"] = s["Volume"].rolling(20, min_periods=5).mean()
        s["volume_ratio"] = s["Volume"] / s["volume_ma"]
        s["social_interest"] = np.clip((s["volume_ratio"] - 1) * 2, -1, 1)  # -1 to 1
        
        # 모멘텀 기반 소셜미디어 감정
        s["momentum"] = s["Close"] / s["Close"].rolling(momentum_period, min_periods=5).mean() - 1
        s["social_sentiment_base"] = np.tanh(s["momentum"] * 5)  # -1 to 1
        
        # 소셜미디어 감정 노이즈 추가 (더 변동성이 큼)
        social_noise = np.random.normal(0, 0.4, len(s))
        s["social_sentiment"] = (0.7 * s["social_sentiment_base"] + 0.3 * social_noise).rolling(
            max(1, sentiment_period // 2), min_periods=1).mean()
        
        # 3. 종합 감정 지수
        
        # 뉴스와 소셜미디어 감정 결합
        news_weight = 0.6
        social_weight = 0.4
        s["combined_sentiment"] = (news_weight * s["news_sentiment"] + 
                                  social_weight * s["social_sentiment"])
        
        # 감정 모멘텀 (감정 변화 추세)
        s["sentiment_momentum"] = s["combined_sentiment"].diff(price_sentiment_lag)
        s["sentiment_acceleration"] = s["sentiment_momentum"].diff()
        
        # 감정 극값 탐지
        sentiment_rolling_std = s["combined_sentiment"].rolling(20, min_periods=5).std()
        s["sentiment_zscore"] = ((s["combined_sentiment"] - 
                                s["combined_sentiment"].rolling(20, min_periods=5).mean()) / 
                               sentiment_rolling_std)
        
        # 4. 기술적 지표와 감정 결합
        
        # RSI
        s["rsi"] = self._calculate_rsi(s["Close"], 14)
        
        # MACD
        s["macd"] = self._calculate_macd(s["Close"])
        s["macd_signal"] = self._calculate_macd_signal(s["Close"])
        s["macd_histogram"] = s["macd"] - s["macd_signal"]
        
        # 볼린저 밴드
        s["bb_position"] = self._calculate_bb_position(s["Close"], 20)
        
        # 5. 감정-가격 다이버전스 분석
        
        # 감정과 가격 방향 불일치 (반전 신호)
        price_direction = np.sign(s["returns"].rolling(3, min_periods=1).mean())
        sentiment_direction = np.sign(s["combined_sentiment"])
        
        s["sentiment_price_divergence"] = (
            (price_direction > 0) & (sentiment_direction < -0.3) |
            (price_direction < 0) & (sentiment_direction > 0.3)
        ).astype(float)
        
        # 감정 극값에서 가격 반전 가능성
        s["sentiment_reversal_signal"] = (
            (abs(s["sentiment_zscore"]) > 1.5) & 
            (s["sentiment_momentum"] * s["sentiment_acceleration"] < 0)
        ).astype(float)
        
        # 6. 매매 신호 생성
        
        # 강한 매수 신호: 긍정적 감정 + 기술적 확인
        strong_buy_conditions = [
            s["combined_sentiment"] > sentiment_threshold,
            s["sentiment_momentum"] > 0.1,
            s["rsi"] < 70,
            s["macd_histogram"] > 0,
            s["bb_position"] < 0.8
        ]
        
        # 감정 기반 매수 (감정이 가격을 선행한다는 가정)
        sentiment_buy_conditions = [
            s["combined_sentiment"] > 0.2,
            s["sentiment_momentum"] > 0,
            s["social_interest"] > 0.5,  # 높은 관심도
            s["rsi"] < 60
        ]
        
        # 역행 매수 (감정과 가격 다이버전스)
        contrarian_buy_conditions = [
            s["sentiment_price_divergence"] > 0,
            s["combined_sentiment"] > 0.1,
            s["rsi"] < 40,
            s["bb_position"] < 0.3
        ]
        
        # 강한 매도 신호
        strong_sell_conditions = [
            s["combined_sentiment"] < -sentiment_threshold,
            s["sentiment_momentum"] < -0.1,
            s["rsi"] > 30,
            s["macd_histogram"] < 0,
            s["bb_position"] > 0.2
        ]
        
        # 감정 기반 매도
        sentiment_sell_conditions = [
            s["combined_sentiment"] < -0.2,
            s["sentiment_momentum"] < 0,
            s["social_interest"] > 0.5,
            s["rsi"] > 40
        ]
        
        # 역행 매도
        contrarian_sell_conditions = [
            s["sentiment_price_divergence"] > 0,
            s["combined_sentiment"] < -0.1,
            s["rsi"] > 60,
            s["bb_position"] > 0.7
        ]
        
        # 신호 조합
        strong_buy = pd.concat(strong_buy_conditions, axis=1).all(axis=1)
        sentiment_buy = pd.concat(sentiment_buy_conditions, axis=1).all(axis=1)
        contrarian_buy = pd.concat(contrarian_buy_conditions, axis=1).all(axis=1)
        
        strong_sell = pd.concat(strong_sell_conditions, axis=1).all(axis=1)
        sentiment_sell = pd.concat(sentiment_sell_conditions, axis=1).all(axis=1)
        contrarian_sell = pd.concat(contrarian_sell_conditions, axis=1).all(axis=1)
        
        # 최종 액션
        buy_signal = strong_buy | sentiment_buy | contrarian_buy
        sell_signal = strong_sell | sentiment_sell | contrarian_sell
        
        action = np.where(buy_signal.fillna(False), "BUY",
                 np.where(sell_signal.fillna(False), "SELL", "HOLD"))
        
        # 7. 신뢰도 계산
        
        # 감정 강도
        sentiment_strength = abs(s["combined_sentiment"]).fillna(0)
        
        # 감정 일관성 (최근 감정 방향 일치도)
        sentiment_consistency = (
            s["combined_sentiment"].rolling(3, min_periods=1).apply(
                lambda x: 1 if (x > 0).all() or (x < 0).all() else 0.5
            ).fillna(0.5)
        )
        
        # 기술적 확인도
        technical_score = np.where(
            action == "BUY",
            ((s["rsi"] < 70).astype(float) * 0.3 +
             (s["macd_histogram"] > 0).astype(float) * 0.4 +
             (s["bb_position"] < 0.8).astype(float) * 0.3),
            np.where(
                action == "SELL",
                ((s["rsi"] > 30).astype(float) * 0.3 +
                 (s["macd_histogram"] < 0).astype(float) * 0.4 +
                 (s["bb_position"] > 0.2).astype(float) * 0.3),
                0.5
            )
        )
        
        # 거래량 확인
        volume_confirmation = np.clip(s["volume_ratio"].fillna(1), 0.5, 2) / 2
        
        # 종합 신뢰도
        base_confidence = (
            0.4 * sentiment_strength +
            0.3 * sentiment_consistency +
            0.2 * technical_score +
            0.1 * volume_confirmation
        )
        
        # 변동성 조정
        if p["volatility_adjustment"]:
            volatility = s["returns"].rolling(20, min_periods=5).std().fillna(0.02)
            volatility_factor = np.clip(1 / (1 + volatility * 50), 0.5, 1.5)
            confidence = base_confidence * volatility_factor
        else:
            confidence = base_confidence
        
        confidence = np.clip(confidence.fillna(0.5), 0, 1)
        
        # 8. 리스크 관리
        
        # ATR
        s["atr"] = self._calculate_atr(s["High"], s["Low"], s["Close"], 14)
        
        # 감정 강도에 따른 리스크 조정
        risk_multiplier = 1 + sentiment_strength * 0.5
        
        stop = np.where(action == "BUY", s["Close"] - risk_multiplier * s["atr"],
                       np.where(action == "SELL", s["Close"] + risk_multiplier * s["atr"], np.nan))
        
        target = np.where(action == "BUY", s["Close"] + 2 * risk_multiplier * s["atr"],
                         np.where(action == "SELL", s["Close"] - 2 * risk_multiplier * s["atr"], np.nan))
        
        # 매매 이유
        reason = np.where(
            action == "BUY",
            np.where(strong_buy, "감정+기술적강세",
                    np.where(sentiment_buy, "감정주도매수",
                            "감정가격다이버전스")),
            np.where(
                action == "SELL", 
                np.where(strong_sell, "감정+기술적약세",
                        np.where(sentiment_sell, "감정주도매도", 
                                "감정가격다이버전스")),
                "보유"
            )
        )
        
        # 결과
        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = confidence
        out["reason"] = reason
        out["stop"] = stop
        out["target"] = target
        out["size"] = 1.0
        
        # 워밍업 적용
        warmup = int(p.get("warmup", 50))
        if len(out) <= warmup:
            return out.tail(1) if len(out) > 0 else out
        return out.iloc[warmup:]
    
    def _calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        delta = prices.diff()
        gain = delta.clip(lower=0).rolling(period, min_periods=1).mean()
        loss = (-delta.clip(upper=0)).rolling(period, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices, fast=12, slow=26):
        """MACD 계산"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        return ema_fast - ema_slow
    
    def _calculate_macd_signal(self, prices, fast=12, slow=26, signal=9):
        """MACD Signal 계산"""
        macd = self._calculate_macd(prices, fast, slow)
        return macd.ewm(span=signal).mean()
    
    def _calculate_bb_position(self, prices, period=20, std=2):
        """볼린저 밴드 위치 계산"""
        sma = prices.rolling(period, min_periods=1).mean()
        rolling_std = prices.rolling(period, min_periods=1).std()
        upper = sma + std * rolling_std
        lower = sma - std * rolling_std
        return (prices - lower) / (upper - lower)
    
    def _calculate_atr(self, high, low, close, period=14):
        """ATR 계산"""
        high_low = high - low
        high_close = abs(high - close.shift(1))
        low_close = abs(low - close.shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period, min_periods=1).mean()
