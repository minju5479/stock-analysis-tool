"""
차트 스타일링을 위한 모듈
"""

from typing import Dict, Any

class ChartStyles:
    # 차트 색상
    COLORS = {
        'up': '#618fc4',      # 상승
        'down': '#ef5350',    # 하락
        'volume_up': '#618fc4',
        'volume_down': '#ef5350',
        'ma20': 'orange',
        'ma50': 'blue',
        'ma200': 'red',
        'bb': 'gray',
        'rsi': 'violet',
        'macd': 'blue',
        'signal': 'red',
        'histogram_up': '#26a69a',
        'histogram_down': '#ef5350'
    }
    
    # 차트 기본 설정
    LAYOUT_DEFAULTS = {
        'template': 'plotly_white',
        'hovermode': 'x unified',
        'showlegend': True,
        'xaxis_rangeslider_visible': False
    }
    
    # 라인 스타일
    LINE_STYLES = {
        'ma': dict(width=1),
        'bb': dict(width=1, dash='dash'),
        'indicator': dict(width=2)
    }
    
    @staticmethod
    def get_candlestick_style() -> Dict[str, Any]:
        """캔들스틱 차트 스타일을 반환합니다."""
        return {
            'increasing_line_color': ChartStyles.COLORS['up'],
            'decreasing_line_color': ChartStyles.COLORS['down']
        }
    
    @staticmethod
    def get_volume_colors(df):
        """거래량 바 차트의 색상을 반환합니다."""
        return [
            ChartStyles.COLORS['volume_up'] if close >= open else ChartStyles.COLORS['volume_down']
            for close, open in zip(df['Close'], df['Open'])
        ]
    
    @staticmethod
    def get_subplot_layout(chart_type: str) -> Dict[str, Any]:
        """차트 타입에 따른 서브플롯 레이아웃을 반환합니다."""
        layouts = {
            'candlestick': {
                'rows': 4,
                'cols': 1,
                'shared_xaxes': True,
                'vertical_spacing': 0.05,
                'subplot_titles': ('가격 차트', '거래량', 'RSI', 'MACD'),
                'row_heights': [0.5, 0.15, 0.15, 0.2]
            },
            'technical': {
                'rows': 2,
                'cols': 2,
                'subplot_titles': ('RSI', 'MACD', '볼린저 밴드', '스토캐스틱'),
                'specs': [[{"secondary_y": False}, {"secondary_y": False}],
                         [{"secondary_y": False}, {"secondary_y": False}]]
            }
        }
        return layouts.get(chart_type, {})
    
    def apply_chart_layout(self, fig, ticker: str, chart_type: str = 'candlestick'):
        """차트에 레이아웃과 스타일을 적용합니다."""
        titles = {
            'candlestick': f'{ticker} 주식 차트 분석',
            'price': f'{ticker} 가격 및 거래량',
            'technical': f'{ticker} 기술적 지표 분석'
        }
        
        heights = {
            'candlestick': 800,
            'technical': 600,
            'price': 500
        }
        
        # 가격 차트의 경우 특별 설정
        if chart_type == 'price':
            currency_symbol = "￦" if ticker.endswith('.KS') else "$"
            fig.update_layout(
                title=titles.get(chart_type, f'{ticker} 차트'),
                xaxis_title='날짜',
                yaxis_title=f'가격 ({currency_symbol})',
                yaxis2=dict(
                    title='거래량',
                    overlaying='y',
                    side='right'
                ),
                height=heights.get(chart_type, 600),
                xaxis=dict(tickformat='%Y.%m.%d'),
                **self.LAYOUT_DEFAULTS
            )
        else:
            fig.update_layout(
                title=titles.get(chart_type, f'{ticker} 차트'),
                height=heights.get(chart_type, 600),
                **self.LAYOUT_DEFAULTS
            )
            
            # X축 날짜 형식 설정
            if chart_type == 'candlestick':
                for i in range(1, 5):
                    fig.update_xaxes(tickformat='%Y.%m.%d', row=i, col=1)
                    
                # Y축 레이블
                currency_symbol = "￦" if ticker.endswith('.KS') else "$"
                fig.update_yaxes(title_text=f"가격 ({currency_symbol})", row=1, col=1)
                fig.update_yaxes(title_text="거래량", row=2, col=1)
                fig.update_yaxes(title_text="RSI", row=3, col=1)
                fig.update_yaxes(title_text="MACD", row=4, col=1)
            elif chart_type == 'technical':
                for i in range(1, 3):
                    for j in range(1, 3):
                        fig.update_xaxes(tickformat='%Y.%m.%d', row=i, col=j)
        
        return fig
