"""
차트 분석 및 생성을 위한 통합 모듈
"""

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
from typing import Dict, Any

from .renderers import ChartRenderer
from .formatters import ChartFormatters
from .styles import ChartStyles
from ..analysis.technical.indicators import TechnicalAnalyzer


class ChartAnalyzer:
    """주식 차트 분석 및 생성을 담당하는 클래스"""
    
    def __init__(self):
        self.renderer = ChartRenderer()
        self.formatters = ChartFormatters()
        self.styles = ChartStyles()
        self.technical_analyzer = TechnicalAnalyzer()
    
    async def get_stock_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """주식 데이터를 가져옵니다."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            return hist
        except Exception as e:
            raise Exception(f"데이터 조회 실패: {str(e)}")
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """기술적 지표를 계산합니다."""
        # 데이터 유효성 검사
        if df.empty:
            return {}
            
        close = df['Close'].dropna()
        high = df['High'].dropna()
        low = df['Low'].dropna()
        
        if len(close) < 20:  # 최소 데이터 길이 확인
            return {}
        
        # 이동평균
        ma_20 = close.rolling(window=20).mean()
        ma_50 = close.rolling(window=50).mean() if len(close) >= 50 else ma_20
        ma_200 = close.rolling(window=200).mean() if len(close) >= 200 else ma_20
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # 0으로 나누는 것 방지
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)  # NaN 값을 50으로 대체
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        # 볼린저 밴드
        bb_20 = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_20 + (bb_std * 2)
        bb_lower = bb_20 - (bb_std * 2)
        
        # 스토캐스틱
        try:
            low_14 = low.rolling(window=14).min()
            high_14 = high.rolling(window=14).max()
            
            # 분모가 0이 되는 것 방지
            denominator = high_14 - low_14
            denominator = denominator.replace(0, 1e-10)
            
            k_percent = 100 * ((close - low_14) / denominator)
            k_percent = k_percent.fillna(50).clip(0, 100)  # 0-100 범위로 제한
            d_percent = k_percent.rolling(window=3).mean()
        except Exception:
            # 스토캐스틱 계산 실패 시 기본값 사용
            k_percent = pd.Series([50] * len(close), index=close.index)
            d_percent = pd.Series([50] * len(close), index=close.index)
        
        return {
            'ma_20': ma_20.fillna(ma_20.mean()),
            'ma_50': ma_50.fillna(ma_50.mean()),
            'ma_200': ma_200.fillna(ma_200.mean()),
            'rsi': rsi,
            'macd': macd.fillna(0),
            'signal': signal.fillna(0),
            'histogram': histogram.fillna(0),
            'bb_upper': bb_upper.fillna(bb_upper.mean()),
            'bb_middle': bb_20.fillna(bb_20.mean()),
            'bb_lower': bb_lower.fillna(bb_lower.mean()),
            'k_percent': k_percent,
            'd_percent': d_percent
        }
    
    def create_candlestick_chart(self, df: pd.DataFrame, ticker: str, indicators: Dict[str, pd.Series]) -> go.Figure:
        """캔들스틱 차트를 생성합니다."""
        # 서브플롯 생성 (가격, 거래량, RSI, MACD)
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('가격 차트', '거래량', 'RSI', 'MACD'),
            row_heights=[0.5, 0.15, 0.15, 0.2]
        )
        
        # 이동평균선 추가
        self.renderer.add_moving_averages(fig, df, indicators, row=1, col=1)
        
        # 볼린저 밴드 추가
        self.renderer.add_bollinger_bands(fig, df, indicators, row=1, col=1)
        
        # 캔들스틱(가격) trace 추가
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='가격',
                increasing_line_color='#618fc4',
                decreasing_line_color='#ef5350'
            ),
            row=1, col=1
        )
        
        # 거래량 추가
        self.renderer.add_volume_bars(fig, df, row=2, col=1)
        
        # RSI 추가
        self.renderer.add_rsi(fig, indicators, row=3, col=1)
        
        # MACD 추가
        self.renderer.add_macd(fig, df, indicators, row=4, col=1)
        
        # 포맷팅 및 스타일링 적용
        fig = self.formatters.add_korean_weekday_hover(fig)
        fig = self.styles.apply_chart_layout(fig, ticker, chart_type='candlestick')
        
        return fig
    
    def create_price_chart(self, df: pd.DataFrame, ticker: str) -> go.Figure:
        """간단한 가격 차트를 생성합니다."""
        fig = go.Figure()
        
        # 거래량 (오버레이) 추가
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='거래량',
                yaxis='y2',
                opacity=0.3
            )
        )
        
        # 종가 라인 차트 추가
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['Close'],
                mode='lines',
                name='종가',
                line=dict(color='#1f77b4', width=2)
            )
        )
        
        # 포맷팅 및 스타일링 적용
        fig = self.formatters.add_korean_weekday_hover(fig)
        fig = self.styles.apply_chart_layout(fig, ticker, chart_type='price')
        
        return fig
    
    def create_technical_analysis_chart(self, df: pd.DataFrame, ticker: str, indicators: Dict[str, pd.Series]) -> go.Figure:
        """기술적 분석 차트를 생성합니다."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('RSI', 'MACD', '볼린저 밴드', '스토캐스틱'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # RSI 추가
        self.renderer.add_rsi(fig, indicators, row=1, col=1)
        
        # MACD 추가
        self.renderer.add_macd(fig, df, indicators, row=1, col=2)
        
        # 볼린저 밴드 추가
        self.renderer.add_bollinger_bands_with_price(fig, df, indicators, row=2, col=1)
        
        # 스토캐스틱 추가
        self.renderer.add_stochastic(fig, indicators, row=2, col=2)
        
        # 포맷팅 및 스타일링 적용
        fig = self.formatters.add_korean_weekday_hover(fig)
        fig = self.styles.apply_chart_layout(fig, ticker, chart_type='technical')
        
        return fig
    
    async def generate_charts(self, ticker: str, period: str = "1y") -> Dict[str, go.Figure]:
        """모든 차트를 생성합니다."""
        try:
            # 데이터 가져오기
            df = await self.get_stock_data(ticker, period)
            
            if df.empty:
                raise Exception("데이터가 없습니다.")
            
            # 기술적 지표 계산
            indicators = self.calculate_technical_indicators(df)
            
            # 차트 생성
            charts = {
                'candlestick': self.create_candlestick_chart(df, ticker, indicators),
                'price': self.create_price_chart(df, ticker),
                'technical': self.create_technical_analysis_chart(df, ticker, indicators)
            }
            
            return charts
            
        except Exception as e:
            raise Exception(f"차트 생성 실패: {str(e)}")


# 사용 예시
async def main():
    """테스트 함수"""
    analyzer = ChartAnalyzer()
    
    try:
        charts = await analyzer.generate_charts("AAPL", "6mo")
        
        # 차트를 HTML 파일로 저장
        for name, fig in charts.items():
            fig.write_html(f"{name}_chart.html")
            print(f"{name} 차트가 생성되었습니다.")
            
    except Exception as e:
        print(f"오류: {e}")


if __name__ == "__main__":
    asyncio.run(main())
