"""
주식 분석 관련 API 라우트
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import logging
from datetime import datetime

from ...core.data import StockDataFetcher, DataProcessor
from ...core.analysis import TechnicalAnalyzer
from ...core.analysis.financial.earnings import EarningsAnalyzer
from ..schemas.models import StockAnalysis, StockPrice, TechnicalIndicators, ErrorResponse
from ...core.utils.exceptions import StockAnalysisError, DataNotFoundError, NetworkError
from ...core.strategy.rule_based import RuleBasedStrategy
from ...core.strategy.momentum import MomentumStrategy
from ...core.strategy.mean_reversion import MeanReversionStrategy
from ...core.strategy.pattern import PatternStrategy
from ...core.backtest.engine import BacktestEngine
from ...core.backtest.metrics import compute_metrics

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = logging.getLogger(__name__)

@router.get("/price/{ticker}", response_model=StockPrice)
async def get_stock_price(ticker: str):
    """현재 주가 정보를 조회합니다."""
    try:
        fetcher = StockDataFetcher()
        hist = await fetcher.get_stock_data(ticker, "5d")
        info = await fetcher.get_stock_info(ticker)
        
        if hist.empty:
            raise DataNotFoundError(f"티커 {ticker}에 대한 데이터를 찾을 수 없습니다")
        
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        return StockPrice(
            ticker=ticker,
            current_price=current_price,
            previous_close=prev_price,
            price_change=current_price - prev_price,
            price_change_percentage=((current_price - prev_price) / prev_price) * 100,
            open=hist['Open'].iloc[-1],
            high=hist['High'].iloc[-1],
            low=hist['Low'].iloc[-1],
            volume=int(hist['Volume'].iloc[-1]),
            company_name=info.get('longName', 'N/A'),
            currency=info.get('currency', 'USD'),
            timestamp=datetime.now()
        )
    
    except StockAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting stock price for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")

@router.get("/technical/{ticker}", response_model=TechnicalIndicators)
async def get_technical_analysis(
    ticker: str,
    period: str = Query("1mo", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|10y|ytd|max)$")
):
    """기술적 지표를 분석합니다."""
    try:
        fetcher = StockDataFetcher()
        processor = DataProcessor()
        analyzer = TechnicalAnalyzer()

        # 데이터 조회 및 처리
        hist = await fetcher.get_stock_data(ticker, period)
        processed_data = processor.process_stock_data(hist)

        # 기술적 지표 계산 (사전 구조)
        if len(processed_data) < 60:
            ti = analyzer.analyze_technical_indicators(processed_data)
        else:
            ti = analyzer.analyze_technical_indicators(processed_data)

        # 이동평균 데이터 준비
        ma = ti.get('moving_averages', {})
        ma_data = {
            'ma_20': float(ma.get('ma_20', float('nan'))),
            'ma_50': float(ma.get('ma_50', float('nan'))),
            'ma_200': float(ma.get('ma_200', float('nan')))
        }

        # 볼린저 밴드 데이터
        bb = ti.get('bollinger_bands', {})
        bb_data = {
            'upper': float(bb.get('upper', float('nan'))),
            'middle': float(bb.get('middle', float('nan'))),
            'lower': float(bb.get('lower', float('nan')))
        }

        macd = ti.get('macd', {})
        rsi = ti.get('rsi', {})

        return TechnicalIndicators(
            ticker=ticker,
            period=period,
            moving_averages=ma_data,
            rsi={'current': float(rsi.get('current', float('nan')))},
            macd={
                'macd': float(macd.get('macd_line', float('nan'))),
                'signal': float(macd.get('signal_line', float('nan'))),
                'histogram': float(macd.get('histogram', float('nan')))
            },
            bollinger_bands=bb_data,
            volume_analysis={'volume': int(hist['Volume'].iloc[-1])},
            stochastic=None
        )
    except StockAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing technical indicators for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="내부 서버 오류")

@router.get("/earnings/{ticker}")
async def get_earnings_analysis(
    ticker: str,
    include_history: bool = Query(True, description="어닝 이력 포함 여부"),
    include_estimates: bool = Query(True, description="애널리스트 추정치 포함 여부"),
    include_guidance: bool = Query(True, description="가이던스 정보 포함 여부")
):
    """어닝콜 및 가이던스 분석을 조회합니다."""
    try:
        earnings_analyzer = EarningsAnalyzer()
        
        result = {
            "ticker": ticker.upper(),
            "analysis_date": datetime.now().isoformat()
        }
        
        if include_history:
            result["earnings_history"] = earnings_analyzer.get_earnings_history(ticker)
        
        if include_estimates:
            result["analyst_estimates"] = earnings_analyzer.get_analyst_estimates(ticker)
        
        if include_guidance:
            result["guidance"] = earnings_analyzer.get_guidance_info(ticker)
        
        # 어닝 캘린더는 항상 포함
        result["earnings_calendar"] = earnings_analyzer.get_earnings_calendar(ticker)
        
        # 요약 생성
        result["summary"] = earnings_analyzer._generate_earnings_summary(ticker)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting earnings analysis for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="어닝 분석 중 오류가 발생했습니다")

@router.get("/comprehensive/{ticker}")
async def get_comprehensive_analysis(
    ticker: str,
    period: str = Query("1y", description="분석 기간"),
    include_earnings: bool = Query(True, description="어닝 분석 포함 여부")
):
    """종합적인 주식 분석을 수행합니다 (어닝 포함)."""
    try:
        # 기존 분석 수행
        fetcher = StockDataFetcher()
        processor = DataProcessor()
        technical_analyzer = TechnicalAnalyzer()

        hist = await fetcher.get_stock_data(ticker, period)
        info = await fetcher.get_stock_info(ticker)
        
        if hist.empty:
            raise DataNotFoundError(f"티커 {ticker}에 대한 데이터를 찾을 수 없습니다")
        
        # 기본 정보
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        result = {
            "ticker": ticker.upper(),
            "analysis_period": period,
            "basic_info": {
                "current_price": round(current_price, 2),
                "previous_price": round(prev_price, 2),
                "price_change": round(current_price - prev_price, 2),
                "price_change_percentage": round(((current_price - prev_price) / prev_price) * 100, 2),
                "company_name": info.get('longName', 'N/A'),
                "sector": info.get('sector', 'N/A'),
                "market_cap": info.get('marketCap', 'N/A'),
                "pe_ratio": info.get('trailingPE', 'N/A')
            }
        }

        # 기술적 분석
        processed_data = processor.process_stock_data(hist)
        technical_analysis = technical_analyzer.analyze_technical_indicators(processed_data)
        result["technical_analysis"] = technical_analysis

        # 어닝 분석 포함
        if include_earnings:
            earnings_analyzer = EarningsAnalyzer()
            earnings_analysis = earnings_analyzer.get_comprehensive_earnings_analysis(ticker)
            result["earnings_analysis"] = earnings_analysis

        return result
        
    except StockAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error performing comprehensive analysis for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="종합 분석 중 오류가 발생했습니다")


@router.post("/strategy")
async def get_strategy_signal_v2(data: dict):
    """선택된 전략의 최신 신호를 제공합니다."""
    try:
        ticker = data.get("ticker")
        period = data.get("period", "6mo")
        strategy_class = data.get("strategy_class", "RuleBasedStrategy")
        strategy_params = data.get("strategy_params", {})
        warmup = data.get("warmup", 50)
        
        fetcher = StockDataFetcher()
        processor = DataProcessor()
        hist = await fetcher.get_stock_data(ticker, period)
        df = processor.process_stock_data(hist)
        
        # 전략 인스턴스 생성
        if strategy_class == "RuleBasedStrategy":
            strategy = RuleBasedStrategy()
        elif strategy_class == "MomentumStrategy":
            strategy = MomentumStrategy()
        elif strategy_class == "MeanReversionStrategy":
            strategy = MeanReversionStrategy()
        elif strategy_class == "PatternStrategy":
            strategy = PatternStrategy()
        else:
            strategy = RuleBasedStrategy()  # 기본값
            
        # 워밍업 처리
        strategy_params["warmup"] = max(0, min(warmup, max(0, len(df) - 2)))
        
        try:
            signals = strategy.compute_signals(df, params=strategy_params)
        except Exception as e:
            logger.warning(f"Signal computation failed: {e}")
            signals = None
            
        if signals is None or len(signals) == 0:
            return {
                "ticker": ticker.upper(),
                "period": period,
                "signals": {
                    "buy_signals": [],
                    "sell_signals": [],
                    "current_signal": "NONE"
                }
            }
            
        # 매수/매도 신호 분리
        buy_signals = signals[signals['action'] == 'BUY'].to_dict(orient="records")
        sell_signals = signals[signals['action'] == 'SELL'].to_dict(orient="records")
        current_signal = signals.iloc[-1]['action'] if len(signals) > 0 else "NONE"
        
        return {
            "ticker": ticker.upper(),
            "period": period,
            "signals": {
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "current_signal": current_signal
            }
        }
        
    except Exception as e:
        logger.error(f"Error computing strategy signal for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="전략 신호 계산 오류")


@router.post("/backtest")
async def run_backtest_v2(data: dict):
    """선택된 전략으로 백테스트를 수행합니다."""
    try:
        ticker = data.get("ticker")
        period = data.get("period", "1y")
        initial_capital = data.get("initial_capital", 10000)
        fees_bps = data.get("fees_bps", 10.0)
        slippage_bps = data.get("slippage_bps", 10.0)
        strategy_class = data.get("strategy_class", "RuleBasedStrategy")
        strategy_params = data.get("strategy_params", {})
        warmup = data.get("warmup", 50)
        
        fetcher = StockDataFetcher()
        processor = DataProcessor()
        hist = await fetcher.get_stock_data(ticker, period)
        df = processor.process_stock_data(hist)
        
        # 전략 인스턴스 생성
        if strategy_class == "RuleBasedStrategy":
            strategy = RuleBasedStrategy()
        elif strategy_class == "MomentumStrategy":
            strategy = MomentumStrategy()
        elif strategy_class == "MeanReversionStrategy":
            strategy = MeanReversionStrategy()
        elif strategy_class == "PatternStrategy":
            strategy = PatternStrategy()
        else:
            strategy = RuleBasedStrategy()  # 기본값
            
        # 워밍업 처리
        strategy_params["warmup"] = max(0, min(warmup, max(0, len(df) - 2)))
        
        try:
            signals = strategy.compute_signals(df, params=strategy_params)
        except Exception as e:
            logger.warning(f"Signal computation failed: {e}")
            signals = None
            
        if signals is None or len(signals) == 0:
            return {
                "ticker": ticker.upper(),
                "period": period,
                "metrics": {"CAGR": 0.0, "Volatility": 0.0, "Sharpe": 0.0, "MaxDrawdown": 0.0},
                "trades": [],
                "equity": []
            }
            
        engine = BacktestEngine()
        trades, equity = engine.run(df, signals, fee_bps=fees_bps, slippage_bps=slippage_bps)
        metrics = compute_metrics(equity)
        
        return {
            "ticker": ticker.upper(),
            "period": period,
            "metrics": metrics,
            "trades": trades.to_dict(orient="records") if not trades.empty else [],
            "equity": equity.tail(50).reset_index().to_dict(orient="records") if not equity.empty else []
        }
        
    except Exception as e:
        logger.error(f"Error backtesting {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="백테스트 실행 오류")


@router.get("/strategy/{ticker}")
async def get_strategy_signal(
    ticker: str,
    period: str = Query("6mo", description="데이터 기간"),
):
    """룰 기반 베이스라인 전략의 최신 신호를 제공합니다. (레거시)"""
    try:
        fetcher = StockDataFetcher()
        processor = DataProcessor()
        hist = await fetcher.get_stock_data(ticker, period)
        df = processor.process_stock_data(hist)

        strat = RuleBasedStrategy()
        try:
            signals = strat.compute_signals(df)
        except Exception as e:
            logger.warning(f"Signal computation failed: {e}")
            signals = None
        if signals is None or len(signals) == 0:
            return {
                "ticker": ticker.upper(),
                "period": period,
                "signal": {
                    "date": df.index[-1] if not df.empty else None,
                    "action": "HOLD",
                    "confidence": 0.0,
                    "reason": "데이터가 충분하지 않아 기본 보유 신호 반환",
                    "stop": None,
                    "target": None,
                    "size": 0.0,
                }
            }
        latest = signals.iloc[-1]
        def _to_float_or_none(x):
            try:
                return None if x is None or (isinstance(x, float) and (x != x)) else float(x)
            except Exception:
                return None

        return {
            "ticker": ticker.upper(),
            "period": period,
            "signal": {
                "date": latest.name,
                "action": latest["action"],
                "confidence": float(latest["confidence"]),
                "reason": latest["reason"],
                "stop": _to_float_or_none(latest.get("stop", None)),
                "target": _to_float_or_none(latest.get("target", None)),
                "size": float(latest.get("size", 1.0)),
            }
        }
    except Exception as e:
        logger.error(f"Error computing strategy signal for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="전략 신호 계산 오류")


@router.post("/backtest/{ticker}")
async def run_backtest(
    ticker: str,
    period: str = Query("1y", description="백테스트 기간"),
    fee_bps: float = Query(10.0, description="수수료(bps)"),
    slippage_bps: float = Query(10.0, description="슬리피지(bps)")
):
    """룰 기반 베이스라인 전략으로 간단 백테스트를 수행합니다."""
    try:
        fetcher = StockDataFetcher()
        processor = DataProcessor()
        hist = await fetcher.get_stock_data(ticker, period)
        df = processor.process_stock_data(hist)

        strat = RuleBasedStrategy()
        try:
            signals = strat.compute_signals(df)
        except Exception as e:
            logger.warning(f"Signal computation failed: {e}")
            signals = None

        if signals is None or len(signals) == 0:
            return {
                "ticker": ticker.upper(),
                "period": period,
                "metrics": {"CAGR": 0.0, "Volatility": 0.0, "Sharpe": 0.0, "MaxDrawdown": 0.0},
                "trades": [],
                "equity_tail": []
            }

        engine = BacktestEngine()
        trades, equity = engine.run(df, signals, fee_bps=fee_bps, slippage_bps=slippage_bps)
        metrics = compute_metrics(equity)

        return {
            "ticker": ticker.upper(),
            "period": period,
            "metrics": metrics,
            "trades": trades.to_dict(orient="records"),
            "equity_tail": equity.tail(10).reset_index().to_dict(orient="records")
        }
    except Exception as e:
        logger.error(f"Error backtesting {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail="백테스트 실행 오류")
