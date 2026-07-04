import os
import re
import pandas as pd
from scripts.utils import date_utils, station_utils

def normalize_ridership_csv(csv_path: str, period: str, output_base_dir: str = "data") -> pd.DataFrame:
    """
    승하차 원본 CSV를 읽고 정규화하여 Parquet 파일로 저장합니다.
    최종 구조: [date, station, type, hour, count]
    """
    df = pd.read_csv(csv_path, encoding="utf-8")
    
    # 1. 컬럼 식별
    date_col = None
    station_col = None
    type_col = None
    
    for col in df.columns:
        c_clean = col.replace(" ", "")
        if "일자" in c_clean or "날짜" in c_clean or "사용일" in c_clean:
            date_col = col
        elif "역명" in c_clean:
            station_col = col
        elif "구분" in c_clean or "승하차" in c_clean:
            type_col = col
            
    if not date_col or not station_col:
        raise ValueError("일자 및 역명 컬럼을 식별할 수 없습니다.")
        
    # 시간대별 승객수 컬럼 목록 추출 (예: '00시~01시', '06~07' 등 혹은 '00~01')
    hour_cols = []
    hour_pattern = re.compile(r"(\d{1,2})")
    
    for col in df.columns:
        if col in [date_col, station_col, type_col]:
            continue
        # 숫자가 포함된 컬럼이면 시간대 컬럼으로 간주
        if hour_pattern.search(col):
            hour_cols.append(col)
            
    # 2. 행 데이터 정규화 및 가공
    records = []
    for _, row in df.iterrows():
        # 날짜 정규화 (YYYY-MM-DD)
        try:
            raw_date = str(row[date_col]).strip()
            date_obj = date_utils.parse_date(raw_date)
            formatted_date = date_obj.strftime("%Y-%m-%d")
            
            # 대상 분석월 검증
            if date_utils.period_from_yyyymmdd(date_obj.strftime("%Y%m%d")) != period:
                continue
        except Exception:
            continue
            
        # 역명 정규화
        raw_station = str(row[station_col]).strip()
        norm_station = station_utils.normalize_name(raw_station)
        
        # 승하차 구분
        raw_type = str(row[type_col]).strip() if type_col else "승하차합계"
        # 한글 정규화
        if "승차" in raw_type:
            ride_type = "승차"
        elif "하차" in raw_type:
            ride_type = "하차"
        else:
            ride_type = "합계"
            
        # 시간대별 데이터 flat화
        for col in hour_cols:
            # 컬럼명에서 첫 번째 숫자(시작 시간) 추출
            match = hour_pattern.search(col)
            if not match:
                continue
            hour_val = int(match.group(1))
            
            # 값 가공
            val = row[col]
            try:
                count_val = int(float(str(val).replace(",", "")))
                if count_val < 0:
                    count_val = 0
            except (ValueError, TypeError):
                count_val = 0
                
            records.append({
                "date": formatted_date,
                "station": norm_station,
                "type": ride_type,
                "hour": hour_val,
                "count": count_val
            })
            
    normalized_df = pd.DataFrame(records)
    
    # 3. 저장 처리
    processed_dir = os.path.join(output_base_dir, "processed", "monthly", period)
    os.makedirs(processed_dir, exist_ok=True)
    
    parquet_path = os.path.join(processed_dir, "normalized_ridership.parquet")
    normalized_df.to_parquet(parquet_path, index=False)
    
    # 4. 일별 요약 파일 (daily_summary.csv) 추가 저장
    # 일자별, 승하차타입별 총 승객 수 요약
    daily_sum = normalized_df.groupby(["date", "type"])["count"].sum().unstack(fill_value=0).reset_index()
    # 컬럼 없으면 보정
    for t in ["승차", "하차"]:
        if t not in daily_sum.columns:
            daily_sum[t] = 0
    daily_sum["total"] = daily_sum["승차"] + daily_sum["하차"]
    
    daily_csv_path = os.path.join(processed_dir, "daily_summary.csv")
    daily_sum.to_csv(daily_csv_path, index=False, encoding="utf-8")
    
    print(f"[Analyzer] 데이터 정규화 완료 -> {parquet_path}")
    return normalized_df
