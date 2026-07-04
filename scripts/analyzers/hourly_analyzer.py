import os
import pandas as pd

def analyze_hourly_usage(period: str, base_dir: str = "data") -> pd.DataFrame:
    """
    시간대별 이용현황을 분석하여 hourly_summary.csv를 생성합니다.
    """
    processed_dir = os.path.join(base_dir, "processed", "monthly", period)
    parquet_path = os.path.join(processed_dir, "normalized_ridership.parquet")
    
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"정규화된 승하차 데이터가 없습니다: {parquet_path}")
        
    df = pd.read_parquet(parquet_path)
    
    # 시간대별 승차, 하차 수 집계
    ride_df = df[df["type"] == "승차"].groupby("hour")["count"].sum().rename("ride_count")
    alight_df = df[df["type"] == "하차"].groupby("hour")["count"].sum().rename("alight_count")
    
    # 시간 범위 축 생성 (0 ~ 23시)
    summary = pd.DataFrame(index=range(24))
    summary = summary.join(ride_df, how="left").join(alight_df, how="left").fillna(0).astype(int)
    
    summary["total_count"] = summary["ride_count"] + summary["alight_count"]
    total_lrt_users = summary["total_count"].sum()
    
    summary["share_ratio"] = round((summary["total_count"] / total_lrt_users) * 100, 2) if total_lrt_users > 0 else 0.0
    summary = summary.reset_index().rename(columns={"index": "hour"})
    
    csv_path = os.path.join(processed_dir, "hourly_summary.csv")
    summary.to_csv(csv_path, index=False, encoding="utf-8")
    
    print(f"[Analyzer] 시간대별 이용량 분석 완료 -> {csv_path}")
    return summary
