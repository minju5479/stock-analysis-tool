"""
룰 기반 베이스라인 전략: MA/RSI/MACD 결합
"""
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import numpy as np
from .base import Strategy

class RuleBasedStrategy(Strategy):
    name = "baseline"

    def compute_signals(self, df: pd.DataFrame, params: Dict[str, Any] | None = None) -> pd.DataFrame:
        p = {"rsi_buy": 30, "rsi_sell": 70, "risk_rr": 2.0, "warmup": 200}
        if params:
            p.update(params)

        s = df.copy().rename_axis("date")
        # 요구 컬럼 체크
        req_cols = ["Close", "Open", "Daily_Return", "Volatility"]
        for c in req_cols:
            if c not in s.columns:
                raise ValueError(f"필수 컬럼 없음: {c}")

        # 이동평균 (룩어헤드 방지 위해 shift)
        s["ma50"] = s["Close"].rolling(50, min_periods=1).mean().shift(1)
        s["ma200"] = s["Close"].rolling(200, min_periods=1).mean().shift(1)

        # RSI (분모 0 회피)
        delta = s["Close"].diff()
        gain = delta.clip(lower=0).rolling(14, min_periods=1).mean()
        loss = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
        rs = gain / loss.replace(0, np.nan)
        s["rsi"] = (100 - (100 / (1 + rs))).shift(1)

        # MACD (t-1 기준으로 판단)
        macd_line = s["Close"].ewm(span=12, adjust=False).mean() - s["Close"].ewm(span=26, adjust=False).mean()
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_now = macd_line.shift(1)
        signal_now = signal_line.shift(1)
        s["macd_cross"] = (macd_now > signal_now).astype(int)

        # 규칙 (짧은 데이터 허용)
        has_ma200 = s["ma200"].notna()
        trend_up = np.where(has_ma200, s["ma50"] > s["ma200"], s["Close"] > s["ma50"]).astype(bool)
        trend_down = np.where(has_ma200, s["ma50"] < s["ma200"], s["Close"] < s["ma50"]).astype(bool)
        oversold = s["rsi"] <= p["rsi_buy"]
        overbought = s["rsi"] >= p["rsi_sell"]
        macd_up = s["macd_cross"] == 1
        macd_down = s["macd_cross"] == 0

        # 이벤트형 MACD 크로스 (t-1 대비 변화)
        macd_prev = macd_line.shift(2)
        signal_prev = signal_line.shift(2)
        macd_cross_up_evt = (macd_now > signal_now) & (macd_prev <= signal_prev)
        macd_cross_dn_evt = (macd_now < signal_now) & (macd_prev >= signal_prev)

        buy_rule = (trend_up & (oversold | macd_up)) | macd_cross_up_evt
        sell_rule = (trend_down & (overbought | macd_down)) | macd_cross_dn_evt

        action = np.where(buy_rule, "BUY", np.where(sell_rule, "SELL", "HOLD"))
        conf_series = (
            0.4 * pd.Series(trend_up, index=s.index).astype(int)
            + 0.3 * (~pd.Series(overbought, index=s.index)).astype(int)
            + 0.3 * pd.Series(macd_up, index=s.index).astype(int)
        )
        confidence = conf_series.to_numpy()
        confidence = np.where(action == "SELL", 1 - confidence, confidence)

        # 스탑/타겟 (20일 표준편차, t-1)
        vol = s["Close"].rolling(20, min_periods=1).std().shift(1)
        stop = np.where(action == "BUY", s["Close"] - 2 * vol, np.where(action == "SELL", s["Close"] + 2 * vol, np.nan))
        target = np.where(action == "BUY", s["Close"] + 2 * p["risk_rr"] * vol, np.where(action == "SELL", s["Close"] - 2 * p["risk_rr"] * vol, np.nan))

        out = s[["Close"]].copy()
        out["action"] = action
        out["confidence"] = np.clip(confidence, 0, 1)
        out["reason"] = np.where(action == "BUY", "추세상승+과매도/상향크로스",
                           np.where(action == "SELL", "추세하락+과매수/하향크로스", "보유"))
        out["stop"] = stop
        out["target"] = target
        out["size"] = 1.0

        # 전체 타임라인 유지 (HOLD 포함). 워밍업 처리로 초기 구간 최소화
        res = out
        warmup = int(p.get("warmup", 200))
        if len(res) == 0:
            return res
        if len(res) <= warmup:
            return res.tail(1)
        return res.iloc[warmup:]
