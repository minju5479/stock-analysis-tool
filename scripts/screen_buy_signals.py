#!/usr/bin/env python3
"""
국내 주요 종목 4가지 전략별 매수 신호 스크리닝
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_data(ticker, period="1y"):
    """주식 데이터 수집"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        return df
    except:
        return None

def calculate_rsi(prices, window=14):
    """RSI 계산"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(prices, window=20, num_std=2):
    """볼린저 밴드 계산"""
    rolling_mean = prices.rolling(window).mean()
    rolling_std = prices.rolling(window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return upper_band, lower_band, rolling_mean

def analyze_stock_signals(ticker_info):
    """개별 종목 신호 분석"""
    ticker, name = ticker_info
    df = get_data(ticker)
    
    if df is None or len(df) < 50:
        return None
    
    current_price = df['Close'].iloc[-1]
    
    # 각 전략별 신호 분석
    signals = {
        'ticker': ticker,
        'name': name,
        'current_price': current_price,
        'signals': {},
        'score': 0
    }
    
    # 1. Rule-Based 전략 (RSI 기반)
    try:
        rsi = calculate_rsi(df['Close'])
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < 35:  # 과매도
            signals['signals']['rule_based'] = 'BUY'
            signals['score'] += 2
        elif current_rsi > 65:  # 과매수
            signals['signals']['rule_based'] = 'SELL'
            signals['score'] -= 1
        else:
            signals['signals']['rule_based'] = 'HOLD'
            
        signals['rsi'] = current_rsi
    except:
        signals['signals']['rule_based'] = 'ERROR'
    
    # 2. Momentum 전략
    try:
        momentum_15d = df['Close'].pct_change(15).iloc[-1]
        volume_8d_avg = df['Volume'].rolling(8).mean().iloc[-1]
        current_volume = df['Volume'].iloc[-1]
        volume_surge = current_volume > volume_8d_avg * 1.5
        
        if momentum_15d > 0.02 and volume_surge:  # 2% 이상 + 볼륨 급증
            signals['signals']['momentum'] = 'BUY'
            signals['score'] += 2
        elif momentum_15d < -0.01:  # -1% 이하
            signals['signals']['momentum'] = 'SELL'
            signals['score'] -= 1
        else:
            signals['signals']['momentum'] = 'HOLD'
            
        signals['momentum_15d'] = momentum_15d
        signals['volume_surge'] = volume_surge
    except:
        signals['signals']['momentum'] = 'ERROR'
    
    # 3. Mean Reversion 전략
    try:
        upper_bb, lower_bb, middle_bb = calculate_bollinger_bands(df['Close'], 25, 2.2)
        rsi = calculate_rsi(df['Close'])
        current_rsi = rsi.iloc[-1]
        
        bb_position = (current_price - lower_bb.iloc[-1]) / (upper_bb.iloc[-1] - lower_bb.iloc[-1])
        
        if current_price <= lower_bb.iloc[-1] and current_rsi < 30:  # 하단 밴드 + 과매도
            signals['signals']['mean_reversion'] = 'BUY'
            signals['score'] += 2
        elif current_price >= upper_bb.iloc[-1] and current_rsi > 70:  # 상단 밴드 + 과매수
            signals['signals']['mean_reversion'] = 'SELL'
            signals['score'] -= 1
        else:
            signals['signals']['mean_reversion'] = 'HOLD'
            
        signals['bb_position'] = bb_position * 100
    except:
        signals['signals']['mean_reversion'] = 'ERROR'
    
    # 4. Pattern 전략
    try:
        rolling_max_22d = df['High'].rolling(22).max()
        rolling_min_22d = df['Low'].rolling(22).min()
        volume_11d_avg = df['Volume'].rolling(11).mean().iloc[-1]
        current_volume = df['Volume'].iloc[-1]
        volume_surge = current_volume > volume_11d_avg * 1.5
        
        resistance = rolling_max_22d.iloc[-2]  # 전일 기준
        support = rolling_min_22d.iloc[-2]
        
        resistance_breakout = current_price > resistance * 1.011  # 1.1% 돌파
        support_breakdown = current_price < support * 0.989
        
        if resistance_breakout and volume_surge:
            signals['signals']['pattern'] = 'BUY'
            signals['score'] += 2
        elif support_breakdown:
            signals['signals']['pattern'] = 'SELL'
            signals['score'] -= 1
        else:
            signals['signals']['pattern'] = 'HOLD'
            
        signals['resistance'] = resistance
        signals['support'] = support
        signals['pattern_position'] = (current_price - support) / (resistance - support) * 100 if resistance != support else 50
    except:
        signals['signals']['pattern'] = 'ERROR'
    
    return signals

def screen_korean_stocks():
    """한국 주요 종목 스크리닝"""
    
    # 국내 주요 종목들 (코스피 200 주요 종목)
    korean_stocks = [
        # 대형주
        ('005930.KS', '삼성전자'),
        ('000660.KS', 'SK하이닉스'),
        ('035420.KS', 'NAVER'),
        ('051910.KS', 'LG화학'),
        ('006400.KS', '삼성SDI'),
        ('035720.KS', '카카오'),
        ('028260.KS', '삼성물산'),
        ('066570.KS', 'LG전자'),
        ('003670.KS', '포스코홀딩스'),
        ('096770.KS', 'SK이노베이션'),
        
        # 금융주
        ('055550.KS', '신한지주'),
        ('086790.KS', '하나금융지주'),
        ('316140.KS', '우리금융지주'),
        ('105560.KS', 'KB금융'),
        ('323410.KS', 'KG스틸'),
        
        # 바이오/제약
        ('068270.KS', '셀트리온'),
        ('196170.KS', '셀트리온헬스케어'),
        ('207940.KS', '삼성바이오로직스'),
        ('326030.KS', 'SK바이오팜'),
        ('000100.KS', '유한양행'),
        
        # 화학/소재
        ('051900.KS', 'LG생활건강'),
        ('010950.KS', 'S-Oil'),
        ('011170.KS', '롯데케미칼'),
        ('034730.KS', 'SK'),
        ('018260.KS', '삼성에스디에스'),
        
        # 건설/부동산
        ('000720.KS', '현대건설'),
        ('012330.KS', '현대모비스'),
        ('009150.KS', '삼성전기'),
        ('017670.KS', 'SK텔레콤'),
        ('030200.KS', 'KT'),
        
        # 유통/소비재
        ('139480.KS', '이마트'),
        ('004170.KS', '신세계'),
        ('161390.KS', '한국타이어앤테크놀로지'),
        ('011780.KS', '금호석유'),
        ('028670.KS', '팬오션'),
        
        # 자동차
        ('005380.KS', '현대차'),
        ('000270.KS', '기아'),
        ('012330.KS', '현대모비스'),
        
        # 조선/중공업  
        ('009540.KS', 'HD한국조선해양'),
        ('010140.KS', '삼성중공업'),
        
        # 항공/운송
        ('003490.KS', '대한항공'),
        ('047810.KS', '한국항공우주'),
        
        # 에너지
        ('015760.KS', '한국전력'),
        ('036460.KS', 'S&T중공업'),
        
        # IT/게임
        ('251270.KS', ' 넷마블'),
        ('112040.KS', '위메이드'),
        ('263750.KS', '펄어비스'),
    ]
    
    print("🔍 국내 주요 종목 매수 신호 스크리닝")
    print("=" * 80)
    print(f"📊 분석 대상: {len(korean_stocks)}개 종목")
    print("📅 분석 기준일:", datetime.now().strftime('%Y-%m-%d'))
    print()
    
    results = []
    
    for i, stock_info in enumerate(korean_stocks, 1):
        ticker, name = stock_info
        print(f"📈 ({i:2d}/{len(korean_stocks)}) {name}({ticker}) 분석 중...", end=" ")
        
        try:
            result = analyze_stock_signals(stock_info)
            if result:
                results.append(result)
                print("✅")
            else:
                print("❌ (데이터 없음)")
        except Exception as e:
            print(f"❌ (오류: {str(e)[:20]})")
    
    print("\n" + "=" * 80)
    
    # 결과 정렬 (점수 높은 순)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 매수 추천 종목 (점수 3점 이상)
    buy_recommendations = [r for r in results if r['score'] >= 3]
    
    print(f"\n🎯 매수 추천 종목 ({len(buy_recommendations)}개)")
    print("-" * 50)
    
    if buy_recommendations:
        for i, stock in enumerate(buy_recommendations, 1):
            print(f"{i:2d}. {stock['name']}({stock['ticker']})")
            print(f"    💰 현재가: {stock['current_price']:,.0f}원")
            print(f"    🎯 종합점수: {stock['score']}점")
            
            # 신호 상태 표시
            signals_str = []
            for strategy, signal in stock['signals'].items():
                emoji = "✅" if signal == "BUY" else "❌" if signal == "SELL" else "⏸️"
                signals_str.append(f"{emoji}{strategy}")
            print(f"    📊 신호: {' | '.join(signals_str)}")
            
            # 추가 정보
            if 'rsi' in stock:
                print(f"    📈 RSI: {stock['rsi']:.1f}")
            if 'momentum_15d' in stock:
                print(f"    🚀 15일 모멘텀: {stock['momentum_15d']:.1%}")
            if 'bb_position' in stock:
                print(f"    📊 BB 위치: {stock['bb_position']:.1f}%")
            if 'pattern_position' in stock:
                print(f"    🎪 패턴 위치: {stock['pattern_position']:.1f}%")
            print()
    else:
        print("❌ 현재 매수 추천할 만한 종목이 없습니다.")
    
    # 관심 종목 (점수 1-2점)
    watch_list = [r for r in results if 1 <= r['score'] <= 2]
    
    if watch_list:
        print(f"\n👀 관심 종목 ({len(watch_list)}개)")
        print("-" * 30)
        
        for i, stock in enumerate(watch_list[:10], 1):  # 상위 10개만
            signals_str = []
            buy_count = sum(1 for s in stock['signals'].values() if s == "BUY")
            print(f"{i:2d}. {stock['name']}({stock['ticker']}) - {stock['score']}점 (매수신호 {buy_count}개)")
    
    # 매도 고려 종목 (점수 -2점 이하)
    sell_list = [r for r in results if r['score'] <= -2]
    
    if sell_list:
        print(f"\n⚠️  매도 고려 종목 ({len(sell_list)}개)")
        print("-" * 30)
        
        for i, stock in enumerate(sell_list, 1):
            sell_count = sum(1 for s in stock['signals'].values() if s == "SELL")
            print(f"{i:2d}. {stock['name']}({stock['ticker']}) - {stock['score']}점 (매도신호 {sell_count}개)")
    
    print(f"\n💡 분석 완료: 총 {len(results)}개 종목 분석")
    print(f"   🟢 매수 추천: {len(buy_recommendations)}개")
    print(f"   🟡 관심 종목: {len(watch_list)}개") 
    print(f"   🔴 매도 고려: {len(sell_list)}개")
    
    print(f"\n📋 투자 가이드라인:")
    print(f"   • 3점 이상: 적극 매수 고려")
    print(f"   • 1-2점: 관심 있게 지켜보기") 
    print(f"   • 0점: 중립")
    print(f"   • -1점 이하: 매도 또는 관망")
    
    return results

if __name__ == "__main__":
    screen_korean_stocks()
