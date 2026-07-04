import os
import pandas as pd
from scripts.utils import date_utils

def analyze_weekday_usage(period: str, base_dir: str = "data") -> pd.DataFrame:
    """
    요일별 이용현황을 분석하여 요일당 평균 이용객 등을 포함하는 weekday_summary.csv를 생성합니다.
    """
    processed_dir = os.path.join(base_dir, "processed", "monthly", period)
    parquet_path = os.path.join(processed_dir, "normalized_ridership.parquet")
    
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"정규화된 승하차 데이터가 없습니다: {parquet_path}")
        
    df = pd.read_parquet(parquet_path)
    
    # 일자별 요일 정보 및 요일 한글명 매핑 추가
    # 중복 계산 방지를 위해 일자별 승하차 총합 데이터를 준비
    daily_df = df.groupby(["date", "type"])["count"].sum().unstack(fill_value=0).reset_index()
    daily_df["total"] = daily_df["승차"] + daily_df["하차"]
    daily_df["weekday"] = daily_df["date"].apply(lambda d: date_utils.parse_date(d).weekday())
    
    # 1. 요일별 총 이용량 집계
    weekday_grouped = daily_df.groupby("weekday").agg(
        ride_count=("승차", "sum"),
        alight_count=("하차", "sum"),
        total_count=("total", "sum"),
        days_count=("date", "nunique") # 해당 요일이 해당 월에 며칠 있었는지 count
    ).reset_index()
    
    # 2. 일평균 승객수 계산
    weekday_grouped["average_daily_count"] = (
        (weekday_grouped["total_count"] / weekday_grouped["days_count"]).round(1)
    )
    
    # 3. 한글 요일명 컬럼 추가
    weekdays_ko_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
    weekday_grouped["weekday_ko"] = weekday_grouped["weekday"].map(weekdays_ko_map)
    
    # 정렬 및 컬럼 순서 조정
    weekday_grouped = weekday_grouped.sort_values(by="weekday")
    weekday_grouped = weekday_grouped[
        ["weekday", "weekday_ko", "ride_count", "alight_count", "total_count", "days_count", "average_daily_count"]
    ]
    
    csv_path = os.path.join(processed_dir, "weekday_summary.csv")
    weekday_grouped.to_csv(csv_path, index=False, encoding="utf-8")
    
    print(f"[Analyzer] 요일별 이용량 분석 완료 -> {csv_path}")
    return weekday_grouped
