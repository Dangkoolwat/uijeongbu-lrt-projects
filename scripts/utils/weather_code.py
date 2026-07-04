# Open-Meteo WMO Weather Code 한글 설명 변환 모듈 (scripts/utils/weather_code.py)

WEATHER_CODE_MAP = {
    0: "맑음",
    1: "대체로 맑음",
    2: "부분적으로 흐림",
    3: "흐림",
    45: "안개",
    48: "짙은 안개",
    51: "약한 이슬비",
    53: "보통 이슬비",
    55: "강한 이슬비",
    61: "약한 비",
    63: "비",
    65: "강한 비",
    71: "약한 눈",
    73: "눈",
    75: "폭설",
    80: "소나기",
    81: "강한 소나기",
    82: "매우 강한 소나기",
    95: "뇌우",
    96: "뇌우 및 약한 우박",
    99: "뇌우 및 강한 우박"
}

def to_korean(code: int) -> str:
    """WMO 날씨 코드를 한글 설명 문자열로 변환"""
    try:
        val = int(code)
        return WEATHER_CODE_MAP.get(val, f"알 수 없음(코드:{val})")
    except (ValueError, TypeError):
        return "알 수 없음"
