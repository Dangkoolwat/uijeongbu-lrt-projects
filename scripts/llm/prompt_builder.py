import os
import json

def build_user_prompt(period: str, base_dir: str = "data", prompt_dir: str = "prompts") -> str:
    """
    processed 데이터를 로드하여 LLM 용 사용자 프롬프트 파일(monthly_report_user.md)을 작성합니다.
    """
    processed_dir = os.path.join(base_dir, "processed", "monthly", period)
    data_json_path = os.path.join(processed_dir, "report_data.json")
    context_json_path = os.path.join(processed_dir, "external_context.json")
    
    if not os.path.exists(data_json_path):
        raise FileNotFoundError(f"분석 데이터 파일이 존재하지 않습니다: {data_json_path}")
        
    with open(data_json_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)
        
    external_context = {}
    if os.path.exists(context_json_path):
        with open(context_json_path, "r", encoding="utf-8") as f:
            external_context = json.load(f)
            
    # 프롬프트 바인딩 텍스트 작성
    prompt_content = f"""# 의정부 경전철 월간 이용 분석 데이터 ({period})

다음 원본 요약 데이터를 근거로, 시스템 지침에 맞게 보고서 서술형 본문 문장을 작성해 주십시오.

## 1. 정량 요약 데이터
- 분석 대상 기간: {report_data.get('period', period)}
- 총 이용객 수 (승차+하차): {report_data.get('total_ridership', 0):,} 명
- 일평균 이용객 수: {report_data.get('daily_average_ridership', 0):,} 명
- 평일 일평균 이용객 수: {report_data.get('weekday_average', 0):,} 명
- 주말/공휴일 일평균 이용객 수: {report_data.get('weekend_average', 0):,} 명

## 2. 역별 순위 및 점유율 Top 3
{chr(10).join([f"- {s['rank']}위: {s['station']}역 (이용객: {s['total_count']:,}명, 점유율: {s['share_ratio']}%)" for s in report_data.get('top_stations', [])[:3]])}

## 3. 역별 순위 및 점유율 Bottom 3
{chr(10).join([f"- 하위 {s['rank']}위: {s['station']}역 (이용객: {s['total_count']:,}명, 점유율: {s['share_ratio']}%)" for s in report_data.get('bottom_stations', [])[:3]])}

## 4. 시간대별 피크 타임
- 출근 피크 시간대: {report_data.get('morning_peak_hour', '08')}시 (이용객: {report_data.get('morning_peak_count', 0):,} 명)
- 퇴근 피크 시간대: {report_data.get('evening_peak_hour', '18')}시 (이용객: {report_data.get('evening_peak_count', 0):,} 명)

## 5. 기상 요약
- 월 평균기온: {external_context.get('weather_summary', {}).get('avg_temp', 0)} ℃
- 최고기온: {external_context.get('weather_summary', {}).get('max_temp', 0)} ℃
- 최저기온: {external_context.get('weather_summary', {}).get('min_temp', 0)} ℃
- 강수일수: {external_context.get('weather_summary', {}).get('precipitation_days', 0)} 일
- 총 강수량: {external_context.get('weather_summary', {}).get('total_precipitation', 0)} mm
- 대표 기상 상태: {external_context.get('weather_summary', {}).get('representative_weather', '맑음')}

## 6. 특이 일자(이상치) 및 관련 요인
"""
    
    anomalies = report_data.get("anomalies", [])
    if anomalies:
        for an in anomalies:
            prompt_content += f"- 날짜: {an['date']} ({an['day_type']}), 이용객: {an['total_count']:,}명 (기준 평균 대비 {an['deviation_percent']}% {an['anomaly_type']})\n"
            prompt_content += f"  * 기상 상태: {an['weather_summary']}\n"
            prompt_content += f"  * 진행 행사: {an['matching_events']}\n"
    else:
        prompt_content += "- 특이 일자 감지 사항 없음.\n"
        
    prompt_content += """
## 7. 응답 양식 및 제약
- 반드시 JSON 포맷으로 작성하십시오.
- JSON Key 목록: executive_summary, key_findings(배열), station_analysis, hourly_analysis, weekday_analysis, weather_event_context, operational_notes, limitations
- 지침에 명시된 금지 단어를 절대 피하고, 권장하는 문장 투를 완벽하게 사용하십시오.
"""
    
    os.makedirs(prompt_dir, exist_ok=True)
    prompt_path = os.path.join(prompt_dir, "monthly_report_user.md")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt_content)
        
    print(f"[LLM] 사용자 프롬프트 생성 완료 -> {prompt_path}")
    return prompt_path
