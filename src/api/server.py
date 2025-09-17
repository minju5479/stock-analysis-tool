"""
API 서버 설정
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import analysis, charts
from .middleware.error_handlers import (
    stock_analysis_exception_handler,
    general_exception_handler
)
from ..core.utils.exceptions import StockAnalysisError

def create_app() -> FastAPI:
    """FastAPI 애플리케이션을 생성하고 설정합니다."""
    app = FastAPI(
        title="주식 분석 도구 API",
        description="주식 데이터 분석 및 차트 생성을 위한 API",
        version="1.0.0"
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 라우터 등록
    app.include_router(analysis.router)
    app.include_router(charts.router)
    
    # 예외 핸들러 등록
    app.add_exception_handler(StockAnalysisError, stock_analysis_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    @app.get("/health")
    async def health_check():
        """헬스 체크 엔드포인트"""
        return {"status": "healthy"}
    
    return app
