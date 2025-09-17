#!/usr/bin/env python3
"""
API 서버 실행 스크립트
"""

import subprocess
import sys
import os

def main():
    """API 서버를 실행합니다."""
    try:
        # 프로젝트 루트 디렉토리로 이동 및 Python 경로 추가
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        os.chdir(project_root)
        
        # Python 모듈 경로에 프로젝트 루트 추가
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # src/api/api_server.py 실행
        api_server_path = os.path.join("src", "api", "api_server.py")
        
        if not os.path.exists(api_server_path):
            print(f"❌ 오류: {api_server_path} 파일을 찾을 수 없습니다.")
            return
        
        print("🚀 API 서버를 시작합니다...")
        print("📊 API 문서: http://localhost:8000/docs")
        print("📊 ReDoc 문서: http://localhost:8000/redoc")
        print("⏹️  종료하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        # API 서버 실행
        from src.api.api_server import app
        import uvicorn
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\n👋 API 서버를 종료합니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main() 