#!/usr/bin/env python3
"""
SADS/SUDS AUTOSAR SWC 분석기 실행 스크립트
다른 PC에서 쉽게 실행할 수 있도록 자동 설정을 포함합니다.
"""

import os
import sys
import subprocess
import webbrowser
import time

def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"   현재 버전: {sys.version}")
        return False
    print(f"✅ Python 버전 확인: {sys.version}")
    return True

def install_requirements():
    """필요한 패키지 자동 설치"""
    print("\n📦 필요한 패키지 설치 중...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "pandas", "pydantic"])
        print("✅ 패키지 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 패키지 설치 실패: {e}")
        print("   수동으로 설치해주세요: pip install flask pandas pydantic")
        return False

def create_directories():
    """필요한 디렉토리 생성"""
    dirs = ["uploads", "outputs"]
    for dir_name in dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"✅ 디렉토리 생성: {dir_name}")

def start_server():
    """Flask 서버 시작"""
    print("\n🚀 웹 서버 시작 중...")
    print("   서버 주소: http://localhost:5000")
    print("   종료하려면 Ctrl+C를 누르세요")
    
    try:
        # 잠시 후 브라우저 자동 열기
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:5000')
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Flask 앱 실행
        from app import app
        app.run(debug=False, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n👋 서버를 종료합니다.")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")

def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("🔧 SADS/SUDS AUTOSAR SWC 분석기")
    print("=" * 50)
    
    # Python 버전 확인
    if not check_python_version():
        return
    
    # 필요한 디렉토리 생성
    create_directories()
    
    # 패키지 설치 확인 및 설치
    try:
        import flask
        import pandas
        import pydantic
        print("✅ 필요한 패키지가 이미 설치되어 있습니다.")
    except ImportError:
        if not install_requirements():
            return
    
    # 서버 시작
    start_server()

if __name__ == "__main__":
    main()
