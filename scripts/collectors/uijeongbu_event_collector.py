import os
import csv
import json
import datetime
import requests
import urllib3
import yaml
import holidays

urllib3.disable_warnings()

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config", "collectors.yml"
)

def get_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return yaml.safe_load(f).get("city_events", {})
        except Exception:
            pass
    return {
        "source_url": "https://ui4u.go.kr/portal/eventNoti/custom/monthlyData.do",
        "request_timeout": 15
    }

def collect_events(period: str, output_base_dir: str = "data") -> tuple[str, str]:
    """
    의정부시청 행사 숨겨진 API(JSON)를 호출하여 파싱 후 CSV 파일로 저장합니다.
    - period: 'YYYY-MM' 형식
    """
    cfg = get_config()
    # config 파일에 기존 calendar.do 주소가 남아있을 수 있으므로 JSON 전용 API로 강제 고정
    api_endpoint_url = "https://ui4u.go.kr/portal/eventNoti/custom/monthlyData.do"
    source_url = cfg.get("source_url", api_endpoint_url) # 이건 detail_url 용도로 남겨둠
    timeout = cfg.get("request_timeout", 15)
    
    # 1. 경로 설정
    json_dir = os.path.join(output_base_dir, "raw", "external_cache", "city_events", "json")
    csv_dir = os.path.join(output_base_dir, "raw", "external_cache", "city_events", "csv")
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)
    
    json_path = os.path.join(json_dir, f"{period}_events.json")
    csv_path = os.path.join(csv_dir, f"{period}_events.csv")
    
    events_data = []
    
    # 2. 수집 및 캐싱 (JSON 저장)
    if os.path.exists(json_path):
        print(f"[Events] 이미 캐시된 JSON이 존재합니다: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            events_data = json.load(f)
    else:
        print(f"[Events] 의정부시청 행사 JSON API 크롤링 요청: {api_endpoint_url} (searchByMonth: {period})")
        try:
            payload = {"searchByMonth": period, "mId": "0301170200"}
            res = requests.post(api_endpoint_url, data=payload, verify=False, timeout=timeout)
            res.raise_for_status()
            parsed_json = res.json()
            if "list" in parsed_json:
                events_data = parsed_json["list"]
            else:
                events_data = []
                
        except Exception as e:
            print(f"[Events] 웹 스크래핑(API) 실패 ({e}). 데이터 없음으로 처리합니다.")
            events_data = []
            
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(events_data, f, ensure_ascii=False, indent=2)
            
    # 3. CSV 변환
    events = []
    collected_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 3-1. 공휴일 자동 추출 및 병합
    try:
        parts = period.split("-")
        year, month = int(parts[0]), int(parts[1])
        kr_holidays = holidays.KR(years=year)
        
        for date_obj, name in sorted(kr_holidays.items()):
            if date_obj.month == month:
                date_str = date_obj.strftime("%Y-%m-%d")
                events.append({
                    "event_id": f"HOL_{date_str.replace('-', '')}",
                    "event_title": name,
                    "start_date": date_str,
                    "end_date": date_str,
                    "place": "전국",
                    "department": "법정공휴일",
                    "category": "공휴일",
                    "detail_url": "",
                    "source_url": "holidays.KR",
                    "collected_at": collected_at,
                    "validation_status": "VALIDATED"
                })
    except Exception as e:
        print(f"[Events] 공휴일 로드 실패 ({e})")
    
    for idx, item in enumerate(events_data):
        events.append({
            "event_id": f"EVT_{period.replace('-', '')}_{idx+1:03d}",
            "event_title": item.get("colTitle", ""),
            "start_date": item.get("colSday", ""),
            "end_date": item.get("colEday", ""),
            "place": "의정부시 관내",
            "department": "시청 부서",
            "category": item.get("colCate", "기타"),
            "detail_url": f"https://ui4u.go.kr/portal/eventNoti/custom/view.do?eventSeq={item.get('idx', '')}",
            "source_url": source_url,
            "collected_at": collected_at,
            "validation_status": "UNVALIDATED"
        })
            
    # 4. CSV 저장
    columns = [
        "event_id", "event_title", "start_date", "end_date", "place", 
        "department", "category", "detail_url", "source_url", "collected_at", 
        "validation_status"
    ]
    
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for ev in events:
            writer.writerow(ev)
            
    print(f"[Events] 행사 데이터 저장 완료: CSV -> {csv_path} (총 {len(events)}건)")
    return json_path, csv_path

if __name__ == "__main__":
    import sys
    period = sys.argv[1] if len(sys.argv) > 1 else "2026-05"
    collect_events(period)
