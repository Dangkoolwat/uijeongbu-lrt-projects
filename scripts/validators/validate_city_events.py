import os
import json
import csv
import re
from datetime import datetime

def validate_city_events(period: str, base_dir: str = "data") -> dict:
    """
    수집된 의정부 행사 CSV 파일을 읽어 무결성 검증을 수행하고,
    CSV의 validation_status 열을 갱신하며 검증 보고서 JSON을 생성합니다.
    """
    csv_path = os.path.join(base_dir, "raw", "external_cache", "city_events", "csv", f"{period}_events.csv")
    val_dir = os.path.join(base_dir, "raw", "external_cache", "city_events", "validation")
    os.makedirs(val_dir, exist_ok=True)
    val_json_path = os.path.join(val_dir, f"{period}_events_validation.json")
    
    report = {
        "period": period,
        "csv_path": csv_path,
        "status": "PASS",
        "total_events": 0,
        "valid_events": 0,
        "warning_events": 0,
        "invalid_events": 0,
        "errors": [],
        "warnings": []
    }
    
    if not os.path.exists(csv_path):
        report["status"] = "FAIL"
        report["errors"].append(f"행사 CSV 파일이 존재하지 않습니다: {csv_path}")
        with open(val_json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return report
        
    events = []
    seen_combinations = set()
    
    # 1. CSV 데이터 로드
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(dict(row))
            
    report["total_events"] = len(events)
    
    # 2. 개별 행사 검증 및 보정
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    updated_events = []
    
    for idx, ev in enumerate(events):
        row_status = "VALID"
        row_msg = []
        
        # 규칙 1: event_title 비어있는지 체크
        title = ev.get("event_title", "").strip()
        if not title:
            row_status = "INVALID"
            row_msg.append("행사명이 비어 있습니다.")
            
        # 규칙 2: start_date YYYY-MM-DD 형식 체크
        start_date = ev.get("start_date", "").strip()
        if not date_regex.match(start_date):
            row_status = "INVALID"
            row_msg.append(f"시작일 형식이 YYYY-MM-DD가 아닙니다: '{start_date}'")
            
        # 규칙 3: end_date 비어 있으면 start_date와 동일 보정
        end_date = ev.get("end_date", "").strip()
        if not end_date:
            end_date = start_date
            ev["end_date"] = end_date
            
        # 규칙 4: end_date가 start_date보다 빠르면 오류
        if date_regex.match(start_date) and date_regex.match(end_date):
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                if end_dt < start_dt:
                    row_status = "INVALID"
                    row_msg.append(f"종료일({end_date})이 시작일({start_date})보다 빠릅니다.")
            except Exception as e:
                row_status = "INVALID"
                row_msg.append(f"날짜 비교 중 요류 발생: {e}")
                
        # 규칙 5: detail_url 상대경로 절대화 (수집기에서 수행하나 재검증)
        detail_url = ev.get("detail_url", "").strip()
        if detail_url and detail_url.startswith("/"):
            detail_url = f"https://ui4u.go.kr{detail_url}"
            ev["detail_url"] = detail_url
            
        # 규칙 6: 중복 검사 (event_title + start_date + place)
        place = ev.get("place", "").strip()
        combo = (title, start_date, place)
        if combo in seen_combinations:
            row_status = "WARNING"
            row_msg.append("중복된 행사 정보입니다.")
        else:
            seen_combinations.add(combo)
            
        # 규칙 7: 대상 월(period)과 겹치는지 체크
        if date_regex.match(start_date) and date_regex.match(end_date):
            # period: YYYY-MM
            p_year, p_month = map(int, period.split("-"))
            try:
                s_dt = datetime.strptime(start_date, "%Y-%m-%d")
                e_dt = datetime.strptime(end_date, "%Y-%m-%d")
                
                # 해당 월 범위
                import calendar
                last_day = calendar.monthrange(p_year, p_month)[1]
                month_start = datetime(p_year, p_month, 1)
                month_end = datetime(p_year, p_month, last_day)
                
                # 날짜 교집합 여부 확인
                if s_dt > month_end or e_dt < month_start:
                    row_status = "WARNING"
                    row_msg.append(f"분석 대상 기간({period})에 속하지 않는 행사입니다.")
            except Exception:
                pass
                
        # 상태 기록
        ev["validation_status"] = row_status
        updated_events.append(ev)
        
        # 리포트 통계 업데이트
        if row_status == "INVALID":
            report["invalid_events"] += 1
            report["errors"].append(f"행사 ID {ev.get('event_id')}: {', '.join(row_msg)}")
        elif row_status == "WARNING":
            report["warning_events"] += 1
            report["warnings"].append(f"행사 ID {ev.get('event_id')}: {', '.join(row_msg)}")
        else:
            report["valid_events"] += 1
            
    # 전체 정합성 결정
    if report["invalid_events"] > 0:
        report["status"] = "FAIL"
    elif report["warning_events"] > 0:
        report["status"] = "WARNING"
        
    # 3. CSV 파일 업데이트
    if updated_events:
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=updated_events[0].keys())
            writer.writeheader()
            for ev in updated_events:
                writer.writerow(ev)
                
    # 4. 검증 리포트 JSON 저장
    with open(val_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        
    print(f"[Events] 검증 완료: Status -> {report['status']} (Errors: {len(report['errors'])}, Warnings: {len(report['warnings'])})")
    return report

if __name__ == "__main__":
    import sys
    period = sys.argv[1] if len(sys.argv) > 1 else "2026-05"
    validate_city_events(period)
