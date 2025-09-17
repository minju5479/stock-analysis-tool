"""
차트 데이터 포맷팅을 위한 모듈
"""

import plotly.graph_objects as go
from typing import Dict

class ChartFormatters:
    @staticmethod
    def get_korean_weekday(weekday_num: str) -> str:
        """날짜 문자열에서 한글 요일을 반환합니다."""
        weekday_map = {
            '0': '월', '1': '화', '2': '수', '3': '목', 
            '4': '금', '5': '토', '6': '일'
        }
        return weekday_map.get(str(weekday_num), '')
    
    @staticmethod
    def format_price_hover(date_str: str, weekday: str, open_price: float, 
                          high: float, low: float, close: float) -> str:
        """가격 데이터의 hover 텍스트를 포맷팅합니다."""
        return (
            f"{date_str}({ChartFormatters.get_korean_weekday(weekday)})<br>"
            f"시가: {open_price:.2f}<br>"
            f"고가: {high:.2f}<br>"
            f"저가: {low:.2f}<br>"
            f"종가: {close:.2f}"
        )
    
    @staticmethod
    def format_volume_hover(date_str: str, weekday: str, volume: int) -> str:
        """거래량 데이터의 hover 텍스트를 포맷팅합니다."""
        return f"{date_str}({ChartFormatters.get_korean_weekday(weekday)})<br>거래량: {int(volume):,}"
    
    @staticmethod
    def format_indicator_hover(date_str: str, weekday: str, 
                             indicator_name: str, value: float) -> str:
        """지표 데이터의 hover 텍스트를 포맷팅합니다."""
        return f"{date_str}({ChartFormatters.get_korean_weekday(weekday)})<br>{indicator_name}: {value:.2f}"
    
    @staticmethod
    def get_currency_symbol(ticker: str) -> str:
        """티커에 따른 통화 기호를 반환합니다."""
        return "￦" if ticker.endswith('.KS') else "$"
    
    def add_korean_weekday_hover(self, fig: go.Figure) -> go.Figure:
        """차트의 모든 trace에 한글 요일 hover 텍스트를 추가합니다."""
        for trace in fig.data:
            if hasattr(trace, 'x') and trace.x is not None:
                if isinstance(trace, go.Candlestick):
                    # 캔들스틱의 경우 hover 텍스트 설정
                    hover_texts = []
                    for x, o, h, l, c in zip(trace.x, trace.open, trace.high, trace.low, trace.close):
                        weekday = x.strftime('%w')
                        date_str = x.strftime('%Y.%m.%d')
                        hover_text = self.format_price_hover(date_str, weekday, o, h, l, c)
                        hover_texts.append(hover_text)
                    trace.text = hover_texts
                    trace.hoverinfo = 'text'
                elif isinstance(trace, go.Bar):
                    # 거래량 바 차트의 경우
                    hover_texts = []
                    for x, v in zip(trace.x, trace.y):
                        weekday = x.strftime('%w')
                        date_str = x.strftime('%Y.%m.%d')
                        hover_text = self.format_volume_hover(date_str, weekday, v)
                        hover_texts.append(hover_text)
                    trace.text = hover_texts
                    trace.hoverinfo = 'text'
                elif isinstance(trace, go.Scatter) and trace.name in ['RSI', 'MACD', 'Signal']:
                    # RSI와 MACD의 경우
                    hover_texts = []
                    for x, y in zip(trace.x, trace.y):
                        weekday = x.strftime('%w')
                        date_str = x.strftime('%Y.%m.%d')
                        hover_text = self.format_indicator_hover(date_str, weekday, trace.name, y)
                        hover_texts.append(hover_text)
                    trace.text = hover_texts
                    trace.hoverinfo = 'text'
                else:
                    # 나머지 요소들은 hover 정보 숨김
                    trace.hoverinfo = 'skip'
        return fig
