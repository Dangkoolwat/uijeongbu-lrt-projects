import os
import sys
import json
import argparse
import glob
from datetime import datetime

# 유틸리티 및 모듈 임포트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils import date_utils, weather_summary
from scripts.collectors import open_meteo_historical_collector, uijeongbu_event_collector
from scripts.validators import validate_ridership, validate_city_events, validate_weather
from scripts.analyzers import monthly_analyzer, station_analyzer, hourly_analyzer, weekday_analyzer, anomaly_analyzer
from scripts.charts import station_rank_chart, hourly_pattern_chart, weekday_pattern_chart, daily_weather_usage_chart
from scripts.llm import prompt_builder, narrative_generator
from scripts.renderers import html_renderer, pdf_renderer

def main():
    parser = argparse.ArgumentParser(description="의정부 경전철 월간 분석 보고서 자동 생성 오케스트레이터")
    parser.add_argument("--period", type=str, default="2026-05", help="분석 대상 기간 (YYYY-MM)")
    args = parser.parse_args()
    
    period = args.period
    print(f"=== 의정부 경전철 월간 HTML 보고서 생성 시작 (대상 기간: {period}) ===")
    
    # 1. 파일 경로 지정
    base_dir = "data"
    output_dir = "outputs"
    processed_dir = os.path.join(base_dir, "processed", "monthly", period)
    
    # 2. ridership CSV 파일 탐색 (YYYYMMDD가 포함됨)
    # period 가 2026-05 이면 YYYYMM 형식은 202605 임.
    search_pattern = f"{period.replace('-', '')}*"
    ridership_dir = os.path.join(base_dir, "raw", "ridership")
    csv_files = glob.glob(os.path.join(ridership_dir, f"*{search_pattern}.csv"))
    
    if not csv_files:
        print(f"[Error] '{ridership_dir}' 경로에서 분석 기간 {period}에 해당하는 CSV 파일을 찾을 수 없습니다.")
        sys.exit(1)
        
    target_ridership_csv = csv_files[0]
    print(f"[Ridership] 분석 대상 원본 파일 선정: {target_ridership_csv}")
    
    # 3. 승하차 데이터 검증 수행
    print("[Ridership] 데이터 품질 검증 시작...")
    ridership_val_result = validate_ridership.validate_ridership_data(target_ridership_csv, period)
    
    # 4. 외부 데이터(날씨, 행사) 수집 및 기본 검증
    # 4-1. 날씨 데이터 수집
    print("[Weather] 수집 및 캐싱 프로세스 가동...")
    weather_json_path, weather_csv_path = open_meteo_historical_collector.collect_weather(period, base_dir)
    print("[Weather] 수집 데이터 검증 시작...")
    weather_val_result = validate_weather.validate_weather_data(period, base_dir)
    
    # 4-2. 의정부 행사 데이터 수집
    print("[Events] 수집 및 HTML 파싱 프로세스 가동...")
    event_html_path, event_csv_path = uijeongbu_event_collector.collect_events(period, base_dir)
    print("[Events] 수집 데이터 검증 시작...")
    event_val_result = validate_city_events.validate_city_events(period, base_dir)
    
    # 5. 승하차 데이터 정규화 및 요약 생성
    print("[Analyzer] 승하차 데이터 정규화(Melt) 및 Parquet 변환 가동...")
    normalized_df = monthly_analyzer.normalize_ridership_csv(target_ridership_csv, period, base_dir)
    
    # 6. 세부 통계 분석 수행
    print("[Analyzer] 역사별, 시간대별, 요일별, 이상치 및 요인 매핑 분석 가동...")
    station_summary_df = station_analyzer.analyze_station_usage(period, base_dir)
    hourly_summary_df = hourly_analyzer.analyze_hourly_usage(period, base_dir)
    weekday_summary_df = weekday_analyzer.analyze_weekday_usage(period, base_dir)
    anomalies_df = anomaly_analyzer.analyze_anomalies(period, base_dir)
    
    # 7. external_context.json 조립 및 저장
    # 날씨 요약 수집
    import pandas as pd
    weather_df = pd.read_csv(weather_csv_path)
    weather_summary_dict = weather_summary.summarize_monthly_weather(weather_df)
    
    external_context = {
        "weather_summary": weather_summary_dict,
        "ridership_validation": ridership_val_result,
        "event_validation": event_val_result,
        "weather_validation": weather_val_result
    }
    
    context_path = os.path.join(processed_dir, "external_context.json")
    with open(context_path, "w", encoding="utf-8") as f:
        json.dump(external_context, f, ensure_ascii=False, indent=2)
    print(f"[Context] external_context.json 생성 완료 -> {context_path}")
    
    # 8. report_data.json 조립 및 저장
    # 정량 통계량 추출
    total_ridership = int(normalized_df["count"].sum())
    daily_average = int(round(total_ridership / normalized_df["date"].nunique()))
    
    # 평일/주말 평균 구하기
    daily_totals = normalized_df.groupby(["date", "type"])["count"].sum().unstack(fill_value=0)
    daily_totals["total"] = daily_totals.get("승차", 0) + daily_totals.get("하차", 0)
    daily_totals = daily_totals.reset_index()
    daily_totals["day_type"] = daily_totals["date"].apply(date_utils.get_day_type)
    
    weekday_df = daily_totals[daily_totals["day_type"] == "평일"]
    weekend_df = daily_totals[daily_totals["day_type"] != "평일"]
    
    weekday_avg = int(round(weekday_df["total"].mean())) if not weekday_df.empty else 0
    weekend_avg = int(round(weekend_df["total"].mean())) if not weekend_df.empty else 0
    
    # 역사 상위/하위 5개씩 정리
    top_stations = station_summary_df.head(5).to_dict(orient="records")
    bottom_stations = station_summary_df.tail(5).sort_values(by="total_count").to_dict(orient="records")
    
    # 시간대 피크
    morning_peak_row = hourly_summary_df.loc[hourly_summary_df[hourly_summary_df["hour"].between(7, 9)]["total_count"].idxmax()]
    evening_peak_row = hourly_summary_df.loc[hourly_summary_df[hourly_summary_df["hour"].between(17, 19)]["total_count"].idxmax()]
    
    # 요일 데이터 정비
    weekday_data = weekday_summary_df.to_dict(orient="records")
    
    # 이상치 일자만 필터링
    anomalies_only = anomalies_df[anomalies_df["anomaly_type"] != "정상"].to_dict(orient="records")
    
    report_data = {
        "period": period,
        "period_ko": f"{period.split('-')[0]}년 {int(period.split('-')[1])}월",
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "total_ridership": total_ridership,
        "daily_average_ridership": daily_average,
        "weekday_average": weekday_avg,
        "weekend_average": weekend_avg,
        "top_stations": top_stations,
        "bottom_stations": bottom_stations,
        "morning_peak_hour": int(morning_peak_row["hour"]),
        "morning_peak_count": int(morning_peak_row["total_count"]),
        "evening_peak_hour": int(evening_peak_row["hour"]),
        "evening_peak_count": int(evening_peak_row["total_count"]),
        "weekday_data": weekday_data,
        "anomalies": anomalies_only
    }
    
    data_path = os.path.join(processed_dir, "report_data.json")
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print(f"[Context] report_data.json 생성 완료 -> {data_path}")
    
    # 9. Matplotlib 시각화 차트 이미지 4종 빌드
    print("[Chart] Matplotlib 시각화 차트 4종 생성 가동...")
    station_rank_chart.generate_station_rank_chart(period, base_dir, output_dir)
    hourly_pattern_chart.generate_hourly_pattern_chart(period, base_dir, output_dir)
    weekday_pattern_chart.generate_weekday_pattern_chart(period, base_dir, output_dir)
    daily_weather_usage_chart.generate_daily_weather_usage_chart(period, base_dir, output_dir)
    
    # 10. LLM 프롬프트 빌드 및 서술문 내러티브 생성
    print("[LLM] LLM 사용자 프롬프트 작성 및 내러티브 Fallback 생성 가동...")
    prompt_builder.build_user_prompt(period, base_dir)
    narrative_generator.generate_report_narrative(period, base_dir)
    
    # 11. HTML 보고서 렌더링
    print("[Renderer] HTML 템플릿 컴파일 및 report.html 생성 가동...")
    html_path = html_renderer.render_html_report(period, base_dir, "templates", output_dir)
    
    # 12. PDF 보고서 더미 호출 (후속 준비)
    pdf_renderer.convert_html_to_pdf(html_path, html_path.replace(".html", ".pdf"))
    
    print(f"=== 의정부 경전철 월간 HTML 보고서 생성 완료 (outputs/monthly/{period}/report.html) ===")

if __name__ == "__main__":
    main()
