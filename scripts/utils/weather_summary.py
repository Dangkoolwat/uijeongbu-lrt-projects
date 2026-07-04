import pandas as pd
from collections import Counter
from scripts.utils import weather_code

def summarize_monthly_weather(weather_df: pd.DataFrame) -> dict:
    """
    일별 날씨 DataFrame을 읽어 월간 보고서용 요약 정보를 산출합니다.
    DataFrame 컬럼 구성 기대치:
      - temperature_2m_mean: 평균 기온
      - temperature_2m_max: 최고 기온
      - temperature_2m_min: 최저 기온
      - precipitation_sum: 일강수량 (mm)
      - weather_code: WMO 날씨 코드
      - wind_speed_10m_max: 최대 풍속 (m/s)
    """
    if weather_df.empty:
        return {
            "avg_temp": 0.0,
            "max_temp": 0.0,
            "min_temp": 0.0,
            "precipitation_days": 0,
            "total_precipitation": 0.0,
            "representative_weather": "데이터 없음",
            "heavy_rain_days": 0,
            "strong_wind_days": 0,
            "no_precipitation_days": 0
        }
    
    # 1. 기온 통계
    avg_temp = round(weather_df["temperature_2m_mean"].mean(), 1)
    max_temp = round(weather_df["temperature_2m_max"].max(), 1)
    min_temp = round(weather_df["temperature_2m_min"].min(), 1)
    
    # 2. 강수 통계
    # 강수일수는 일강수량이 0.1mm 이상인 일수를 기준으로 함
    precip_series = weather_df["precipitation_sum"].fillna(0.0)
    precipitation_days = int((precip_series >= 0.1).sum())
    total_precipitation = round(precip_series.sum(), 1)
    no_precipitation_days = int((precip_series < 0.1).sum())
    
    # 폭우일수 (일강수량 30mm 이상)
    heavy_rain_days = int((precip_series >= 30.0).sum())
    
    # 3. 강풍일수 (최대풍속 8.0m/s 이상 기준)
    wind_series = weather_df["wind_speed_10m_max"].fillna(0.0)
    strong_wind_days = int((wind_series >= 8.0).sum())
    
    # 4. 대표 날씨 (가장 많이 나타난 날씨 코드 기준)
    code_series = weather_df["weather_code"].fillna(-1).astype(int)
    # 유효한 코드만 필터링
    valid_codes = [c for c in code_series if c >= 0]
    if valid_codes:
        most_common_code = Counter(valid_codes).most_common(1)[0][0]
        representative_weather = weather_code.to_korean(most_common_code)
    else:
        representative_weather = "알 수 없음"

    return {
        "avg_temp": avg_temp,
        "max_temp": max_temp,
        "min_temp": min_temp,
        "precipitation_days": precipitation_days,
        "total_precipitation": total_precipitation,
        "representative_weather": representative_weather,
        "heavy_rain_days": heavy_rain_days,
        "strong_wind_days": strong_wind_days,
        "no_precipitation_days": no_precipitation_days
    }
