import os
import json
import pandas as pd
from scripts.utils import date_utils, station_utils

def validate_ridership_data(file_path: str, period: str) -> dict:
    """
    승하차 원본 CSV 데이터의 품질을 검증하고 결과를 요약 딕셔너리로 반환합니다.
    """
    results = {
        "file_name": os.path.basename(file_path),
        "status": "PASS",
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "errors": [],
        "warnings": []
    }
    
    if not os.path.exists(file_path):
        results["status"] = "FAIL"
        results["errors"].append(f"파일이 존재하지 않습니다: {file_path}")
        return results
        
    try:
        # 데이터 로드
        df = pd.read_csv(file_path, encoding="utf-8")
        results["total_rows"] = len(df)
        
        if df.empty:
            results["status"] = "FAIL"
            results["errors"].append("CSV 파일에 행 데이터가 존재하지 않습니다.")
            return results
            
        # 필수 컬럼 검사 (가정: 일자/날짜, 역명, 승하차 구분, 승하차 인원 컬럼 존재 여부)
        # 우리 프로젝트에서는 유연한 스키마 매칭을 위해 컬럼 정형화를 수행하므로, 
        # '역명' 및 '일자'(혹은 '날짜' 혹은 '사용일자') 컬럼 존재를 우선적으로 체크합니다.
        col_map = {c.replace(" ", ""): c for c in df.columns}
        
        required_keywords = ["역명", "일자", "날짜", "사용일"]
        found_keywords = [k for k in required_keywords if any(k in col_name for col_name in col_map.keys())]
        
        if not any("역명" in col for col in col_map.keys()):
            results["status"] = "FAIL"
            results["errors"].append("필수 컬럼인 '역명' 관련 컬럼이 누락되었습니다.")
            
        # 개별 행 검사
        invalid_cnt = 0
        valid_cnt = 0
        
        # 역명 검사 및 날짜 형식 검사
        # '일자' 컬럼 특정
        date_col = None
        for col in df.columns:
            c_clean = col.replace(" ", "")
            if "일자" in c_clean or "날짜" in c_clean or "사용일" in c_clean:
                date_col = col
                break
                
        station_col = None
        for col in df.columns:
            c_clean = col.replace(" ", "")
            if "역명" in c_clean:
                station_col = col
                break
                
        if not date_col or not station_col:
            results["status"] = "FAIL"
            results["errors"].append("일자 또는 역명 컬럼을 식별할 수 없습니다.")
            return results
            
        for idx, row in df.iterrows():
            row_valid = True
            
            # 1. 날짜 유효성 검사
            raw_date = str(row[date_col]).strip()
            try:
                date_obj = date_utils.parse_date(raw_date)
                # 대상 월(period)에 속하는지 체크
                row_period = date_utils.period_from_yyyymmdd(date_obj.strftime("%Y%m%d"))
                if row_period != period:
                    results["warnings"].append(f"라인 {idx+2}: 데이터 날짜({raw_date})가 대상 분석 월({period})과 다릅니다.")
            except Exception:
                row_valid = False
                results["errors"].append(f"라인 {idx+2}: 잘못된 날짜 형식입니다 -> '{raw_date}'")
                
            # 2. 역명 정규화 가능 여부 검사
            raw_station = str(row[station_col]).strip()
            norm_station = station_utils.normalize_name(raw_station)
            if norm_station not in station_utils.get_ordered_stations():
                results["warnings"].append(f"라인 {idx+2}: 공식 의정부 경전철 역명이 아닙니다 -> '{raw_station}'")
                
            # 3. 승하차 승객수 음수 검사
            # 승차/하차인원 컬럼(혹은 시간대별 승하차컬럼) 중 수치값이 음수인 항목이 있는지 체크
            for col in df.columns:
                if col in [date_col, station_col]:
                    continue
                val = row[col]
                try:
                    # 수치형 컬럼인 경우에만 음수 검사
                    num_val = float(val)
                    if num_val < 0:
                        row_valid = False
                        results["errors"].append(f"라인 {idx+2}, 컬럼 {col}: 승객 수는 음수일 수 없습니다 -> {val}")
                except ValueError:
                    # 텍스트 형태(예: '승차', '하차')는 넘어감
                    pass
            
            if row_valid:
                valid_cnt += 1
            else:
                invalid_cnt += 1
                
        results["valid_rows"] = valid_cnt
        results["invalid_rows"] = invalid_cnt
        
        if invalid_cnt > 0 or len(results["errors"]) > 0:
            results["status"] = "WARNING" if valid_cnt > 0 else "FAIL"
            
    except Exception as e:
        results["status"] = "FAIL"
        results["errors"].append(f"승하차 검증 실행 실패: {e}")
        
    return results

if __name__ == "__main__":
    import sys
    # 실행 테스트
    if len(sys.argv) > 2:
        res = validate_ridership_data(sys.argv[1], sys.argv[2])
        print(json.dumps(res, indent=2, ensure_ascii=False))
