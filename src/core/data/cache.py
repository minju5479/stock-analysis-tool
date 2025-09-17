"""
데이터 캐싱을 위한 모듈
"""

from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DataCache:
    def __init__(self, max_age: int = 300):  # 기본 5분
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_age = max_age
    
    def get(self, key: str) -> Optional[Any]:
        """캐시된 데이터를 가져옵니다."""
        if key in self.cache:
            entry = self.cache[key]
            if (datetime.now() - entry['timestamp']).total_seconds() < self.max_age:
                return entry['data']
            else:
                # 캐시 만료
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """데이터를 캐시에 저장합니다."""
        self.cache[key] = {
            'data': value,
            'timestamp': datetime.now()
        }
        logger.debug(f"데이터가 캐시에 저장되었습니다: {key}")
    
    def clear(self, key: Optional[str] = None):
        """캐시를 초기화합니다."""
        if key:
            if key in self.cache:
                del self.cache[key]
                logger.info(f"캐시 항목이 삭제되었습니다: {key}")
        else:
            self.cache.clear()
            logger.info("전체 캐시가 초기화되었습니다.")
    
    def is_valid(self, key: str) -> bool:
        """캐시 항목이 유효한지 확인합니다."""
        if key in self.cache:
            entry = self.cache[key]
            return (datetime.now() - entry['timestamp']).total_seconds() < self.max_age
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계를 반환합니다."""
        total_items = len(self.cache)
        valid_items = sum(1 for k in self.cache.keys() if self.is_valid(k))
        
        return {
            'total_items': total_items,
            'valid_items': valid_items,
            'expired_items': total_items - valid_items
        }
