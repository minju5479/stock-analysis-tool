"""
기술적 분석 모듈
"""

import pandas as pd
from typing import Dict, Any

class TechnicalAnalyzer:
    """기술적 지표 분석 클래스"""
    
    @staticmethod
    def calculate_moving_averages(close_prices: pd.Series) -> Dict[str, float]:
        """이동평균을 계산합니다."""
        return {
            "ma_20": close_prices.rolling(window=20).mean().iloc[-1],
            "ma_50": close_prices.rolling(window=50).mean().iloc[-1],
            "ma_200": close_prices.rolling(window=200).mean().iloc[-1]
        }

    @staticmethod
    def calculate_rsi(close_prices: pd.Series) -> Dict[str, Any]:
        """RSI를 계산합니다."""
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        return {
            "current": round(current_rsi, 2),
            "interpretation": TechnicalAnalyzer._interpret_rsi(current_rsi)
        }
    
    @staticmethod
    def calculate_macd(close_prices: pd.Series) -> Dict[str, Any]:
        """MACD를 계산합니다."""
        ema_12 = close_prices.ewm(span=12).mean()
        ema_26 = close_prices.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        return {
            "macd_line": round(macd.iloc[-1], 2),
            "signal_line": round(signal.iloc[-1], 2),
            "histogram": round(histogram.iloc[-1], 2),
            "interpretation": TechnicalAnalyzer._interpret_macd(macd.iloc[-1], signal.iloc[-1])
        }
    
    @staticmethod
    def calculate_bollinger_bands(close_prices: pd.Series) -> Dict[str, Any]:
        """볼린저 밴드를 계산합니다."""
        bb_20 = close_prices.rolling(window=20).mean()
        bb_std = close_prices.rolling(window=20).std()
        bb_upper = bb_20 + (bb_std * 2)
        bb_lower = bb_20 - (bb_std * 2)
        
        return {
            "upper": round(bb_upper.iloc[-1], 2),
            "middle": round(bb_20.iloc[-1], 2),
            "lower": round(bb_lower.iloc[-1], 2)
        }

    @staticmethod
    def calculate_roc(data: pd.DataFrame, period: int = 12) -> pd.Series:
        """Rate of Change (ROC) 계산"""
        return ((data['Close'] - data['Close'].shift(period)) / data['Close'].shift(period)) * 100

    @staticmethod
    def calculate_williams_r(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Williams %R 계산"""
        highest_high = data['High'].rolling(window=period).max()
        lowest_low = data['Low'].rolling(window=period).min()
        williams_r = ((highest_high - data['Close']) / (highest_high - lowest_low)) * -100
        return williams_r

    @staticmethod
    def calculate_obv(data: pd.DataFrame) -> pd.Series:
        """On Balance Volume (OBV) 계산"""
        obv = pd.Series(index=data.index, dtype=float)
        obv.iloc[0] = 0
        
        for i in range(1, len(data)):
            if data['Close'].iloc[i] > data['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + data['Volume'].iloc[i]
            elif data['Close'].iloc[i] < data['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - data['Volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        return obv

    def calculate_mfi(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Money Flow Index (MFI) 계산"""
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        money_flow = typical_price * data['Volume']
        
        positive_flow = pd.Series(0.0, index=data.index)
        negative_flow = pd.Series(0.0, index=data.index)
        
        # Calculate positive and negative money flow
        for i in range(1, len(data)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                positive_flow.iloc[i] = money_flow.iloc[i]
            else:
                negative_flow.iloc[i] = money_flow.iloc[i]
        """Money Flow Index (MFI) 계산"""
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        money_flow = typical_price * data['Volume']
        
        positive_flow = pd.Series(0.0, index=data.index)
        negative_flow = pd.Series(0.0, index=data.index)
        
        for i in range(1, len(data)):
            if typical_price.iloc[i] > typical_price.iloc[i-1]:
                positive_flow.iloc[i] = money_flow.iloc[i]
            else:
                negative_flow.iloc[i] = money_flow.iloc[i]
        
        positive_mf = positive_flow.rolling(window=period).sum()
        negative_mf = negative_flow.rolling(window=period).sum()
        
        mfi = 100 - (100 / (1 + positive_mf / negative_mf))
        return mfi

    @staticmethod
    def _interpret_rsi(rsi: float) -> str:
        """RSI 해석"""
        if rsi > 70:
            return "과매수 구간 (매도 신호)"
        elif rsi < 30:
            return "과매도 구간 (매수 신호)"
        return "중립 구간"
    
    @staticmethod
    def _interpret_macd(macd: float, signal: float) -> str:
        """MACD 해석"""
        if macd > signal:
            return "상승 신호 (MACD가 시그널선 위)"
        return "하락 신호 (MACD가 시그널선 아래)"
    
    @staticmethod
    def analyze_technical_indicators(hist: pd.DataFrame) -> Dict[str, Any]:
        """모든 기술적 지표를 분석합니다."""
        close_prices = hist['Close']
        
        # 기본 지표 계산
        moving_averages = TechnicalAnalyzer.calculate_moving_averages(close_prices)
        rsi_data = TechnicalAnalyzer.calculate_rsi(close_prices)
        macd_data = TechnicalAnalyzer.calculate_macd(close_prices)
        bb_data = TechnicalAnalyzer.calculate_bollinger_bands(close_prices)
        
        # ROC 계산
        roc_data = TechnicalAnalyzer.calculate_roc(hist)
        current_roc = roc_data.iloc[-1]
        
        # Williams %R 계산
        williams_r_data = TechnicalAnalyzer.calculate_williams_r(hist)
        current_williams_r = williams_r_data.iloc[-1]
        
        # OBV 계산
        obv_data = TechnicalAnalyzer.calculate_obv(hist)
        current_obv = obv_data.iloc[-1]
        obv_sma = obv_data.rolling(window=20).mean()
        obv_trend = "상승" if current_obv > obv_sma.iloc[-1] else "하락"
        
        # MFI 계산
        mfi_data = TechnicalAnalyzer.calculate_mfi(hist)
        current_mfi = mfi_data.iloc[-1]
        
        return {
            "moving_averages": moving_averages,
            "rsi": rsi_data,
            "macd": macd_data,
            "bollinger_bands": bb_data,
            "roc": {
                "current": round(current_roc, 2),
                "interpretation": "상승 모멘텀" if current_roc > 0 else "하락 모멘텀"
            },
            "williams_r": {
                "current": round(current_williams_r, 2),
                "interpretation": "과매도" if current_williams_r <= -80 else "과매수" if current_williams_r >= -20 else "중립"
            },
            "obv": {
                "current": round(current_obv, 2),
                "trend": obv_trend,
                "interpretation": f"거래량 기반 {obv_trend} 추세"
            },
            "mfi": {
                "current": round(current_mfi, 2),
                "interpretation": "과매수" if current_mfi > 80 else "과매도" if current_mfi < 20 else "중립"
            }
        }
