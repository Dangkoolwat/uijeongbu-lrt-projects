import os
import json
import requests
import pandas as pd
import yaml
from scripts.utils import date_utils

# 설정 파일 로딩
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config", "collectors.yml"
)

def get_config():
    """collectors.yml 설정 로드"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f).get("weather", {})
        except Exception:
            pass
    # 기본값 반환
    return {
        "api_url": "https://archive-api.open-meteo.com/v1/archive",
        "default_params": {
            "latitude": 37.74,
            "longitude": 127.03,
            "timezone": "Asia/Seoul",
            "daily": [
                "temperature_2m_mean", "temperature_2m_max", "temperature_2m_min",
                "precipitation_sum", "rain_sum", "weather_code", "wind_speed_10m_max"
            ]
        }
    }

def collect_weather(period: str, output_base_dir: str = "data") -> tuple[str, str]:
    """
    Open-Meteo Archive API를 사용하여 대상 월의 날씨 데이터를 수집 및 캐싱합니다.
    - period: 'YYYY-MM' 형식
    - 반환값: (json_path, csv_path)
    """
    cfg = get_config()
    
    # 1. 파일 저장 경로 설정
    json_dir = os.path.join(output_base_dir, "raw", "external_cache", "weather", "json")
    csv_dir = os.path.join(output_base_dir, "raw", "external_cache", "weather", "csv")
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)
    
    json_path = os.path.join(json_dir, f"{period}_weather.json")
    csv_path = os.path.join(csv_dir, f"{period}_weather.csv")
    
    # 2. 캐시 확인
    if os.path.exists(json_path) and os.path.exists(csv_path):
        print(f"[Weather] 이미 캐시된 데이터가 존재합니다: {json_path}")
        return json_path, csv_path
        
    # 3. 날짜 범위 산출 (예: 2026-05-01 ~ 2026-05-31)
    start_date, end_date = date_utils.month_range(period)
    
    # 4. API 파라미터 빌드
    api_url = cfg.get("api_url", "https://archive-api.open-meteo.com/v1/archive")
    params = cfg.get("default_params", {}).copy()
    params["start_date"] = start_date
    params["end_date"] = end_date
    
    # daily 파라미터를 API가 기대하는 comma-separated 문자열로 결합
    if isinstance(params.get("daily"), list):
        params["daily"] = ",".join(params["daily"])
        
    print(f"[Weather] Open-Meteo API 호출 시작: {api_url} ({start_date} ~ {end_date})")
    
    try:
        response = requests.get(api_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # 5. Raw JSON 캐시 저장
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        # 6. CSV 변환 저장
        if "daily" in data:
            daily_data = data["daily"]
            df = pd.DataFrame(daily_data)
            # time 열을 date로 이름 변경
            df = df.rename(columns={"time": "date"})
            df.to_csv(csv_path, index=False, encoding="utf-8")
            print(f"[Weather] 날씨 데이터 저장 완료: CSV -> {csv_path}")
        else:
            raise KeyError("API 응답에 'daily' 데이터가 포함되어 있지 않습니다.")
            
    except Exception as e:
        print(f"[Weather] 데이터 수집 오류 발생: {e}")
        # 혹시 기존 캐시가 없는데 실패한 경우 에러 전파
        raise e
        
    return json_path, csv_path

if __name__ == "__main__":
    import sys
    period = sys.argv[1] if len(sys.argv) > 1 else "2026-05"
    collect_weather(period)
