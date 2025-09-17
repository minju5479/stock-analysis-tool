"""
차트 렌더링을 위한 모듈
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List
from .styles import ChartStyles
from .formatters import ChartFormatters

class ChartRenderer:
    def __init__(self):
        self.styles = ChartStyles()
        self.formatters = ChartFormatters()
    
    def add_moving_averages(self, fig: go.Figure, df: pd.DataFrame, 
                           indicators: Dict[str, pd.Series], row: int = 1, col: int = 1):
        """이동평균선을 차트에 추가합니다."""
        ma_types = [('ma_20', 'MA20', 'orange'), 
                   ('ma_50', 'MA50', 'blue'), 
                   ('ma_200', 'MA200', 'red')]
        
        for ma_key, ma_name, color in ma_types:
            if ma_key in indicators and not indicators[ma_key].empty:
                # NaN 값 제거 및 유효성 검사
                ma_data = indicators[ma_key].dropna()
                if len(ma_data) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=ma_data.index,
                            y=ma_data,
                            mode='lines',
                            name=ma_name,
                            line=dict(color=color, width=1),
                            hoverinfo='skip'
                        ),
                        row=row, col=col
                    )
    
    def add_bollinger_bands(self, fig: go.Figure, df: pd.DataFrame, 
                           indicators: Dict[str, pd.Series], row: int = 1, col: int = 1):
        """볼린저 밴드를 차트에 추가합니다."""
        bb_keys = ['bb_upper', 'bb_middle', 'bb_lower']
        
        # 모든 BB 지표가 있고 유효한지 확인
        if all(key in indicators and not indicators[key].empty for key in bb_keys):
            try:
                # NaN 값 처리
                bb_upper = indicators['bb_upper'].dropna()
                bb_middle = indicators['bb_middle'].dropna()
                bb_lower = indicators['bb_lower'].dropna()
                
                if len(bb_upper) > 0 and len(bb_middle) > 0 and len(bb_lower) > 0:
                    # BB 하단
                    fig.add_trace(
                        go.Scatter(
                            x=bb_lower.index,
                            y=bb_lower,
                            mode='lines',
                            name='BB 하단',
                            line=dict(color='gray', width=1, dash='dash'),
                            hoverinfo='skip'
                        ),
                        row=row, col=col
                    )
                    
                    # BB 상단 (fill 적용)
                    fig.add_trace(
                        go.Scatter(
                            x=bb_upper.index,
                            y=bb_upper,
                            mode='lines',
                            name='BB 상단',
                            line=dict(color='gray', width=1, dash='dash'),
                            fill='tonexty',
                            fillcolor='rgba(128,128,128,0.1)',
                            hoverinfo='skip'
                        ),
                        row=row, col=col
                    )
                    
                    # BB 중앙선
                    fig.add_trace(
                        go.Scatter(
                            x=bb_middle.index,
                            y=bb_middle,
                            mode='lines',
                            name='BB 중앙',
                            line=dict(color='purple', width=1),
                            hoverinfo='skip'
                        ),
                        row=row, col=col
                    )
            except Exception as e:
                print(f"볼린저 밴드 추가 중 오류: {e}")
                pass
    
    def add_candlestick(self, fig: go.Figure, df: pd.DataFrame, row: int = 1, col: int = 1):
        """캔들스틱 차트를 추가합니다."""
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='가격',
                **self.styles.get_candlestick_style()
            ),
            row=row, col=col
        )
    
    def add_volume(self, fig: go.Figure, df: pd.DataFrame, row: int = 2, col: int = 1):
        """거래량 차트를 추가합니다."""
        colors = self.styles.get_volume_colors(df)
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='거래량',
                marker_color=colors,
                opacity=0.7
            ),
            row=row, col=col
        )
    
    def add_rsi(self, fig: go.Figure, df: pd.DataFrame, indicators: Dict[str, pd.Series],
                row: int = 3, col: int = 1):
        """RSI 차트를 추가합니다."""
        if 'rsi' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=indicators['rsi'],
                    mode='lines',
                    name='RSI',
                    line=dict(color=self.styles.COLORS['rsi'], width=2)
                ),
                row=row, col=col
            )
            
            # RSI 기준선
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=row, col=col)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=row, col=col)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", row=row, col=col)
    
    def add_macd(self, fig: go.Figure, df: pd.DataFrame, indicators: Dict[str, pd.Series],
                 row: int = 4, col: int = 1):
        """MACD 차트를 추가합니다."""
        if 'macd' in indicators:
            # MACD 라인
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=indicators['macd'],
                    mode='lines',
                    name='MACD',
                    line=dict(color=self.styles.COLORS['macd'], width=2)
                ),
                row=row, col=col
            )
            
            # Signal 라인
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=indicators['signal'],
                    mode='lines',
                    name='Signal',
                    line=dict(color=self.styles.COLORS['signal'], width=2)
                ),
                row=row, col=col
            )
            
            # MACD 히스토그램
            colors_hist = [
                self.styles.COLORS['histogram_up'] if h >= 0 
                else self.styles.COLORS['histogram_down']
                for h in indicators['histogram']
            ]
            
            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=indicators['histogram'],
                    name='Histogram',
                    marker_color=colors_hist,
                    opacity=0.7
                ),
                row=row, col=col
            )
    
    def update_layout(self, fig: go.Figure, ticker: str, chart_type: str = 'candlestick'):
        """차트 레이아웃을 설정합니다."""
        title = {
            'candlestick': f'{ticker} 주식 차트 분석',
            'price': f'{ticker} 가격 및 거래량',
            'technical': f'{ticker} 기술적 지표 분석'
        }.get(chart_type, f'{ticker} 차트')
        
        height = {'candlestick': 800, 'technical': 600, 'price': 500}.get(chart_type, 600)
        
        fig.update_layout(
            title=title,
            height=height,
            **self.styles.LAYOUT_DEFAULTS
        )
    
    def update_axes(self, fig: go.Figure, ticker: str, rows: int, cols: int):
        """축 레이블과 형식을 설정합니다."""
        # X축 날짜 형식 설정
        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                fig.update_xaxes(
                    tickformat='%Y.%m.%d',
                    row=i, col=j
                )
        
        # Y축 레이블 설정 (캔들스틱 차트의 경우)
        if rows == 4 and cols == 1:
            currency = self.formatters.get_currency_symbol(ticker)
            fig.update_yaxes(title_text=f"가격 ({currency})", row=1, col=1)
            fig.update_yaxes(title_text="거래량", row=2, col=1)
            fig.update_yaxes(title_text="RSI", row=3, col=1)
            fig.update_yaxes(title_text="MACD", row=4, col=1)
    
    def add_volume_bars(self, fig: go.Figure, df: pd.DataFrame, row: int = 1, col: int = 1):
        """거래량 바 차트를 추가합니다."""
        colors = [
            self.styles.COLORS['volume_up'] if close >= open else self.styles.COLORS['volume_down']
            for close, open in zip(df['Close'], df['Open'])
        ]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='거래량',
                marker_color=colors,
                opacity=0.7
            ),
            row=row, col=col
        )
    
    def add_rsi(self, fig: go.Figure, indicators: Dict[str, pd.Series], row: int = 1, col: int = 1):
        """RSI 지표를 추가합니다."""
        if 'rsi' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=indicators['rsi'].index,
                    y=indicators['rsi'],
                    mode='lines',
                    name='RSI',
                    line=dict(color='violet', width=2)
                ),
                row=row, col=col
            )
            
            # RSI 기준선
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=row, col=col)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=row, col=col)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", row=row, col=col)
    
    def add_bollinger_bands_with_price(self, fig: go.Figure, df: pd.DataFrame, 
                                     indicators: Dict[str, pd.Series], row: int = 1, col: int = 1):
        """볼린저 밴드와 가격을 함께 표시합니다."""
        if 'bb_upper' in indicators:
            # 가격 라인
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['Close'],
                    mode='lines',
                    name='가격',
                    line=dict(color='black', width=2)
                ),
                row=row, col=col
            )
            
            # 볼린저 밴드
            self.add_bollinger_bands(fig, df, indicators, row, col)
    
    def add_stochastic(self, fig: go.Figure, indicators: Dict[str, pd.Series], row: int = 1, col: int = 1):
        """스토캐스틱 지표를 추가합니다."""
        if 'k_percent' in indicators:
            fig.add_trace(
                go.Scatter(
                    x=indicators['k_percent'].index,
                    y=indicators['k_percent'],
                    mode='lines',
                    name='%K',
                    line=dict(color='blue', width=2)
                ),
                row=row, col=col
            )
            
            fig.add_trace(
                go.Scatter(
                    x=indicators['d_percent'].index,
                    y=indicators['d_percent'],
                    mode='lines',
                    name='%D',
                    line=dict(color='red', width=2)
                ),
                row=row, col=col
            )
            
            fig.add_hline(y=80, line_dash="dash", line_color="red", row=row, col=col)
            fig.add_hline(y=20, line_dash="dash", line_color="green", row=row, col=col)
