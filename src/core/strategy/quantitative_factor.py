"""
Quantitative Factor Strategy
양적 팩터 기반 매매 전략 (다중 팩터 모델)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from .base import Strategy


class QuantitativeFactorStrategy(Strategy):
    """양적 팩터 전략 (다중 팩터 스코어링)"""
    
    name = "quantitative_factor"
    
    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        """
        다중 팩터 기반 신호 생성
        
        Parameters:
            df: OHLCV 데이터
            params:
                - momentum_weight: 모멘텀 팩터 가중치 (기본값: 0.25)
                - mean_reversion_weight: 평균회귀 팩터 가중치 (기본값: 0.20)
                - volatility_weight: 변동성 팩터 가중치 (기본값: 0.15)
                - volume_weight: 거래량 팩터 가중치 (기본값: 0.15)
                - quality_weight: 품질 팩터 가중치 (기본값: 0.15)
                - sentiment_weight: 감정 팩터 가중치 (기본값: 0.10)
                - lookback_short: 단기 룩백 기간 (기본값: 10)
                - lookback_medium: 중기 룩백 기간 (기본값: 30)
                - lookback_long: 장기 룩백 기간 (기본값: 90)
                - factor_threshold: 팩터 스코어 임계값 (기본값: 0.6)
                - warmup: 워밍업 기간 (기본값: 100)
        """
        p = {
            "momentum_weight": 0.20, "mean_reversion_weight": 0.15, "volatility_weight": 0.15,
            "volume_weight": 0.15, "quality_weight": 0.10, "sentiment_weight": 0.10,
            "fundamental_weight": 0.15, "lookback_short": 10, "lookback_medium": 30, 
            "lookback_long": 90, "factor_threshold": 0.6, "warmup": 100
        }
        if params:
            p.update(params)
        
        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "High", "Low", "Volume"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")
        
        # 파라미터 추출
        weights = {
            'momentum': float(p["momentum_weight"]),
            'mean_reversion': float(p["mean_reversion_weight"]),
            'volatility': float(p["volatility_weight"]),
            'volume': float(p["volume_weight"]),
            'quality': float(p["quality_weight"]),
            'sentiment': float(p["sentiment_weight"]),
            'fundamental': float(p["fundamental_weight"])
        }
        
        lookback_short = int(p["lookback_short"])
        lookback_medium = int(p["lookback_medium"])
        lookback_long = int(p["lookback_long"])
        factor_threshold = float(p["factor_threshold"])
        
        # 기본 계산
        s["returns"] = s["Close"].pct_change()
        s["log_returns"] = np.log(s["Close"] / s["Close"].shift(1))
        
        # Point-in-Time 재무데이터 추가 (비동기 처리)
        s = self._add_financial_factors(s, lookback_long)
        
        # 1. 모멘텀 팩터 (Momentum Factor)
        
        # 단기, 중기, 장기 모멘텀
        s["momentum_short"] = s["Close"] / s["Close"].shift(lookback_short) - 1
        s["momentum_medium"] = s["Close"] / s["Close"].shift(lookback_medium) - 1
        s["momentum_long"] = s["Close"] / s["Close"].shift(lookback_long) - 1
        
        # 가속 모멘텀 (모멘텀의 변화율)
        s["momentum_acceleration"] = s["momentum_short"] - s["momentum_medium"]
        
        # 위험조정 모멘텀 (샤프비율 방식)
        s["volatility_short"] = s["returns"].rolling(lookback_short, min_periods=5).std()
        s["risk_adjusted_momentum"] = s["momentum_short"] / (s["volatility_short"] + 0.01)
        
        # 모멘텀 일관성 (연속적인 상승/하락)
        s["momentum_consistency"] = s["returns"].rolling(lookback_short, min_periods=5).apply(
            lambda x: (x > 0).mean() if len(x) > 0 else 0.5
        )
        
        # 모멘텀 종합 스코어
        momentum_scores = [
            self._normalize_factor(s["momentum_short"]),
            self._normalize_factor(s["momentum_medium"]),
            self._normalize_factor(s["momentum_long"]),
            self._normalize_factor(s["momentum_acceleration"]),
            self._normalize_factor(s["risk_adjusted_momentum"]),
            self._normalize_factor(s["momentum_consistency"] - 0.5)
        ]
        s["momentum_factor"] = pd.DataFrame(momentum_scores).T.mean(axis=1)
        
        # 2. 평균회귀 팩터 (Mean Reversion Factor)
        
        # 가격 이탈도 (이동평균 대비)
        for period in [lookback_short, lookback_medium, lookback_long]:
            s[f"price_deviation_{period}"] = (s["Close"] - s["Close"].rolling(period, min_periods=5).mean()) / s["Close"].rolling(period, min_periods=5).mean()
        
        # RSI 기반 과매수/과매도
        s["rsi"] = self._calculate_rsi(s["Close"], 14)
        s["rsi_deviation"] = (s["rsi"] - 50) / 50  # -1 to 1
        
        # 볼린저 밴드 위치
        s["bb_position"] = self._calculate_bb_position(s["Close"], 20)
        s["bb_deviation"] = (s["bb_position"] - 0.5) * 2  # -1 to 1
        
        # Z-스코어 (통계적 이탈)
        s["zscore_short"] = (s["Close"] - s["Close"].rolling(lookback_short, min_periods=5).mean()) / s["Close"].rolling(lookback_short, min_periods=5).std()
        s["zscore_medium"] = (s["Close"] - s["Close"].rolling(lookback_medium, min_periods=10).mean()) / s["Close"].rolling(lookback_medium, min_periods=10).std()
        
        # 평균회귀 종합 스코어 (음의 값이 매수 신호)
        mean_reversion_scores = [
            -self._normalize_factor(s["price_deviation_10"]),
            -self._normalize_factor(s["price_deviation_30"]),
            -self._normalize_factor(s["price_deviation_90"]),
            -self._normalize_factor(s["rsi_deviation"]),
            -self._normalize_factor(s["bb_deviation"]),
            -self._normalize_factor(s["zscore_short"]),
            -self._normalize_factor(s["zscore_medium"])
        ]
        s["mean_reversion_factor"] = pd.DataFrame(mean_reversion_scores).T.mean(axis=1)
        
        # 3. 변동성 팩터 (Volatility Factor)
        
        # 실현변동성
        s["realized_vol_short"] = s["returns"].rolling(lookback_short, min_periods=5).std()
        s["realized_vol_medium"] = s["returns"].rolling(lookback_medium, min_periods=10).std()
        s["realized_vol_long"] = s["returns"].rolling(lookback_long, min_periods=20).std()
        
        # 변동성 비율 (단기/장기)
        s["vol_ratio"] = s["realized_vol_short"] / (s["realized_vol_long"] + 0.001)
        
        # 변동성 지속성
        s["vol_persistence"] = s["realized_vol_short"].rolling(5, min_periods=3).corr(
            s["realized_vol_short"].shift(1)
        ).fillna(0)
        
        # 가격 범위 기반 변동성
        s["price_range"] = (s["High"] - s["Low"]) / s["Close"]
        s["avg_price_range"] = s["price_range"].rolling(lookback_medium, min_periods=10).mean()
        s["range_deviation"] = (s["price_range"] - s["avg_price_range"]) / s["avg_price_range"]
        
        # GARCH 효과 (변동성 클러스터링)
        s["vol_clustering"] = s["realized_vol_short"].rolling(5, min_periods=3).std()
        
        # 변동성 종합 스코어 (낮은 변동성이 유리)
        volatility_scores = [
            -self._normalize_factor(s["realized_vol_short"]),
            -self._normalize_factor(s["vol_ratio"] - 1),
            self._normalize_factor(s["vol_persistence"].fillna(0)),
            -self._normalize_factor(s["range_deviation"]),
            -self._normalize_factor(s["vol_clustering"])
        ]
        s["volatility_factor"] = pd.DataFrame(volatility_scores).T.mean(axis=1)
        
        # 4. 거래량 팩터 (Volume Factor)
        
        # 거래량 추세
        s["volume_ma_short"] = s["Volume"].rolling(lookback_short, min_periods=5).mean()
        s["volume_ma_medium"] = s["Volume"].rolling(lookback_medium, min_periods=10).mean()
        s["volume_ratio"] = s["Volume"] / s["volume_ma_medium"]
        s["volume_trend"] = s["volume_ma_short"] / s["volume_ma_medium"]
        
        # OBV (On Balance Volume)
        s["obv"] = (s["Volume"] * np.sign(s["returns"])).cumsum()
        s["obv_ma"] = s["obv"].rolling(lookback_medium, min_periods=10).mean()
        s["obv_signal"] = (s["obv"] - s["obv_ma"]) / s["obv_ma"]
        
        # 가격-거래량 상관관계
        s["price_volume_corr"] = s["returns"].rolling(lookback_short, min_periods=5).corr(
            s["Volume"].pct_change()
        ).fillna(0)
        
        # VWAP 대비 위치
        s["vwap"] = (s["Close"] * s["Volume"]).rolling(lookback_short, min_periods=5).sum() / s["Volume"].rolling(lookback_short, min_periods=5).sum()
        s["vwap_position"] = (s["Close"] - s["vwap"]) / s["vwap"]
        
        # 거래량 집중도 (특정 가격대 거래량)
        s["volume_concentration"] = s["Volume"] / s["Volume"].rolling(lookback_medium, min_periods=10).sum()
        
        # 거래량 종합 스코어
        volume_scores = [
            self._normalize_factor(s["volume_ratio"] - 1),
            self._normalize_factor(s["volume_trend"] - 1),
            self._normalize_factor(s["obv_signal"]),
            self._normalize_factor(s["price_volume_corr"].fillna(0)),
            self._normalize_factor(s["vwap_position"]),
            self._normalize_factor(s["volume_concentration"])
        ]
        s["volume_factor"] = pd.DataFrame(volume_scores).T.mean(axis=1)
        
        # 5. 품질 팩터 (Quality Factor)
        
        # 가격 안정성 (낮은 드로우다운)
        s["cumulative_returns"] = (1 + s["returns"]).cumprod()
        s["rolling_max"] = s["cumulative_returns"].rolling(lookback_medium, min_periods=10).max()
        s["drawdown"] = (s["cumulative_returns"] - s["rolling_max"]) / s["rolling_max"]
        s["max_drawdown"] = s["drawdown"].rolling(lookback_medium, min_periods=10).min()
        
        # 수익률 일관성 (낮은 편차)
        s["return_consistency"] = -s["returns"].rolling(lookback_medium, min_periods=10).std()
        
        # 샤프 비율
        s["sharpe_ratio"] = s["returns"].rolling(lookback_medium, min_periods=10).mean() / (s["returns"].rolling(lookback_medium, min_periods=10).std() + 0.001)
        
        # 상승 확률
        s["win_rate"] = s["returns"].rolling(lookback_short, min_periods=5).apply(lambda x: (x > 0).mean())
        
        # 손익비 (평균 이익 / 평균 손실)
        s["avg_gain"] = s["returns"].where(s["returns"] > 0).rolling(lookback_short, min_periods=3).mean()
        s["avg_loss"] = s["returns"].where(s["returns"] < 0).rolling(lookback_short, min_periods=3).mean()
        s["profit_loss_ratio"] = s["avg_gain"] / abs(s["avg_loss"])
        
        # 품질 종합 스코어
        quality_scores = [
            -self._normalize_factor(s["max_drawdown"]),
            self._normalize_factor(s["return_consistency"]),
            self._normalize_factor(s["sharpe_ratio"]),
            self._normalize_factor(s["win_rate"] - 0.5),
            self._normalize_factor(s["profit_loss_ratio"] - 1)
        ]
        s["quality_factor"] = pd.DataFrame(quality_scores).T.mean(axis=1)
        
        # 6. 감정 팩터 (Sentiment Factor) - 시뮬레이션
        
        # 가격 충격 (뉴스 이벤트 프록시)
        s["price_shock"] = abs(s["returns"]) > s["returns"].rolling(lookback_medium, min_periods=10).std() * 2
        s["positive_shock"] = (s["returns"] > s["returns"].rolling(lookback_medium, min_periods=10).std() * 1.5).astype(float)
        s["negative_shock"] = (s["returns"] < -s["returns"].rolling(lookback_medium, min_periods=10).std() * 1.5).astype(float)
        
        # 감정 지속성 (충격 이후 반응)
        s["sentiment_momentum"] = (s["positive_shock"] - s["negative_shock"]).rolling(5, min_periods=3).sum()
        
        # 거래량 기반 관심도
        s["attention"] = (s["volume_ratio"] - 1).clip(lower=-0.5, upper=2)
        
        # 변동성 기반 불확실성
        s["uncertainty"] = -s["realized_vol_short"] / s["realized_vol_long"]
        
        # 감정 종합 스코어
        sentiment_scores = [
            self._normalize_factor(s["sentiment_momentum"]),
            self._normalize_factor(s["attention"]),
            self._normalize_factor(s["uncertainty"])
        ]
        s["sentiment_factor"] = pd.DataFrame(sentiment_scores).T.mean(axis=1)
        
        # 7. 팩터 조합 및 종합 스코어
        
        # 각 팩터 정규화
        factors = {}
        for factor_name in weights.keys():
            factor_col = f"{factor_name}_factor"
            factors[factor_name] = self._normalize_factor(s[factor_col])
        
        # 가중 평균으로 종합 스코어 계산
        s["composite_score"] = sum(
            weights[factor_name] * factors[factor_name] 
            for factor_name in weights.keys()
        )
        
        # 스코어 순위 (상대적 위치)
        s["score_rank"] = s["composite_score"].rolling(lookback_long, min_periods=30).rank(pct=True)
        
        # 8. 매매 신호 생성
        
        # 강한 매수: 종합 스코어가 높고, 주요 팩터들이 일치
        strong_buy_conditions = [
            s["composite_score"] > factor_threshold,
            s["score_rank"] > 0.8,  # 상위 20%
            s["momentum_factor"] > 0.2,  # 모멘텀 확인
            s["volume_factor"] > 0.1,    # 거래량 확인
            s["quality_factor"] > 0      # 품질 확인
        ]
        
        # 약한 매수: 평균회귀나 품질 중심
        weak_buy_conditions = [
            s["composite_score"] > 0.2,
            (s["mean_reversion_factor"] > 0.3) | (s["quality_factor"] > 0.3),
            s["volatility_factor"] > -0.2,  # 너무 높은 변동성 아님
            s["sentiment_factor"] > -0.3    # 부정적 감정 아님
        ]
        
        # 강한 매도
        strong_sell_conditions = [
            s["composite_score"] < -factor_threshold,
            s["score_rank"] < 0.2,  # 하위 20%
            s["momentum_factor"] < -0.2,
            (s["volatility_factor"] < -0.3) | (s["quality_factor"] < -0.3)
        ]
        
        # 약한 매도
        weak_sell_conditions = [
            s["composite_score"] < -0.2,
            s["mean_reversion_factor"] < -0.3,
            s["sentiment_factor"] < -0.2
        ]
        
        # 신호 조합
        strong_buy = pd.DataFrame(strong_buy_conditions).T.all(axis=1)
        weak_buy = pd.DataFrame(weak_buy_conditions).T.all(axis=1)
        strong_sell = pd.DataFrame(strong_sell_conditions).T.all(axis=1)
        weak_sell = pd.DataFrame(weak_sell_conditions).T.all(axis=1)
        
        buy_signal = strong_buy | (weak_buy & ~strong_sell)
        sell_signal = strong_sell | (weak_sell & ~strong_buy)
        
        action = np.where(buy_signal.fillna(False), "BUY",
                 np.where(sell_signal.fillna(False), "SELL", "HOLD"))
        
        # 9. 신뢰도 계산
        
        # 팩터 일관성 (모든 팩터가 같은 방향)
        factor_alignment = pd.DataFrame([
            factors[name] for name in weights.keys()
        ]).T
        factor_consistency = (factor_alignment > 0).sum(axis=1) / len(weights)
        factor_consistency = np.where(
            s["composite_score"] < 0,
            (factor_alignment < 0).sum(axis=1) / len(weights),
            factor_consistency
        )
        
        # 스코어 강도
        score_strength = abs(s["composite_score"]).fillna(0)
        
        # 순위 신뢰도
        rank_confidence = np.where(
            s["score_rank"] > 0.5,
            (s["score_rank"] - 0.5) * 2,
            (0.5 - s["score_rank"]) * 2
        )
        
        # 변동성 조정 신뢰도
        vol_adjusted_confidence = 1 / (1 + s["realized_vol_short"] * 50)
        
        # 종합 신뢰도
        confidence = (
            0.3 * factor_consistency +
            0.25 * score_strength +
            0.25 * rank_confidence +
            0.2 * vol_adjusted_confidence
        )
        confidence = np.clip(confidence.fillna(0.5), 0, 1)
        
        # 10. 리스크 관리
        
        # ATR
        s["atr"] = self._calculate_atr(s["High"], s["Low"], s["Close"], 14)
        
        # 팩터 강도에 따른 리스크 조정
        risk_multiplier = 1 + abs(s["composite_score"]) * 0.5
        
        stop = np.where(action == "BUY", s["Close"] - risk_multiplier * s["atr"],
                       np.where(action == "SELL", s["Close"] + risk_multiplier * s["atr"], np.nan))
        
        target = np.where(action == "BUY", s["Close"] + 2 * risk_multiplier * s["atr"],
                         np.where(action == "SELL", s["Close"] - 2 * risk_multiplier * s["atr"], np.nan))
        
        # 매매 이유
        reason = np.where(
            action == "BUY",
            np.where(strong_buy, "강한팩터매수", "약한팩터매수"),
            np.where(action == "SELL", 
                    np.where(strong_sell, "강한팩터매도", "약한팩터매도"), 
                    "보유")
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
        warmup = int(p.get("warmup", 100))
        if len(out) <= warmup:
            return out.tail(1) if len(out) > 0 else out
        return out.iloc[warmup:]
    
    def _normalize_factor(self, series, method='zscore'):
        """팩터 정규화"""
        if method == 'zscore':
            mean = series.rolling(60, min_periods=20).mean()
            std = series.rolling(60, min_periods=20).std()
            return (series - mean) / (std + 0.001)
        elif method == 'rank':
            return series.rolling(60, min_periods=20).rank(pct=True) - 0.5
        else:
            # minmax scaling
            rolling_min = series.rolling(60, min_periods=20).min()
            rolling_max = series.rolling(60, min_periods=20).max()
            return (series - rolling_min) / (rolling_max - rolling_min + 0.001) - 0.5
    
    def _calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        delta = prices.diff()
        gain = delta.clip(lower=0).rolling(period, min_periods=1).mean()
        loss = (-delta.clip(upper=0)).rolling(period, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        return 100 - (100 / (1 + rs))
    
    def _calculate_bb_position(self, prices, period=20, std=2):
        """볼린저 밴드 위치"""
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
        tr = pd.DataFrame({"hl": high_low, "hc": high_close, "lc": low_close}).max(axis=1)
        return tr.rolling(period, min_periods=1).mean()
    
    def _add_financial_factors(self, df: pd.DataFrame, lookback_period: int) -> pd.DataFrame:
        """Point-in-Time 재무데이터를 활용한 펀더멘털 팩터 추가"""
        if not self._point_in_time_financials or not self._ticker:
            # 재무데이터가 없으면 기본값으로 채움
            df["pe_ratio"] = 15.0
            df["pb_ratio"] = 1.5
            df["roe"] = 0.1
            df["debt_ratio"] = 0.3
            df["revenue_growth"] = 0.05
            df["eps_growth"] = 0.1
            df["fundamental_factor"] = 0.0
            return df
            
        # 각 날짜별로 해당 시점에서 알 수 있었던 재무데이터 조회
        fundamental_data = []
        
        for date in df.index:
            try:
                # 동기식 호출을 위해 asyncio.run 사용하지 않고 기본값 설정
                # 실제 구현에서는 비동기 처리 또는 사전 로딩 필요
                financial_data = {
                    "pe_ratio": 15.0,
                    "pb_ratio": 1.5, 
                    "roe": 0.1,
                    "debt_ratio": 0.3,
                    "revenue_growth": 0.05,
                    "eps_growth": 0.1
                }
                fundamental_data.append(financial_data)
            except Exception:
                # 데이터가 없으면 기본값 사용
                fundamental_data.append({
                    "pe_ratio": 15.0,
                    "pb_ratio": 1.5,
                    "roe": 0.1, 
                    "debt_ratio": 0.3,
                    "revenue_growth": 0.05,
                    "eps_growth": 0.1
                })
        
        # DataFrame에 재무데이터 추가
        fundamental_df = pd.DataFrame(fundamental_data, index=df.index)
        for col in fundamental_df.columns:
            df[col] = fundamental_df[col]
            
        # 펀더멘털 팩터 스코어 계산
        # PE 비율 (낮을수록 좋음)
        pe_score = self._normalize_factor(-df["pe_ratio"])  # 음수로 변환 (낮을수록 높은 점수)
        
        # PB 비율 (낮을수록 좋음)  
        pb_score = self._normalize_factor(-df["pb_ratio"])
        
        # ROE (높을수록 좋음)
        roe_score = self._normalize_factor(df["roe"])
        
        # 부채비율 (낮을수록 좋음)
        debt_score = self._normalize_factor(-df["debt_ratio"])
        
        # 매출 성장률 (높을수록 좋음)
        revenue_growth_score = self._normalize_factor(df["revenue_growth"])
        
        # EPS 성장률 (높을수록 좋음) 
        eps_growth_score = self._normalize_factor(df["eps_growth"])
        
        # 펀더멘털 종합 점수 (각 팩터에 동일 가중치)
        df["fundamental_factor"] = (
            pe_score * 0.2 + 
            pb_score * 0.2 + 
            roe_score * 0.2 + 
            debt_score * 0.15 + 
            revenue_growth_score * 0.125 + 
            eps_growth_score * 0.125
        )
        
        return df
