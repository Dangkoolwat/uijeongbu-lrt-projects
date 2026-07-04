# 풍향 각도를 8방위 문자열로 변환하는 모듈 (scripts/utils/wind_direction.py)

def to_text(degree: float) -> str:
    """풍향 각도(0 ~ 360)를 사람이 읽기 쉬운 한글 8방위 텍스트로 변환"""
    try:
        deg = float(degree)
    except (ValueError, TypeError):
        return "풍향 불명"

    # 360도로 노멀라이즈
    deg = deg % 360

    if (deg >= 337.5) or (deg < 22.5):
        return "북풍"
    elif 22.5 <= deg < 67.5:
        return "북동풍"
    elif 67.5 <= deg < 112.5:
        return "동풍"
    elif 112.5 <= deg < 157.5:
        return "남동풍"
    elif 157.5 <= deg < 202.5:
        return "남풍"
    elif 202.5 <= deg < 247.5:
        return "남서풍"
    elif 247.5 <= deg < 292.5:
        return "서풍"
    elif 292.5 <= deg < 337.5:
        return "북서풍"
    return "풍향 불명"
