"""
차트 분석 및 생성을 위한 통합 모듈
"""

import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy import stats
from scipy.signal import find_peaks

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
    
    def calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
        """지지선과 저항선을 계산합니다."""
        high_prices = df['High'].values
        low_prices = df['Low'].values
        close_prices = df['Close'].values
        
        # 피크와 밸리 찾기
        high_peaks, _ = find_peaks(high_prices, distance=window//2)
        low_peaks, _ = find_peaks(-low_prices, distance=window//2)
        
        # 저항선 계산 (최고점들)
        resistance_levels = []
        if len(high_peaks) >= 2:
            resistance_prices = high_prices[high_peaks]
            # 빈도 기반으로 주요 저항선 찾기
            for price in resistance_prices:
                count = np.sum(np.abs(resistance_prices - price) <= price * 0.02)  # 2% 범위
                if count >= 2:  # 최소 2번 이상 터치된 레벨
                    resistance_levels.append(price)
        
        # 지지선 계산 (최저점들)
        support_levels = []
        if len(low_peaks) >= 2:
            support_prices = low_prices[low_peaks]
            for price in support_prices:
                count = np.sum(np.abs(support_prices - price) <= price * 0.02)  # 2% 범위
                if count >= 2:  # 최소 2번 이상 터치된 레벨
                    support_levels.append(price)
        
        # 중복 제거 및 정렬
        resistance_levels = sorted(list(set([round(r, 2) for r in resistance_levels])), reverse=True)
        support_levels = sorted(list(set([round(s, 2) for s in support_levels])))
        
        return {
            'resistance': resistance_levels[:3],  # 상위 3개만
            'support': support_levels[-3:]  # 하위 3개만
        }
    
    def calculate_fibonacci_levels(self, df: pd.DataFrame, lookback: int = 100) -> Dict[str, float]:
        """피보나치 되돌림 레벨을 계산합니다."""
        if len(df) < lookback:
            lookback = len(df)
        
        recent_data = df.tail(lookback)
        high_price = recent_data['High'].max()
        low_price = recent_data['Low'].min()
        
        diff = high_price - low_price
        
        fibonacci_levels = {
            '0.0': high_price,
            '23.6': high_price - (diff * 0.236),
            '38.2': high_price - (diff * 0.382),
            '50.0': high_price - (diff * 0.5),
            '61.8': high_price - (diff * 0.618),
            '78.6': high_price - (diff * 0.786),
            '100.0': low_price
        }
        
        return fibonacci_levels
    
    def calculate_price_channels(self, df: pd.DataFrame, window: int = 20) -> Dict[str, pd.Series]:
        """가격 채널을 계산합니다."""
        # 선형 회귀 기반 채널
        close = df['Close']
        x = np.arange(len(close))
        
        # 채널 계산을 위한 롤링 윈도우
        upper_channel = pd.Series(index=close.index, dtype=float)
        lower_channel = pd.Series(index=close.index, dtype=float)
        middle_channel = pd.Series(index=close.index, dtype=float)
        
        for i in range(window, len(close)):
            y = close.iloc[i-window:i].values
            x_window = np.arange(window)
            
            # 선형 회귀
            slope, intercept, _, _, std_err = stats.linregress(x_window, y)
            
            # 채널 계산
            residuals = y - (slope * x_window + intercept)
            std_residuals = np.std(residuals)
            
            current_x = window - 1
            middle_value = slope * current_x + intercept
            
            middle_channel.iloc[i] = middle_value
            upper_channel.iloc[i] = middle_value + (2 * std_residuals)
            lower_channel.iloc[i] = middle_value - (2 * std_residuals)
        
        return {
            'upper': upper_channel.bfill(),
            'middle': middle_channel.bfill(),
            'lower': lower_channel.bfill()
        }
    
    def create_advanced_price_chart(self, df: pd.DataFrame, ticker: str) -> go.Figure:
        """고급 가격 차트를 생성합니다 (채널, 지지저항선, 피보나치 포함)."""
        fig = go.Figure()
        
        # 캔들스틱 차트 추가
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='가격',
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350',
                increasing_fillcolor='#26a69a',
                decreasing_fillcolor='#ef5350'
            )
        )
        
        # 가격 채널 추가
        try:
            channels = self.calculate_price_channels(df)
            
            # 상단 채널
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=channels['upper'],
                    mode='lines',
                    name='상단 채널',
                    line=dict(color='rgba(255, 152, 0, 0.8)', width=1, dash='dash'),
                    hovertemplate='상단 채널: %{y:.2f}<extra></extra>'
                )
            )
            
            # 중간 채널 (추세선)
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=channels['middle'],
                    mode='lines',
                    name='추세선',
                    line=dict(color='rgba(255, 193, 7, 0.9)', width=2),
                    hovertemplate='추세선: %{y:.2f}<extra></extra>'
                )
            )
            
            # 하단 채널
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=channels['lower'],
                    mode='lines',
                    name='하단 채널',
                    line=dict(color='rgba(255, 152, 0, 0.8)', width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(255, 193, 7, 0.1)',
                    hovertemplate='하단 채널: %{y:.2f}<extra></extra>'
                )
            )
        except Exception as e:
            print(f"채널 계산 오류: {e}")
        
        # 지지선과 저항선 추가
        try:
            support_resistance = self.calculate_support_resistance(df)
            
            # 저항선 추가
            for i, resistance in enumerate(support_resistance['resistance']):
                fig.add_hline(
                    y=resistance,
                    line=dict(color='rgba(244, 67, 54, 0.7)', width=2, dash='dot'),
                    annotation_text=f'저항선 {i+1}: {resistance:.2f}',
                    annotation_position='top right'
                )
            
            # 지지선 추가
            for i, support in enumerate(support_resistance['support']):
                fig.add_hline(
                    y=support,
                    line=dict(color='rgba(76, 175, 80, 0.7)', width=2, dash='dot'),
                    annotation_text=f'지지선 {i+1}: {support:.2f}',
                    annotation_position='bottom right'
                )
        except Exception as e:
            print(f"지지저항선 계산 오류: {e}")
        
        # 피보나치 되돌림 레벨 추가
        try:
            fib_levels = self.calculate_fibonacci_levels(df)
            
            fib_colors = {
                '23.6': 'rgba(156, 39, 176, 0.6)',
                '38.2': 'rgba(103, 58, 183, 0.6)',
                '50.0': 'rgba(63, 81, 181, 0.8)',
                '61.8': 'rgba(33, 150, 243, 0.6)',
                '78.6': 'rgba(0, 188, 212, 0.6)'
            }
            
            for level, price in fib_levels.items():
                if level in fib_colors:
                    fig.add_hline(
                        y=price,
                        line=dict(color=fib_colors[level], width=1, dash='longdash'),
                        annotation_text=f'Fib {level}%: {price:.2f}',
                        annotation_position='left'
                    )
        except Exception as e:
            print(f"피보나치 레벨 계산 오류: {e}")
        
        # 이동평균선 추가
        try:
            # 20일 이동평균
            ma20 = df['Close'].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=ma20,
                    mode='lines',
                    name='MA20',
                    line=dict(color='rgba(255, 87, 34, 0.8)', width=1),
                    hovertemplate='MA20: %{y:.2f}<extra></extra>'
                )
            )
            
            # 50일 이동평균
            if len(df) >= 50:
                ma50 = df['Close'].rolling(window=50).mean()
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=ma50,
                        mode='lines',
                        name='MA50',
                        line=dict(color='rgba(121, 85, 72, 0.8)', width=2),
                        hovertemplate='MA50: %{y:.2f}<extra></extra>'
                    )
                )
        except Exception as e:
            print(f"이동평균 계산 오류: {e}")
        
        # 레이아웃 설정
        fig.update_layout(
            title=f'{ticker} - 고급 차트 분석 (채널, 지지저항선, 피보나치)',
            yaxis_title='가격',
            xaxis_title='날짜',
            template='plotly_white',
            height=700,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            xaxis=dict(
                rangeslider=dict(visible=False),
                type='date'
            ),
            yaxis=dict(
                fixedrange=False
            )
        )
        
        # 범위 선택 버튼 추가
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=False),
                type="date"
            )
        )
        
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
                'technical': self.create_technical_analysis_chart(df, ticker, indicators),
                'advanced_price': self.create_advanced_price_chart(df, ticker)
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
