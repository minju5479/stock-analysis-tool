"""
API 에러 처리 미들웨어
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from typing import Union

from ...core.utils.exceptions import (
    StockAnalysisError, DataNotFoundError, NetworkError,
    ValidationError, CalculationError
)

logger = logging.getLogger(__name__)

async def stock_analysis_exception_handler(
    request: Request,
    exc: StockAnalysisError
) -> JSONResponse:
    """주식 분석 관련 예외 처리"""
    error_map = {
        DataNotFoundError: 404,
        NetworkError: 503,
        ValidationError: 400,
        CalculationError: 500
    }
    
    status_code = error_map.get(type(exc), 500)
    
    error_response = {
        "error": exc.__class__.__name__,
        "detail": str(exc),
        "timestamp": datetime.now().isoformat()
    }
    
    logger.error(f"Error handling request {request.url}: {str(exc)}")
    return JSONResponse(status_code=status_code, content=error_response)

async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """일반 예외 처리"""
    error_response = {
        "error": "InternalServerError",
        "detail": "내부 서버 오류가 발생했습니다",
        "timestamp": datetime.now().isoformat()
    }
    
    logger.exception(f"Unexpected error handling request {request.url}: {str(exc)}")
    return JSONResponse(status_code=500, content=error_response)
