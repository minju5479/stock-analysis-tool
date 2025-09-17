"""
Volume Profile 전략
거래량 프로파일을 기반으로 한 지지/저항 분석 및 매매 신호 생성
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from .base import Strategy


class VolumeProfileStrategy(Strategy):
    """거래량 프로파일 전략"""
    
    name = "volume_profile"
    
    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        """
        거래량 프로파일 기반 신호 생성
        
        Parameters:
            df: OHLCV 데이터
            params:
                - profile_period: 거래량 프로파일 분석 기간 (기본값: 50)
                - price_bins: 가격 구간 개수 (기본값: 20)
                - vwap_period: VWAP 계산 기간 (기본값: 20)
                - volume_threshold: 거래량 임계값 배수 (기본값: 1.5)
                - breakout_threshold: 돌파 임계값 (기본값: 0.015)
                - warmup: 워밍업 기간 (기본값: 60)
        """
        p = {
            "profile_period": 50, "price_bins": 20, "vwap_period": 20,
            "volume_threshold": 1.5, "breakout_threshold": 0.015, "warmup": 60
        }
        if params:
            p.update(params)
        
        s = df.copy().rename_axis("date")
        req_cols = ["Close", "Open", "High", "Low", "Volume"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")
        
        profile_period = int(p["profile_period"])
        price_bins = int(p["price_bins"])
        vwap_period = int(p["vwap_period"])
        volume_threshold = float(p["volume_threshold"])
        breakout_threshold = float(p["breakout_threshold"])
        
        # VWAP (Volume Weighted Average Price)
        s["typical_price"] = (s["High"] + s["Low"] + s["Close"]) / 3
        s["volume_price"] = s["typical_price"] * s["Volume"]
        s["vwap"] = (s["volume_price"].rolling(vwap_period, min_periods=1).sum() / 
                    s["Volume"].rolling(vwap_period, min_periods=1).sum()).shift(1)
        
        # 거래량 프로파일 계산
        s["volume_support"] = np.nan
        s["volume_resistance"] = np.nan
        s["high_volume_node"] = np.nan
        s["low_volume_node"] = np.nan
        s["volume_strength"] = np.nan
        
        for i in range(profile_period, len(s)):
            # 최근 N일 데이터 추출
            period_data = s.iloc[i-profile_period:i].copy()
            
            if len(period_data) == 0:
                continue
                
            # 가격 범위 설정
            min_price = period_data["Low"].min()
            max_price = period_data["High"].max()
            
            if min_price == max_price:
                continue
                
            # 가격 구간별 거래량 집계
            price_levels = np.linspace(min_price, max_price, price_bins + 1)
            volume_profile = np.zeros(price_bins)
            
            for j in range(len(period_data)):
                row = period_data.iloc[j]
                # 각 봉의 거래량을 가격 구간에 분배
                typical = row["typical_price"]
                volume = row["Volume"]
                
                # 해당하는 구간 찾기
                bin_idx = np.digitize(typical, price_levels) - 1
                bin_idx = max(0, min(price_bins - 1, bin_idx))
                volume_profile[bin_idx] += volume
            
            # 고거래량 구간 (Volume-at-Price 높은 구간)
            max_volume_idx = np.argmax(volume_profile)
            high_volume_price = (price_levels[max_volume_idx] + price_levels[max_volume_idx + 1]) / 2
            
            # 저거래량 구간 (Volume-at-Price 낮은 구간)  
            min_volume_idx = np.argmin(volume_profile[volume_profile > 0] if np.any(volume_profile > 0) else volume_profile)
            if len(volume_profile[volume_profile > 0]) > 0:
                valid_indices = np.where(volume_profile > 0)[0]
                min_volume_idx = valid_indices[np.argmin(volume_profile[valid_indices])]
            low_volume_price = (price_levels[min_volume_idx] + price_levels[min_volume_idx + 1]) / 2
            
            # 현재 가격 기준으로 지지/저항 결정
            current_price = s.iloc[i]["Close"]
            
            # 현재가 아래 고거래량 구간 = 지지선
            # 현재가 위 고거래량 구간 = 저항선
            if high_volume_price < current_price:
                s.loc[s.index[i], "volume_support"] = high_volume_price
            else:
                s.loc[s.index[i], "volume_resistance"] = high_volume_price
                
            s.loc[s.index[i], "high_volume_node"] = high_volume_price
            s.loc[s.index[i], "low_volume_node"] = low_volume_price
            s.loc[s.index[i], "volume_strength"] = np.max(volume_profile) / np.mean(volume_profile) if np.mean(volume_profile) > 0 else 1
        
        # 거래량 분석
        s["volume_sma"] = s["Volume"].rolling(20, min_periods=1).mean().shift(1)
        s["volume_ratio"] = (s["Volume"] / s["volume_sma"]).shift(1)
        
        # 가격과 VWAP 관계
        s["price_vs_vwap"] = (s["Close"] / s["vwap"] - 1).shift(1)
        
        # 지지/저항선 근접도
        s["distance_to_support"] = np.where(
            ~s["volume_support"].isna(),
            (s["Close"] / s["volume_support"] - 1).shift(1),
            np.nan
        )
        
        s["distance_to_resistance"] = np.where(
            ~s["volume_resistance"].isna(), 
            (s["volume_resistance"] / s["Close"] - 1).shift(1),
            np.nan
        )
        
        # 매매 신호 조건
        high_volume = (s["volume_ratio"] > volume_threshold).fillna(False).infer_objects(copy=False)
        strong_volume_node = (s["volume_strength"] > 2.0).fillna(False).infer_objects(copy=False)  # 평균 대비 2배 이상
        
        # 매수 신호: 거래량 지지선 근처 + VWAP 위 + 고거래량
        near_support = (s["distance_to_support"] > -0.02).fillna(False).infer_objects(copy=False) & (s["distance_to_support"] < 0.01).fillna(False).infer_objects(copy=False)
        above_vwap = (s["price_vs_vwap"] > 0).fillna(False).infer_objects(copy=False)
        
        # 매도 신호: 거래량 저항선 근처 + VWAP 아래로 하락 + 고거래량
        near_resistance = (s["distance_to_resistance"] > -0.01).fillna(False).infer_objects(copy=False) & (s["distance_to_resistance"] < 0.02).fillna(False).infer_objects(copy=False)
        below_vwap = (s["price_vs_vwap"] < -0.01).fillna(False).infer_objects(copy=False)
        
        # 저거래량 구간 돌파 (갭 매수/매도)
        low_volume_breakout = (
            (~s["low_volume_node"].isna()) &
            (abs(s["Close"] - s["low_volume_node"]) / s["Close"] < 0.005)  # 0.5% 이내
        ).fillna(False)
        
        # 최종 매매 신호
        buy_rule = (near_support & above_vwap & high_volume & strong_volume_node) | \
                  (low_volume_breakout & above_vwap & high_volume)
        
        sell_rule = (near_resistance & below_vwap & high_volume) | \
                   (low_volume_breakout & below_vwap & high_volume)
        
        action = np.where(buy_rule.fillna(False), "BUY",
                 np.where(sell_rule.fillna(False), "SELL", "HOLD"))
        
        # 신뢰도 계산 (거래량 강도 + VWAP 관계 + 지지저항 근접도)
        volume_score = np.clip((s["volume_ratio"].fillna(1) - 1) / 2, 0, 1)
        vwap_score = np.clip(abs(s["price_vs_vwap"].fillna(0)) * 10, 0, 1)
        node_score = np.clip((s["volume_strength"].fillna(1) - 1) / 3, 0, 1)
        
        confidence = (0.4 * volume_score + 0.3 * vwap_score + 0.3 * node_score).fillna(0.5)
        confidence = np.clip(confidence, 0, 1)
        
        # 손절/목표가 (거래량 프로파일 기준)
        stop = np.where(
            action == "BUY",
            np.where(~s["volume_support"].isna(), s["volume_support"] * 0.98, s["Close"] * 0.97),
            np.where(
                action == "SELL",
                np.where(~s["volume_resistance"].isna(), s["volume_resistance"] * 1.02, s["Close"] * 1.03),
                np.nan
            )
        )
        
        target = np.where(
            action == "BUY",
            np.where(~s["volume_resistance"].isna(), s["volume_resistance"], s["Close"] * 1.05),
            np.where(
                action == "SELL", 
                np.where(~s["volume_support"].isna(), s["volume_support"], s["Close"] * 0.95),
                np.nan
            )
        )
        
        # 결과 조합
        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = confidence
        out["reason"] = np.where(action == "BUY", "거래량지지선+VWAP상승+고거래량",
                           np.where(action == "SELL", "거래량저항선+VWAP하락+고거래량", "보유"))
        out["stop"] = stop
        out["target"] = target
        out["size"] = 1.0
        
        # 워밍업 적용
        warmup = int(p.get("warmup", 60))
        if len(out) <= warmup:
            return out.tail(1) if len(out) > 0 else out
        return out.iloc[warmup:]
