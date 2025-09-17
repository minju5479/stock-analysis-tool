#!/usr/bin/env python3
"""
전략 추천 시스템
과거 데이터를 기반으로 최적의 투자 전략을 추천하는 시스템
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import asyncio
from datetime import datetime, timedelta

from src.core.data import StockDataFetcher, DataProcessor, PointInTimeFinancialData
from src.core.strategy.rule_based import RuleBasedStrategy
from src.core.strategy.momentum import MomentumStrategy
from src.core.strategy.mean_reversion import MeanReversionStrategy
from src.core.strategy.pattern import PatternStrategy
from src.core.strategy.quantitative_factor import QuantitativeFactorStrategy
from src.core.strategy.machine_learning import MachineLearningStrategy
from src.core.strategy.market_regime import MarketRegimeStrategy
from src.core.strategy.multi_timeframe import MultiTimeframeStrategy
from src.core.strategy.statistical_arbitrage import StatisticalArbitrageStrategy
from src.core.strategy.volume_profile import VolumeProfileStrategy
from src.core.strategy.sentiment_analysis import SentimentAnalysisStrategy
from src.core.backtest.engine import BacktestEngine
from src.core.backtest.metrics import compute_metrics


class StrategyRecommendationEngine:
    """전략 추천 엔진"""
    
    def __init__(self):
        self.strategies = {
            'quantitative_factor': QuantitativeFactorStrategy,
            'machine_learning': MachineLearningStrategy,
            'market_regime': MarketRegimeStrategy,
            'rule_based': RuleBasedStrategy,
            'momentum': MomentumStrategy,
            'mean_reversion': MeanReversionStrategy,
            'pattern': PatternStrategy,
            'multi_timeframe': MultiTimeframeStrategy,
            'statistical_arbitrage': StatisticalArbitrageStrategy,
            'volume_profile': VolumeProfileStrategy,
            'sentiment_analysis': SentimentAnalysisStrategy
        }
        
        # Point-in-Time 재무데이터 소스 초기화
        self.financial_data = PointInTimeFinancialData()
        
        self.strategy_names = {
            'quantitative_factor': '🏆 Quantitative Factor (1위 전략)',
            'machine_learning': '🤖 Machine Learning (2위 전략)',
            'market_regime': '📊 Market Regime (3위 전략)',
            'rule_based': '📏 Rule-Based',
            'momentum': '🚀 Momentum',
            'mean_reversion': '🔄 Mean Reversion',
            'pattern': '🔍 Pattern Recognition',
            'multi_timeframe': '⏰ Multi-Timeframe',
            'statistical_arbitrage': '📈 Statistical Arbitrage',
            'volume_profile': '📊 Volume Profile',
            'sentiment_analysis': '💭 Sentiment Analysis',
            'options_strategy': '📋 Options Strategy',
            'crypto_arbitrage': '🪙 Crypto Arbitrage'
        }
        
        # 전략별 특성 정의
        self.strategy_characteristics = {
            'quantitative_factor': {
                'type': 'hybrid',
                'volatility': 'medium',
                'holding_period': 'medium',
                'market_condition': 'all',
                'risk_level': 'medium',
                'complexity': 'high'
            },
            'machine_learning': {
                'type': 'predictive',
                'volatility': 'medium',
                'holding_period': 'short',
                'market_condition': 'trending',
                'risk_level': 'medium',
                'complexity': 'very_high'
            },
            'market_regime': {
                'type': 'adaptive',
                'volatility': 'low',
                'holding_period': 'medium',
                'market_condition': 'all',
                'risk_level': 'low',
                'complexity': 'high'
            },
            'rule_based': {
                'type': 'technical',
                'volatility': 'medium',
                'holding_period': 'short',
                'market_condition': 'trending',
                'risk_level': 'medium',
                'complexity': 'low'
            },
            'momentum': {
                'type': 'technical',
                'volatility': 'high',
                'holding_period': 'short',
                'market_condition': 'trending',
                'risk_level': 'high',
                'complexity': 'medium'
            },
            'mean_reversion': {
                'type': 'technical',
                'volatility': 'medium',
                'holding_period': 'short',
                'market_condition': 'sideways',
                'risk_level': 'medium',
                'complexity': 'medium'
            },
            'pattern': {
                'type': 'technical',
                'volatility': 'high',
                'holding_period': 'medium',
                'market_condition': 'trending',
                'risk_level': 'high',
                'complexity': 'high'
            },
            'multi_timeframe': {
                'type': 'technical',
                'volatility': 'low',
                'holding_period': 'long',
                'market_condition': 'trending',
                'risk_level': 'low',
                'complexity': 'high'
            },
            'statistical_arbitrage': {
                'type': 'quantitative',
                'volatility': 'low',
                'holding_period': 'short',
                'market_condition': 'sideways',
                'risk_level': 'low',
                'complexity': 'very_high'
            },
            'volume_profile': {
                'type': 'technical',
                'volatility': 'medium',
                'holding_period': 'medium',
                'market_condition': 'all',
                'risk_level': 'medium',
                'complexity': 'high'
            },
            'sentiment_analysis': {
                'type': 'fundamental',
                'volatility': 'high',
                'holding_period': 'short',
                'market_condition': 'volatile',
                'risk_level': 'high',
                'complexity': 'medium'
            },
            'options_strategy': {
                'type': 'derivatives',
                'volatility': 'very_high',
                'holding_period': 'short',
                'market_condition': 'volatile',
                'risk_level': 'very_high',
                'complexity': 'very_high'
            },
            'crypto_arbitrage': {
                'type': 'arbitrage',
                'volatility': 'very_high',
                'holding_period': 'very_short',
                'market_condition': 'volatile',
                'risk_level': 'very_high',
                'complexity': 'high'
            }
        }

    async def analyze_stock_profile(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        """종목 프로필 분석"""
        try:
            # 데이터 수집
            fetcher = StockDataFetcher()
            processor = DataProcessor()
            
            # 가격 데이터 가져오기
            stock_data = await fetcher.get_stock_data(ticker, period)
            if stock_data is None or stock_data.empty:
                return {"error": "데이터를 가져올 수 없습니다"}
            
            # 데이터 전처리
            processed_data = self._preprocess_data(stock_data)
            
            # 기본 통계 계산
            returns = processed_data['Daily_Return'].dropna()
            
            # 시장 상태 분석
            market_condition = self._analyze_market_condition(processed_data)
            
            # 변동성 분석
            volatility = returns.std() * np.sqrt(252)  # 연간화
            
            # 추세 강도 분석
            trend_strength = self._calculate_trend_strength(processed_data)
            
            # 거래량 패턴 분석
            volume_pattern = self._analyze_volume_pattern(processed_data)
            
            # 가격 모멘텀 분석
            momentum_score = self._calculate_momentum_score(processed_data)
            
            return {
                'ticker': ticker,
                'period': period,
                'market_condition': market_condition,
                'volatility': volatility,
                'volatility_level': self._categorize_volatility(volatility),
                'trend_strength': trend_strength,
                'volume_pattern': volume_pattern,
                'momentum_score': momentum_score,
                'data_points': len(processed_data),
                'latest_price': processed_data['Close'].iloc[-1],
                'price_change': ((processed_data['Close'].iloc[-1] / processed_data['Close'].iloc[0]) - 1) * 100
            }
            
        except Exception as e:
            return {"error": f"분석 중 오류 발생: {str(e)}"}

    def _analyze_market_condition(self, data: pd.DataFrame) -> str:
        """시장 상태 분석"""
        try:
            # 20일, 50일 이동평균 계산
            ma20 = data['Close'].rolling(20).mean()
            ma50 = data['Close'].rolling(50).mean()
            
            # 최근 상태 확인
            recent_price = data['Close'].iloc[-10:].mean()
            recent_ma20 = ma20.iloc[-10:].mean()
            recent_ma50 = ma50.iloc[-10:].mean()
            
            # 추세 방향 확인
            if recent_price > recent_ma20 > recent_ma50:
                return "상승추세"
            elif recent_price < recent_ma20 < recent_ma50:
                return "하락추세"
            else:
                # 볼린저 밴드로 횡보 확인
                bb_width = (data['Close'].rolling(20).std() / data['Close'].rolling(20).mean()).iloc[-20:].mean()
                if bb_width < 0.02:  # 2% 미만이면 횡보
                    return "횡보장"
                else:
                    return "변동성장"
                    
        except:
            return "분석불가"

    def _calculate_trend_strength(self, data: pd.DataFrame) -> float:
        """추세 강도 계산 (0-1 사이 값)"""
        try:
            # ADX와 유사한 개념으로 추세 강도 계산
            high = data['High']
            low = data['Low']
            close = data['Close']
            
            # True Range 계산
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # 방향성 이동 계산
            up_move = high - high.shift(1)
            down_move = low.shift(1) - low
            
            # 양/음 방향성 이동
            plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0), index=data.index)
            minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0), index=data.index)
            
            # 14일 평균
            atr = tr.rolling(14).mean()
            plus_di = (plus_dm.rolling(14).mean() / atr) * 100
            minus_di = (minus_dm.rolling(14).mean() / atr) * 100
            
            # ADX 계산
            dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
            adx = dx.rolling(14).mean()
            
            # 0-1 사이로 정규화
            latest_adx = adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 25
            return min(max(latest_adx / 100, 0), 1)
            
        except:
            return 0.5

    def _analyze_volume_pattern(self, data: pd.DataFrame) -> str:
        """거래량 패턴 분석"""
        try:
            volume = data['Volume']
            recent_volume = volume.iloc[-20:].mean()
            avg_volume = volume.mean()
            
            volume_ratio = recent_volume / avg_volume
            
            if volume_ratio > 1.5:
                return "고거래량"
            elif volume_ratio < 0.7:
                return "저거래량"
            else:
                return "보통거래량"
                
        except:
            return "분석불가"

    def _calculate_momentum_score(self, data: pd.DataFrame) -> float:
        """모멘텀 점수 계산 (0-1 사이 값)"""
        try:
            # 다양한 기간의 수익률
            returns_1w = (data['Close'].iloc[-1] / data['Close'].iloc[-7] - 1) if len(data) >= 7 else 0
            returns_1m = (data['Close'].iloc[-1] / data['Close'].iloc[-21] - 1) if len(data) >= 21 else 0
            returns_3m = (data['Close'].iloc[-1] / data['Close'].iloc[-63] - 1) if len(data) >= 63 else 0
            
            # 가중 평균 (최근 기간에 더 높은 가중치)
            momentum = (returns_1w * 0.5 + returns_1m * 0.3 + returns_3m * 0.2)
            
            # -1에서 1 사이를 0에서 1 사이로 변환
            return max(min((momentum + 1) / 2, 1), 0)
            
        except:
            return 0.5

    def _categorize_volatility(self, volatility: float) -> str:
        """변동성 수준 분류"""
        if volatility < 0.15:
            return "낮음"
        elif volatility < 0.25:
            return "보통"
        elif volatility < 0.40:
            return "높음"
        else:
            return "매우높음"

    async def recommend_single_strategies(self, ticker: str, period: str = "1y", top_n: int = 5) -> List[Dict[str, Any]]:
        """단일 전략 추천"""
        try:
            # 종목 프로필 분석
            stock_profile = await self.analyze_stock_profile(ticker, period)
            if "error" in stock_profile:
                return []
            
            # 현재 주가 가져오기
            current_price = await self._get_current_price(ticker)
            
            # 각 전략 테스트
            strategy_results = []
            
            for strategy_key, strategy_class in self.strategies.items():
                try:
                    # 백테스트 실행
                    result = await self._test_strategy(ticker, period, strategy_class)
                    if result and "cagr" in result:
                        # 종목 프로필과의 적합성 점수 계산
                        compatibility_score = self._calculate_compatibility_score(
                            stock_profile, self.strategy_characteristics[strategy_key]
                        )
                        
                        # 종합 점수 (성과 50% + 적합성 50%)
                        performance_score = min(max(result.get("cagr", 0) / 30, 0), 1)  # CAGR 30%를 1.0으로 정규화
                        total_score = (performance_score * 0.5 + compatibility_score * 0.5)
                        
                        # 가격 목표 계산
                        risk_level = self.strategy_characteristics[strategy_key].get('risk_level', 'medium')
                        price_targets = self._calculate_price_targets(result, current_price, risk_level)
                        
                        strategy_results.append({
                            'strategy': strategy_key,
                            'name': self.strategy_names[strategy_key],
                            'cagr': result.get("cagr", 0),
                            'sharpe': result.get("sharpe_ratio", 0),
                            'max_drawdown': result.get("max_drawdown", 0),
                            'win_rate': result.get("win_rate", 0),
                            'total_trades': result.get("total_trades", 0),
                            'compatibility_score': compatibility_score,
                            'total_score': total_score,
                            'reason': self._generate_strategy_reason(strategy_key, stock_profile, result),
                            'price_targets': price_targets
                        })
                        
                except Exception as e:
                    print(f"전략 {strategy_key} 테스트 중 오류: {e}")
                    continue
            
            # 점수순으로 정렬
            strategy_results.sort(key=lambda x: x['total_score'], reverse=True)
            
            return strategy_results[:top_n]
            
        except Exception as e:
            print(f"전략 추천 중 오류: {e}")
            return []

    async def _get_current_price(self, ticker: str) -> float:
        """현재 주가 가져오기"""
        try:
            fetcher = StockDataFetcher()
            # 최근 1일 데이터 가져오기
            data = await fetcher.get_stock_data(ticker, "1d")
            if data is not None and not data.empty:
                return float(data['Close'].iloc[-1])
            return 100.0  # 기본값
        except Exception as e:
            print(f"현재 주가 조회 중 오류: {e}")
            return 100.0  # 기본값

    async def recommend_combination_strategies(self, ticker: str, period: str = "1y", top_n: int = 3) -> List[Dict[str, Any]]:
        """조합 전략 추천"""
        try:
            # 단일 전략 결과 먼저 얻기
            single_results = await self.recommend_single_strategies(ticker, period, 8)
            if len(single_results) < 3:
                return []
            
            # 현재 주가 가져오기
            current_price = await self._get_current_price(ticker)
            
            # 상위 전략들로 조합 생성
            top_strategies = single_results[:6]
            combinations = []
            
            # 2개 조합
            for i in range(len(top_strategies)):
                for j in range(i+1, len(top_strategies)):
                    strategy1 = top_strategies[i]
                    strategy2 = top_strategies[j]
                    
                    # 전략 특성이 상호보완적인지 확인
                    if self._are_strategies_complementary(strategy1['strategy'], strategy2['strategy']):
                        combo_result = await self._test_combination_strategy(
                            ticker, period, [strategy1['strategy'], strategy2['strategy']], [0.5, 0.5]
                        )
                        
                        if combo_result and "cagr" in combo_result:
                            # 조합 전략의 평균 리스크 레벨 계산
                            risk_levels = [self.strategy_characteristics[strategy1['strategy']].get('risk_level', 'medium'),
                                         self.strategy_characteristics[strategy2['strategy']].get('risk_level', 'medium')]
                            avg_risk_level = self._calculate_average_risk_level(risk_levels)
                            
                            # 가격 목표 계산
                            price_targets = self._calculate_price_targets(combo_result, current_price, avg_risk_level)
                            
                            combinations.append({
                                'strategies': [strategy1['name'], strategy2['name']],
                                'strategy_keys': [strategy1['strategy'], strategy2['strategy']],
                                'weights': [0.5, 0.5],
                                'cagr': combo_result.get("cagr", 0),
                                'sharpe': combo_result.get("sharpe_ratio", 0),
                                'max_drawdown': combo_result.get("max_drawdown", 0),
                                'win_rate': combo_result.get("win_rate", 0),
                                'total_trades': combo_result.get("total_trades", 0),
                                'reason': self._generate_combination_reason(
                                    [strategy1['strategy'], strategy2['strategy']], combo_result
                                ),
                                'price_targets': price_targets
                            })
            
            # 3개 조합 (상위 3개만)
            if len(top_strategies) >= 3:
                strategy1, strategy2, strategy3 = top_strategies[0], top_strategies[1], top_strategies[2]
                combo_result = await self._test_combination_strategy(
                    ticker, period, 
                    [strategy1['strategy'], strategy2['strategy'], strategy3['strategy']], 
                    [0.4, 0.3, 0.3]
                )
                
                if combo_result and "cagr" in combo_result:
                    # 조합 전략의 평균 리스크 레벨 계산
                    risk_levels = [self.strategy_characteristics[strategy1['strategy']].get('risk_level', 'medium'),
                                 self.strategy_characteristics[strategy2['strategy']].get('risk_level', 'medium'),
                                 self.strategy_characteristics[strategy3['strategy']].get('risk_level', 'medium')]
                    avg_risk_level = self._calculate_average_risk_level(risk_levels)
                    
                    # 가격 목표 계산
                    price_targets = self._calculate_price_targets(combo_result, current_price, avg_risk_level)
                    
                    combinations.append({
                        'strategies': [strategy1['name'], strategy2['name'], strategy3['name']],
                        'strategy_keys': [strategy1['strategy'], strategy2['strategy'], strategy3['strategy']],
                        'weights': [0.4, 0.3, 0.3],
                        'cagr': combo_result.get("cagr", 0),
                        'sharpe': combo_result.get("sharpe_ratio", 0),
                        'max_drawdown': combo_result.get("max_drawdown", 0),
                        'win_rate': combo_result.get("win_rate", 0),
                        'total_trades': combo_result.get("total_trades", 0),
                        'reason': self._generate_combination_reason(
                            [strategy1['strategy'], strategy2['strategy'], strategy3['strategy']], combo_result
                        ),
                        'price_targets': price_targets
                    })
            
            # CAGR 기준으로 정렬
            combinations.sort(key=lambda x: x['cagr'], reverse=True)
            
            return combinations[:top_n]
            
        except Exception as e:
            print(f"조합 전략 추천 중 오류: {e}")
            return []

    def _calculate_compatibility_score(self, stock_profile: Dict, strategy_char: Dict) -> float:
        """종목과 전략의 적합성 점수 계산"""
        score = 0.0
        
        try:
            # 시장 상태와 전략 적합성
            market_condition = stock_profile.get('market_condition', '')
            strategy_market = strategy_char.get('market_condition', '')
            
            if strategy_market == 'all' or market_condition == strategy_market:
                score += 0.3
            elif (market_condition == '상승추세' or market_condition == '하락추세') and strategy_market == 'trending':
                score += 0.25
            elif market_condition == '횡보장' and strategy_market == 'sideways':
                score += 0.25
            elif market_condition == '변동성장' and strategy_market == 'volatile':
                score += 0.25
            
            # 변동성과 전략 적합성
            volatility_level = stock_profile.get('volatility_level', '')
            strategy_vol = strategy_char.get('volatility', '')
            
            volatility_match = {
                ('낮음', 'low'): 0.2,
                ('보통', 'medium'): 0.2,
                ('높음', 'high'): 0.2,
                ('매우높음', 'very_high'): 0.2,
                ('낮음', 'medium'): 0.15,
                ('보통', 'low'): 0.15,
                ('보통', 'high'): 0.15,
                ('높음', 'medium'): 0.15
            }
            
            score += volatility_match.get((volatility_level, strategy_vol), 0.1)
            
            # 추세 강도와 전략 적합성
            trend_strength = stock_profile.get('trend_strength', 0.5)
            if strategy_char.get('type') == 'technical' and trend_strength > 0.6:
                score += 0.2
            elif strategy_char.get('type') == 'quantitative' and trend_strength < 0.4:
                score += 0.2
            else:
                score += 0.1
            
            # 거래량과 전략 적합성
            volume_pattern = stock_profile.get('volume_pattern', '')
            if volume_pattern == '고거래량' and strategy_char.get('type') == 'technical':
                score += 0.15
            elif volume_pattern == '저거래량' and strategy_char.get('type') == 'quantitative':
                score += 0.15
            else:
                score += 0.1
            
            # 모멘텀과 전략 적합성
            momentum_score = stock_profile.get('momentum_score', 0.5)
            if momentum_score > 0.6 and strategy_char.get('type') in ['technical', 'predictive']:
                score += 0.15
            elif momentum_score < 0.4 and strategy_char.get('market_condition') in ['sideways', 'all']:
                score += 0.15
            else:
                score += 0.1
            
        except:
            score = 0.5  # 기본 점수
        
        return min(max(score, 0), 1)

    def _calculate_investment_amounts(self, metrics: Dict[str, Any], risk_level: str, base_amount: float = 1000000) -> Dict[str, Any]:
        """전략별 매수 추천 금액과 목표 금액 계산"""
        try:
            # 전략 성과 지표 추출
            cagr = metrics.get('cagr', 0) * 100  # 연평균 수익률
            max_dd = abs(metrics.get('max_drawdown', 0)) * 100  # 최대 낙폭
            sharpe = metrics.get('sharpe_ratio', 0)  # 샤프 비율
            win_rate = metrics.get('win_rate', 0) * 100  # 승률
            
            # 리스크 레벨에 따른 기본 투자 비율 설정
            risk_multiplier = {
                'very_low': 0.05,    # 5%
                'low': 0.10,         # 10%  
                'medium': 0.15,      # 15%
                'high': 0.20,        # 20%
                'very_high': 0.25    # 25%
            }.get(risk_level, 0.15)
            
            # 성과 기반 조정
            performance_multiplier = 1.0
            
            # CAGR 기반 조정 (10% 이상이면 증가)
            if cagr > 10:
                performance_multiplier *= (1 + (cagr - 10) / 100)
            elif cagr < 0:
                performance_multiplier *= 0.5  # 마이너스 수익률이면 절반
            
            # 최대 낙폭 기반 조정 (20% 이상이면 감소)
            if max_dd > 20:
                performance_multiplier *= (1 - (max_dd - 20) / 200)
            
            # 샤프 비율 기반 조정
            if sharpe > 1.0:
                performance_multiplier *= 1.2
            elif sharpe < 0.5:
                performance_multiplier *= 0.8
            
            # 승률 기반 조정
            if win_rate > 60:
                performance_multiplier *= 1.1
            elif win_rate < 40:
                performance_multiplier *= 0.9
            
            # 최종 투자 금액 계산
            recommended_amount = int(base_amount * risk_multiplier * performance_multiplier)
            
            # 목표 금액 계산 (1년 기준 예상 수익)
            expected_return = max(cagr / 100, 0.02)  # 최소 2% 수익률 가정
            target_amount = int(recommended_amount * (1 + expected_return))
            
            # 투자 기간 추천 (CAGR과 변동성 기반)
            if cagr > 15 and max_dd < 15:
                investment_period = "6개월 - 1년"
            elif cagr > 8:
                investment_period = "1년 - 2년"
            else:
                investment_period = "2년 이상"
            
            return {
                'recommended_amount': recommended_amount,
                'target_amount': target_amount,
                'expected_return_rate': expected_return * 100,
                'investment_period': investment_period,
                'risk_adjusted_score': performance_multiplier
            }
            
        except Exception as e:
            print(f"투자 금액 계산 중 오류: {e}")
            return {
                'recommended_amount': int(base_amount * 0.1),  # 기본 10%
                'target_amount': int(base_amount * 0.1 * 1.08),  # 8% 수익률 가정
                'expected_return_rate': 8.0,
                'investment_period': "1년",
                'risk_adjusted_score': 1.0
            }

    def _calculate_price_targets(self, metrics: Dict[str, Any], current_price: float, risk_level: str) -> Dict[str, Any]:
        """전략별 매수가(진입가)와 매도가(목표가) 계산"""
        try:
            # 전략 성과 지표 추출
            cagr = metrics.get('cagr', 0) * 100  # 연평균 수익률
            max_dd = abs(metrics.get('max_drawdown', 0)) * 100  # 최대 낙폭
            sharpe = metrics.get('sharpe_ratio', 0)  # 샤프 비율
            win_rate = metrics.get('win_rate', 0) * 100  # 승률
            
            # 리스크 레벨에 따른 진입 할인율 설정
            entry_discount = {
                'very_low': 0.02,    # 2% 할인
                'low': 0.03,         # 3% 할인
                'medium': 0.05,      # 5% 할인
                'high': 0.07,        # 7% 할인
                'very_high': 0.10    # 10% 할인
            }.get(risk_level, 0.05)
            
            # 성과에 따른 목표가 조정
            target_multiplier = 1.0
            
            # CAGR 기반 목표가 조정
            if cagr > 20:
                target_multiplier = 1.25  # 25% 상승 목표
            elif cagr > 15:
                target_multiplier = 1.20  # 20% 상승 목표
            elif cagr > 10:
                target_multiplier = 1.15  # 15% 상승 목표
            elif cagr > 5:
                target_multiplier = 1.10  # 10% 상승 목표
            else:
                target_multiplier = 1.08  # 8% 상승 목표
            
            # 샤프 비율이 높으면 목표가 상향 조정
            if sharpe > 1.5:
                target_multiplier *= 1.05
            elif sharpe < 0.5:
                target_multiplier *= 0.95
            
            # 승률이 높으면 목표가 상향 조정
            if win_rate > 70:
                target_multiplier *= 1.03
            elif win_rate < 40:
                target_multiplier *= 0.97
            
            # 최대 낙폭이 크면 보수적 접근
            if max_dd > 25:
                entry_discount += 0.02  # 추가 할인
                target_multiplier *= 0.95
            
            # 매수가(진입가) 계산
            entry_price = current_price * (1 - entry_discount)
            
            # 매도가(목표가) 계산
            target_price = current_price * target_multiplier
            
            # 손절가 계산 (진입가 기준 10-15% 하락)
            stop_loss_rate = {
                'very_low': 0.08,    # 8% 손절
                'low': 0.10,         # 10% 손절
                'medium': 0.12,      # 12% 손절
                'high': 0.15,        # 15% 손절
                'very_high': 0.18    # 18% 손절
            }.get(risk_level, 0.12)
            
            stop_loss_price = entry_price * (1 - stop_loss_rate)
            
            # 기대 수익률 계산
            expected_return = ((target_price - entry_price) / entry_price) * 100
            
            # 리스크/리워드 비율 계산
            risk_reward_ratio = (target_price - entry_price) / (entry_price - stop_loss_price)
            
            return {
                'current_price': current_price,
                'entry_price': entry_price,
                'target_price': target_price,
                'stop_loss_price': stop_loss_price,
                'expected_return': expected_return,
                'risk_reward_ratio': risk_reward_ratio,
                'entry_discount_rate': entry_discount * 100,
                'target_gain_rate': ((target_price - current_price) / current_price) * 100
            }
            
        except Exception as e:
            print(f"가격 목표 계산 중 오류: {e}")
            return {
                'current_price': current_price,
                'entry_price': current_price * 0.95,  # 5% 할인
                'target_price': current_price * 1.10,  # 10% 상승
                'stop_loss_price': current_price * 0.90,  # 10% 손절
                'expected_return': 10.0,
                'risk_reward_ratio': 2.0,
                'entry_discount_rate': 5.0,
                'target_gain_rate': 10.0
            }

    def _calculate_average_risk_level(self, risk_levels: List[str]) -> str:
        """여러 전략의 평균 리스크 레벨 계산"""
        risk_mapping = {
            'very_low': 1,
            'low': 2, 
            'medium': 3,
            'high': 4,
            'very_high': 5
        }
        
        reverse_mapping = {
            1: 'very_low',
            2: 'low',
            3: 'medium', 
            4: 'high',
            5: 'very_high'
        }
        
        # 평균 계산
        total = sum(risk_mapping.get(level, 3) for level in risk_levels)
        avg = round(total / len(risk_levels))
        
        return reverse_mapping.get(avg, 'medium')

    def _are_strategies_complementary(self, strategy1: str, strategy2: str) -> bool:
        """두 전략이 상호보완적인지 확인"""
        char1 = self.strategy_characteristics.get(strategy1, {})
        char2 = self.strategy_characteristics.get(strategy2, {})
        
        # 서로 다른 타입의 전략이면 보완적
        if char1.get('type') != char2.get('type'):
            return True
        
        # 서로 다른 시장 조건에 특화되어 있으면 보완적
        market1 = char1.get('market_condition')
        market2 = char2.get('market_condition')
        if market1 != market2 and 'all' not in [market1, market2]:
            return True
        
        # 서로 다른 보유 기간이면 보완적
        if char1.get('holding_period') != char2.get('holding_period'):
            return True
        
        return False

    async def _test_strategy(self, ticker: str, period: str, strategy_class) -> Dict[str, Any]:
        """개별 전략 테스트"""
        try:
            # 데이터 가져오기
            fetcher = StockDataFetcher()
            data = await fetcher.get_stock_data(ticker, period)
            if data is None or data.empty:
                return {}
            
            # 데이터 전처리 - 전략이 필요로 하는 컬럼 추가
            processed_data = self._preprocess_data(data)
            
            # 전략 초기화 및 백테스트
            strategy = strategy_class()
            
            # 전략에 종목 코드와 재무데이터 소스 설정
            strategy.set_ticker(ticker)
            strategy.set_financial_data_source(self.financial_data)
            
            backtest_engine = BacktestEngine(strategy)
            
            # 기본 파라미터로 백테스트
            results = backtest_engine.run_backtest(processed_data, initial_capital=100000)
            
            if results and 'trades' in results:
                # 백테스트 결과 로깅
                print(f"전략 결과 - 초기자본: {results.get('initial_capital', 0)}, 최종자본: {results.get('final_capital', 0)}, 거래수: {len(results.get('trades', []))}")
                
                metrics = compute_metrics(results, processed_data)
                
                # 메트릭스 로깅
                print(f"계산된 메트릭스: {metrics}")
                
                return metrics
            
            return {}
            
        except Exception as e:
            print(f"전략 테스트 중 오류: {e}")
            return {}

    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """전략이 필요로 하는 컬럼들을 추가하여 데이터 전처리"""
        processed_data = data.copy()
        
        # Daily_Return 컬럼 추가
        if 'Daily_Return' not in processed_data.columns:
            processed_data['Daily_Return'] = processed_data['Close'].pct_change()
        
        # Volatility 컬럼 추가 (20일 롤링 표준편차)
        if 'Volatility' not in processed_data.columns:
            processed_data['Volatility'] = processed_data['Daily_Return'].rolling(20, min_periods=1).std()
        
        return processed_data

    async def _test_combination_strategy(self, ticker: str, period: str, strategy_keys: List[str], weights: List[float]) -> Dict[str, Any]:
        """조합 전략 테스트"""
        try:
            # 각 전략별로 신호 생성
            fetcher = StockDataFetcher()
            data = await fetcher.get_stock_data(ticker, period)
            if data is None or data.empty:
                return {}
            
            # 데이터 전처리
            processed_data = self._preprocess_data(data)
            
            # 각 전략의 신호 수집
            strategy_signals = []
            for strategy_key in strategy_keys:
                strategy_class = self.strategies[strategy_key]
                strategy = strategy_class()
                
                # 전략에 종목 코드와 재무데이터 소스 설정
                strategy.set_ticker(ticker)
                strategy.set_financial_data_source(self.financial_data)
                
                signals = strategy.compute_signals(processed_data)
                strategy_signals.append(signals)
            
            # 가중 평균으로 조합 신호 생성
            combined_signals = self._combine_signals(strategy_signals, weights)
            
            # 조합 신호로 백테스트
            results = self._run_combined_backtest(processed_data, combined_signals, initial_capital=100000)
            
            if results and 'trades' in results:
                metrics = compute_metrics(results, processed_data)
                return metrics
            
            return {}
            
        except Exception as e:
            print(f"조합 전략 테스트 중 오류: {e}")
            return {}

    def _combine_signals(self, strategy_signals: List[pd.DataFrame], weights: List[float]) -> pd.Series:
        """여러 전략의 신호를 가중 평균으로 조합"""
        try:
            if not strategy_signals:
                return pd.Series()
            
            # 각 전략 결과에서 action 컬럼 추출하여 숫자로 변환
            numeric_signals = []
            common_index = None
            
            for signals_df in strategy_signals:
                if signals_df is None or signals_df.empty:
                    continue
                
                # action 컬럼이 있는지 확인
                if 'action' in signals_df.columns:
                    action_series = signals_df['action']
                else:
                    # action 컬럼이 없으면 기본값 사용
                    action_series = pd.Series('HOLD', index=signals_df.index)
                
                # 문자열 신호를 숫자로 변환 (BUY: 1, SELL: -1, HOLD: 0)
                numeric_signal = pd.Series(0, index=action_series.index)
                numeric_signal[action_series == 'BUY'] = 1
                numeric_signal[action_series == 'SELL'] = -1
                
                numeric_signals.append(numeric_signal)
                
                # 공통 인덱스 계산
                if common_index is None:
                    common_index = numeric_signal.index
                else:
                    common_index = common_index.intersection(numeric_signal.index)
            
            if not numeric_signals or common_index is None or len(common_index) == 0:
                return pd.Series()
            
            # 가중 평균 계산
            weighted_signals = pd.Series(0.0, index=common_index)
            
            for signals, weight in zip(numeric_signals, weights):
                aligned_signals = signals.reindex(common_index, fill_value=0)
                weighted_signals += aligned_signals * weight
            
            # 임계값 적용 (0.5 이상이면 1, -0.5 이하면 -1)
            final_signals = pd.Series(0, index=common_index)
            final_signals[weighted_signals >= 0.5] = 1
            final_signals[weighted_signals <= -0.5] = -1
            
            return final_signals
            
        except Exception as e:
            print(f"신호 조합 중 오류: {e}")
            return pd.Series()

    def _run_combined_backtest(self, data: pd.DataFrame, signals: pd.Series, initial_capital: float = 100000) -> Dict[str, Any]:
        """조합 신호로 백테스트 실행"""
        try:
            capital = initial_capital
            position = 0
            trades = []
            equity_curve = []
            
            for i, (date, signal) in enumerate(signals.items()):
                if date not in data.index:
                    continue
                
                current_price = data.loc[date, 'Close']
                
                # 매수 신호
                if signal == 1 and position == 0:
                    shares = capital // current_price
                    if shares > 0:
                        position = shares
                        capital = capital - (shares * current_price)
                        trades.append({
                            'date': date,
                            'action': 'buy',
                            'price': current_price,
                            'shares': shares
                        })
                
                # 매도 신호
                elif signal == -1 and position > 0:
                    capital = capital + (position * current_price)
                    trades.append({
                        'date': date,
                        'action': 'sell',
                        'price': current_price,
                        'shares': position
                    })
                    position = 0
                
                # 포트폴리오 가치 계산
                portfolio_value = capital + (position * current_price)
                equity_curve.append({
                    'date': date,
                    'equity': portfolio_value
                })
            
            # 마지막에 보유 포지션이 있으면 청산
            if position > 0 and not data.empty:
                final_price = data['Close'].iloc[-1]
                capital = capital + (position * final_price)
                trades.append({
                    'date': data.index[-1],
                    'action': 'sell',
                    'price': final_price,
                    'shares': position
                })
            
            return {
                'trades': trades,
                'equity_curve': equity_curve,
                'final_capital': capital,
                'initial_capital': initial_capital
            }
            
        except Exception as e:
            print(f"조합 백테스트 중 오류: {e}")
            return {}

    def _generate_strategy_reason(self, strategy_key: str, stock_profile: Dict, result: Dict) -> str:
        """전략 추천 근거 생성"""
        try:
            char = self.strategy_characteristics[strategy_key]
            market_condition = stock_profile.get('market_condition', '')
            volatility_level = stock_profile.get('volatility_level', '')
            
            reasons = []
            
            # 성과 기반 근거
            cagr = result.get('cagr', 0)
            if cagr > 15:
                reasons.append(f"연 수익률 {cagr:.1f}%로 우수한 성과")
            elif cagr > 5:
                reasons.append(f"연 수익률 {cagr:.1f}%로 양호한 성과")
            
            # 샤프 비율 기반 근거
            sharpe = result.get('sharpe_ratio', 0)
            if sharpe > 1.0:
                reasons.append(f"샤프 비율 {sharpe:.2f}로 위험 대비 수익률 우수")
            
            # 시장 상태 기반 근거
            if market_condition == '상승추세' and char.get('market_condition') in ['trending', 'all']:
                reasons.append("현재 상승추세와 전략이 잘 부합")
            elif market_condition == '하락추세' and char.get('market_condition') in ['trending', 'all']:
                reasons.append("하락추세에서도 효과적인 전략")
            elif market_condition == '횡보장' and char.get('market_condition') in ['sideways', 'all']:
                reasons.append("횡보장에 특화된 전략")
            
            # 변동성 기반 근거
            if volatility_level == '높음' and char.get('volatility') in ['high', 'medium']:
                reasons.append("높은 변동성 환경에 적합")
            elif volatility_level == '낮음' and char.get('volatility') in ['low', 'medium']:
                reasons.append("안정적인 변동성 환경에 최적")
            
            return ' / '.join(reasons) if reasons else "과거 데이터 기반 분석 결과"
            
        except:
            return "데이터 기반 전략 분석"

    def _generate_combination_reason(self, strategy_keys: List[str], result: Dict) -> str:
        """조합 전략 추천 근거 생성"""
        try:
            strategy_names = [self.strategy_names[key].replace('🏆 ', '').replace('🤖 ', '').replace('📊 ', '').replace(' (1위 전략)', '').replace(' (2위 전략)', '').replace(' (3위 전략)', '') for key in strategy_keys]
            
            reasons = []
            
            # 성과 기반 근거
            cagr = result.get('cagr', 0)
            if cagr > 20:
                reasons.append(f"조합 효과로 연 수익률 {cagr:.1f}% 달성")
            elif cagr > 10:
                reasons.append(f"다각화 효과로 연 수익률 {cagr:.1f}% 실현")
            
            # 위험 분산 효과
            max_dd = abs(result.get('max_drawdown', 0))
            if max_dd < 15:
                reasons.append(f"위험 분산으로 최대 낙폭 {max_dd:.1f}%로 제한")
            
            # 전략별 특성
            strategy_types = [self.strategy_characteristics[key].get('type', '') for key in strategy_keys]
            unique_types = list(set(strategy_types))
            
            if len(unique_types) > 1:
                reasons.append("서로 다른 유형의 전략으로 포트폴리오 안정성 증대")
            
            return f"{' + '.join(strategy_names)} 조합: {' / '.join(reasons)}" if reasons else "다중 전략 조합 효과"
            
        except:
            return "조합 전략 분석 결과"

    async def generate_investment_guide(self, ticker: str, period: str = "1y") -> Dict[str, Any]:
        """투자 가이드 생성"""
        try:
            # 종목 프로필 분석
            stock_profile = await self.analyze_stock_profile(ticker, period)
            if "error" in stock_profile:
                return {"error": stock_profile["error"]}
            
            # 단일 전략 추천
            single_strategies = await self.recommend_single_strategies(ticker, period, 5)
            
            # 조합 전략 추천
            combination_strategies = await self.recommend_combination_strategies(ticker, period, 3)
            
            # 현재 시장 상황 기반 가이드
            market_guide = self._generate_market_guide(stock_profile, single_strategies)
            
            # 위험 관리 가이드
            risk_guide = self._generate_risk_guide(stock_profile, single_strategies)
            
            # 투자 기간별 추천
            period_guide = self._generate_period_guide(single_strategies, combination_strategies)
            
            return {
                'ticker': ticker,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stock_profile': stock_profile,
                'single_strategies': single_strategies,
                'combination_strategies': combination_strategies,
                'market_guide': market_guide,
                'risk_guide': risk_guide,
                'period_guide': period_guide,
                'overall_recommendation': self._generate_overall_recommendation(
                    stock_profile, single_strategies, combination_strategies
                )
            }
            
        except Exception as e:
            return {"error": f"투자 가이드 생성 중 오류: {str(e)}"}

    def _generate_market_guide(self, stock_profile: Dict, strategies: List[Dict]) -> Dict[str, str]:
        """현재 시장 상황 기반 가이드"""
        market_condition = stock_profile.get('market_condition', '')
        volatility_level = stock_profile.get('volatility_level', '')
        
        guides = {
            'current_situation': f"현재 {market_condition} 상황, 변동성 수준 {volatility_level}",
            'recommended_approach': "",
            'caution_points': ""
        }
        
        if market_condition == '상승추세':
            guides['recommended_approach'] = "모멘텀 전략 또는 추세 추종 전략이 유리한 시점입니다. 기술적 분석 기반 전략을 우선 고려하세요."
            guides['caution_points'] = "과열 구간에서는 언제든 조정이 올 수 있으니 손절선을 명확히 설정하세요."
        elif market_condition == '하락추세':
            guides['recommended_approach'] = "평균회귀 전략이나 역추세 전략 고려. 단, 추가 하락 위험도 염두에 두세요."
            guides['caution_points'] = "하락추세에서는 손실을 최소화하는 것이 우선. 무리한 진입보다는 관망이 나을 수 있습니다."
        elif market_condition == '횡보장':
            guides['recommended_approach'] = "평균회귀 전략이나 변동성 활용 전략이 효과적. 레인지 트레이딩을 고려하세요."
            guides['caution_points'] = "횡보 구간에서는 거래 빈도가 높아질 수 있어 수수료 부담을 주의하세요."
        else:
            guides['recommended_approach'] = "변동성이 큰 시장에서는 적응형 전략이나 다각화 전략을 추천합니다."
            guides['caution_points'] = "예측하기 어려운 시장 상황이므로 리스크 관리를 더욱 철저히 하세요."
        
        return guides

    def _generate_risk_guide(self, stock_profile: Dict, strategies: List[Dict]) -> Dict[str, Any]:
        """위험 관리 가이드"""
        volatility = stock_profile.get('volatility', 0.2)
        
        # 포지션 사이즈 권장
        if volatility < 0.15:
            position_size = "보수적: 포트폴리오의 15-25%"
        elif volatility < 0.25:
            position_size = "적정: 포트폴리오의 10-20%"
        elif volatility < 0.40:
            position_size = "공격적: 포트폴리오의 5-15%"
        else:
            position_size = "매우 제한적: 포트폴리오의 3-10%"
        
        # 손절선 권장
        if volatility < 0.15:
            stop_loss = "5-8%"
        elif volatility < 0.25:
            stop_loss = "8-12%"
        elif volatility < 0.40:
            stop_loss = "12-18%"
        else:
            stop_loss = "18-25%"
        
        return {
            'position_sizing': position_size,
            'stop_loss_level': stop_loss,
            'diversification': "단일 종목 집중도를 낮추고 여러 전략을 조합하여 위험을 분산하세요",
            'monitoring': "변동성이 높은 종목은 더 자주 모니터링이 필요합니다"
        }

    def _generate_period_guide(self, single_strategies: List[Dict], combination_strategies: List[Dict]) -> Dict[str, str]:
        """투자 기간별 추천"""
        guides = {}
        
        # 단기 (1-3개월)
        short_term_strategies = [s for s in single_strategies if 
                               self.strategy_characteristics[s['strategy']]['holding_period'] in ['very_short', 'short']]
        if short_term_strategies:
            guides['단기 (1-3개월)'] = f"추천 전략: {short_term_strategies[0]['name']} - 빠른 수익 실현 가능성"
        
        # 중기 (3-12개월)
        medium_term_strategies = [s for s in single_strategies if 
                                self.strategy_characteristics[s['strategy']]['holding_period'] == 'medium']
        if medium_term_strategies:
            guides['중기 (3-12개월)'] = f"추천 전략: {medium_term_strategies[0]['name']} - 안정적 성장 추구"
        
        # 장기 (1년 이상)
        if combination_strategies:
            guides['장기 (1년 이상)'] = f"추천 조합: {' + '.join(combination_strategies[0]['strategies'])} - 위험 분산과 지속 성장"
        
        return guides

    def _generate_overall_recommendation(self, stock_profile: Dict, single_strategies: List[Dict], combination_strategies: List[Dict]) -> str:
        """전체적인 추천 의견"""
        if not single_strategies:
            return "분석 데이터가 부족하여 구체적인 추천을 제공하기 어렵습니다."
        
        best_single = single_strategies[0]
        market_condition = stock_profile.get('market_condition', '')
        
        recommendation = f"현재 {market_condition} 상황에서 {best_single['name']} 전략이 "
        recommendation += f"가장 적합합니다 (예상 연수익률: {best_single['cagr']:.1f}%). "
        
        if combination_strategies:
            best_combo = combination_strategies[0]
            recommendation += f"\n\n위험을 분산하고 싶다면 {' + '.join(best_combo['strategies'])} 조합을 고려해보세요 "
            recommendation += f"(예상 연수익률: {best_combo['cagr']:.1f}%)."
        
        recommendation += f"\n\n⚠️ 이 분석은 과거 데이터를 바탕으로 한 것이며, 실제 투자 시에는 "
        recommendation += "시장 상황 변화, 리스크 허용도, 투자 목적 등을 종합적으로 고려해야 합니다."
        
        return recommendation


# 전역 인스턴스 생성
recommendation_engine = StrategyRecommendationEngine()
