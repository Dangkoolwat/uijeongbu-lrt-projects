import os
import json
import calendar
import pandas as pd
from scripts.utils import date_utils

def validate_weather_data(period: str, base_dir: str = "data") -> dict:
    """
    수집된 과거 날씨 CSV 파일의 정합성을 검증하고 결과를 JSON 리포트로 저장합니다.
    """
    csv_path = os.path.join(base_dir, "raw", "external_cache", "weather", "csv", f"{period}_weather.csv")
    val_dir = os.path.join(base_dir, "raw", "external_cache", "weather", "validation")
    os.makedirs(val_dir, exist_ok=True)
    val_json_path = os.path.join(val_dir, f"{period}_weather_validation.json")
    
    report = {
        "period": period,
        "csv_path": csv_path,
        "status": "PASS",
        "total_days": 0,
        "valid_days": 0,
        "errors": [],
        "warnings": []
    }
    
    if not os.path.exists(csv_path):
        report["status"] = "FAIL"
        report["errors"].append(f"기상 CSV 파일이 존재하지 않습니다: {csv_path}")
        with open(val_json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return report
        
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
        report["total_days"] = len(df)
        
        # 1. 일수 정합성 검사 (윤년 고려 월의 총 일수 체크)
        year, month = map(int, period.split("-"))
        expected_days = calendar.monthrange(year, month)[1]
        
        if len(df) != expected_days:
            report["status"] = "FAIL"
            report["errors"].append(f"날씨 일수 데이터가 부족하거나 초과되었습니다: 기대치 {expected_days}일, 실측치 {len(df)}일")
            
        valid_cnt = 0
        for idx, row in df.iterrows():
            row_valid = True
            
            # 날짜 파싱
            date_str = str(row["date"]).strip()
            
            # 2. 기온 이상치 검사 (-40도 이하 혹은 50도 이상)
            for temp_col in ["temperature_2m_mean", "temperature_2m_max", "temperature_2m_min"]:
                if temp_col in df.columns:
                    val = row[temp_col]
                    if pd.isna(val):
                        row_valid = False
                        report["errors"].append(f"{date_str}: 기온 컬럼({temp_col})에 결측값이 존재합니다.")
                    elif val < -40.0 or val > 50.0:
                        row_valid = False
                        report["errors"].append(f"{date_str}: 기온 값({val})이 정상 범위(-40도 ~ 50도)를 이탈했습니다.")
                        
            # 3. 강수량 음수 검사
            if "precipitation_sum" in df.columns:
                p_sum = row["precipitation_sum"]
                if pd.isna(p_sum):
                    row_valid = False
                    report["errors"].append(f"{date_str}: 강수량 데이터가 누락되었습니다.")
                elif p_sum < 0.0:
                    row_valid = False
                    report["errors"].append(f"{date_str}: 강수량 값({p_sum})이 음수입니다.")
                    
            # 4. WMO 날씨 코드 유효성 검사 (0 ~ 99 범위)
            if "weather_code" in df.columns:
                w_code = row["weather_code"]
                if pd.isna(w_code):
                    row_valid = False
                    report["errors"].append(f"{date_str}: 기상 코드 데이터가 누락되었습니다.")
                elif int(w_code) < 0 or int(w_code) > 99:
                    row_valid = False
                    report["errors"].append(f"{date_str}: 잘못된 WMO 기상 코드 범위입니다 -> {w_code}")
                    
            if row_valid:
                valid_cnt += 1
                
        report["valid_days"] = valid_cnt
        if valid_cnt < expected_days:
            report["status"] = "FAIL" if valid_cnt == 0 else "WARNING"
            
    except Exception as e:
        report["status"] = "FAIL"
        report["errors"].append(f"기상 데이터 검증 프로세스 실행 중 예외 발생: {e}")
        
    # JSON 파일 저장
    with open(val_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        
    print(f"[Weather] 검증 완료: Status -> {report['status']} (Errors: {len(report['errors'])}, Warnings: {len(report['warnings'])})")
    return report

if __name__ == "__main__":
    import sys
    period = sys.argv[1] if len(sys.argv) > 1 else "2026-05"
    validate_weather_data(period)
