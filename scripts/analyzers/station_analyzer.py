import os
import pandas as pd
from scripts.utils import station_utils

def analyze_station_usage(period: str, base_dir: str = "data") -> pd.DataFrame:
    """
    역별 이용현황을 분석하여 station_summary.csv를 생성합니다.
    """
    processed_dir = os.path.join(base_dir, "processed", "monthly", period)
    parquet_path = os.path.join(processed_dir, "normalized_ridership.parquet")
    
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"정규화된 승하차 데이터가 없습니다: {parquet_path}")
        
    df = pd.read_parquet(parquet_path)
    
    # 1. 역별 승차, 하차 수 집계
    ride_df = df[df["type"] == "승차"].groupby("station")["count"].sum().rename("ride_count")
    alight_df = df[df["type"] == "하차"].groupby("station")["count"].sum().rename("alight_count")
    
    # 조인
    summary = pd.DataFrame(index=station_utils.get_ordered_stations())
    summary = summary.join(ride_df, how="left").join(alight_df, how="left").fillna(0).astype(int)
    
    # total 및 점유율, 순위 계산
    summary["total_count"] = summary["ride_count"] + summary["alight_count"]
    total_lrt_users = summary["total_count"].sum()
    
    summary["share_ratio"] = round((summary["total_count"] / total_lrt_users) * 100, 2) if total_lrt_users > 0 else 0.0
    summary = summary.sort_values(by="total_count", ascending=False)
    summary["rank"] = range(1, len(summary) + 1)
    
    # 출력 경로 정렬 (노선 순으로 다시 돌리거나 순위 순으로 유지)
    # 보고서 및 차트 표현을 위해 순위 순으로 보존하되 파일로 저장
    summary = summary.reset_index().rename(columns={"index": "station"})
    
    # 권역 정보 추가
    summary["zone"] = summary["station"].apply(station_utils.get_station_zone)
    
    csv_path = os.path.join(processed_dir, "station_summary.csv")
    summary.to_csv(csv_path, index=False, encoding="utf-8")
    
    print(f"[Analyzer] 역별 이용량 분석 완료 -> {csv_path}")
    return summary
