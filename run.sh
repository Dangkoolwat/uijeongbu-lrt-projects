#!/bin/bash

# 한글 출력 인코딩 및 환경 변수 설정
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

echo "================================================="
echo "   의정부 경전철 월간 분석 시스템 구동 (Mac/Linux)"
echo "================================================="

# 1. 파이썬 설치 확인
if ! command -v python3 &> /dev/null
then
    echo "[오류] python3가 설치되어 있지 않습니다. Python을 설치해 주세요."
    exit 1
fi

# 2. 가상 환경 유무 확인 및 생성
if [ ! -d "venv" ]; then
    echo ">> 가상환경(venv) 폴더를 생성합니다..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[오류] 가상환경 생성에 실패했습니다."
        exit 1
    fi
    echo ">> 가상환경 생성이 완료되었습니다."
else
    echo ">> 기존 가상환경(venv)을 사용합니다."
fi

# 3. 가상 환경 활성화
echo ">> 가상환경 활성화 중..."
source venv/bin/activate

# 4. 의존성 패키지 설치
if [ -f "requirements.txt" ]; then
    echo ">> 패키지 최신화 및 설치 진행 (requirements.txt)..."
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    echo ">> Playwright 브라우저 엔진 설치..."
    python3 -m playwright install
    echo ">> 패키지 설치 완료."
else
    echo "[경고] requirements.txt 파일이 존재하지 않습니다."
fi

# 5. 스크립트 실행
echo "-------------------------------------------------"
echo ">> 분석 스크립트를 실행합니다..."
python scripts/run_monthly_report.py "$@"

# 6. 종료
echo "-------------------------------------------------"
echo ">> 구동이 종료되었습니다."
deactivate
