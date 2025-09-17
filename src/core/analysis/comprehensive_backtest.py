"""
종합 백테스트 시스템
섹터별 종목에 대해 다양한 전략과 파라미터로 백테스트를 수행
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import json
import os
import sys
import asyncio
from concurrent.futures import ThreadPoolExecutor
import itertools
import time

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.core.data import StockDataFetcher, DataProcessor
from src.core.strategy.rule_based import RuleBasedStrategy
from src.core.strategy.momentum import MomentumStrategy
from src.core.strategy.mean_reversion import MeanReversionStrategy
from src.core.strategy.pattern import PatternStrategy
# 새로운 고급 전략들
from src.core.strategy.multi_timeframe import MultiTimeframeStrategy
from src.core.strategy.volume_profile import VolumeProfileStrategy
from src.core.strategy.market_regime import MarketRegimeStrategy
from src.core.strategy.statistical_arbitrage import StatisticalArbitrageStrategy
from src.core.strategy.machine_learning import MachineLearningStrategy
from src.core.strategy.sentiment_analysis import SentimentAnalysisStrategy
from src.core.strategy.quantitative_factor import QuantitativeFactorStrategy
from src.core.backtest.engine import BacktestEngine
from src.core.backtest.metrics import compute_metrics


class ComprehensiveBacktester:
    """종합 백테스트 시스템"""
    
    def __init__(self):
        self.fetcher = StockDataFetcher()
        self.processor = DataProcessor()
        self.backtest_engine = BacktestEngine()
        
        # 섹터별 대표 종목 (각 섹터당 3개)
        self.sector_stocks = {
            "🇺🇸 기술주": ["AAPL", "MSFT", "GOOGL"],
            "🇺🇸 소비재": ["AMZN", "WMT", "HD"],
            "🇺🇸 금융": ["JPM", "BAC", "WFC"],
            "🇺🇸 헬스케어": ["JNJ", "UNH", "PFE"],
            "🇺🇸 산업재": ["BA", "CAT", "GE"],
            "🇰🇷 대형주": ["005930.KS", "000660.KS", "035420.KS"],
            "🇰🇷 금융": ["323410.KS", "086790.KS", "105560.KS"],
            "🇰🇷 화학/소재": ["051910.KS", "096770.KS", "010950.KS"],
            "🇰🇷 바이오/제약": ["207940.KS", "068270.KS", "196170.KS"]
        }
        
        # 전략별 파라미터 조합 (각 10회)
        self.strategy_params = {
            "rule_based": [
                {"warmup": 20, "rsi_buy": 25, "rsi_sell": 75, "risk_rr": 1.5},
                {"warmup": 30, "rsi_buy": 30, "rsi_sell": 70, "risk_rr": 2.0},
                {"warmup": 40, "rsi_buy": 35, "rsi_sell": 65, "risk_rr": 2.5},
                {"warmup": 50, "rsi_buy": 20, "rsi_sell": 80, "risk_rr": 1.8},
                {"warmup": 60, "rsi_buy": 28, "rsi_sell": 72, "risk_rr": 2.2},
                {"warmup": 25, "rsi_buy": 32, "rsi_sell": 68, "risk_rr": 1.7},
                {"warmup": 35, "rsi_buy": 27, "rsi_sell": 73, "risk_rr": 2.3},
                {"warmup": 45, "rsi_buy": 33, "rsi_sell": 67, "risk_rr": 1.9},
                {"warmup": 55, "rsi_buy": 29, "rsi_sell": 71, "risk_rr": 2.1},
                {"warmup": 65, "rsi_buy": 31, "rsi_sell": 69, "risk_rr": 2.4}
            ],
            "momentum": [
                {"warmup": 20, "momentum_period": 10, "breakout_threshold": 0.015, "volume_sma": 5},
                {"warmup": 30, "momentum_period": 15, "breakout_threshold": 0.020, "volume_sma": 8},
                {"warmup": 40, "momentum_period": 20, "breakout_threshold": 0.025, "volume_sma": 10},
                {"warmup": 50, "momentum_period": 25, "breakout_threshold": 0.030, "volume_sma": 12},
                {"warmup": 25, "momentum_period": 12, "breakout_threshold": 0.018, "volume_sma": 6},
                {"warmup": 35, "momentum_period": 18, "breakout_threshold": 0.022, "volume_sma": 9},
                {"warmup": 45, "momentum_period": 22, "breakout_threshold": 0.028, "volume_sma": 11},
                {"warmup": 55, "momentum_period": 28, "breakout_threshold": 0.032, "volume_sma": 13},
                {"warmup": 60, "momentum_period": 30, "breakout_threshold": 0.035, "volume_sma": 15},
                {"warmup": 65, "momentum_period": 35, "breakout_threshold": 0.040, "volume_sma": 18}
            ],
            "mean_reversion": [
                {"warmup": 20, "bb_period": 15, "bb_std": 1.8, "rsi_oversold": 20, "rsi_overbought": 80},
                {"warmup": 30, "bb_period": 20, "bb_std": 2.0, "rsi_oversold": 25, "rsi_overbought": 75},
                {"warmup": 40, "bb_period": 25, "bb_std": 2.2, "rsi_oversold": 30, "rsi_overbought": 70},
                {"warmup": 50, "bb_period": 30, "bb_std": 2.5, "rsi_oversold": 18, "rsi_overbought": 82},
                {"warmup": 25, "bb_period": 18, "bb_std": 1.9, "rsi_oversold": 22, "rsi_overbought": 78},
                {"warmup": 35, "bb_period": 22, "bb_std": 2.1, "rsi_oversold": 27, "rsi_overbought": 73},
                {"warmup": 45, "bb_period": 28, "bb_std": 2.3, "rsi_oversold": 32, "rsi_overbought": 68},
                {"warmup": 55, "bb_period": 32, "bb_std": 2.4, "rsi_oversold": 15, "rsi_overbought": 85},
                {"warmup": 60, "bb_period": 35, "bb_std": 2.6, "rsi_oversold": 28, "rsi_overbought": 72},
                {"warmup": 65, "bb_period": 40, "bb_std": 2.8, "rsi_oversold": 35, "rsi_overbought": 65}
            ],
            "pattern": [
                {"warmup": 20, "pattern_window": 8, "support_resistance_window": 15, "breakout_threshold": 0.008},
                {"warmup": 30, "pattern_window": 10, "support_resistance_window": 20, "breakout_threshold": 0.010},
                {"warmup": 40, "pattern_window": 12, "support_resistance_window": 25, "breakout_threshold": 0.012},
                {"warmup": 50, "pattern_window": 15, "support_resistance_window": 30, "breakout_threshold": 0.015},
                {"warmup": 25, "pattern_window": 9, "support_resistance_window": 18, "breakout_threshold": 0.009},
                {"warmup": 35, "pattern_window": 11, "support_resistance_window": 22, "breakout_threshold": 0.011},
                {"warmup": 45, "pattern_window": 13, "support_resistance_window": 28, "breakout_threshold": 0.013},
                {"warmup": 55, "pattern_window": 16, "support_resistance_window": 32, "breakout_threshold": 0.016},
                {"warmup": 60, "pattern_window": 18, "support_resistance_window": 35, "breakout_threshold": 0.018},
                {"warmup": 65, "pattern_window": 20, "support_resistance_window": 40, "breakout_threshold": 0.020}
            ],
            # 새로운 고급 전략들
            "multi_timeframe": [
                {"warmup": 60, "ma_short": 5, "ma_medium": 20, "ma_long": 60, "atr_period": 14, "atr_multiplier": 2.0},
                {"warmup": 70, "ma_short": 8, "ma_medium": 25, "ma_long": 65, "atr_period": 10, "atr_multiplier": 1.8},
                {"warmup": 80, "ma_short": 10, "ma_medium": 30, "ma_long": 70, "atr_period": 20, "atr_multiplier": 2.2},
                {"warmup": 90, "ma_short": 7, "ma_medium": 22, "ma_long": 55, "atr_period": 12, "atr_multiplier": 1.5},
                {"warmup": 75, "ma_short": 6, "ma_medium": 18, "ma_long": 50, "atr_period": 16, "atr_multiplier": 2.5},
                {"warmup": 85, "ma_short": 9, "ma_medium": 28, "ma_long": 75, "atr_period": 18, "atr_multiplier": 1.7},
                {"warmup": 95, "ma_short": 12, "ma_medium": 32, "ma_long": 80, "atr_period": 24, "atr_multiplier": 2.3},
                {"warmup": 65, "ma_short": 4, "ma_medium": 15, "ma_long": 45, "atr_period": 8, "atr_multiplier": 1.9},
                {"warmup": 100, "ma_short": 15, "ma_medium": 35, "ma_long": 85, "atr_period": 28, "atr_multiplier": 2.1},
                {"warmup": 110, "ma_short": 20, "ma_medium": 40, "ma_long": 90, "atr_period": 30, "atr_multiplier": 2.4}
            ],
            "volume_profile": [
                {"warmup": 50, "lookback_period": 50, "price_bins": 20, "volume_ma_period": 20, "atr_period": 14},
                {"warmup": 60, "lookback_period": 60, "price_bins": 25, "volume_ma_period": 25, "atr_period": 10},
                {"warmup": 70, "lookback_period": 70, "price_bins": 30, "volume_ma_period": 30, "atr_period": 20},
                {"warmup": 80, "lookback_period": 80, "price_bins": 15, "volume_ma_period": 15, "atr_period": 12},
                {"warmup": 55, "lookback_period": 45, "price_bins": 18, "volume_ma_period": 18, "atr_period": 16},
                {"warmup": 65, "lookback_period": 65, "price_bins": 22, "volume_ma_period": 22, "atr_period": 18},
                {"warmup": 75, "lookback_period": 75, "price_bins": 28, "volume_ma_period": 28, "atr_period": 24},
                {"warmup": 85, "lookback_period": 40, "price_bins": 12, "volume_ma_period": 12, "atr_period": 8},
                {"warmup": 90, "lookback_period": 90, "price_bins": 35, "volume_ma_period": 35, "atr_period": 28},
                {"warmup": 100, "lookback_period": 100, "price_bins": 40, "volume_ma_period": 40, "atr_period": 30}
            ],
            "market_regime": [
                {"warmup": 50, "lookback_period": 20, "volatility_threshold": 0.02, "trend_threshold": 0.015, "rsi_period": 14},
                {"warmup": 60, "lookback_period": 25, "volatility_threshold": 0.025, "trend_threshold": 0.020, "rsi_period": 10},
                {"warmup": 70, "lookback_period": 30, "volatility_threshold": 0.030, "trend_threshold": 0.025, "rsi_period": 20},
                {"warmup": 80, "lookback_period": 35, "volatility_threshold": 0.018, "trend_threshold": 0.012, "rsi_period": 12},
                {"warmup": 55, "lookback_period": 22, "volatility_threshold": 0.022, "trend_threshold": 0.018, "rsi_period": 16},
                {"warmup": 65, "lookback_period": 28, "volatility_threshold": 0.028, "trend_threshold": 0.022, "rsi_period": 18},
                {"warmup": 75, "lookback_period": 32, "volatility_threshold": 0.032, "trend_threshold": 0.028, "rsi_period": 24},
                {"warmup": 85, "lookback_period": 18, "volatility_threshold": 0.015, "trend_threshold": 0.010, "rsi_period": 8},
                {"warmup": 90, "lookback_period": 40, "volatility_threshold": 0.035, "trend_threshold": 0.030, "rsi_period": 28},
                {"warmup": 100, "lookback_period": 45, "volatility_threshold": 0.040, "trend_threshold": 0.035, "rsi_period": 30}
            ],
            "statistical_arbitrage": [
                {"warmup": 60, "lookback_window": 30, "zscore_threshold": 2.0, "mean_reversion_period": 15, "hurst_period": 20},
                {"warmup": 70, "lookback_window": 40, "zscore_threshold": 2.5, "mean_reversion_period": 20, "hurst_period": 25},
                {"warmup": 80, "lookback_window": 50, "zscore_threshold": 1.8, "mean_reversion_period": 25, "hurst_period": 30},
                {"warmup": 90, "lookback_window": 35, "zscore_threshold": 2.2, "mean_reversion_period": 12, "hurst_period": 15},
                {"warmup": 65, "lookback_window": 32, "zscore_threshold": 1.9, "mean_reversion_period": 18, "hurst_period": 22},
                {"warmup": 75, "lookback_window": 45, "zscore_threshold": 2.3, "mean_reversion_period": 22, "hurst_period": 28},
                {"warmup": 85, "lookback_window": 55, "zscore_threshold": 2.7, "mean_reversion_period": 28, "hurst_period": 32},
                {"warmup": 95, "lookback_window": 25, "zscore_threshold": 1.5, "mean_reversion_period": 10, "hurst_period": 12},
                {"warmup": 100, "lookback_window": 60, "zscore_threshold": 3.0, "mean_reversion_period": 30, "hurst_period": 35},
                {"warmup": 110, "lookback_window": 65, "zscore_threshold": 2.8, "mean_reversion_period": 35, "hurst_period": 40}
            ],
            "machine_learning": [
                {"warmup": 120, "feature_period": 20, "prediction_horizon": 5, "ensemble_models": 3, "lookback_window": 100},
                {"warmup": 130, "feature_period": 25, "prediction_horizon": 7, "ensemble_models": 5, "lookback_window": 120},
                {"warmup": 140, "feature_period": 30, "prediction_horizon": 3, "ensemble_models": 4, "lookback_window": 80},
                {"warmup": 150, "feature_period": 15, "prediction_horizon": 10, "ensemble_models": 6, "lookback_window": 150},
                {"warmup": 125, "feature_period": 22, "prediction_horizon": 6, "ensemble_models": 3, "lookback_window": 110},
                {"warmup": 135, "feature_period": 28, "prediction_horizon": 8, "ensemble_models": 4, "lookback_window": 90},
                {"warmup": 145, "feature_period": 18, "prediction_horizon": 4, "ensemble_models": 5, "lookback_window": 130},
                {"warmup": 155, "feature_period": 35, "prediction_horizon": 12, "ensemble_models": 7, "lookback_window": 160},
                {"warmup": 160, "feature_period": 40, "prediction_horizon": 15, "ensemble_models": 8, "lookback_window": 180},
                {"warmup": 170, "feature_period": 12, "prediction_horizon": 2, "ensemble_models": 2, "lookback_window": 60}
            ],
            "sentiment_analysis": [
                {"warmup": 50, "sentiment_period": 5, "sentiment_threshold": 0.3, "momentum_period": 10, "volume_weight": 0.3},
                {"warmup": 60, "sentiment_period": 7, "sentiment_threshold": 0.4, "momentum_period": 15, "volume_weight": 0.4},
                {"warmup": 70, "sentiment_period": 10, "sentiment_threshold": 0.25, "momentum_period": 20, "volume_weight": 0.2},
                {"warmup": 80, "sentiment_period": 3, "sentiment_threshold": 0.35, "momentum_period": 8, "volume_weight": 0.5},
                {"warmup": 55, "sentiment_period": 6, "sentiment_threshold": 0.32, "momentum_period": 12, "volume_weight": 0.35},
                {"warmup": 65, "sentiment_period": 8, "sentiment_threshold": 0.38, "momentum_period": 18, "volume_weight": 0.25},
                {"warmup": 75, "sentiment_period": 12, "sentiment_threshold": 0.28, "momentum_period": 25, "volume_weight": 0.45},
                {"warmup": 85, "sentiment_period": 4, "sentiment_threshold": 0.42, "momentum_period": 6, "volume_weight": 0.55},
                {"warmup": 90, "sentiment_period": 15, "sentiment_threshold": 0.22, "momentum_period": 30, "volume_weight": 0.15},
                                {"warmup": 100, "sentiment_period": 20, "sentiment_threshold": 0.45, "momentum_period": 35, "volume_weight": 0.1}
            ]
        }
            ],
            "crypto_arbitrage": [
                {"warmup": 50, "spread_threshold": 0.015, "momentum_period": 5, "mean_reversion_period": 20, "volume_threshold": 1.5},
                {"warmup": 60, "spread_threshold": 0.020, "momentum_period": 8, "mean_reversion_period": 25, "volume_threshold": 2.0},
                {"warmup": 70, "spread_threshold": 0.012, "momentum_period": 10, "mean_reversion_period": 15, "volume_threshold": 1.2},
                {"warmup": 80, "spread_threshold": 0.025, "momentum_period": 12, "mean_reversion_period": 30, "volume_threshold": 2.5},
                {"warmup": 55, "spread_threshold": 0.018, "momentum_period": 6, "mean_reversion_period": 22, "volume_threshold": 1.8},
                {"warmup": 65, "spread_threshold": 0.022, "momentum_period": 9, "mean_reversion_period": 28, "volume_threshold": 1.6},
                {"warmup": 75, "spread_threshold": 0.010, "momentum_period": 15, "mean_reversion_period": 12, "volume_threshold": 3.0},
                {"warmup": 85, "spread_threshold": 0.030, "momentum_period": 4, "mean_reversion_period": 35, "volume_threshold": 1.3},
                {"warmup": 90, "spread_threshold": 0.008, "momentum_period": 20, "mean_reversion_period": 10, "volume_threshold": 2.2},
                {"warmup": 100, "spread_threshold": 0.035, "momentum_period": 25, "mean_reversion_period": 40, "volume_threshold": 1.1}
            ],
            "options_strategy": [
                {"warmup": 60, "iv_period": 30, "volatility_threshold": 0.25, "strategy_type": "straddle", "profit_target": 0.15},
                {"warmup": 70, "iv_period": 35, "volatility_threshold": 0.30, "strategy_type": "iron_condor", "profit_target": 0.12},
                {"warmup": 80, "iv_period": 25, "volatility_threshold": 0.20, "strategy_type": "covered_call", "profit_target": 0.18},
                {"warmup": 90, "iv_period": 40, "volatility_threshold": 0.35, "strategy_type": "protective_put", "profit_target": 0.10},
                {"warmup": 65, "iv_period": 28, "volatility_threshold": 0.22, "strategy_type": "straddle", "profit_target": 0.20},
                {"warmup": 75, "iv_period": 32, "volatility_threshold": 0.28, "strategy_type": "iron_condor", "profit_target": 0.14},
                {"warmup": 85, "iv_period": 22, "volatility_threshold": 0.18, "strategy_type": "covered_call", "profit_target": 0.16},
                {"warmup": 95, "iv_period": 45, "volatility_threshold": 0.40, "strategy_type": "protective_put", "profit_target": 0.08},
                {"warmup": 100, "iv_period": 50, "volatility_threshold": 0.45, "strategy_type": "straddle", "profit_target": 0.25},
                {"warmup": 110, "iv_period": 20, "volatility_threshold": 0.15, "strategy_type": "iron_condor", "profit_target": 0.22}
            ],
            "quantitative_factor": [
                {"warmup": 60, "momentum_weight": 0.2, "mean_reversion_weight": 0.3, "volatility_weight": 0.15, "volume_weight": 0.1, "quality_weight": 0.15, "sentiment_weight": 0.1, "factor_threshold": 0.6},
                {"warmup": 70, "momentum_weight": 0.25, "mean_reversion_weight": 0.25, "volatility_weight": 0.12, "volume_weight": 0.13, "quality_weight": 0.15, "sentiment_weight": 0.1, "factor_threshold": 0.5},
                {"warmup": 80, "momentum_weight": 0.3, "mean_reversion_weight": 0.2, "volatility_weight": 0.15, "volume_weight": 0.15, "quality_weight": 0.1, "sentiment_weight": 0.1, "factor_threshold": 0.7},
                {"warmup": 90, "momentum_weight": 0.15, "mean_reversion_weight": 0.35, "volatility_weight": 0.15, "volume_weight": 0.15, "quality_weight": 0.1, "sentiment_weight": 0.1, "factor_threshold": 0.4},
                {"warmup": 65, "momentum_weight": 0.22, "mean_reversion_weight": 0.28, "volatility_weight": 0.13, "volume_weight": 0.12, "quality_weight": 0.15, "sentiment_weight": 0.1, "factor_threshold": 0.55},
                {"warmup": 75, "momentum_weight": 0.28, "mean_reversion_weight": 0.22, "volatility_weight": 0.15, "volume_weight": 0.15, "quality_weight": 0.1, "sentiment_weight": 0.1, "factor_threshold": 0.65},
                {"warmup": 85, "momentum_weight": 0.35, "mean_reversion_weight": 0.15, "volatility_weight": 0.12, "volume_weight": 0.13, "quality_weight": 0.15, "sentiment_weight": 0.1, "factor_threshold": 0.8},
                {"warmup": 95, "momentum_weight": 0.18, "mean_reversion_weight": 0.32, "volatility_weight": 0.15, "volume_weight": 0.15, "quality_weight": 0.1, "sentiment_weight": 0.1, "factor_threshold": 0.3},
                {"warmup": 100, "momentum_weight": 0.32, "mean_reversion_weight": 0.18, "volatility_weight": 0.13, "volume_weight": 0.12, "quality_weight": 0.15, "sentiment_weight": 0.1, "factor_threshold": 0.75},
                {"warmup": 110, "momentum_weight": 0.25, "mean_reversion_weight": 0.25, "volatility_weight": 0.15, "volume_weight": 0.15, "quality_weight": 0.1, "sentiment_weight": 0.1, "factor_threshold": 0.6}
            ]
        }
        
        # 전략 인스턴스
        self.strategies = {
            # 기본 4개 전략
            "rule_based": RuleBasedStrategy(),
            "momentum": MomentumStrategy(),
            "mean_reversion": MeanReversionStrategy(),
            "pattern": PatternStrategy(),
            # 새로운 8개 고급 전략
            "multi_timeframe": MultiTimeframeStrategy(),
            "volume_profile": VolumeProfileStrategy(),
            "market_regime": MarketRegimeStrategy(),
            "statistical_arbitrage": StatisticalArbitrageStrategy(),
            "quantitative_factor": QuantitativeFactorStrategy(),
            "machine_learning": MachineLearningStrategy(),
            "sentiment_analysis": SentimentAnalysisStrategy(),
            "crypto_arbitrage": CryptoArbitrageStrategy(),
            "options_strategy": OptionsStrategy()
        }

    async def get_processed_df_async(self, ticker: str, period: str = "3y") -> pd.DataFrame:
        """비동기로 가격 데이터 조회 후 가공"""
        try:
            hist = await self.fetcher.get_stock_data(ticker, period)
            if hist is None or hist.empty:
                return pd.DataFrame()
            return self.processor.process_stock_data(hist)
        except Exception as e:
            print(f"데이터 조회 오류 ({ticker}): {e}")
            return pd.DataFrame()

    def run_single_backtest(self, ticker: str, strategy_name: str, params: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """단일 백테스트 실행"""
        try:
            if df.empty or len(df) < params.get("warmup", 50) + 10:
                return {
                    "ticker": ticker,
                    "strategy": strategy_name,
                    "params": params,
                    "error": "Insufficient data",
                    "status": "failed"
                }
            
            strategy = self.strategies[strategy_name]
            signals = strategy.compute_signals(df, params=params)
            
            if signals is None or signals.empty:
                return {
                    "ticker": ticker,
                    "strategy": strategy_name,
                    "params": params,
                    "error": "No signals generated",
                    "status": "failed"
                }
            
            trades, equity = self.backtest_engine.run(
                df, signals, fee_bps=10.0, slippage_bps=10.0
            )
            
            if equity is None or equity.empty:
                return {
                    "ticker": ticker,
                    "strategy": strategy_name,
                    "params": params,
                    "error": "No equity curve generated",
                    "status": "failed"
                }
            
            metrics = compute_metrics(equity)
            
            return {
                "ticker": ticker,
                "strategy": strategy_name,
                "params": params,
                "metrics": metrics,
                "trades_count": len(trades) if trades is not None else 0,
                "final_equity": equity.iloc[-1]["equity"] if not equity.empty else 1.0,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "ticker": ticker,
                "strategy": strategy_name,
                "params": params,
                "error": str(e),
                "status": "failed"
            }

    async def run_comprehensive_backtest(self, progress_callback=None) -> Dict[str, Any]:
        """종합 백테스트 실행"""
        print("🚀 종합 백테스트 시작...")
        start_time = time.time()
        
        all_results = []
        sector_summaries = {}
        strategy_summaries = {}
        
        total_tests = sum(len(stocks) for stocks in self.sector_stocks.values()) * len(self.strategies) * 10
        print(f"📊 총 백테스트 수행 예정: {total_tests:,}개")
        print(f"   - 섹터: {len(self.sector_stocks)}개")
        print(f"   - 종목: {sum(len(stocks) for stocks in self.sector_stocks.values())}개")
        print(f"   - 전략: {len(self.strategies)}개 (기본 4개 + 새로운 9개, quantitative_factor 포함)")
        print(f"   - 각 전략별 파라미터: 10개")
        completed_tests = 0
        
        for sector, stocks in self.sector_stocks.items():
            print(f"\n📊 {sector} 섹터 백테스트 시작...")
            sector_results = []
            
            for ticker in stocks:
                print(f"  📈 {ticker} 데이터 수집 중...")
                
                # 데이터 수집
                df = await self.get_processed_df_async(ticker, "3y")
                if df.empty:
                    print(f"  ❌ {ticker} 데이터 수집 실패")
                    completed_tests += len(self.strategies) * 10
                    continue
                
                print(f"  ✅ {ticker} 데이터 수집 완료 ({len(df)}일)")
                
                for strategy_name in self.strategies.keys():
                    strategy_params = self.strategy_params[strategy_name]
                    
                    for i, params in enumerate(strategy_params, 1):
                        try:
                            result = self.run_single_backtest(ticker, strategy_name, params, df)
                            all_results.append(result)
                            sector_results.append(result)
                            
                            completed_tests += 1
                            
                            if progress_callback:
                                progress_callback(completed_tests, total_tests, 
                                                f"{ticker} - {strategy_name} #{i}")
                            
                            # 진행상황 출력
                            if completed_tests % 20 == 0:
                                elapsed = time.time() - start_time
                                progress = (completed_tests / total_tests) * 100
                                print(f"  📈 진행률: {progress:.1f}% ({completed_tests}/{total_tests}) - 경과시간: {elapsed:.1f}초")
                        
                        except Exception as e:
                            print(f"  ❌ 백테스트 실패: {ticker} - {strategy_name} #{i} - {e}")
                            completed_tests += 1
                            continue
            
            # 섹터 요약 생성
            sector_summaries[sector] = self.create_sector_summary(sector_results)
        
        # 전략별 요약 생성
        for strategy_name in self.strategies.keys():
            strategy_results = [r for r in all_results if r.get("strategy") == strategy_name and r.get("status") == "success"]
            strategy_summaries[strategy_name] = self.create_strategy_summary(strategy_results)
        
        # 전체 요약
        overall_summary = self.create_overall_summary(all_results)
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ 종합 백테스트 완료! 총 소요시간: {elapsed_time:.1f}초")
        
        return {
            "summary": overall_summary,
            "sector_summaries": sector_summaries,
            "strategy_summaries": strategy_summaries,
            "detailed_results": all_results,
            "metadata": {
                "total_tests": total_tests,
                "completed_tests": completed_tests,
                "success_rate": (sum(1 for r in all_results if r.get("status") == "success") / len(all_results)) * 100 if all_results else 0,
                "elapsed_time": elapsed_time,
                "timestamp": datetime.now().isoformat()
            }
        }

    def create_sector_summary(self, sector_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """섹터별 요약 생성"""
        successful_results = [r for r in sector_results if r.get("status") == "success" and "metrics" in r]
        
        if not successful_results:
            return {"status": "no_successful_tests", "count": 0}
        
        # 성과 지표별 평균
        cagrs = [r["metrics"]["CAGR"] for r in successful_results]
        sharpes = [r["metrics"]["Sharpe"] for r in successful_results]
        max_dds = [r["metrics"]["MaxDrawdown"] for r in successful_results]
        volatilities = [r["metrics"]["Volatility"] for r in successful_results]
        
        return {
            "total_tests": len(sector_results),
            "successful_tests": len(successful_results),
            "success_rate": (len(successful_results) / len(sector_results)) * 100,
            "avg_cagr": np.mean(cagrs),
            "avg_sharpe": np.mean(sharpes),
            "avg_max_dd": np.mean(max_dds),
            "avg_volatility": np.mean(volatilities),
            "best_result": max(successful_results, key=lambda x: x["metrics"]["Sharpe"]),
            "worst_result": min(successful_results, key=lambda x: x["metrics"]["Sharpe"])
        }

    def create_strategy_summary(self, strategy_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """전략별 요약 생성"""
        if not strategy_results:
            return {"status": "no_successful_tests", "count": 0}
        
        # 성과 지표별 통계
        cagrs = [r["metrics"]["CAGR"] for r in strategy_results]
        sharpes = [r["metrics"]["Sharpe"] for r in strategy_results]
        max_dds = [r["metrics"]["MaxDrawdown"] for r in strategy_results]
        
        return {
            "total_tests": len(strategy_results),
            "avg_cagr": np.mean(cagrs),
            "std_cagr": np.std(cagrs),
            "avg_sharpe": np.mean(sharpes),
            "std_sharpe": np.std(sharpes),
            "avg_max_dd": np.mean(max_dds),
            "win_rate": sum(1 for cagr in cagrs if cagr > 0) / len(cagrs) * 100,
            "best_params": max(strategy_results, key=lambda x: x["metrics"]["Sharpe"])["params"],
            "top_3_results": sorted(strategy_results, key=lambda x: x["metrics"]["Sharpe"], reverse=True)[:3]
        }

    def create_overall_summary(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """전체 요약 생성"""
        successful_results = [r for r in all_results if r.get("status") == "success" and "metrics" in r]
        
        if not successful_results:
            return {"status": "no_successful_tests"}
        
        # 전체 통계
        cagrs = [r["metrics"]["CAGR"] for r in successful_results]
        sharpes = [r["metrics"]["Sharpe"] for r in successful_results]
        
        # 전략별 성과 비교
        strategy_performance = {}
        for strategy in self.strategies.keys():
            strategy_results = [r for r in successful_results if r["strategy"] == strategy]
            if strategy_results:
                strategy_performance[strategy] = {
                    "count": len(strategy_results),
                    "avg_cagr": np.mean([r["metrics"]["CAGR"] for r in strategy_results]),
                    "avg_sharpe": np.mean([r["metrics"]["Sharpe"] for r in strategy_results])
                }
        
        return {
            "total_successful_tests": len(successful_results),
            "overall_avg_cagr": np.mean(cagrs),
            "overall_avg_sharpe": np.mean(sharpes),
            "best_overall_result": max(successful_results, key=lambda x: x["metrics"]["Sharpe"]),
            "strategy_performance": strategy_performance,
            "top_10_results": sorted(successful_results, key=lambda x: x["metrics"]["Sharpe"], reverse=True)[:10]
        }

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """결과를 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_backtest_{timestamp}.json"
        
        # results 디렉토리 생성
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "results")
        os.makedirs(results_dir, exist_ok=True)
        
        filepath = os.path.join(results_dir, filename)
        
        # JSON 직렬화 가능하도록 변환
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            return obj
        
        # 결과 데이터 정리
        cleaned_results = json.loads(json.dumps(results, default=convert_numpy))
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cleaned_results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 결과가 {filepath}에 저장되었습니다.")
        return filepath

    def print_summary_report(self, results: Dict[str, Any]):
        """요약 보고서 출력"""
        print("\n" + "="*80)
        print("📊 종합 백테스트 결과 요약 보고서")
        print("="*80)
        
        metadata = results["metadata"]
        print(f"📅 실행 시간: {metadata['timestamp']}")
        print(f"⏱️  총 소요 시간: {metadata['elapsed_time']:.1f}초")
        print(f"📈 총 테스트 수: {metadata['total_tests']}")
        print(f"✅ 성공률: {metadata['success_rate']:.1f}%")
        
        # 전체 요약
        overall = results["summary"]
        if "total_successful_tests" in overall:
            print(f"\n🎯 전체 성과:")
            print(f"  • 성공한 테스트: {overall['total_successful_tests']}개")
            print(f"  • 평균 CAGR: {overall['overall_avg_cagr']*100:.2f}%")
            print(f"  • 평균 샤프 비율: {overall['overall_avg_sharpe']:.3f}")
            
            # 최고 성과
            best = overall["best_overall_result"]
            print(f"\n🏆 최고 성과:")
            print(f"  • 종목: {best['ticker']}")
            print(f"  • 전략: {best['strategy']}")
            print(f"  • CAGR: {best['metrics']['CAGR']*100:.2f}%")
            print(f"  • 샤프 비율: {best['metrics']['Sharpe']:.3f}")
            print(f"  • 최대 낙폭: {best['metrics']['MaxDrawdown']*100:.2f}%")
        
        # 전략별 성과
        print(f"\n📋 전략별 성과:")
        for strategy, summary in results["strategy_summaries"].items():
            if "total_tests" in summary:
                print(f"  🔸 {strategy}:")
                print(f"    - 평균 CAGR: {summary['avg_cagr']*100:.2f}%")
                print(f"    - 평균 샤프 비율: {summary['avg_sharpe']:.3f}")
                print(f"    - 승률: {summary['win_rate']:.1f}%")
        
        # 섹터별 성과
        print(f"\n🌐 섹터별 성과:")
        for sector, summary in results["sector_summaries"].items():
            if "total_tests" in summary:
                print(f"  🔸 {sector}:")
                print(f"    - 성공률: {summary['success_rate']:.1f}%")
                print(f"    - 평균 CAGR: {summary['avg_cagr']*100:.2f}%")
                print(f"    - 평균 샤프 비율: {summary['avg_sharpe']:.3f}")

    def create_summary_csv(self, results: Dict[str, Any]) -> str:
        """요약 결과를 CSV로 저장"""
        successful_results = [r for r in results["detailed_results"] 
                            if r.get("status") == "success" and "metrics" in r]
        
        if not successful_results:
            print("성공한 결과가 없어 CSV를 생성할 수 없습니다.")
            return ""
        
        # DataFrame 생성
        csv_data = []
        for result in successful_results:
            row = {
                "Ticker": result["ticker"],
                "Strategy": result["strategy"],
                "CAGR (%)": result["metrics"]["CAGR"] * 100,
                "Sharpe Ratio": result["metrics"]["Sharpe"],
                "Max Drawdown (%)": result["metrics"]["MaxDrawdown"] * 100,
                "Volatility (%)": result["metrics"]["Volatility"] * 100,
                "Trades Count": result["trades_count"],
                "Final Equity": result["final_equity"],
            }
            
            # 파라미터 추가
            for key, value in result["params"].items():
                row[f"Param_{key}"] = value
            
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        df = df.sort_values("Sharpe Ratio", ascending=False)
        
        # 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "results")
        os.makedirs(results_dir, exist_ok=True)
        
        csv_filename = f"comprehensive_backtest_summary_{timestamp}.csv"
        csv_filepath = os.path.join(results_dir, csv_filename)
        
        df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
        print(f"📊 CSV 요약 파일이 {csv_filepath}에 저장되었습니다.")
        
        return csv_filepath


async def run_comprehensive_backtest():
    """종합 백테스트 실행 함수"""
    backtester = ComprehensiveBacktester()
    
    def progress_callback(current, total, current_task):
        progress = (current / total) * 100
        print(f"진행률: {progress:.1f}% ({current}/{total}) - 현재: {current_task}")
    
    # 백테스트 실행
    results = await backtester.run_comprehensive_backtest(progress_callback)
    
    # 결과 저장
    json_filepath = backtester.save_results(results)
    csv_filepath = backtester.create_summary_csv(results)
    
    # 요약 보고서 출력
    backtester.print_summary_report(results)
    
    return results, json_filepath, csv_filepath


if __name__ == "__main__":
    # 백테스트 실행
    results, json_file, csv_file = asyncio.run(run_comprehensive_backtest())
    
    print(f"\n📁 결과 파일:")
    print(f"  - JSON: {json_file}")
    print(f"  - CSV: {csv_file}")
