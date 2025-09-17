"""
Machine Learning Strategy
머신러닝 기반 주가 예측 및 매매 신호 생성
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from .base import Strategy


class MachineLearningStrategy(Strategy):
    """머신러닝 전략"""
    
    name = "machine_learning"
    
    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        """
        머신러닝 기반 신호 생성 (단순 선형 회귀 + 앙상블)
        
        Parameters:
            df: OHLCV 데이터
            params:
                - feature_period: 피처 계산 기간 (기본값: 20)
                - prediction_horizon: 예측 기간 (기본값: 5)
                - confidence_threshold: 신뢰도 임계값 (기본값: 0.6)
                - ensemble_models: 앙상블 모델 수 (기본값: 3)
                - lookback_window: 학습 데이터 윈도우 (기본값: 100)
                - warmup: 워밍업 기간 (기본값: 120)
        """
        p = {
            "feature_period": 20, "prediction_horizon": 5, "confidence_threshold": 0.6,
            "ensemble_models": 3, "lookback_window": 100, "warmup": 120
        }
        if params:
            p.update(params)
        
        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "High", "Low", "Volume"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")
        
        feature_period = int(p["feature_period"])
        prediction_horizon = int(p["prediction_horizon"])
        confidence_threshold = float(p["confidence_threshold"])
        ensemble_models = int(p["ensemble_models"])
        lookback_window = int(p["lookback_window"])
        
        # 1. 피처 엔지니어링
        
        # Point-in-Time 재무데이터 추가 
        s = self._add_financial_features(s, feature_period)
        
        # 가격 기반 피처
        s["returns"] = s["Close"].pct_change().shift(1)
        s["log_returns"] = np.log(s["Close"] / s["Close"].shift(1)).shift(1)
        
        # 기술적 지표 피처
        s["rsi"] = self._calculate_rsi(s["Close"], 14).shift(1)
        s["macd"], s["macd_signal"] = self._calculate_macd(s["Close"]).shift(1), self._calculate_macd_signal(s["Close"]).shift(1)
        s["bb_position"] = self._calculate_bb_position(s["Close"], feature_period).shift(1)
        
        # 모멘텀 피처
        for period in [5, 10, 20]:
            s[f"momentum_{period}"] = (s["Close"] / s["Close"].shift(period) - 1).shift(1)
            s[f"volatility_{period}"] = s["returns"].rolling(period, min_periods=1).std().shift(1)
        
        # 거래량 피처
        s["volume_ma"] = s["Volume"].rolling(feature_period, min_periods=1).mean().shift(1)
        s["volume_ratio"] = (s["Volume"] / s["volume_ma"]).shift(1)
        s["price_volume"] = (s["Close"] * s["Volume"]).rolling(10, min_periods=1).mean().shift(1)
        
        # 패턴 피처 (간단한 패턴 인식)
        s["higher_high"] = ((s["High"] > s["High"].shift(1)) & 
                           (s["High"].shift(1) > s["High"].shift(2))).astype(float).shift(1)
        s["lower_low"] = ((s["Low"] < s["Low"].shift(1)) & 
                         (s["Low"].shift(1) < s["Low"].shift(2))).astype(float).shift(1)
        
        # 시장 구조 피처
        s["daily_range"] = ((s["High"] - s["Low"]) / s["Close"]).shift(1)
        s["gap"] = ((s["Open"] - s["Close"].shift(1)) / s["Close"].shift(1)).shift(1)
        
        # 2. 타겟 변수 (미래 수익률)
        s[f"target_{prediction_horizon}d"] = (s["Close"].shift(-prediction_horizon) / s["Close"] - 1)
        
        # 3. 피처 선택 및 정규화
        feature_columns = [
            "returns", "rsi", "macd", "bb_position", "momentum_5", "momentum_10", "momentum_20",
            "volatility_5", "volatility_10", "volatility_20", "volume_ratio", 
            "higher_high", "lower_low", "daily_range", "gap"
        ]
        
        # 결측치 처리
        for col in feature_columns:
            s[col] = s[col].fillna(s[col].median())
        
        # 정규화 (Z-score)
        for col in feature_columns:
            if col in s.columns:
                rolling_mean = s[col].rolling(50, min_periods=10).mean()
                rolling_std = s[col].rolling(50, min_periods=10).std()
                s[f"{col}_norm"] = ((s[col] - rolling_mean) / rolling_std).fillna(0)
        
        # 4. 단순 머신러닝 모델 (이동 윈도우 선형 회귀)
        
        s["ml_prediction"] = np.nan
        s["ml_confidence"] = np.nan
        s["ensemble_prediction"] = np.nan
        
        normalized_features = [f"{col}_norm" for col in feature_columns if f"{col}_norm" in s.columns]
        
        for i in range(lookback_window, len(s) - prediction_horizon):
            try:
                # 학습 데이터 준비
                start_idx = max(0, i - lookback_window)
                end_idx = i
                
                # 피처와 타겟 추출
                X = s[normalized_features].iloc[start_idx:end_idx].values
                y = s[f"target_{prediction_horizon}d"].iloc[start_idx:end_idx].values
                
                # NaN 제거
                valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
                if valid_mask.sum() < 20:  # 최소 학습 데이터
                    continue
                    
                X_clean = X[valid_mask]
                y_clean = y[valid_mask]
                
                # 현재 피처
                X_current = s[normalized_features].iloc[i].values.reshape(1, -1)
                
                if np.isnan(X_current).any():
                    continue
                
                # 앙상블 예측
                predictions = []
                
                for model_idx in range(ensemble_models):
                    # 부트스트랩 샘플링
                    sample_size = min(len(X_clean), 80)
                    sample_indices = np.random.choice(len(X_clean), size=sample_size, replace=True)
                    X_sample = X_clean[sample_indices]
                    y_sample = y_clean[sample_indices]
                    
                    # 단순 선형 회귀 (최소제곱법)
                    if len(X_sample) > len(X_sample[0]):  # 피처 수보다 많은 샘플
                        # Ridge 회귀 (L2 정규화)
                        lambda_reg = 0.1
                        XtX = X_sample.T @ X_sample + lambda_reg * np.eye(X_sample.shape[1])
                        
                        try:
                            Xty = X_sample.T @ y_sample
                            weights = np.linalg.solve(XtX, Xty)
                            
                            # 예측
                            prediction = X_current @ weights
                            predictions.append(prediction[0])
                            
                        except np.linalg.LinAlgError:
                            continue
                
                if predictions:
                    # 앙상블 평균
                    ensemble_pred = np.mean(predictions)
                    prediction_std = np.std(predictions)
                    
                    # 신뢰도 (예측 일관성)
                    confidence = max(0, 1 - prediction_std / (abs(ensemble_pred) + 0.01))
                    
                    s.loc[s.index[i], "ml_prediction"] = ensemble_pred
                    s.loc[s.index[i], "ml_confidence"] = confidence
                    s.loc[s.index[i], "ensemble_prediction"] = ensemble_pred
                    
            except Exception as e:
                continue
        
        # 5. 매매 신호 생성
        
        # 예측 기반 신호
        strong_buy_signal = (
            (s["ml_prediction"] > 0.02) &  # 2% 이상 상승 예측
            (s["ml_confidence"] > confidence_threshold)
        ).fillna(False)
        
        strong_sell_signal = (
            (s["ml_prediction"] < -0.02) &  # 2% 이상 하락 예측
            (s["ml_confidence"] > confidence_threshold)
        ).fillna(False)
        
        # 기술적 지표와 결합 (필터링)
        technical_confirm_buy = (
            (s["rsi"] < 70) &  # 과매수 아님
            (s["volume_ratio"] > 1.1) &  # 거래량 증가
            (s["bb_position"] < 0.8)  # BB 상단 근처 아님
        ).fillna(False)
        
        technical_confirm_sell = (
            (s["rsi"] > 30) &  # 과매도 아님
            (s["volume_ratio"] > 1.1) &  # 거래량 증가
            (s["bb_position"] > 0.2)  # BB 하단 근처 아님
        ).fillna(False)
        
        # 최종 신호
        buy_rule = strong_buy_signal & technical_confirm_buy
        sell_rule = strong_sell_signal & technical_confirm_sell
        
        action = np.where(buy_rule.fillna(False), "BUY",
                 np.where(sell_rule.fillna(False), "SELL", "HOLD"))
        
        # 신뢰도 (ML 신뢰도 + 기술적 확인)
        ml_confidence_score = s["ml_confidence"].fillna(0)
        technical_score = np.where(
            action == "BUY", 
            (technical_confirm_buy.astype(float)).fillna(0),
            np.where(action == "SELL", 
                    (technical_confirm_sell.astype(float)).fillna(0), 0.5)
        )
        
        confidence = (0.7 * ml_confidence_score + 0.3 * technical_score).fillna(0.5)
        confidence = np.clip(confidence, 0, 1)
        
        # 리스크 관리 (예측 불확실성 고려)
        prediction_magnitude = abs(s["ml_prediction"].fillna(0))
        risk_multiplier = np.clip(prediction_magnitude * 10, 1, 3)  # 예측 크기에 따른 리스크 조정
        
        # ATR 계산
        s["high_low"] = s["High"] - s["Low"]
        s["high_close"] = abs(s["High"] - s["Close"].shift(1))
        s["low_close"] = abs(s["Low"] - s["Close"].shift(1))
        s["tr"] = s[["high_low", "high_close", "low_close"]].max(axis=1)
        s["atr"] = s["tr"].rolling(14, min_periods=1).mean().shift(1)
        
        stop = np.where(action == "BUY", s["Close"] - risk_multiplier * s["atr"],
                       np.where(action == "SELL", s["Close"] + risk_multiplier * s["atr"], np.nan))
        
        target = np.where(action == "BUY", s["Close"] * (1 + abs(s["ml_prediction"])),
                         np.where(action == "SELL", s["Close"] * (1 - abs(s["ml_prediction"])), np.nan))
        
        # 결과 조합
        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = confidence
        out["reason"] = np.where(action == "BUY", "ML상승예측+기술적확인",
                           np.where(action == "SELL", "ML하락예측+기술적확인", "보유"))
        out["stop"] = stop
        out["target"] = target
        out["size"] = 1.0
        
        # 워밍업 적용
        warmup = int(p.get("warmup", 120))
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
    
    def _add_financial_features(self, df: pd.DataFrame, feature_period: int) -> pd.DataFrame:
        """Point-in-Time 재무데이터를 활용한 ML 피처 추가"""
        if not self._point_in_time_financials or not self._ticker:
            # 재무데이터가 없으면 기본값으로 채움
            df["pe_ratio"] = 15.0
            df["pb_ratio"] = 1.5
            df["roe"] = 0.1
            df["debt_ratio"] = 0.3
            df["revenue_growth"] = 0.05
            df["eps_growth"] = 0.1
            df["current_ratio"] = 2.0
            df["roa"] = 0.08
            return df
            
        # 각 날짜별로 해당 시점에서 알 수 있었던 재무데이터 조회
        fundamental_data = []
        
        for date in df.index:
            try:
                # 실제 구현에서는 비동기 처리 필요
                financial_data = {
                    "pe_ratio": 15.0,
                    "pb_ratio": 1.5,
                    "roe": 0.1,
                    "debt_ratio": 0.3,
                    "revenue_growth": 0.05,
                    "eps_growth": 0.1,
                    "current_ratio": 2.0,
                    "roa": 0.08
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
                    "eps_growth": 0.1,
                    "current_ratio": 2.0,
                    "roa": 0.08
                })
        
        # DataFrame에 재무데이터 추가
        fundamental_df = pd.DataFrame(fundamental_data, index=df.index)
        for col in fundamental_df.columns:
            df[col] = fundamental_df[col]
            
        # 재무데이터 기반 파생 피처 생성
        # PE/PB 비율 변화
        df["pe_change"] = df["pe_ratio"].pct_change(feature_period)
        df["pb_change"] = df["pb_ratio"].pct_change(feature_period)
        
        # 수익성 지표 조합
        df["profitability_score"] = (df["roe"] * 0.6 + df["roa"] * 0.4)
        
        # 재무건전성 지표
        df["financial_health"] = (df["current_ratio"] / 3.0) - (df["debt_ratio"] / 0.5)
        
        # 성장성 지표  
        df["growth_score"] = (df["revenue_growth"] * 0.6 + df["eps_growth"] * 0.4)
        
        # 상대적 밸류에이션 (롤링 순위)
        df["pe_rank"] = df["pe_ratio"].rolling(feature_period * 2, min_periods=10).rank(pct=True)
        df["pb_rank"] = df["pb_ratio"].rolling(feature_period * 2, min_periods=10).rank(pct=True)
        
        return df

    def _add_financial_features(self, df: pd.DataFrame, feature_period: int) -> pd.DataFrame:
        """Point-in-Time 재무데이터를 활용한 ML 피처 추가"""
        if not self._point_in_time_financials or not self._ticker:
            # 재무데이터가 없으면 기본값으로 채움
            financial_features = {
                "pe_ratio": 15.0, "pb_ratio": 1.5, "roe": 0.1, "roa": 0.05,
                "debt_ratio": 0.3, "current_ratio": 2.0, "revenue_growth": 0.05, 
                "eps_growth": 0.1
            }
            for col, default_val in financial_features.items():
                df[col] = default_val
            return self._create_financial_ml_features(df, feature_period)
            
        # 각 날짜별로 해당 시점에서 알 수 있었던 재무데이터 조회
        # 실제 구현에서는 비동기 처리가 필요하지만 여기서는 기본값 사용
        financial_features = {
            "pe_ratio": 15.0, "pb_ratio": 1.5, "roe": 0.1, "roa": 0.05,
            "debt_ratio": 0.3, "current_ratio": 2.0, "revenue_growth": 0.05, 
            "eps_growth": 0.1
        }
        
        for col, default_val in financial_features.items():
            df[col] = default_val
            
        return self._create_financial_ml_features(df, feature_period)

    def _create_financial_ml_features(self, df: pd.DataFrame, feature_period: int) -> pd.DataFrame:
        """재무데이터를 기반으로 ML 피처 생성"""
        # PE/PB 비율 변화
        df["pe_change"] = df["pe_ratio"].pct_change(feature_period)
        df["pb_change"] = df["pb_ratio"].pct_change(feature_period)
        
        # 수익성 지표 조합
        df["profitability_score"] = (df["roe"] * 0.6 + df["roa"] * 0.4)
        
        # 재무건전성 지표
        df["financial_health"] = (df["current_ratio"] / 3.0) - (df["debt_ratio"] / 0.5)
        
        # 성장성 지표  
        df["growth_score"] = (df["revenue_growth"] * 0.6 + df["eps_growth"] * 0.4)
        
        # 상대적 밸류에이션 (롤링 순위)
        df["pe_rank"] = df["pe_ratio"].rolling(feature_period * 2, min_periods=10).rank(pct=True)
        df["pb_rank"] = df["pb_ratio"].rolling(feature_period * 2, min_periods=10).rank(pct=True)
        
        return df
