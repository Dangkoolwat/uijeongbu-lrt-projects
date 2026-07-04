@echo off
:: 한글 깨짐 방지를 위한 UTF-8 설정
chcp 65001 >nul

echo =================================================
echo    의정부 경전철 월간 분석 시스템 구동 (Windows)
echo =================================================

:: 1. 파이썬 설치 확인
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [오류] 파이썬이 설치되어 있지 않거나 환경 변수 PATH에 추가되어 있지 않습니다.
    echo 파이썬을 설치하시고 "Add Python to PATH" 옵션을 꼭 체크해 주세요.
    pause
    exit /b 1
)

:: 2. 가상 환경 유무 확인 및 생성
if not exist "venv" (
    echo ^>^> 가상환경(venv) 폴더를 생성합니다...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [오류] 가상환경 생성에 실패했습니다.
        pause
        exit /b 1
    )
    echo ^>^> 가상환경 생성이 완료되었습니다.
) else (
    echo ^>^> 기존 가상환경(venv)을 사용합니다.
)

:: 3. 가상 환경 활성화
echo ^>^> 가상환경 활성화 중...
call venv\Scripts\activate.bat

:: 4. 의존성 패키지 설치
if exist "requirements.txt" (
    echo ^>^> 패키지 최신화 및 설치 진행 (requirements.txt)...
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    echo ^>^> Playwright 브라우저 엔진 설치...
    python -m playwright install
    echo ^>^> 패키지 설치 완료.
) else (
    echo [경고] requirements.txt 파일이 존재하지 않습니다.
)

:: 5. 스크립트 실행
echo -------------------------------------------------
echo ^>^> 분석 스크립트를 실행합니다...
python scripts\run_monthly_report.py %*

:: 6. 종료
echo -------------------------------------------------
echo ^>^> 구동이 종료되었습니다.
deactivate
pause
