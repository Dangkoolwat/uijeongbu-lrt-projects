import os
import yaml

# project.yml 경로 설정
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config", "project.yml"
)

# 기본값 매핑 (project.yml 로드 실패 대비 예비용)
FALLBACK_STATIONS = [
    {"id": "LRT101", "name": "발곡", "zone": "신곡권역"},
    {"id": "LRT102", "name": "회룡", "zone": "호원권역"},
    {"id": "LRT103", "name": "범골", "zone": "호원권역"},
    {"id": "LRT104", "name": "경전철의정부", "zone": "의정부권역"},
    {"id": "LRT105", "name": "의정부시청", "zone": "의정부권역"},
    {"id": "LRT106", "name": "흥선", "zone": "흥선권역"},
    {"id": "LRT107", "name": "의정부중앙", "zone": "의정부권역"},
    {"id": "LRT108", "name": "동오", "zone": "신곡권역"},
    {"id": "LRT109", "name": "새말", "zone": "신곡권역"},
    {"id": "LRT110", "name": "경기도청북부청사", "zone": "송산권역"},
    {"id": "LRT111", "name": "효자", "zone": "송산권역"},
    {"id": "LRT112", "name": "곤제", "zone": "송산권역"},
    {"id": "LRT113", "name": "어룡", "zone": "송산권역"},
    {"id": "LRT114", "name": "송산", "zone": "송산권역"},
    {"id": "LRT115", "name": "탑석", "zone": "송산권역"}
]

# 설정 로드
stations_list = FALLBACK_STATIONS
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            if cfg and "stations" in cfg:
                stations_list = cfg["stations"]
    except Exception:
        pass

# 검색 최적화를 위한 딕셔너리 구축
STATION_MAP = {s["name"]: s for s in stations_list}
STATION_ORDER = {s["name"]: i for i, s in enumerate(stations_list)}

def normalize_name(raw_name: str) -> str:
    """역명을 내부 표준 명칭(예: 회룡역 -> 회룡, 경전철 의정부 -> 경전철의정부)으로 정규화"""
    if not raw_name:
        return ""
    
    # 공백 제거 및 '역' 접미사 제거
    clean = str(raw_name).strip().replace(" ", "")
    if clean.endswith("역") and len(clean) > 2:
        # 단, '동오역' -> '동오', '새말역' -> '새말', '탑석역' -> '탑석'
        clean = clean[:-1]
    
    # 매핑 목록에 있는지 확인 후 유사 매칭 처리
    for std_name in STATION_MAP.keys():
        if std_name in clean or clean in std_name:
            return std_name
            
    return clean

def get_station_id(station_name: str) -> str:
    """정규화된 역명 기준으로 역 ID 반환"""
    norm = normalize_name(station_name)
    if norm in STATION_MAP:
        return STATION_MAP[norm]["id"]
    return "LRT999"

def get_station_zone(station_name: str) -> str:
    """정규화된 역명 기준으로 권역 반환"""
    norm = normalize_name(station_name)
    if norm in STATION_MAP:
        return STATION_MAP[norm]["zone"]
    return "기타권역"

def get_station_order(station_name: str) -> int:
    """정규화된 역명 기준으로 노선 순번 반환"""
    norm = normalize_name(station_name)
    return STATION_ORDER.get(norm, 999)

def get_ordered_stations() -> list[str]:
    """정렬된 순서대로 표준 역명 리스트 반환"""
    return [s["name"] for s in stations_list]
