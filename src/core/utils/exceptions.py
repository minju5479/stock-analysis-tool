"""
주식 분석 도구의 예외 처리를 위한 커스텀 예외 클래스들
"""

class StockAnalysisError(Exception):
    """주식 분석 도구의 기본 예외 클래스"""
    pass

class InvalidTickerError(StockAnalysisError):
    """유효하지 않은 티커 심볼"""
    pass

class DataNotFoundError(StockAnalysisError):
    """요청한 데이터를 찾을 수 없음"""
    pass

class CalculationError(StockAnalysisError):
    """지표 계산 중 오류 발생"""
    pass

class EmptyDataError(StockAnalysisError):
    """빈 데이터셋"""
    pass

class NetworkError(StockAnalysisError):
    """네트워크 관련 오류"""
    pass

class ValidationError(StockAnalysisError):
    """입력값 검증 오류"""
    pass

class ProcessingError(StockAnalysisError):
    """데이터 처리 중 오류 발생"""
    pass
