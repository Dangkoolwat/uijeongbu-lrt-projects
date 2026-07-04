# 의정부 경전철 월간 HTML 분석 보고서 자동 생성 Skill (SKILL.md)

본 문서는 사용자가 월간 경전철 데이터 보고서 분석을 요청했을 때의 워크플로우와 처리 가이드를 정의한 Skill 명세입니다.

## 1. Skill 목적
의정부 경전철의 특정 월(YYYY-MM) 승하차 통계 데이터와 해당 월의 기상 및 공공 행사 데이터를 결합 분석하고, 이를 직관적이고 고급스러운 디자인의 HTML 보고서 및 고해상도 시각화 차트로 자동 렌더링하는 것을 목적으로 합니다.

## 2. 요청 처리 절차
사용자가 "2026-05월 경전철 보고서를 생성해 줘"와 같은 월간 보고서 작업을 지시할 때 수행되는 과정입니다.

1. **분석 대상월 식별**: 입력받은 타겟 월(예: 2026-05)을 바탕으로 데이터 매칭을 대기합니다.
2. **승하차 원본 탐색**: `data/raw/ridership/` 경로에서 해당 년월을 포함하는 CSV 파일을 식별합니다.
3. **데이터 수집 및 캐싱**:
   - Open-Meteo API를 호출하여 해당 월의 매일 기상 통계를 수집하고 json/csv로 캐싱합니다.
   - 의정부시청 행사 페이지 정보를 파싱하여 csv로 캐싱합니다.
4. **데이터 품질 검증**: 승하차, 기상, 행사 데이터의 데이터 무결성을 검증하고 그 결과를 json 리포트로 기록합니다.
5. **데이터 가공 및 요약**:
   - 일별, 역별, 시간대별, 요일별로 구분하여 분석 지표를 산출하고 Parquet 및 CSV 형식으로 정제합니다.
   - 평소 이용객 패턴 대비 이상 급증/급감이 확인되는 이상치(Anomaly)를 정의하고 이를 해당 날짜의 기상 상태 및 축제 행사 일정과 매핑합니다.
6. **차트 시각화**: `design.md`를 바탕으로 한 4종의 고해상도 차트 이미지를 생성합니다.
7. **컨텍스트 파일 생성**: `report_data.json` 및 `external_context.json`을 기록합니다.
8. **보고서 문장 생성(LLM)**: LLM(또는 템플릿 Fallback 모듈)을 구동하여 두 json을 근거로 하는 서술형 내러티브(`report_narrative.json`)를 작성합니다.
9. **HTML 렌더링**: 최종 3개의 JSON과 차트 이미지들을 매핑하여 프리미엄 반응형 HTML 보고서(`report.html`)를 생성합니다.

## 3. 필요한 입력 파일
- **승하차 데이터**: `data/raw/ridership/경기도_의정부시_경전철_승하차_현황_YYYYMMDD.csv`
- **역 위치 매칭용**: `data/raw/external_static/station/국가철도공단_의정부경전철_역위치_20241015.csv` (필요시 참조)

## 4. 실행 명령
```bash
python scripts/run_monthly_report.py --period 2026-05
```

## 5. 산출물 위치
- **종합 데이터**: `data/processed/monthly/YYYY-MM/`
  - `normalized_ridership.parquet`, `report_data.json`, `external_context.json`, `report_narrative.json` 등
- **최종 보고서**: `outputs/monthly/YYYY-MM/report.html`
- **차트 이미지**: `outputs/monthly/YYYY-MM/charts/`
  - `station_rank.png`, `hourly_pattern.png`, `weekday_pattern.png`, `daily_weather_usage.png`

## 6. LLM 내러티브 범위 및 문체 원칙
- LLM은 절대로 원본 통계 CSV를 읽지 않고, `report_data.json`과 `external_context.json`에 정제되어 기술된 내용만을 토대로 요약합니다.
- 공공기관 보고서 형식의 격식 있고 간결한 어조를 적용합니다.
- 날씨와 행사의 영향도 서술 시 단정적인 표현은 절대 금지합니다.
  - *금지*: "비가 와서 이용객이 줄어들었다."
  - *권장*: "강수 현상과 이용량 변화 시점이 일부 일치하여 기상 상태가 일정 부분 영향이 있을 가능성이 있으나 추가적인 요인 검토가 필요합니다."

## 7. Utility 모듈 사용 원칙
- 수집기는 날것의 파일 저장만 전담하며, 한글 요일 판정, 기상 코드 및 8방위 가독화 작업은 반드시 `scripts/utils/` 아래의 유틸리티 라이브러리를 활용합니다.

## 8. 주의사항
- 보고서 생성 도중 네트워크 오류 등이 발생할 경우, 작업이 강제 중단되지 않도록 기상/행사의 캐시 데이터 존재 시 이를 활용하도록 예외처리를 세밀하게 구현해야 합니다.
