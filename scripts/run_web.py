#!/usr/bin/env python3
"""
웹 인터페이스 실행 스크립트
"""

import subprocess
import sys
import os

def main():
    """웹 인터페이스를 실행합니다."""
    try:
        # 프로젝트 루트 디렉토리로 이동 및 Python 경로 추가
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        os.chdir(project_root)
        
        # Python 모듈 경로에 프로젝트 루트 추가
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Docker 환경에서는 직접 실행하지 않음 (docker-compose에서 처리)
        if os.environ.get('DOCKER_ENV') == 'true' or os.path.exists('/.dockerenv'):
            print("🐳 Docker 환경에서 실행 중입니다.")
            print("📊 브라우저에서 http://localhost:8501 에 접속하세요")
            print("⏹️  종료하려면 Ctrl+C를 누르세요")
            print("-" * 50)
            # Docker 환경에서는 무한 대기
            import time
            while True:
                time.sleep(1)
        
        # src/web/web_interface.py 실행
        web_interface_path = os.path.join("src", "web", "web_interface.py")
        
        if not os.path.exists(web_interface_path):
            print(f"❌ 오류: {web_interface_path} 파일을 찾을 수 없습니다.")
            return
        
        print("🚀 웹 인터페이스를 시작합니다...")
        print("📊 브라우저에서 http://localhost:8501 에 접속하세요")
        print("⏹️  종료하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        # Streamlit 실행
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            web_interface_path, 
            "--server.port", "8501"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 웹 인터페이스를 종료합니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main() 