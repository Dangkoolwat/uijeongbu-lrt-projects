# 의정부 경전철 월간 HTML 및 PDF 분석 보고서 자동 생성 시스템 (uijeongbu-lrt-report-skill)

본 프로젝트는 의정부 경전철의 월별 승하차 CSV 데이터를 기상 정보 및 지역 행사 정보와 연계 분석하여 프리미엄 품질의 HTML 및 PDF 보고서를 생성하는 시스템입니다.

## 1. 프로젝트 개요
의정부 경전철 이용 현황의 단순 통계 조회를 넘어 기상 요인(강수량, 기온, 강풍 등) 및 의정부시의 주요 문화/행사 일정과의 연관성을 분석합니다. 분석 결과를 시각화된 차트와 함께 직관적인 HTML 및 PDF 보고서로 제공하여 경전철 운영 및 마케팅 인사이트를 도출하도록 돕습니다.

## 2. 입력 데이터 설명
- **승하차 현황 CSV**: `data/raw/ridership/` 경로에 배치되며 파일명 끝에 `YYYYMMDD` 형식의 날짜가 포함되어야 합니다. (예: `경기도_의정부시_경전철_승하차_현황_20260531.csv`)
- **혼잡도 CSV (선택적 참고)**: `data/raw/external_static/congestion/`
- **역 위치 정보 CSV (선택적 참고)**: `data/raw/external_static/station/`

## 3. 디렉토리 구조
프로젝트는 다음과 같은 디렉토리 구조로 구성됩니다.
```
uijeongbu-lrt-report-skill/
  config/                  # project.yml, collectors.yml 등의 설정 파일
  data/
    raw/                   # 가공되지 않은 승하차, 기상 캐시, 행사 캐시 데이터
    processed/             # 정규화 및 분석 완료된 파일 (report_data.json 등)
  scripts/
    collectors/            # 날씨 API 및 행사 크롤러
    validators/            # 데이터 품질 검증 모듈
    analyzers/             # 승하차 패턴 및 이상 분석 모듈
    charts/                # Matplotlib 차트 생성 모듈
    utils/                 # 기상 코드 변환 및 요일 변환 등 유틸리티
    llm/                   # 프롬프트 빌더 및 내러티브 생성
    renderers/             # HTML 렌더러
  templates/               # HTML 보고서 Jinja2 템플릿 및 design.md
  outputs/                 # 최종 렌더링된 HTML 및 차트 이미지
```

## 4. 시작하기 (사용자 가이드)

### 1단계: 프로젝트 다운로드 및 데이터 준비
1. Git을 통해 본 프로젝트를 로컬 저장소로 다운로드(`git clone`)합니다.
2. 분석하고자 하는 의정부 경전철 승하차 현황 CSV 데이터가 없다면, [공공데이터포털(data.go.kr)](https://www.data.go.kr/)에 접속하여 **"경기도 의정부시_경전철 승하차 현황"**을 검색하여 해당 월 데이터를 다운로드합니다.
3. 다운로드한 파일을 프로젝트의 `data/raw/ridership/` 위치에 배치합니다.

### 2단계: 프로젝트 세팅 (초기 1회)
이 프로젝트는 사용자가 일일이 파이썬과 라이브러리를 설치할 필요 없이 래퍼 스크립트를 제공합니다.
- **Windows**: `run.bat` 스크립트 실행
- **Mac/Linux**: 터미널에서 `./run.sh` 스크립트 실행
(위 스크립트는 가상 환경(venv)을 자동으로 만들고 필요한 패키지들을 설치해 줍니다.)

### 3단계: AI 에이전트(Antigravity / Codex App)와 대화하기
1. Antigravity IDE에서 **폴더 열기** 또는 Codex App에서 **프로젝트 만들기**를 선택한 후, 이 프로젝트가 설치된 경로를 지정합니다.
2. AI 대화창에서 에이전트에게 지시를 내립니다. 에이전트는 규칙에 따라 자동으로 대화하고 작업합니다.

**[대화 예시]**
- 에이전트: "현재 `data/raw/ridership/` 폴더에 분석 데이터가 존재합니까?" (데이터 누락 시 안내)
- 사용자: "의정부 승하차 현황 보고서 작성해줘. PDF 도 같이 생성해줘"
- 에이전트: "어느 월(YYYY-MM)을 희망하시나요?" (다중 파일일 경우 선택 요구)
- 사용자: "2026-05월로 부탁해"

### 4단계: 결과 확인
에이전트가 "보고서 작성이 완료되었습니다"라고 안내하면 시스템 구동이 종료된 것입니다.
- `outputs/monthly/YYYY-MM/` 폴더로 이동하여 최종 완성된 HTML 페이지와 PDF 파일을 확인합니다.

## 5. 샘플 보고서 (Sample)
실제 시스템이 어떻게 결과물을 생성하는지 확인하실 수 있도록 2026년 5월 기준의 샘플 보고서를 미리 생성해 두었습니다.
- HTML 렌더링 예시: [samples/2026-05/report.html](samples/2026-05/report.html)
- PDF 렌더링 예시: [samples/2026-05/report.pdf](samples/2026-05/report.pdf)

## 7. 외부 데이터 수집 방식
- 수집기는 오직 외부 API 및 웹 요청을 통해 날것의 데이터(Raw HTML/JSON)를 저장하는 역할만 담당합니다.
- 사람이 읽기 쉬운 형태의 한글 맵핑 및 가공은 수집 단계가 아닌 Utility 레이어에서 처리합니다.

## 8. Open-Meteo 사용 방식
- Open-Meteo Archive API를 활용하여 의정부 좌표(위도 37.74, 경도 127.03) 기준으로 대상 기간의 기온(평균, 최고, 최저), 강수량, 기상 코드(WMO), 최대풍속을 수집합니다.
- 수집된 데이터는 JSON 및 CSV 형식으로 `data/raw/external_cache/weather/`에 캐시하여 중복 요청을 방지합니다.

## 9. 의정부 행사 HTML 파싱 방식
- 의정부시청 행사 일정 페이지(`https://ui4u.go.kr/portal/eventNoti/custom/calendar.do?mId=0301170200`)의 HTML 소스를 긁어와 `city_events/html/`에 저장합니다.
- BeautifulSoup을 사용해 캘린더 요소를 파싱하여 행사명, 시작일, 종료일, 상세 URL 등을 추출하고, 데이터 무결성 검증을 거친 후 CSV 파일로 캐시합니다.

## 10. Utility 모듈 설명
- `date_utils.py`: 분석 기간 변환, 공휴일 및 평일 여부, 한글 요일 등을 판단합니다.
- `weather_code.py`: WMO 기상 코드를 한글 명칭(예: 63 -> 비)으로 변환합니다.
- `wind_direction.py`: 360도 각도를 8방위 풍향 명칭(예: 0 -> 북풍)으로 변환합니다.
- `weather_summary.py`: 일별 기상 통계를 집계하여 월간 기상 요약 정보를 산출합니다.
- `station_utils.py`: 역명을 표준 명칭으로 정규화하고 노선도 상의 거리에 맞게 정렬합니다.
- `chart_style.py`: `templates/design.md`에 설정된 CSS/디자인 가이드라인을 Matplotlib 스타일 객체로 변환하여 통일감 있는 그래픽을 만듭니다.

## 11. LLM 보고서 문장 생성 방식
- LLM 엔진은 `report_data.json` 및 `external_context.json` 형태의 정제된 통계 수치만을 바탕으로 기술합니다.
- 인과 관계를 확증 편향적으로 표현하는 단정적 문장(예: 날씨 때문에 이용객이 감소했다)을 금지하고, 개연성 중심의 공공기관 보고서 투를 고수합니다. (예: 기상 변동이 일부 겹쳐 기상 요인을 참고 요인으로 검토할 수 있음)
- LLM API를 호출할 수 없는 로컬 오프라인 환경에서는 규칙 기반 내러티브 템플릿(Fallback)을 활용해 `report_narrative.json`을 완성합니다.

## 12. 산출물 설명
실행 결과로 생성되는 파일 리스트입니다.
- `data/processed/monthly/YYYY-MM/report_data.json`: 정량 수치 분석 집계 데이터
- `data/processed/monthly/YYYY-MM/external_context.json`: 날씨 및 행사 연계 데이터
- `data/processed/monthly/YYYY-MM/report_narrative.json`: 보고서용 서술형 문장 데이터
- `outputs/monthly/YYYY-MM/report.html`: 최종 반응형 HTML 보고서
- `outputs/monthly/YYYY-MM/charts/*.png`: 분석 시각화 차트 4종

## 13. 향후 확장 계획
- 계절별, 반기별, 연도별 누적 분석 및 트렌드 시계열 분석 확장.
