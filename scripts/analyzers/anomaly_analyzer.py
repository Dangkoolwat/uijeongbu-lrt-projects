import os
import json
import pandas as pd
from datetime import datetime
from scripts.utils import date_utils, weather_code

def analyze_anomalies(period: str, base_dir: str = "data") -> pd.DataFrame:
    """
    평일/주말별 평균 이용객 대비 급증/급감한 특이 일자(Anomaly)를 찾아내고,
    해당 일자의 날씨 정보 및 행사 정보와 매핑하여 event_matches.csv를 생성합니다.
    """
    processed_dir = os.path.join(base_dir, "processed", "monthly", period)
    daily_summary_path = os.path.join(processed_dir, "daily_summary.csv")
    weather_csv_path = os.path.join(base_dir, "raw", "external_cache", "weather", "csv", f"{period}_weather.csv")
    events_csv_path = os.path.join(base_dir, "raw", "external_cache", "city_events", "csv", f"{period}_events.csv")
    
    if not os.path.exists(daily_summary_path):
        raise FileNotFoundError(f"일별 요약 데이터가 존재하지 않습니다: {daily_summary_path}")
        
    # 1. 데이터 로드
    daily_df = pd.read_csv(daily_summary_path)
    
    # 날씨 데이터 로드
    weather_df = pd.DataFrame()
    if os.path.exists(weather_csv_path):
        weather_df = pd.read_csv(weather_csv_path)
        
    # 행사 데이터 로드
    events_df = pd.DataFrame()
    if os.path.exists(events_csv_path):
        events_df = pd.read_csv(events_csv_path)
        # VALID/WARNING 데이터만 필터링
        events_df = events_df[events_df["validation_status"] != "INVALID"]
        
    # 2. 요일 유형(평일/주말) 할당
    daily_df["day_type"] = daily_df["date"].apply(date_utils.get_day_type)
    
    # 3. 평일/주말 기준 평균 및 표준편차 산출
    stats = daily_df.groupby("day_type")["total"].agg(["mean", "std"]).reset_index()
    stats_map = stats.set_index("day_type").to_dict(orient="index")
    
    anomalies = []
    
    # 4. 특이일자 감지 및 외부 요인 매핑
    for _, row in daily_df.iterrows():
        d_val = row["date"]
        d_type = row["day_type"]
        t_val = row["total"]
        
        mean_val = stats_map[d_type]["mean"]
        std_val = stats_map[d_type]["std"] if pd.notna(stats_map[d_type]["std"]) else 0.0
        
        # 편차율 계산
        deviation_pct = round(((t_val - mean_val) / mean_val) * 100, 1) if mean_val > 0 else 0.0
        
        # 이상치 판단 조건: 평균 대비 편차가 ±15% 이상 벗어난 날 (경전철 일별 특성 반영)
        anomaly_type = "정상"
        if deviation_pct >= 15.0:
            anomaly_type = "급증"
        elif deviation_pct <= -15.0:
            anomaly_type = "급감"
            
        # 해당 일자 날씨 매핑
        w_desc = "날씨 정보 없음"
        p_sum = 0.0
        if not weather_df.empty:
            w_row = weather_df[weather_df["date"] == d_val]
            if not w_row.empty:
                w_code = int(w_row.iloc[0]["weather_code"])
                w_name = weather_code.to_korean(w_code)
                p_sum = float(w_row.iloc[0]["precipitation_sum"])
                max_wind = float(w_row.iloc[0]["wind_speed_10m_max"])
                
                w_desc = f"{w_name}"
                if p_sum >= 0.1:
                    w_desc += f"(강수량:{p_sum}mm)"
                if max_wind >= 8.0:
                    w_desc += f"(강풍:{max_wind}m/s)"
                    
        # 해당 일자 행사 매핑
        matching_evs = []
        if not events_df.empty:
            for _, ev_row in events_df.iterrows():
                try:
                    s_date = datetime.strptime(str(ev_row["start_date"]).strip(), "%Y-%m-%d")
                    e_date = datetime.strptime(str(ev_row["end_date"]).strip(), "%Y-%m-%d")
                    cur_date = datetime.strptime(d_val, "%Y-%m-%d")
                    
                    # 행사가 해당 날짜 범위에 포함되는지 검사
                    if s_date <= cur_date <= e_date:
                        matching_evs.append(ev_row["event_title"])
                except Exception:
                    pass
                    
        events_desc = ", ".join(matching_evs) if matching_evs else "진행 행사 없음"
        
        # 이상치인 날 또는 행사/강수 등 기상 변동이 유의미한 날을 기록
        # 보고서 매핑용으로 전체 날짜에 대해 계산한 결과를 CSV로 저장하되,
        # '급증'/'급감'만 따로 정리해서 특이사항 도출에 사용 가능하도록 함
        anomalies.append({
            "date": d_val,
            "day_type": d_type,
            "total_count": int(t_val),
            "mean_count": int(mean_val),
            "deviation_percent": deviation_pct,
            "anomaly_type": anomaly_type,
            "weather_summary": w_desc,
            "precipitation_sum": p_sum,
            "matching_events": events_desc
        })
        
    anomalies_df = pd.DataFrame(anomalies)
    
    # 5. CSV 저장
    csv_path = os.path.join(processed_dir, "event_matches.csv")
    anomalies_df.to_csv(csv_path, index=False, encoding="utf-8")
    
    print(f"[Analyzer] 특이일자 및 기상/행사 매핑 분석 완료 -> {csv_path}")
    return anomalies_df
