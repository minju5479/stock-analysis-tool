#!/usr/bin/env python3
"""
주식 분석 웹 인터페이스
Streamlit을 사용한 사용자 친화적인 웹 인터페이스
"""

import streamlit as st
import asyncio
import json
import pandas as pd
import sys
import os
import importlib
import yfinance as yf

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 모듈 캐시 클리어 (개발 중 모듈 변경사항 반영을 위해)
if 'src.core.backtest.engine' in sys.modules:
    importlib.reload(sys.modules['src.core.backtest.engine'])
if 'src.core.backtest.metrics' in sys.modules:
    importlib.reload(sys.modules['src.core.backtest.metrics'])
if 'src.core.analysis.strategy_recommender' in sys.modules:
    importlib.reload(sys.modules['src.core.analysis.strategy_recommender'])

from src.core.analysis.stock_analyzer import StockAnalyzer
from src.core.analysis.stock_screener import UndervaluedStockScreener
from src.core.analysis.strategy_recommender import recommendation_engine
from src.core.chart.analyzer import ChartAnalyzer
from src.core.data import StockDataFetcher, DataProcessor
from src.core.strategy.rule_based import RuleBasedStrategy
from src.core.strategy.momentum import MomentumStrategy
from src.core.strategy.mean_reversion import MeanReversionStrategy
from src.core.strategy.pattern import PatternStrategy
from src.core.backtest.engine import BacktestEngine
from src.core.backtest.metrics import compute_metrics

# 페이지 설정
st.set_page_config(
    page_title="주식 분석 도구",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 페이지 모드 설정
if 'page_mode' not in st.session_state:
    st.session_state.page_mode = "전체분석"

# 커스텀 버튼 스타일 추가
st.markdown("""
<style>
/* 커스텀 액션 버튼 스타일 */

.stButton > button[data-testid="baseButton-secondary"] {
    background: linear-gradient(90deg, #232526 0%, #414345 50%, #232526 100%) !important;
    color: #f5f5f5 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(35, 37, 38, 0.3) !important;
    transition: all 0.3s ease !important;
}


.stButton > button[data-testid="baseButton-secondary"]:hover {
    background: linear-gradient(90deg, #1a1a1a 0%, #232526 50%, #414345 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(35, 37, 38, 0.4) !important;
}

/* 주요 액션 버튼을 위한 특별 클래스 */

div[data-testid="stButton"] button[kind="secondary"] {
    background: linear-gradient(135deg, #232526 0%, #414345 50%, #232526 100%) !important;
    color: #f5f5f5 !important;
    border: none !important;
    padding: 0.75rem 1.5rem !important;
    font-size: 16px !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(35, 37, 38, 0.4) !important;
}
</style>
""", unsafe_allow_html=True)

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .positive-change {
        color: #28a745;
    }
    .negative-change {
        color: #dc3545;
    }
    .neutral-change {
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def get_popular_stocks():
    """섹터별 인기 주식 목록을 반환합니다."""
    return {
        "🇺🇸 미국 - 기술주": {
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft Corporation", 
            "GOOGL": "Alphabet Inc.",
            "META": "Meta Platforms Inc.",
            "NVDA": "NVIDIA Corporation",
            "TSLA": "Tesla Inc.",
            "NFLX": "Netflix Inc.",
            "AMD": "Advanced Micro Devices Inc.",
            "ORCL": "Oracle Corporation",
            "CRM": "Salesforce Inc."
        },
        "🇺🇸 미국 - 소비재": {
            "AMZN": "Amazon.com Inc.",
            "WMT": "Walmart Inc.",
            "HD": "Home Depot Inc.",
            "MCD": "McDonald's Corporation",
            "NKE": "Nike Inc.",
            "SBUX": "Starbucks Corporation",
            "TGT": "Target Corporation",
            "LOW": "Lowe's Companies Inc.",
            "KO": "Coca-Cola Company",
            "PEP": "PepsiCo Inc."
        },
        "🇺🇸 미국 - 금융": {
            "JPM": "JPMorgan Chase & Co.",
            "BAC": "Bank of America Corp",
            "WFC": "Wells Fargo & Company",
            "GS": "Goldman Sachs Group Inc.",
            "MS": "Morgan Stanley",
            "C": "Citigroup Inc.",
            "USB": "U.S. Bancorp",
            "PNC": "PNC Financial Services",
            "BLK": "BlackRock Inc.",
            "AXP": "American Express Company"
        },
        "🇺🇸 미국 - 헬스케어": {
            "JNJ": "Johnson & Johnson",
            "UNH": "UnitedHealth Group Inc.",
            "PFE": "Pfizer Inc.",
            "ABT": "Abbott Laboratories",
            "MRK": "Merck & Co. Inc.",
            "TMO": "Thermo Fisher Scientific",
            "DHR": "Danaher Corporation",
            "BMY": "Bristol Myers Squibb",
            "ABBV": "AbbVie Inc.",
            "LLY": "Eli Lilly and Company"
        },
        "🇺🇸 미국 - 산업재": {
            "BA": "Boeing Company",
            "CAT": "Caterpillar Inc.",
            "GE": "General Electric Company",
            "MMM": "3M Company",
            "HON": "Honeywell International",
            "UPS": "United Parcel Service",
            "RTX": "Raytheon Technologies",
            "LMT": "Lockheed Martin Corp",
            "DE": "Deere & Company",
            "UNP": "Union Pacific Corporation"
        },
        "🇰🇷 한국 - 대형주": {
            "005930.KS": "삼성전자",
            "000660.KS": "SK하이닉스",
            "035420.KS": "NAVER",
            "005380.KS": "현대차",
            "051910.KS": "LG화학",
            "035720.KS": "카카오",
            "006400.KS": "삼성SDI",
            "207940.KS": "삼성바이오로직스",
            "068270.KS": "셀트리온",
            "373220.KS": "LG에너지솔루션"
        },
        "🇰🇷 한국 - 금융": {
            "323410.KS": "카카오뱅크",
            "086790.KS": "하나금융지주",
            "105560.KS": "KB금융",
            "316140.KS": "우리금융지주",
            "138040.KS": "메리츠금융지주",
            "024110.KS": "기업은행",
            "055550.KS": "신한지주",
            "000810.KS": "삼성화재",
            "003540.KS": "대신증권",
            "029780.KS": "삼성카드"
        },
        "🇰🇷 한국 - 화학/소재": {
            "051910.KS": "LG화학",
            "096770.KS": "SK이노베이션",
            "010950.KS": "S-Oil",
            "011170.KS": "롯데케미칼",
            "001570.KS": "금양",
            "002380.KS": "KCC",
            "014680.KS": "한솔케미칼",
            "000120.KS": "CJ대한통운",
            "180640.KS": "한진칼",
            "003230.KS": "삼양식품"
        },
        "🇰🇷 한국 - 바이오/제약": {
            "207940.KS": "삼성바이오로직스",
            "068270.KS": "셀트리온",
            "196170.KS": "알테오젠",
            "302440.KS": "SK바이오사이언스",
            "145020.KS": "휴젤",
            "326030.KS": "SK바이오팜",
            "028300.KS": "HLB",
            "000100.KS": "유한양행",
            "009420.KS": "한올바이오파마",
            "185750.KS": "종근당"
        }
    }

@st.cache_data(ttl=300)  # 5분 캐시
def get_trending_stocks():
    """소셜 미디어에서 트렌딩 중인 주식 목록을 반환합니다."""
    return {
        "🔥 실시간 급상승": {
            "TSLA": {"name": "Tesla Inc.", "mentions": 15420, "sentiment": "긍정", "change": "+8.5%", "reason": "자율주행 기술 발표"},
            "GME": {"name": "GameStop Corp.", "mentions": 12850, "sentiment": "긍정", "change": "+15.2%", "reason": "NFT 플랫폼 확장"},
            "AMC": {"name": "AMC Entertainment", "mentions": 11200, "sentiment": "혼재", "change": "+5.8%", "reason": "영화 산업 회복"},
            "NVDA": {"name": "NVIDIA Corporation", "mentions": 9800, "sentiment": "긍정", "change": "+4.2%", "reason": "AI 반도체 수요 증가"},
            "AAPL": {"name": "Apple Inc.", "mentions": 8900, "sentiment": "긍정", "change": "+2.1%", "reason": "새로운 iPhone 출시"},
        },
        "💬 X(Twitter) 인기": {
            "DOGE": {"name": "Dogecoin", "mentions": 18500, "sentiment": "긍정", "change": "+12.8%", "reason": "일론 머스크 언급"},
            "BTC": {"name": "Bitcoin", "mentions": 16200, "sentiment": "긍정", "change": "+6.4%", "reason": "기관 투자 유입"},
            "META": {"name": "Meta Platforms", "mentions": 7300, "sentiment": "혼재", "change": "-1.2%", "reason": "메타버스 투자 확대"},
            "COIN": {"name": "Coinbase Global", "mentions": 6800, "sentiment": "긍정", "change": "+9.1%", "reason": "암호화폐 거래량 증가"},
            "PLTR": {"name": "Palantir Technologies", "mentions": 5600, "sentiment": "긍정", "change": "+7.3%", "reason": "정부 계약 체결"},
        },
        "📸 인스타그램/틱톡": {
            "NKE": {"name": "Nike Inc.", "mentions": 9200, "sentiment": "긍정", "change": "+3.4%", "reason": "인플루언서 마케팅 확대"},
            "LULU": {"name": "Lululemon Athletica", "mentions": 7800, "sentiment": "긍정", "change": "+5.7%", "reason": "애슬레저 트렌드"},
            "SBUX": {"name": "Starbucks Corporation", "mentions": 6900, "sentiment": "긍정", "change": "+2.9%", "reason": "신제품 출시"},
            "DIS": {"name": "Walt Disney Company", "mentions": 6200, "sentiment": "긍정", "change": "+4.1%", "reason": "스트리밍 서비스 성장"},
            "NFLX": {"name": "Netflix Inc.", "mentions": 5800, "sentiment": "긍정", "change": "+3.8%", "reason": "오리지널 콘텐츠 화제"},
        },
        "📊 Reddit/Discord": {
            "BB": {"name": "BlackBerry Limited", "mentions": 8400, "sentiment": "긍정", "change": "+11.2%", "reason": "보안 소프트웨어 관심"},
            "NOK": {"name": "Nokia Corporation", "mentions": 7600, "sentiment": "긍정", "change": "+6.8%", "reason": "5G 인프라 투자"},
            "WISH": {"name": "ContextLogic Inc.", "mentions": 6500, "sentiment": "혼재", "change": "-2.1%", "reason": "e-commerce 경쟁 심화"},
            "CLOV": {"name": "Clover Health", "mentions": 5200, "sentiment": "긍정", "change": "+8.9%", "reason": "헬스케어 AI 기술"},
            "SPCE": {"name": "Virgin Galactic", "mentions": 4800, "sentiment": "긍정", "change": "+13.4%", "reason": "우주 관광 사업 확대"},
        },
        "🇰🇷 한국 SNS 화제": {
            "005930.KS": {"name": "삼성전자", "mentions": 12400, "sentiment": "긍정", "change": "+2.8%", "reason": "반도체 수요 회복"},
            "035420.KS": {"name": "NAVER", "mentions": 8900, "sentiment": "긍정", "change": "+4.5%", "reason": "AI 서비스 확장"},
            "035720.KS": {"name": "카카오", "mentions": 7600, "sentiment": "혼재", "change": "-1.3%", "reason": "규제 이슈"},
            "373220.KS": {"name": "LG에너지솔루션", "mentions": 6200, "sentiment": "긍정", "change": "+6.7%", "reason": "전기차 배터리 수주"},
            "323410.KS": {"name": "카카오뱅크", "mentions": 5800, "sentiment": "긍정", "change": "+3.2%", "reason": "디지털 금융 성장"},
        }
    }

async def analyze_stock_async(ticker, period):
    """비동기로 주식 분석을 수행합니다."""
    analyzer = StockAnalyzer()
    return await analyzer.analyze_stock(ticker, period)

async def get_stock_price_async(ticker):
    """비동기로 주식 가격을 조회합니다."""
    analyzer = StockAnalyzer()
    return await analyzer.get_stock_price(ticker)

async def generate_charts_async(ticker, period):
    """비동기로 차트를 생성합니다."""
    chart_analyzer = ChartAnalyzer()
    return await chart_analyzer.generate_charts(ticker, period)

async def get_processed_df_async(ticker: str, period: str) -> pd.DataFrame:
    """비동기로 가격 데이터 조회 후 가공합니다."""
    fetcher = StockDataFetcher()
    processor = DataProcessor()
    hist = await fetcher.get_stock_data(ticker, period)
    return processor.process_stock_data(hist)

def get_currency_symbol(ticker):
    """티커에 따라 통화 기호를 반환합니다."""
    if ticker.endswith('.KS'):  # 한국 주식
        return '￦'
    else:  # 해외 주식 (기본값)
        return '$'

def format_price(price, ticker):
    """가격을 통화 기호와 함께 포맷합니다."""
    currency_symbol = get_currency_symbol(ticker)
    return f"{currency_symbol}{price:,.2f}"

def display_basic_info(basic_info, ticker):
    """기본 정보를 표시합니다."""
    # 1행: 가격/변화율, 시총, P/E, 통화
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        delta = basic_info.get('price_change_percentage', 0.0)
        st.metric(
            "현재가",
            format_price(basic_info['current_price'], ticker),
            f"{delta:+.2f}%"
        )

    with c2:
        mcap = basic_info.get('market_cap', 'N/A')
        mcap_fmt = format_large_number(mcap) if mcap != 'N/A' else 'N/A'
        st.metric("시가총액", mcap_fmt)

    with c3:
        pe = basic_info.get('pe_ratio', 'N/A')
        st.metric("P/E 비율", f"{pe:.2f}" if isinstance(pe, (int, float)) else "N/A")

    with c4:
        currency = basic_info.get('currency', 'USD') if 'currency' in basic_info else 'USD'
        st.metric("통화", currency)

    # 2행: 회사명, 섹터, 산업, 전일 종가
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        st.metric("회사명", basic_info.get('company_name', 'N/A'))
    with c6:
        st.metric("섹터", basic_info.get('sector', 'N/A'))
    with c7:
        st.metric("산업", basic_info.get('industry', 'N/A'))
    with c8:
        prev = basic_info.get('previous_price', 'N/A') or basic_info.get('previous_close', 'N/A')
        st.metric("전일 종가", format_price(prev, ticker) if isinstance(prev, (int, float)) else 'N/A')

def display_technical_indicators(tech_indicators, ticker):
    """기술적 지표를 표시합니다."""
    st.subheader("📊 기술적 지표")

    tab_sum, tab_det = st.tabs(["요약", "상세"])

    with tab_sum:
        # 핵심 요약 지표 4개
        s1, s2, s3, s4 = st.columns(4)
        # RSI
        if 'rsi' in tech_indicators:
            rsi = tech_indicators['rsi']
            with s1:
                st.metric("RSI", f"{rsi['current']:.2f}", rsi['interpretation'])
        # MACD
        if 'macd' in tech_indicators:
            macd = tech_indicators['macd']
            with s2:
                st.metric("MACD", f"{macd['macd_line']:.2f}", macd['interpretation'])
        # 이동평균 추세(50 vs 200)
        if 'moving_averages' in tech_indicators:
            ma = tech_indicators['moving_averages']
            ma_trend = "골든 크로스" if ma['ma_50'] > ma['ma_200'] else "데드 크로스"
            with s3:
                st.metric("이동평균 추세", ma_trend, f"50일: {format_price(ma['ma_50'], ticker)} / 200일: {format_price(ma['ma_200'], ticker)}")
        # OBV 추세
        if 'obv' in tech_indicators:
            obv = tech_indicators['obv']
            with s4:
                st.metric("OBV", obv['trend'], obv['interpretation'])

    with tab_det:
        col1, col2, col3 = st.columns(3)

        with col1:
            if 'moving_averages' in tech_indicators:
                ma = tech_indicators['moving_averages']
                st.write("**이동평균선**")
                st.write(f"20일: {format_price(ma['ma_20'], ticker)}")
                st.write(f"50일: {format_price(ma['ma_50'], ticker)}")
                st.write(f"200일: {format_price(ma['ma_200'], ticker)}")
            if 'roc' in tech_indicators:
                roc = tech_indicators['roc']
                st.metric("ROC (모멘텀)", f"{roc['current']:.2f}%", roc['interpretation'])
            if 'williams_r' in tech_indicators:
                wr = tech_indicators['williams_r']
                st.metric("Williams %R", f"{wr['current']:.2f}", wr['interpretation'])

        with col2:
            if 'macd' in tech_indicators:
                macd = tech_indicators['macd']
                st.write("**MACD**")
                st.write(f"MACD: {macd['macd_line']:.2f}")
                st.write(f"Signal: {macd['signal_line']:.2f}")
                st.write(f"Histogram: {macd['histogram']:.2f}")
                st.write(f"해석: {macd['interpretation']}")
            if 'mfi' in tech_indicators:
                mfi = tech_indicators['mfi']
                st.metric("MFI (자금흐름)", f"{mfi['current']:.2f}", mfi['interpretation'])

        with col3:
            if 'bollinger_bands' in tech_indicators:
                bb = tech_indicators['bollinger_bands']
                st.write("**볼린저 밴드**")
                st.write(f"상단: {format_price(bb['upper'], ticker)}")
                st.write(f"중간: {format_price(bb['middle'], ticker)}")
                st.write(f"하단: {format_price(bb['lower'], ticker)}")
            if 'obv' in tech_indicators:
                obv = tech_indicators['obv']
                st.write("**OBV (거래량 동향)**")
                st.write(f"추세: {obv['trend']}")
                st.write(f"해석: {obv['interpretation']}")

def display_earnings_analysis(earnings_analysis, ticker):
    """어닝콜 및 가이던스 분석 결과를 표시합니다."""
    st.subheader("📈 어닝콜 & 가이던스 분석")
    
    if "error" in earnings_analysis:
        st.warning(f"어닝 데이터 조회 실패: {earnings_analysis['error']}")
        return
    
    # 애널리스트 추천 및 목표가
    guidance = earnings_analysis.get('guidance', {})
    if guidance and 'error' not in guidance:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rec_text = guidance.get('recommendation_text', 'N/A')
            rec_mean = guidance.get('recommendation_mean', 'N/A')
            if rec_mean != 'N/A':
                st.metric("애널리스트 추천", rec_text, f"점수: {rec_mean:.2f}/5")
            else:
                st.metric("애널리스트 추천", rec_text)
        
        with col2:
            target_price = guidance.get('analyst_target_price', 'N/A')
            if target_price != 'N/A':
                st.metric("목표 주가", format_price(target_price, ticker))
            else:
                st.metric("목표 주가", "N/A")
        
        with col3:
            analyst_count = guidance.get('number_of_analyst_opinions', 'N/A')
            st.metric("분석가 수", f"{analyst_count}명" if analyst_count != 'N/A' else 'N/A')
    
    # 어닝 추정치
    estimates = earnings_analysis.get('analyst_estimates', {})
    if estimates and 'error' not in estimates:
        st.write("**📊 애널리스트 추정치**")

        labels = [
            ("현재 분기", "current_quarter"),
            ("다음 분기", "next_quarter"),
            ("현재 연도", "current_year"),
            ("다음 연도", "next_year"),
        ]
        table = []
        for title, key in labels:
            row = estimates.get(key, {})
            eps = row.get('eps_estimate', 'N/A')
            rev = row.get('revenue_estimate', 'N/A')
            table.append({
                "구분": title,
                "EPS 추정치": f"${eps:.2f}" if isinstance(eps, (int, float)) else "N/A",
                "매출 추정치": format_large_number(rev) if isinstance(rev, (int, float)) else "N/A",
            })
        st.dataframe(pd.DataFrame(table), width="stretch")
    
    # 최근 어닝 이력
    earnings_history = earnings_analysis.get('earnings_history', [])
    if earnings_history and not any('error' in item for item in earnings_history):
        st.write("**📅 최근 어닝 발표 이력**")
        
        # 테이블로 표시
        history_data = []
        for item in earnings_history[:4]:  # 최근 4분기
            history_data.append({
                "분기": item.get('quarter', 'N/A'),
                "발표일": item.get('date', 'N/A'),
                "매출": format_large_number(item.get('revenue', 'N/A')) if item.get('revenue', 'N/A') != 'N/A' else 'N/A',
                "순이익": format_large_number(item.get('earnings', 'N/A')) if item.get('earnings', 'N/A') != 'N/A' else 'N/A',
                "EPS": f"${item.get('eps', 'N/A')}" if item.get('eps', 'N/A') != 'N/A' else 'N/A'
            })
        
        if history_data:
            df_history = pd.DataFrame(history_data)
            st.dataframe(df_history, width="stretch")
    
    # 어닝 캘린더
    calendar = earnings_analysis.get('earnings_calendar', {})
    if calendar and 'error' not in calendar:
        upcoming = calendar.get('upcoming_earnings', [])
        if upcoming:
            st.write("**📅 예정된 어닝 발표**")
            for earning in upcoming[:2]:  # 최근 2개만 표시
                date = earning.get('date', 'N/A')
                eps_est = earning.get('eps_estimate', 'N/A')
                st.info(f"발표 예정일: {date} | EPS 추정치: ${eps_est}" if eps_est != 'N/A' else f"발표 예정일: {date}")
    
    # 요약
    summary = earnings_analysis.get('summary', '')
    if summary and 'error' not in summary:
        st.info(f"💡 **어닝 분석 요약**: {summary}")

def display_strategy_signal(ticker: str, period: str):
    """전략 매수/매도 신호를 표시합니다."""
    st.subheader("🧭 매수/매도 가이드")
    try:
        df = asyncio.run(get_processed_df_async(ticker, period))
        if df is None or df.empty or len(df) < 2:
            st.info("신호를 생성하기에 데이터가 충분하지 않습니다. 기간을 늘려주세요 (예: 1y).")
            return

        # 선택된 전략 파라미터 가져오기
        sp = st.session_state.get("strategy_params", {})
        selected_strategy = sp.get("selected_strategy", {"class": "RuleBasedStrategy", "name": "rule_based", "desc": "MA/RSI/MACD 조합"})
        
        # 전략 인스턴스 생성 및 파라미터 준비
        if selected_strategy["name"] == "rule_based":
            strategy = RuleBasedStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "rsi_buy": sp.get("rsi_buy", 30),
                "rsi_sell": sp.get("rsi_sell", 70),
                "risk_rr": sp.get("risk_rr", 2.0),
            }
        elif selected_strategy["name"] == "momentum":
            strategy = MomentumStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "momentum_period": sp.get("momentum_period", 20),
                "breakout_threshold": sp.get("breakout_threshold", 0.02),
                "volume_sma": sp.get("volume_sma", 10)
            }
        elif selected_strategy["name"] == "mean_reversion":
            strategy = MeanReversionStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "bb_period": sp.get("bb_period", 20),
                "bb_std": sp.get("bb_std", 2.0),
                "rsi_oversold": sp.get("rsi_oversold", 25),
                "rsi_overbought": sp.get("rsi_overbought", 75)
            }
        elif selected_strategy["name"] == "pattern":
            strategy = PatternStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "pattern_window": sp.get("pattern_window", 10),
                "support_resistance_window": sp.get("support_resistance_window", 20),
                "breakout_threshold": sp.get("breakout_threshold", 0.01)
            }
        else:
            # 기본값으로 RuleBasedStrategy 사용
            strategy = RuleBasedStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "rsi_buy": sp.get("rsi_buy", 30),
                "rsi_sell": sp.get("rsi_sell", 70),
                "risk_rr": sp.get("risk_rr", 2.0),
            }
        
        signals = strategy.compute_signals(df, params=params)

        if signals is None or len(signals) == 0:
            st.info(f"{selected_strategy['desc']} 전략에서 생성된 시그널이 없습니다. 기간을 늘리거나 파라미터를 조정하세요.")
            return

        latest = signals.iloc[-1]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("액션", latest["action"])
        with c2:
            st.metric("신뢰도", f"{float(latest['confidence'])*100:.0f}%")
        with c3:
            stop = latest.get("stop")
            st.metric("스탑", format_price(stop, ticker) if pd.notna(stop) else "-")
        with c4:
            target = latest.get("target")
            st.metric("타겟", format_price(target, ticker) if pd.notna(target) else "-")
        st.caption(f"근거: {latest['reason']}")
        
        # 전략 타입 표시
        st.info(f"사용된 전략: **{selected_strategy['desc']}**")
        
    except Exception as e:
        st.warning(f"전략 신호 계산 중 오류: {e}")

def display_backtest_section(ticker: str, period: str):
    """전략 백테스트 결과를 표시합니다."""
    try:
        st.subheader("🧪 전략 백테스트")
        df = asyncio.run(get_processed_df_async(ticker, period))
        if df is None or df.empty or len(df) < 2:
            st.info("백테스트를 수행하기에 데이터가 충분하지 않습니다. 기간을 늘려주세요 (예: 1y).")
            return

        # 선택된 전략 파라미터 가져오기
        sp = st.session_state.get("strategy_params", {})
        selected_strategy = sp.get("selected_strategy", {"class": "RuleBasedStrategy", "name": "rule_based", "desc": "MA/RSI/MACD 조합"})
        
        # 전략 인스턴스 생성
        if selected_strategy["name"] == "rule_based":
            strategy = RuleBasedStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "rsi_buy": sp.get("rsi_buy", 30),
                "rsi_sell": sp.get("rsi_sell", 70),
                "risk_rr": sp.get("risk_rr", 2.0),
            }
        elif selected_strategy["name"] == "momentum":
            strategy = MomentumStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "momentum_period": sp.get("momentum_period", 20),
                "breakout_threshold": sp.get("breakout_threshold", 0.02),
                "volume_sma": sp.get("volume_sma", 10)
            }
        elif selected_strategy["name"] == "mean_reversion":
            strategy = MeanReversionStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "bb_period": sp.get("bb_period", 20),
                "bb_std": sp.get("bb_std", 2.0),
                "rsi_oversold": sp.get("rsi_oversold", 25),
                "rsi_overbought": sp.get("rsi_overbought", 75)
            }
        elif selected_strategy["name"] == "pattern":
            strategy = PatternStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "pattern_window": sp.get("pattern_window", 10),
                "support_resistance_window": sp.get("support_resistance_window", 20),
                "breakout_threshold": sp.get("breakout_threshold", 0.01)
            }
        else:
            # 기본값으로 RuleBasedStrategy 사용
            strategy = RuleBasedStrategy()
            params = {
                "warmup": max(0, min(sp.get("warmup", 50), max(0, len(df) - 2))),
                "rsi_buy": sp.get("rsi_buy", 30),
                "rsi_sell": sp.get("rsi_sell", 70),
                "risk_rr": sp.get("risk_rr", 2.0),
            }
        
        signals = strategy.compute_signals(df, params=params)
        if signals is None or len(signals) == 0:
            st.info(f"{selected_strategy['desc']} 전략에서 생성된 시그널이 없어 백테스트를 표시할 수 없습니다. 기간을 늘리거나 파라미터를 조정하세요.")
            return

        engine = BacktestEngine()
        trades, equity = engine.run(
            df,
            signals,
            fee_bps=float(sp.get("fee_bps", 10.0)),
            slippage_bps=float(sp.get("slippage_bps", 10.0)),
        )

        if equity is None or equity.empty:
            st.info("백테스트 결과가 비어 있습니다. 더 긴 기간으로 다시 시도하세요.")
            return
        metrics = compute_metrics(equity)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("CAGR", f"{metrics['CAGR']*100:.2f}%")
        with m2:
            st.metric("Volatility", f"{metrics['Volatility']*100:.2f}%")
        with m3:
            st.metric("Sharpe", f"{metrics['Sharpe']:.2f}")
        with m4:
            st.metric("Max DD", f"{metrics['MaxDrawdown']*100:.2f}%")

        st.line_chart(equity.rename(columns={"equity": f"{ticker} Equity"}))

        with st.expander("체결 내역 보기"):
            if not trades.empty:
                st.dataframe(trades.tail(20), width="stretch")
            else:
                st.write("체결 내역 없음")
    except Exception as e:
        st.warning(f"백테스트 실행 중 오류: {e}")

def format_large_number(value):
    """큰 숫자를 읽기 쉽게 포맷팅합니다."""
    if value == 'N/A' or not isinstance(value, (int, float)):
        return "N/A"
    
    if value >= 1e12:
        return f"${value/1e12:.1f}T"
    elif value >= 1e9:
        return f"${value/1e9:.1f}B"
    elif value >= 1e6:
        return f"${value/1e6:.1f}M"
    else:
        return f"${value:,.0f}"

def display_financial_analysis(financial_analysis):
    """재무제표 분석 결과를 표시합니다."""
    st.subheader("📊 재무제표 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 수익성 지표
        st.write("**수익성 지표**")
        profitability = financial_analysis["profitability"]
        metrics = {
            "순이익률": format_percentage(profitability["profit_margin"]),
            "영업이익률": format_percentage(profitability["operating_margin"]),
            "ROE": format_percentage(profitability["roe"]),
            "ROA": format_percentage(profitability["roa"])
        }
        for key, value in metrics.items():
            st.metric(key, value)
        
        # 재무 건전성
        st.write("**재무 건전성**")
        health = financial_analysis["financial_health"]
        metrics = {
            "부채비율": format_ratio(health["debt_to_equity"]),
            "유동비율": format_ratio(health["current_ratio"]),
            "당좌비율": format_ratio(health["quick_ratio"])
        }
        for key, value in metrics.items():
            st.metric(key, value)
    
    with col2:
        # 밸류에이션
        st.write("**밸류에이션**")
        valuation = financial_analysis["valuation"]
        metrics = {
            "P/E": format_ratio(valuation["pe_ratio"]),
            "Forward P/E": format_ratio(valuation["forward_pe"]),
            "P/B": format_ratio(valuation["price_to_book"]),
            "P/S": format_ratio(valuation["price_to_sales"])
        }
        for key, value in metrics.items():
            st.metric(key, value)
        
        # 성장성 & 배당
        st.write("**성장성 & 배당**")
        growth = financial_analysis["growth"]
        dividend = financial_analysis["dividend"]
        metrics = {
            "매출 성장률": format_percentage(growth["revenue_growth"]),
            "순이익 성장률": format_percentage(growth["earnings_growth"]),
            "배당수익률": format_percentage(dividend["dividend_yield"]),
            "배당성향": format_percentage(dividend["payout_ratio"])
        }
        for key, value in metrics.items():
            st.metric(key, value)
    
    # 재무분석 요약
    st.info(f"💡 **재무분석 요약**: {financial_analysis.get('summary', '분석 불가')}")

def format_percentage(value):
    """퍼센트 값을 포맷팅합니다."""
    if value == "N/A" or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value * 100:.2f}%"

def format_ratio(value):
    """비율 값을 포맷팅합니다."""
    if value == "N/A" or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value:.2f}"

def display_analysis_summary(result):
    """분석 요약을 표시합니다."""
    st.subheader("📝 분석 요약")
    
    # 추세 분석
    trend = result.get('trend_analysis', {})
    if trend:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("단기 추세", f"{trend.get('short_term_trend', 0):.2f}%")
        with col2:
            st.metric("중기 추세", f"{trend.get('medium_term_trend', 0):.2f}%")
        with col3:
            st.metric("추세 강도", trend.get('trend_strength', 'N/A'))
    
    # 변동성 분석
    volatility = result.get('volatility_analysis', {})
    if volatility:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("연간 변동성", f"{volatility.get('annual_volatility', 0):.2f}%")
        with col2:
            st.metric("변동성 해석", volatility.get('interpretation', 'N/A'))
    
    # 거래량 분석
    volume = result.get('volume_analysis', {})
    if volume:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("거래량 비율", f"{volume.get('volume_ratio', 0):.2f}x")
        with col2:
            st.metric("거래량 해석", volume.get('interpretation', 'N/A'))
    
    # 요약 텍스트
    summary = result.get('summary', '')
    if summary:
        st.info(summary)

def display_strategy_only_page(ticker_to_analyze: str, period: str):
    """전략 전용 페이지: 매수/매도 가이드와 백테스트만 표시"""
    st.markdown(f'<h1 class="main-header">🎯 {ticker_to_analyze} 전략 분석</h1>', unsafe_allow_html=True)
    
    # 간단한 현재가 정보만 표시
    try:
        basic_price = asyncio.run(get_stock_price_async(ticker_to_analyze))
        if "error" not in basic_price:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("현재가", format_price(basic_price['current_price'], ticker_to_analyze))
            with col2:
                st.metric("변화율", f"{basic_price['price_change_percentage']:+.2f}%")
            with col3:
                st.metric("회사명", basic_price.get('company_name', 'N/A'))
            with col4:
                st.metric("분석기간", period.upper())
    except Exception:
        st.info("기본 가격 정보를 불러오는 중...")
    
    # 전략 신호 및 백테스트
    display_strategy_signal(ticker_to_analyze, period)
    display_backtest_section(ticker_to_analyze, period)
    
    # 간단한 설명
    with st.expander("📘 전략 설명"):
        st.markdown("""
        ### 룰 기반 전략 (Rule-Based Strategy)
        
        **신호 생성 규칙:**
        - **매수**: 상승추세 + 과매도(RSI) 또는 MACD 상향교차
        - **매도**: 하락추세 + 과매수(RSI) 또는 MACD 하향교차
        - **보유**: 위 조건에 해당하지 않는 경우
        
        **백테스트 가정:**
        - 신호 발생 다음날 시가에 체결
        - 매일 종가 기준으로 자산 평가
        - 수수료 및 슬리피지 반영
        - 롱 포지션만 허용 (현금 ↔ 주식)
        """)


def display_portfolio_management_page():
    """포트폴리오 관리 전용 페이지"""    
    # 포트폴리오 입력 섹션
    st.subheader("📝 보유 주식 등록")
    
    # 세션 상태 초기화
    if 'portfolio_stocks' not in st.session_state:
        st.session_state.portfolio_stocks = []
    
    # 주식 추가 폼
    with st.expander("➕ 새 주식 추가", expanded=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            new_ticker = st.text_input("티커", placeholder="예: AAPL, MSFT, 005930.KS")
        with col2:
            new_quantity = st.number_input("보유 수량", min_value=0, value=0, step=1)
        with col3:
            new_avg_price = st.number_input("평균 단가", min_value=0.0, value=0.0, step=0.01)
        
        # 추가 버튼을 별도 행으로 배치
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 주식 추가", type="secondary", width="stretch"):
            if new_ticker and new_quantity > 0 and new_avg_price > 0:
                st.session_state.portfolio_stocks.append({
                    "ticker": new_ticker.upper().strip(),
                    "quantity": new_quantity,
                    "avg_price": new_avg_price,
                    "target_price": 0,
                    "stop_loss": 0
                })
                st.success(f"✅ {new_ticker.upper()} 추가완료!")
                st.rerun()
            else:
                st.error("모든 필드를 올바르게 입력해주세요.")
    
    # 현재 포트폴리오 표시
    if st.session_state.portfolio_stocks:
        st.subheader("📊 현재 포트폴리오")
        
        for i, stock in enumerate(st.session_state.portfolio_stocks):
            with st.container():
                st.markdown("---")
                
                # 주식 기본 정보
                col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{stock['ticker']}**")
                    st.caption(f"보유: {stock['quantity']}주 @ {stock['avg_price']:,.0f}원")
                
                # 현재가 가져오기 (간단 버전)
                with col2:
                    try:
                        ticker_obj = yf.Ticker(stock['ticker'])
                        current_price = ticker_obj.info.get('currentPrice', 0)
                        if current_price == 0:
                            current_price = ticker_obj.history(period='1d')['Close'].iloc[-1] if not ticker_obj.history(period='1d').empty else 0
                        
                        st.metric("현재가", f"{current_price:,.0f}")
                        
                        # 수익률 계산
                        if stock['avg_price'] > 0:
                            profit_rate = ((current_price - stock['avg_price']) / stock['avg_price']) * 100
                            profit_color = "🟢" if profit_rate >= 0 else "🔴"
                            st.caption(f"{profit_color} {profit_rate:+.1f}%")
                    except:
                        st.metric("현재가", "조회 실패")
                
                with col3:
                    stock['target_price'] = st.number_input(
                        "목표가", 
                        min_value=0.0, 
                        value=float(stock.get('target_price', 0)), 
                        step=100.0,
                        key=f"target_{i}"
                    )
                
                with col4:
                    stock['stop_loss'] = st.number_input(
                        "손절가", 
                        min_value=0.0, 
                        value=float(stock.get('stop_loss', 0)), 
                        step=100.0,
                        key=f"stop_{i}"
                    )
                
                with col5:
                    col5_1, col5_2 = st.columns(2)
                    with col5_1:
                        if st.button("🤖 AI분석", key=f"ai_analyze_{i}", help="AI 전략 분석"):
                            # AI 전략 분석 실행
                            with st.spinner(f"{stock['ticker']} AI 분석 중..."):
                                try:
                                    # 전략 추천 분석 실행
                                    recommendation_result = asyncio.run(recommendation_engine.generate_investment_guide(stock['ticker'], "1y"))
                                    
                                    # 결과를 세션 스테이트에 저장
                                    st.session_state[f"ai_analysis_{stock['ticker']}"] = recommendation_result
                                    st.success(f"{stock['ticker']} AI 분석 완료!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"AI 분석 실패: {str(e)}")
                    
                    with col5_2:
                        if st.button("❌", key=f"delete_{i}", help="삭제"):
                            st.session_state.portfolio_stocks.pop(i)
                            st.rerun()
                
                # AI 분석 결과가 있으면 표시
                if f"ai_analysis_{stock['ticker']}" in st.session_state:
                    ai_result = st.session_state[f"ai_analysis_{stock['ticker']}"]
                    
                    with st.expander(f"🤖 {stock['ticker']} AI 전략 분석 결과", expanded=True):
                        if "error" not in ai_result:
                            # AI 추천 목표가/손절가 표시
                            st.markdown("### 💡 AI 추천 목표가/손절가")
                            
                            # 현재가 대비 추천 가격 계산
                            try:
                                if current_price > 0:
                                    # 상위 3개 전략의 평균 기대수익률을 활용
                                    top_strategies = ai_result.get("single_strategies", [])[:3]
                                    avg_expected_return = sum(s.get("cagr", 0) for s in top_strategies) / len(top_strategies) if top_strategies else 0
                                    
                                    # 보수적 목표가 (기대수익률의 70%)
                                    conservative_target = current_price * (1 + avg_expected_return * 0.7 / 100)
                                    # 적극적 목표가 (기대수익률의 100%)
                                    aggressive_target = current_price * (1 + avg_expected_return / 100)
                                    
                                    # 손절가 (평균 최대손실의 80% 지점)
                                    avg_max_loss = sum(abs(s.get("max_drawdown", -10)) for s in top_strategies) / len(top_strategies) if top_strategies else 10
                                    stop_loss_price = current_price * (1 - avg_max_loss * 0.8 / 100)
                                    
                                    col_ai1, col_ai2, col_ai3 = st.columns(3)
                                    with col_ai1:
                                        st.metric("🎯 보수적 목표가", f"{conservative_target:,.0f}원", 
                                                f"{((conservative_target - current_price) / current_price * 100):+.1f}%")
                                    with col_ai2:
                                        st.metric("🚀 적극적 목표가", f"{aggressive_target:,.0f}원", 
                                                f"{((aggressive_target - current_price) / current_price * 100):+.1f}%")
                                    with col_ai3:
                                        st.metric("🛑 AI 손절가", f"{stop_loss_price:,.0f}원", 
                                                f"{((stop_loss_price - current_price) / current_price * 100):+.1f}%")
                                    
                                    # AI 추천 근거
                                    st.markdown("### 📊 추천 근거")
                                    if top_strategies:
                                        st.markdown("**상위 3개 추천 전략:**")
                                        for idx, strategy in enumerate(top_strategies[:3], 1):
                                            strategy_name = strategy.get("strategy", "Unknown")
                                            annual_return = strategy.get("cagr", 0)
                                            max_dd = strategy.get("max_drawdown", 0)
                                            win_rate = strategy.get("win_rate", 0)
                                            
                                            st.markdown(f"""
                                            **{idx}. {strategy_name}**
                                            - 기대 연수익률: {annual_return:+.1f}%
                                            - 최대 손실: {max_dd:.1f}%
                                            - 승률: {win_rate:.1f}%
                                            """)
                                    
                                    # 자동으로 AI 추천값을 입력란에 적용하는 버튼
                                    col_apply1, col_apply2 = st.columns(2)
                                    with col_apply1:
                                        if st.button("🎯 보수적 목표가 적용", key=f"apply_conservative_{i}"):
                                            st.session_state.portfolio_stocks[i]['target_price'] = conservative_target
                                            st.rerun()
                                    with col_apply2:
                                        if st.button("🛑 AI 손절가 적용", key=f"apply_stoploss_{i}"):
                                            st.session_state.portfolio_stocks[i]['stop_loss'] = stop_loss_price
                                            st.rerun()
                                            
                            except Exception as e:
                                st.error(f"AI 추천 계산 오류: {str(e)}")
                        else:
                            st.error(f"AI 분석 오류: {ai_result.get('error', '알 수 없는 오류')}")
                
                # 기존 투자 대응 방향 제시
                if stock.get('target_price', 0) > 0 or stock.get('stop_loss', 0) > 0:
                    st.markdown("**💡 대응 방향:**")
                    
                    try:
                        if current_price > 0:
                            advice_text = ""
                            
                            if stock.get('target_price', 0) > 0 and current_price >= stock['target_price']:
                                advice_text += f"🎯 목표가 달성! 수익실현을 고려하세요. "
                            elif stock.get('stop_loss', 0) > 0 and current_price <= stock['stop_loss']:
                                advice_text += f"🛑 손절가 도달! 손절 매도를 고려하세요. "
                            else:
                                if stock.get('target_price', 0) > 0:
                                    target_gap = ((stock['target_price'] - current_price) / current_price) * 100
                                    advice_text += f"📈 목표가까지 {target_gap:+.1f}% "
                                if stock.get('stop_loss', 0) > 0:
                                    stop_gap = ((current_price - stock['stop_loss']) / current_price) * 100
                                    advice_text += f"🛡️ 손절가까지 -{stop_gap:.1f}% 여유"
                            
                            if advice_text:
                                st.info(advice_text)
                    except:
                        st.warning("가격 정보 조회에 실패했습니다.")
    
    else:
        st.info("아직 등록된 주식이 없습니다. 위에서 보유 주식을 추가해주세요.")
    
    # 포트폴리오 분석 버튼
    if st.session_state.portfolio_stocks:
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔍 포트폴리오 종합 분석", type="primary", width="stretch"):
                st.subheader("📈 포트폴리오 종합 분석")
                
                total_investment = sum(stock['quantity'] * stock['avg_price'] for stock in st.session_state.portfolio_stocks)
                total_current_value = 0
                
                analysis_text = f"**📊 포트폴리오 요약:**\n\n"
                analysis_text += f"- 총 투자금액: {total_investment:,.0f}원\n"
                analysis_text += f"- 보유 종목 수: {len(st.session_state.portfolio_stocks)}개\n\n"
                
                analysis_text += "**💡 종목별 추천 액션:**\n\n"
                
                for stock in st.session_state.portfolio_stocks:
                    try:
                        ticker_obj = yf.Ticker(stock['ticker'])
                        current_price = ticker_obj.info.get('currentPrice', 0)
                        if current_price == 0:
                            hist = ticker_obj.history(period='1d')
                            current_price = hist['Close'].iloc[-1] if not hist.empty else 0
                        
                        if current_price > 0:
                            profit_rate = ((current_price - stock['avg_price']) / stock['avg_price']) * 100
                            
                            analysis_text += f"**{stock['ticker']}**: "
                            analysis_text += f"현재 {profit_rate:+.1f}% "
                            
                            # AI 분석 결과가 있으면 활용
                            if f"ai_analysis_{stock['ticker']}" in st.session_state:
                                ai_result = st.session_state[f"ai_analysis_{stock['ticker']}"]
                                if "error" not in ai_result:
                                    top_strategies = ai_result.get("single_strategies", [])[:3]
                                    if top_strategies:
                                        avg_expected_return = sum(s.get("cagr", 0) for s in top_strategies) / len(top_strategies)
                                        analysis_text += f"(AI 기대수익률: {avg_expected_return:+.1f}%) "
                            
                            if stock.get('target_price', 0) > 0 and current_price >= stock['target_price']:
                                analysis_text += "→ 🎯 목표가 달성, 수익실현 고려\n"
                            elif stock.get('stop_loss', 0) > 0 and current_price <= stock['stop_loss']:
                                analysis_text += "→ 🛑 손절가 도달, 손절 고려\n"
                            else:
                                analysis_text += "→ 📊 관망 또는 전략적 대응\n"
                            
                            total_current_value += stock['quantity'] * current_price
                    except:
                        analysis_text += f"**{stock['ticker']}**: 가격 조회 실패\n"
                
                if total_current_value > 0:
                    total_profit_rate = ((total_current_value - total_investment) / total_investment) * 100
                    analysis_text += f"\n**📊 전체 포트폴리오 수익률: {total_profit_rate:+.1f}%**"
                
                st.markdown(analysis_text)
        
        with col2:
            if st.button("🤖 전체 AI 분석 실행", type="secondary", width="stretch"):
                st.subheader("🤖 전체 포트폴리오 AI 분석")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, stock in enumerate(st.session_state.portfolio_stocks):
                    status_text.text(f"분석 중: {stock['ticker']} ({i+1}/{len(st.session_state.portfolio_stocks)})")
                    progress_bar.progress((i+1) / len(st.session_state.portfolio_stocks))
                    
                    try:
                        # AI 분석이 아직 없거나 오래된 경우에만 실행
                        if f"ai_analysis_{stock['ticker']}" not in st.session_state:
                            recommendation_result = asyncio.run(recommendation_engine.generate_investment_guide(stock['ticker'], "1y"))
                            st.session_state[f"ai_analysis_{stock['ticker']}"] = recommendation_result
                    except Exception as e:
                        st.error(f"{stock['ticker']} AI 분석 실패: {str(e)}")
                
                status_text.text("전체 AI 분석 완료!")
                progress_bar.progress(1.0)
                st.success("모든 종목의 AI 분석이 완료되었습니다!")
                st.rerun()


def display_undervalued_screening_page():
    """저평가 종목 스크리닝 전용 페이지"""
    st.subheader("🔍 저평가 종목 스크리닝")
    
    # 스크리닝 설정
    col1, col2, col3 = st.columns(3)
    
    with col1:
        market_type = st.selectbox(
            "시장 선택",
            ["한국 주식", "미국 주식", "전체"],
            index=0,
            help="스크리닝할 시장을 선택하세요"
        )
    
    with col2:
        min_score = st.slider(
            "최소 점수",
            min_value=0.0,
            max_value=10.0,
            value=6.0,
            step=0.5,
            help="저평가 점수 기준 (높을수록 엄격)"
        )
    
    with col3:
        max_results = st.slider(
            "최대 결과 수",
            min_value=10,
            max_value=100,
            value=20,
            step=5,
            help="표시할 최대 종목 수"
        )
    
    # 추가 필터 설정
    with st.expander("🔧 고급 필터 설정", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            min_market_cap = st.number_input(
                "최소 시가총액 (억원/백만달러)",
                min_value=0,
                value=1000,
                step=100,
                help="너무 작은 회사 제외"
            )
        
        with col2:
            max_pe_ratio = st.number_input(
                "최대 P/E 비율",
                min_value=0.0,
                value=30.0,
                step=1.0,
                help="과도한 고평가 종목 제외"
            )
        
        with col3:
            min_roe = st.number_input(
                "최소 ROE (%)",
                min_value=-50.0,
                max_value=100.0,
                value=5.0,
                step=1.0,
                help="수익성 기준"
            )
        
        with col4:
            min_current_ratio = st.number_input(
                "최소 유동비율",
                min_value=0.0,
                value=1.0,
                step=0.1,
                help="재무 안정성 기준"
            )
    
    # 스크리닝 실행 버튼
    if st.button("🚀 스크리닝 시작", type="secondary", width="stretch"):
        
        with st.spinner("🔍 전체 종목을 분석하고 있습니다... (수 분이 소요될 수 있습니다)"):
            try:
                screener = UndervaluedStockScreener()
                
                # 필터 조건 설정
                filters = {
                    'min_market_cap': min_market_cap * 1e8 if market_type == "한국 주식" else min_market_cap * 1e6,  # 억원 -> 원, 백만달러 -> 달러
                    'max_pe_ratio': max_pe_ratio,
                    'min_roe': min_roe / 100,  # % -> 비율
                    'min_current_ratio': min_current_ratio
                }
                
                # 시장 타입별 스크리닝
                if market_type == "한국 주식":
                    results = screener.screen_korean_stocks(
                        min_score=min_score,
                        max_results=max_results,
                        filters=filters
                    )
                elif market_type == "미국 주식":
                    results = screener.screen_us_stocks(
                        min_score=min_score,
                        max_results=max_results,
                        filters=filters
                    )
                else:  # 전체
                    korean_results = screener.screen_korean_stocks(
                        min_score=min_score,
                        max_results=max_results // 2,
                        filters=filters
                    )
                    us_results = screener.screen_us_stocks(
                        min_score=min_score,
                        max_results=max_results // 2,
                        filters=filters
                    )
                    # 점수순으로 정렬하여 결합
                    combined = korean_results + us_results
                    results = sorted(combined, key=lambda x: x['undervalued_score'], reverse=True)[:max_results]
                
                if not results:
                    st.warning("설정된 조건에 맞는 저평가 종목이 없습니다. 조건을 완화해보세요.")
                    return
                
                # 결과 표시
                st.success(f"✅ {len(results)}개의 저평가 종목을 발견했습니다!")
                
                # 요약 통계
                col1, col2, col3, col4 = st.columns(4)
                avg_score = sum(stock['undervalued_score'] for stock in results) / len(results)
                avg_pe = sum(stock['pe_ratio'] for stock in results if stock['pe_ratio'] > 0) / max(1, sum(1 for stock in results if stock['pe_ratio'] > 0))
                avg_pb = sum(stock['pb_ratio'] for stock in results if stock['pb_ratio'] > 0) / max(1, sum(1 for stock in results if stock['pb_ratio'] > 0))
                korean_count = sum(1 for stock in results if stock['ticker'].endswith('.KS'))
                
                with col1:
                    st.metric("평균 저평가 점수", f"{avg_score:.1f}/10")
                with col2:
                    st.metric("평균 P/E 비율", f"{avg_pe:.1f}")
                with col3:
                    st.metric("평균 P/B 비율", f"{avg_pb:.1f}")
                with col4:
                    st.metric("한국/미국 종목 수", f"{korean_count}/{len(results)-korean_count}")
                
                # 결과 테이블
                st.subheader("📊 스크리닝 결과")
                
                # 데이터프레임 생성
                df_data = []
                for stock in results:
                    df_data.append({
                        "순위": len(df_data) + 1,
                        "티커": stock['ticker'],
                        "회사명": stock['company_name'],
                        "점수": f"{stock['undervalued_score']:.1f}",
                        "현재가": f"${stock['current_price']:.2f}" if not stock['ticker'].endswith('.KS') else f"₩{stock['current_price']:,.0f}",
                        "P/E": f"{stock['pe_ratio']:.1f}" if stock['pe_ratio'] > 0 else "N/A",
                        "P/B": f"{stock['pb_ratio']:.1f}" if stock['pb_ratio'] > 0 else "N/A",
                        "ROE": f"{stock['roe']*100:.1f}%" if stock['roe'] else "N/A",
                        "부채비율": f"{stock['debt_ratio']:.1f}" if stock['debt_ratio'] else "N/A",
                        "시가총액": format_large_number(stock['market_cap']),
                        "섹터": stock.get('sector', 'N/A')
                    })
                
                df = pd.DataFrame(df_data)
                
                # 점수별 색상 구분을 위한 스타일링
                def highlight_score(row):
                    score = float(row['점수'])
                    if score >= 8.0:
                        return ['background-color: #d4edda'] * len(row)  # 초록색
                    elif score >= 7.0:
                        return ['background-color: #fff3cd'] * len(row)  # 노란색
                    else:
                        return [''] * len(row)
                
                styled_df = df.style.apply(highlight_score, axis=1)
                st.dataframe(styled_df, width="stretch")
                
                # 상세 분석 섹션
                st.subheader("📈 상위 종목 상세 분석")
                
                # 상위 3개 종목 선택
                top_stocks = results[:3]
                
                for i, stock in enumerate(top_stocks, 1):
                    with st.expander(f"#{i} {stock['company_name']} ({stock['ticker']}) - 점수: {stock['undervalued_score']:.1f}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write("**가격 정보**")
                            st.write(f"현재가: ${stock['current_price']:.2f}" if not stock['ticker'].endswith('.KS') else f"현재가: ₩{stock['current_price']:,.0f}")
                            st.write(f"52주 최고: ${stock['high_52w']:.2f}" if stock['high_52w'] and not stock['ticker'].endswith('.KS') else f"52주 최고: ₩{stock['high_52w']:,.0f}" if stock['high_52w'] else "52주 최고: N/A")
                            st.write(f"52주 최저: ${stock['low_52w']:.2f}" if stock['low_52w'] and not stock['ticker'].endswith('.KS') else f"52주 최저: ₩{stock['low_52w']:,.0f}" if stock['low_52w'] else "52주 최저: N/A")
                        
                        with col2:
                            st.write("**밸류에이션**")
                            st.write(f"P/E: {stock['pe_ratio']:.1f}" if stock['pe_ratio'] > 0 else "P/E: N/A")
                            st.write(f"P/B: {stock['pb_ratio']:.1f}" if stock['pb_ratio'] > 0 else "P/B: N/A")
                            st.write(f"P/S: {stock['ps_ratio']:.1f}" if stock['ps_ratio'] > 0 else "P/S: N/A")
                        
                        with col3:
                            st.write("**재무 건전성**")
                            st.write(f"ROE: {stock['roe']*100:.1f}%" if stock['roe'] else "ROE: N/A")
                            st.write(f"부채비율: {stock['debt_ratio']:.1f}" if stock['debt_ratio'] else "부채비율: N/A")
                            st.write(f"유동비율: {stock['current_ratio']:.1f}" if stock['current_ratio'] else "유동비율: N/A")
                        
                        # 저평가 근거
                        st.write("**💡 저평가 근거**")
                        reasons = []
                        if stock['pe_ratio'] > 0 and stock['pe_ratio'] < 15:
                            reasons.append(f"P/E 비율이 {stock['pe_ratio']:.1f}로 낮음")
                        if stock['pb_ratio'] > 0 and stock['pb_ratio'] < 1.5:
                            reasons.append(f"P/B 비율이 {stock['pb_ratio']:.1f}로 낮음")
                        if stock['roe'] and stock['roe'] > 0.1:
                            reasons.append(f"ROE가 {stock['roe']*100:.1f}%로 높은 수익성")
                        if stock['current_ratio'] and stock['current_ratio'] > 1.5:
                            reasons.append(f"유동비율 {stock['current_ratio']:.1f}로 재무 안정성 우수")
                        
                        if reasons:
                            for reason in reasons:
                                st.write(f"• {reason}")
                        else:
                            st.write("• 종합적인 지표 검토 필요")
                
                # 내보내기 옵션
                st.subheader("💾 결과 내보내기")
                
                # CSV 다운로드
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📄 CSV 파일로 다운로드",
                    data=csv,
                    file_name=f"undervalued_stocks_{market_type}_{min_score}점이상.csv",
                    mime="text/csv",
                    help="스크리닝 결과를 CSV 파일로 저장합니다"
                )
                
                # 주의사항
                st.warning("""
                ⚠️ **투자 주의사항**
                - 이 스크리닝 결과는 참고용이며, 투자 결정의 유일한 근거로 사용해서는 안 됩니다
                - 실제 투자 전에는 반드시 추가적인 분석과 리스크 검토가 필요합니다
                - 과거 데이터 기반 분석이므로 미래 성과를 보장하지 않습니다
                - 시장 상황, 산업 전망, 회사 특수 상황 등을 종합적으로 고려하세요
                """)
                
            except Exception as e:
                st.error(f"❌ 스크리닝 중 오류가 발생했습니다: {str(e)}")
                st.info("서버 연결이나 데이터 문제일 수 있습니다. 잠시 후 다시 시도해주세요.")
    
    else:
        # 스크리닝 시작 전 안내
        st.markdown("""
        ### 🎯 저평가 종목 스크리닝 도구
        
        전체 주식 시장에서 저평가된 우수한 투자 기회를 찾아드립니다.
        
        **🔍 분석 기준:**
        - **P/E, P/B, P/S 비율**: 상대적 가치 평가
        - **ROE, ROA**: 수익성 지표
        - **부채비율, 유동비율**: 재무 안정성
        - **매출/이익 성장률**: 성장성 지표
        - **배당수익률**: 배당 매력도
        
        **📊 종합 점수 시스템:**
        - **9~10점**: 매우 강한 저평가 (투자 고려 강추)
        - **7~8점**: 저평가 (추가 분석 권장)
        - **5~6점**: 보통 (신중한 검토 필요)
        - **~4점**: 고평가 위험 (투자 주의)
        
        **💡 사용 팁:**
        - 처음에는 최소 점수를 6~7점으로 설정해보세요
        - 시장 상황이 좋지 않을 때는 점수를 낮춰 더 많은 기회를 발견할 수 있습니다
        - 특정 섹터나 시가총액 구간에 집중하고 싶다면 고급 필터를 활용하세요
        
        위의 설정을 조정하고 **🚀 스크리닝 시작** 버튼을 클릭하세요!
        """)

def main():
    """메인 함수"""
    # 초기화: session_state 설정
    if 'is_analyzed' not in st.session_state:
        st.session_state.is_analyzed = False
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'analyzed_ticker' not in st.session_state:
        st.session_state.analyzed_ticker = None
    if 'charts' not in st.session_state:
        st.session_state.charts = None
    if 'period' not in st.session_state:
        st.session_state.period = "1y"
    if 'selected_chart_type' not in st.session_state:
        st.session_state.selected_chart_type = "캔들스틱 차트"

    # st.markdown('<h1 class="main-header">📈 주식 분석 도구</h1>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        # 페이지 모드 선택을 더 시각적으로 개선
        st.markdown("""
        <style>
        .stRadio > label {
            display: none;
        }
        .mode-button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 16px;
            border-radius: 10px;
            margin: 8px 0;
            text-align: center;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        .mode-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        .mode-button.active {
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
            box-shadow: 0 6px 20px rgba(17, 153, 142, 0.6);
        }
        .mode-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 16px;
            border-radius: 15px;
            margin: 10px 0;
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="mode-header">� 분석 모드 선택</div>', unsafe_allow_html=True)
        
        page_modes = [
            {"key": "전체분석", "icon": "📈", "title": "전체 분석", "desc": "모든 지표와 차트"},
            {"key": "포트폴리오", "icon": "💼", "title": "포트폴리오 관리", "desc": "보유주식 목표가/손절가"},
            {"key": "전략전용", "icon": "🎯", "title": "전략 전용", "desc": "매수매도 가이드"},
            {"key": "저평가 스크리닝", "icon": "💎", "title": "저평가 스크리닝", "desc": "전체 종목 분석"}
        ]
        
        if "page_mode" not in st.session_state:
            st.session_state.page_mode = "전체분석"
        
        # 각 모드를 버튼으로 표시
        for mode in page_modes:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"<div style='font-size: 24px; text-align: center;'>{mode['icon']}</div>", unsafe_allow_html=True)
            with col2:
                is_selected = st.session_state.page_mode == mode['key']
                button_style = "background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%); transform: scale(1.05);" if is_selected else "background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);"
                
                if st.button(
                    f"**{mode['title']}**", 
                    key=f"mode_{mode['key']}", 
                    width="stretch",
                    help=f"{mode['title']}: {mode['desc']}"
                ):
                    st.session_state.page_mode = mode['key']
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
        
        # 추가 정보 및 도움말 섹션
        st.markdown("---")
        
        with st.expander("💡 모드별 안내", expanded=False):
            st.markdown("""
            **📈 전체 분석**
            - 종합적인 주식 분석
            - 기술적/재무적 지표
            - 차트 및 백테스트
            
            **💼 포트폴리오 관리**
            - 보유 주식 분석
            - 목표가/손절가 설정
            - 포지션별 리스크 관리
            
            **🎯 전략 전용**
            - AI 기반 전략 추천
            - 매수매도 시그널
            - 간단하고 직관적
            
            **💎 저평가 스크리닝**
            - 전체 시장 스크리닝
            - 저평가 종목 발굴
            - 투자 기회 탐색
            """)
        
        with st.expander("🔧 시스템 정보", expanded=False):
            st.markdown("""
            **📊 데이터 소스**: Yahoo Finance  
            **🤖 AI 엔진**: Claude 3.5 Sonnet  
            **📈 차트**: Plotly Interactive  
            **⚡ 업데이트**: 실시간  
            
            **💬 문의사항이나 개선사항이 있으시면  
            언제든지 알려주세요!**
            """)
            
        # 간단한 상태 표시
        st.markdown("---")
        st.markdown("""
        <div style="
            background: #f0f2f6;
            padding: 10px;
            border-radius: 8px;
            text-align: center;
            font-size: 12px;
            color: #666;
        ">
            🟢 시스템 정상 작동 중
        </div>
        """, unsafe_allow_html=True)

    # 메인 컨텐츠
    # 전체분석 모드에서만 분석 설정 및 전략 파라미터를 상단에 표시
    if st.session_state.page_mode == "전체분석":
        # 분석 설정 섹션을 상단에 표시
        st.subheader("🔍 분석 설정")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # 분석 기간 선택
            period = st.selectbox(
                "분석 기간",
                ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                index=3,
                key="period_selector",
                help="분석할 기간을 선택하세요"
            )
            st.session_state.period = period
            
            # 직접 입력
            custom_ticker = st.text_input(
                "티커 직접 입력",
                placeholder="예: AAPL, MSFT, 005930.KS",
                help="분석할 주식의 티커를 입력하세요"
            )
        
        with col2:
            # 인기 주식 선택
            popular_stocks = get_popular_stocks()
            
            # 섹터 선택
            selected_sector = st.selectbox(
                "📊 섹터 선택", 
                list(popular_stocks.keys()),
                help="섹터별로 분류된 인기 종목을 선택하세요"
            )
            
            # 선택된 섹터의 주식 선택
            sector_stocks = popular_stocks[selected_sector]
            selected_stock = st.selectbox(
                "🏢 종목 선택",
                list(sector_stocks.keys()),
                format_func=lambda x: f"{x} - {sector_stocks[x]}",
                help=f"{selected_sector}에서 {len(sector_stocks)}개 종목 중 선택"
            )
        
        # 선택된 섹터 정보 표시
        with st.expander(f"📈 {selected_sector} 전체 종목 보기"):
            st.write(f"**총 {len(sector_stocks)}개 종목**")
            for ticker, name in sector_stocks.items():
                st.write(f"• `{ticker}` - {name}")
        
        # 전략 파라미터 섹션을 상단에 표시
        st.header("⚙️ 전략 파라미터")
        with st.expander("전략/백테스트 설정", expanded=False):
            # 전략 선택
            strategy_options = {
                "룰베이스": {"class": "RuleBasedStrategy", "name": "rule_based", "desc": "MA/RSI/MACD 조합"},
                "모멘텀": {"class": "MomentumStrategy", "name": "momentum", "desc": "가격모멘텀+거래량+브레이크아웃"},
                "평균회귀": {"class": "MeanReversionStrategy", "name": "mean_reversion", "desc": "볼린저밴드+RSI 반전"},
                "패턴인식": {"class": "PatternStrategy", "name": "pattern", "desc": "차트패턴+지지저항"}
            }
            
            strategy_name = st.selectbox(
                "전략 선택", 
                list(strategy_options.keys()), 
                format_func=lambda x: f"{x} - {strategy_options[x]['desc']}",
                help="다양한 분석 기법을 활용한 전략 중 선택"
            )
            
            selected_strategy = strategy_options[strategy_name]
            
            presets = {
                "보수적": {"warmup": 100, "rsi_buy": 25, "rsi_sell": 75, "risk_rr": 1.5, "fee_bps": 15, "slippage_bps": 15},
                "중립":   {"warmup": 50,  "rsi_buy": 30, "rsi_sell": 70, "risk_rr": 2.0, "fee_bps": 10, "slippage_bps": 10},
                "공격적": {"warmup": 20,  "rsi_buy": 35, "rsi_sell": 65, "risk_rr": 2.5, "fee_bps": 8,  "slippage_bps": 8},
            }
            preset_name = st.selectbox("프리셋", list(presets.keys()), index=1, help="전략 기본값을 빠르게 불러옵니다")

            # 프리셋 적용 기본값 결정
            pdef = presets[preset_name]
            warmup = st.slider(
                "워밍업 기간 (일)", min_value=0, max_value=200, value=int(pdef["warmup"]), step=5,
                help="지표 안정화를 위해 초기 구간을 무시합니다"
            )
            
            # 전략별 특화 파라미터
            if selected_strategy["name"] == "rule_based":
                c1, c2 = st.columns(2)
                with c1:
                    rsi_buy = st.slider("RSI 매수 기준", min_value=10, max_value=40, value=int(pdef["rsi_buy"]), step=1)
                with c2:
                    rsi_sell = st.slider("RSI 매도 기준", min_value=60, max_value=90, value=int(pdef["rsi_sell"]), step=1)
                risk_rr = st.slider("리스크-리워드(타겟 배수)", min_value=1.0, max_value=3.0, value=float(pdef["risk_rr"]), step=0.1)
                strategy_specific_params = {"rsi_buy": rsi_buy, "rsi_sell": rsi_sell, "risk_rr": risk_rr}
                
            elif selected_strategy["name"] == "momentum":
                c1, c2 = st.columns(2)
                with c1:
                    momentum_period = st.slider("모멘텀 기간", min_value=5, max_value=50, value=20, step=1)
                with c2:
                    breakout_threshold = st.slider("브레이크아웃 임계값", min_value=0.01, max_value=0.05, value=0.02, step=0.001, format="%.3f")
                volume_sma = st.slider("거래량 이평", min_value=5, max_value=20, value=10, step=1)
                strategy_specific_params = {"momentum_period": momentum_period, "breakout_threshold": breakout_threshold, "volume_sma": volume_sma}
                
            elif selected_strategy["name"] == "mean_reversion":
                c1, c2 = st.columns(2)
                with c1:
                    bb_period = st.slider("볼린저밴드 기간", min_value=10, max_value=30, value=20, step=1)
                    rsi_oversold = st.slider("RSI 과매도", min_value=15, max_value=35, value=25, step=1)
                with c2:
                    bb_std = st.slider("볼린저밴드 표준편차", min_value=1.5, max_value=3.0, value=2.0, step=0.1)
                    rsi_overbought = st.slider("RSI 과매수", min_value=65, max_value=85, value=75, step=1)
                strategy_specific_params = {"bb_period": bb_period, "bb_std": bb_std, "rsi_oversold": rsi_oversold, "rsi_overbought": rsi_overbought}
                
            elif selected_strategy["name"] == "pattern":
                c1, c2 = st.columns(2)
                with c1:
                    pattern_window = st.slider("패턴 윈도우", min_value=5, max_value=20, value=10, step=1)
                with c2:
                    sr_window = st.slider("지지저항 윈도우", min_value=10, max_value=30, value=20, step=1)
                breakout_threshold = st.slider("브레이크아웃 임계값", min_value=0.005, max_value=0.02, value=0.01, step=0.001, format="%.3f")
                strategy_specific_params = {"pattern_window": pattern_window, "support_resistance_window": sr_window, "breakout_threshold": breakout_threshold}
            else:
                strategy_specific_params = {}
            
            c3, c4 = st.columns(2)
            with c3:
                fee_bps = st.slider("수수료 (bps)", min_value=0, max_value=50, value=int(pdef["fee_bps"]), step=1)
            with c4:
                slippage_bps = st.slider("슬리피지 (bps)", min_value=0, max_value=50, value=int(pdef["slippage_bps"]), step=1)

            st.session_state.strategy_params = {
                "selected_strategy": selected_strategy,
                "warmup": int(warmup),
                "fee_bps": float(fee_bps),
                "slippage_bps": float(slippage_bps),
                **strategy_specific_params
            }
        
        # 분석 버튼
        analyze_button = st.button("🚀 분석 시작", type="secondary", width="stretch")
        st.markdown("---")
    else:
        # 다른 모드에서는 기본 변수 설정
        period = "1y"
        custom_ticker = ""
        selected_stock = ""
        analyze_button = False

    # 저평가 스크리닝 모드 처리
    if st.session_state.page_mode == "저평가 스크리닝":
        display_undervalued_screening_page()
        return
    
    # 포트폴리오 관리 모드 처리
    if st.session_state.page_mode == "포트폴리오":
        display_portfolio_management_page()
        return
    
    # 분석 실행 및 결과 표시
    if analyze_button or st.session_state.is_analyzed:
        ticker_to_analyze = custom_ticker.strip().upper() if custom_ticker.strip() else selected_stock
        
        if not ticker_to_analyze:
            st.error("분석할 주식 티커를 입력하거나 선택해주세요.")
            return
        
        if analyze_button:
            st.session_state.is_analyzed = True
        
        # 새로운 종목 분석이 시작되면 session state 초기화
        if st.session_state.analyzed_ticker != ticker_to_analyze:
            st.session_state.analysis_result = None
            st.session_state.charts = None
            st.session_state.analyzed_ticker = ticker_to_analyze

        with st.spinner(f"📊 {ticker_to_analyze} 분석 중..."):
            try:
                if st.session_state.analysis_result is None:
                    result = asyncio.run(analyze_stock_async(ticker_to_analyze, period))
                    if "error" in result:
                        st.error(f"❌ 분석 오류: {result['error']}")
                        return
                    st.session_state.analysis_result = result
                
                # 페이지 모드에 따라 다른 내용 표시
                if st.session_state.page_mode == "전략전용":
                    display_strategy_only_page(ticker_to_analyze, period)
                else:
                    # 기존 전체 분석 페이지
                    # 결과 표시
                    st.success(f"✅ {st.session_state.analysis_result['basic_info']['company_name']} 분석 완료!")
                    
                    # 기본 정보
                    st.subheader("💰 기본 정보")
                    display_basic_info(st.session_state.analysis_result['basic_info'], ticker_to_analyze)
                    
                    # 기술적 지표
                    if st.session_state.analysis_result.get('technical_indicators'):
                        display_technical_indicators(st.session_state.analysis_result['technical_indicators'], ticker_to_analyze)
                    
                    # 재무제표 분석
                    if st.session_state.analysis_result.get('financial_analysis'):
                        display_financial_analysis(st.session_state.analysis_result['financial_analysis'])
                    
                    # 어닝콜 & 가이던스 분석
                    if st.session_state.analysis_result.get('earnings_analysis'):
                        display_earnings_analysis(st.session_state.analysis_result['earnings_analysis'], ticker_to_analyze)

                    # 전략 신호 및 백테스트
                    display_strategy_signal(ticker_to_analyze, period)
                    display_backtest_section(ticker_to_analyze, period)
                    
                    # 분석 요약
                    display_analysis_summary(st.session_state.analysis_result)
                    
                    # 차트 섹션
                    st.subheader("📈 차트 분석")
                    
                    # 차트 타입 선택
                    chart_type = st.selectbox(
                        "차트 타입 선택",
                        ["캔들스틱 차트", "가격 차트", "기술적 지표 차트", "고급 가격 차트 (채널/지지저항선/피보나치)"],
                        key="chart_type_selector",
                        help="보고 싶은 차트 타입을 선택하세요"
                    )
                    st.session_state.selected_chart_type = chart_type
                    
                    # 차트 생성
                    with st.spinner("차트 생성 중..."):
                        try:
                            if st.session_state.charts is None:
                                # 차트 생성을 위한 데이터 유효성 검사
                                chart_data = asyncio.run(get_processed_df_async(ticker_to_analyze, period))
                                if chart_data is not None and not chart_data.empty and len(chart_data) > 20:
                                    # NaN 값 처리
                                    chart_data = chart_data.ffill().bfill()
                                    
                                    # 차트 생성
                                    st.session_state.charts = asyncio.run(generate_charts_async(ticker_to_analyze, period))
                                else:
                                    st.warning("차트 생성을 위한 데이터가 부족합니다.")
                                    st.session_state.charts = None
                            
                            if st.session_state.charts is not None:
                                if chart_type == "캔들스틱 차트" and 'candlestick' in st.session_state.charts:
                                    st.plotly_chart(st.session_state.charts['candlestick'], width='stretch')
                                elif chart_type == "가격 차트" and 'price' in st.session_state.charts:
                                    st.plotly_chart(st.session_state.charts['price'], width='stretch')
                                elif chart_type == "기술적 지표 차트" and 'technical' in st.session_state.charts:
                                    st.plotly_chart(st.session_state.charts['technical'], width='stretch')
                                elif chart_type == "고급 가격 차트 (채널/지지저항선/피보나치)" and 'advanced_price' in st.session_state.charts:
                                    st.plotly_chart(st.session_state.charts['advanced_price'], width='stretch')
                                else:
                                    st.warning(f"{chart_type}를 사용할 수 없습니다.")
                            else:
                                st.warning("차트를 생성할 수 없습니다. 데이터를 확인해주세요.")
                            
                            # 차트 설명
                            st.info("""
                            **차트 설명:**
                            - **캔들스틱 차트**: 가격 변동, 이동평균선, 볼린저 밴드, 거래량, RSI, MACD를 한 번에 볼 수 있습니다
                            - **가격 차트**: 간단한 가격 추이와 거래량을 확인할 수 있습니다
                            - **기술적 지표 차트**: RSI, MACD, 볼린저 밴드, 스토캐스틱을 상세히 분석할 수 있습니다
                            - **고급 가격 차트**: 채널, 지지선/저항선, 피보나치 되돌림 레벨을 포함한 고급 차트 분석
                            """)
                            
                        except Exception as e:
                            st.error(f"차트 생성 중 오류가 발생했습니다: {str(e)}")
                            st.info("차트 생성 실패 시 대안:")
                            st.info("1. 다른 종목을 선택해보세요")
                            st.info("2. 분석 기간을 변경해보세요") 
                            st.info("3. 페이지를 새로고침해보세요")
                    
                    # 상세 데이터 (접을 수 있는 섹션)
                    with st.expander("📊 상세 데이터 보기"):
                        st.json(st.session_state.analysis_result)
                
            except Exception as e:
                st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
    
    # 홈 화면 (분석이 수행되지 않았을 때)
    elif not st.session_state.is_analyzed:
        if st.session_state.page_mode == "저평가 스크리닝":
            display_undervalued_screening_page()
        elif st.session_state.page_mode == "전략전용":
            # st.markdown('<h1 class="main-header">🎯 전략 전용 모드</h1>', unsafe_allow_html=True)
            
            st.markdown("""
            ### 🤖 AI 기반 전략 추천 시스템
            
            과거 데이터를 분석하여 해당 종목에 가장 적합한 투자 전략을 추천해드립니다.
            
            **🏆 13개 전략 분석**: Quantitative Factor, Machine Learning, Market Regime 등 모든 전략 포함
            **🔄 조합 전략**: 2~3개 전략을 함께 사용하는 포트폴리오 접근법
            **📈 성과 기반**: 과거 데이터에서 실제로 우수한 성과를 거둔 전략 우선 추천
            **💡 투자 가이드**: 추천 이유와 구체적인 실행 방법 제시
            """)
            
            # 전략 추천용 종목 선택
            rec_col1, rec_col2, rec_col3, rec_col4 = st.columns([2, 2, 1, 1])
            
            with rec_col1:
                rec_ticker = st.selectbox(
                    "분석할 종목 선택",
                    [""] + get_all_popular_tickers(),
                    key="recommendation_ticker",
                    help="전략 추천을 받을 종목을 선택하세요"
                )
            
            with rec_col2:
                # 직접 입력
                custom_rec_ticker = st.text_input(
                    "또는 직접 입력",
                    placeholder="예: AAPL, 005930.KS",
                    key="custom_recommendation_ticker",
                    help="위에서 찾을 수 없는 종목은 직접 입력하세요"
                )
            
            with rec_col3:
                rec_period = st.selectbox(
                    "분석 기간",
                    ["6mo", "1y", "2y", "3y", "5y"],
                    index=3,
                    key="recommendation_period",
                    help="더 긴 기간일수록 정확한 분석이 가능합니다"
                )
            
            with rec_col4:
                rec_top_n = st.selectbox(
                    "추천 전략 수",
                    [3, 5, 7],
                    index=0,
                    key="recommendation_top_n",
                    help="상위 몇 개 전략을 보여드릴까요?"
                )
            
            # 추천 시작 버튼
            if st.button("🚀 전략 추천 시작", type="secondary", width="stretch", key="start_recommendation"):
                final_ticker = custom_rec_ticker if custom_rec_ticker else rec_ticker
                
                if final_ticker:
                    with st.spinner(f"🔍 {final_ticker} 종목에 대한 13개 전략 분석 중..."):
                        # 전략 추천 실행
                        recommendation_result = asyncio.run(
                            recommendation_engine.generate_investment_guide(
                                final_ticker, rec_period
                            )
                        )
                        
                        if "error" not in recommendation_result:
                            display_strategy_recommendations(recommendation_result, rec_top_n)
                        else:
                            st.error(f"❌ 분석 중 오류가 발생했습니다: {recommendation_result['error']}")
                else:
                    st.warning("종목을 선택하거나 입력해주세요.")
        else:
            st.markdown("""
        ### 🎯 사용 방법
        
        1. **왼쪽 사이드바**에서 분석할 주식을 선택하거나 직접 입력하세요
        2. **분석 기간**을 선택하세요 (1개월~5년)
        3. **🚀 분석 시작** 버튼을 클릭하세요
        
        ### 📈 제공되는 분석
        
        - **기본 정보**: 현재가, 변화율, 회사 정보
        - **기술적 지표**: RSI, MACD, 볼린저 밴드, 이동평균선
        - **추세 분석**: 단기/중기/장기 추세 및 강도
        - **변동성 분석**: 연간 변동성 및 위험도
        - **거래량 분석**: 거래량 패턴 및 해석
        
        ### 💡 팁
        
        - 미국 주식: `AAPL`, `MSFT`, `GOOGL` 등
        - 한국 주식: `005930.KS` (삼성전자), `000660.KS` (SK하이닉스) 등
        - 실시간 데이터는 Yahoo Finance API를 사용합니다
        """)


def get_all_popular_tickers():
    """모든 인기 주식 티커 목록을 반환합니다."""
    all_tickers = []
    popular_stocks = get_popular_stocks()
    for sector_stocks in popular_stocks.values():
        all_tickers.extend(list(sector_stocks.keys()))
    return sorted(list(set(all_tickers)))  # 중복 제거 및 정렬


def display_strategy_recommendations(recommendation_result: dict, top_n: int):
    """전략 추천 결과를 표시합니다."""
    
    # 티커 정보 추출
    ticker = recommendation_result.get('ticker', '')
    is_korean_stock = ticker.endswith('.KS')
    
    # 기본 정보
    st.subheader(f"📊 {ticker} 분석 결과")
    
    # 종목 프로필
    stock_profile = recommendation_result.get('stock_profile', {})
    if stock_profile:
        st.markdown("### 📈 종목 프로필")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("시장 상황", stock_profile.get('market_condition', 'N/A'))
        with col2:
            st.metric("변동성 수준", stock_profile.get('volatility_level', 'N/A'))
        with col3:
            volatility = stock_profile.get('volatility', 0)
            st.metric("연간 변동성", f"{volatility:.1%}")
        with col4:
            price_change = stock_profile.get('price_change', 0)
            st.metric("수익률", f"{price_change:.1f}%")
    
    # 단일 전략 추천
    single_strategies = recommendation_result.get('single_strategies', [])
    if single_strategies:
        st.markdown("### 🏆 추천 단일 전략")
        
        for i, strategy in enumerate(single_strategies[:top_n], 1):
            with st.expander(f"{i}등: {strategy['name']} (예상 CAGR: {strategy['cagr']:.1f}%)", expanded=(i==1)):
                # 성과 지표
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("연 수익률 (CAGR)", f"{strategy['cagr']:.1f}%")
                with col2:
                    st.metric("샤프 비율", f"{strategy['sharpe']:.2f}")
                with col3:
                    st.metric("최대 낙폭", f"{abs(strategy['max_drawdown']):.1f}%")
                with col4:
                    st.metric("승률", f"{strategy['win_rate']:.1f}%")
                
                # 가격 목표 정보
                price_targets = strategy.get('price_targets', {})
                if price_targets:
                    st.markdown("#### 💰 가격 목표 정보")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        current_price = price_targets.get('current_price', 0)
                        price_format = f"₩{current_price:,.0f}" if is_korean_stock else f"${current_price:.2f}"
                        st.metric(
                            "📊 현재가", 
                            price_format,
                            help="분석 기준 현재 주가"
                        )
                    with col2:
                        entry_price = price_targets.get('entry_price', 0)
                        entry_discount = price_targets.get('entry_discount_rate', 0)
                        price_format = f"₩{entry_price:,.0f}" if is_korean_stock else f"${entry_price:.2f}"
                        st.metric(
                            "📥 매수가 (진입가)", 
                            price_format,
                            delta=f"-{entry_discount:.1f}%",
                            help="전략 리스크를 고려한 권장 매수가격"
                        )
                    with col3:
                        target_price = price_targets.get('target_price', 0)
                        target_gain = price_targets.get('target_gain_rate', 0)
                        price_format = f"₩{target_price:,.0f}" if is_korean_stock else f"${target_price:.2f}"
                        st.metric(
                            "🎯 매도가 (목표가)", 
                            price_format,
                            delta=f"+{target_gain:.1f}%",
                            help="예상 수익률을 적용한 목표 매도가격"
                        )
                    with col4:
                        stop_loss_price = price_targets.get('stop_loss_price', 0)
                        risk_reward_ratio = price_targets.get('risk_reward_ratio', 0)
                        
                        price_format = f"₩{stop_loss_price:,.0f}" if is_korean_stock else f"${stop_loss_price:.2f}"
                        
                        st.metric(
                            "⛔ 손절가", 
                            price_format,
                            help=f"리스크/리워드 비율: {risk_reward_ratio:.2f}"
                        )
                
                st.markdown(f"**추천 이유:** {strategy['reason']}")
                
                # 적합성 점수 시각화
                compatibility = strategy.get('compatibility_score', 0)
                st.progress(compatibility, text=f"종목 적합도: {compatibility:.1%}")
    
    # 조합 전략 추천
    combination_strategies = recommendation_result.get('combination_strategies', [])
    if combination_strategies:
        st.markdown("### 🔄 추천 조합 전략")
        
        for i, combo in enumerate(combination_strategies, 1):
            strategy_names = ' + '.join(combo['strategies'])
            with st.expander(f"조합 {i}: {strategy_names} (예상 CAGR: {combo['cagr']:.1f}%)", expanded=(i==1)):
                # 성과 지표
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("연 수익률 (CAGR)", f"{combo['cagr']:.1f}%")
                with col2:
                    st.metric("샤프 비율", f"{combo['sharpe']:.2f}")
                with col3:
                    st.metric("최대 낙폭", f"{abs(combo['max_drawdown']):.1f}%")
                with col4:
                    st.metric("총 거래 수", f"{combo['total_trades']}")
                
                # 가격 목표 정보
                price_targets = combo.get('price_targets', {})
                if price_targets:
                    st.markdown("#### 💰 가격 목표 정보")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        current_price = price_targets.get('current_price', 0)
                        price_format = f"₩{current_price:,.0f}" if is_korean_stock else f"${current_price:.2f}"
                        st.metric(
                            "📊 현재가", 
                            price_format,
                            help="분석 기준 현재 주가"
                        )
                    with col2:
                        entry_price = price_targets.get('entry_price', 0)
                        entry_discount = price_targets.get('entry_discount_rate', 0)
                        price_format = f"₩{entry_price:,.0f}" if is_korean_stock else f"${entry_price:.2f}"
                        st.metric(
                            "📥 매수가 (진입가)", 
                            price_format,
                            delta=f"-{entry_discount:.1f}%",
                            help="조합 전략 리스크를 고려한 권장 매수가격"
                        )
                    with col3:
                        target_price = price_targets.get('target_price', 0)
                        target_gain = price_targets.get('target_gain_rate', 0)
                        
                        price_format = f"₩{target_price:,.0f}" if is_korean_stock else f"${target_price:.2f}"
                        
                        st.metric(
                            "🎯 매도가 (목표가)", 
                            price_format,
                            delta=f"+{target_gain:.1f}%",
                            help="예상 수익률을 적용한 목표 매도가격"
                        )
                    with col4:
                        stop_loss_price = price_targets.get('stop_loss_price', 0)
                        risk_reward_ratio = price_targets.get('risk_reward_ratio', 0)
                        
                        price_format = f"₩{stop_loss_price:,.0f}" if is_korean_stock else f"${stop_loss_price:.2f}"
                        
                        st.metric(
                            "⛔ 손절가", 
                            price_format,
                            help=f"리스크/리워드 비율: {risk_reward_ratio:.2f}"
                        )
                
                st.markdown(f"**조합 근거:** {combo['reason']}")
                
                # 가중치 표시
                weights_text = " / ".join([f"{name}: {weight:.0%}" for name, weight in zip(combo['strategies'], combo['weights'])])
                st.info(f"💡 **비중:** {weights_text}")
    
    # 투자 가이드
    st.markdown("### 💡 투자 가이드")
    
    market_guide = recommendation_result.get('market_guide', {})
    if market_guide:
        with st.expander("📊 현재 시장 상황 기반 가이드", expanded=True):
            st.markdown(f"**현재 상황:** {market_guide.get('current_situation', '')}")
            st.markdown(f"**추천 접근법:** {market_guide.get('recommended_approach', '')}")
            st.warning(f"**주의사항:** {market_guide.get('caution_points', '')}")
    
    risk_guide = recommendation_result.get('risk_guide', {})
    if risk_guide:
        with st.expander("⚠️ 위험 관리 가이드", expanded=True):
            st.markdown(f"**포지션 크기:** {risk_guide.get('position_sizing', '')}")
            st.markdown(f"**손절 수준:** {risk_guide.get('stop_loss_level', '')}")
            st.markdown(f"**분산 투자:** {risk_guide.get('diversification', '')}")
            st.markdown(f"**모니터링:** {risk_guide.get('monitoring', '')}")
    
    period_guide = recommendation_result.get('period_guide', {})
    if period_guide:
        with st.expander("⏰ 투자 기간별 추천", expanded=True):
            for period, guide in period_guide.items():
                st.markdown(f"**{period}:** {guide}")
    
    # 종합 추천 의견
    overall_recommendation = recommendation_result.get('overall_recommendation', '')
    if overall_recommendation:
        st.markdown("### 🎯 종합 추천 의견")
        st.info(overall_recommendation)


if __name__ == "__main__":
    main() 