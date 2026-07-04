import re
from datetime import datetime, date
import calendar

# 2026년 공식 공휴일 목록 (분석 타겟인 2026년 기준 공휴일)
# 어린이날(5/5), 부처님오신날(5/24), 부처님오신날 대체공휴일(5/25) 등 5월 주요 공휴일
PUBLIC_HOLIDAYS_2026 = {
    "2026-01-01",  # 신정
    "2026-02-16", "2026-02-17", "2026-02-18",  # 설날 연휴
    "2026-03-01",  # 삼일절
    "2026-03-02",  # 삼일절 대체공휴일
    "2026-05-05",  # 어린이날
    "2026-05-24",  # 부처님오신날
    "2026-05-25",  # 부처님오신날 대체공휴일
    "2026-06-06",  # 현충일
    "2026-08-15",  # 광복절
    "2026-08-17",  # 광복절 대체공휴일
    "2026-09-24", "2026-09-25", "2026-09-26",  # 추석 연휴
    "2026-10-03",  # 개천절
    "2026-10-09",  # 한글날
    "2026-12-25"   # 성탄절
}

def parse_date(date_value: str) -> date:
    """날짜 문자열을 date 객체로 일관성 있게 파싱"""
    clean_val = str(date_value).strip().replace("-", "").replace("/", "")
    if len(clean_val) == 8:
        return datetime.strptime(clean_val, "%Y%m%d").date()
    elif len(clean_val) == 6:
        # YYYYMM 형식인 경우 해당 월의 1일로 파싱
        return datetime.strptime(clean_val + "01", "%Y%m%d").date()
    else:
        raise ValueError(f"지원되지 않는 날짜 형식: {date_value}")

def extract_yyyymmdd_from_filename(filename: str) -> str:
    """파일명에서 YYYYMMDD 형태의 날짜 문자열 추출"""
    match = re.search(r"\d{8}", filename)
    if match:
        return match.group(0)
    raise ValueError(f"파일명에서 8자리 날짜를 찾을 수 없습니다: {filename}")

def period_from_yyyymmdd(value: str) -> str:
    """YYYYMMDD -> YYYY-MM 변환"""
    clean_val = value.replace("-", "").replace("/", "")
    if len(clean_val) < 6:
        raise ValueError(f"잘못된 날짜 값: {value}")
    return f"{clean_val[:4]}-{clean_val[4:6]}"

def month_range(period: str) -> tuple[str, str]:
    """YYYY-MM -> (YYYY-MM-01, YYYY-MM-last_day) 변환"""
    parts = period.split("-")
    year, month = int(parts[0]), int(parts[1])
    last_day = calendar.monthrange(year, month)[1]
    return f"{period}-01", f"{period}-{last_day:02d}"

def weekday_ko(date_value: str) -> str:
    """날짜 문자열 -> 한글 요일명 (월~일)"""
    dt = parse_date(date_value)
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    return weekdays[dt.weekday()]

def is_month_start(date_value: str) -> bool:
    """월초(1일) 여부 판단"""
    dt = parse_date(date_value)
    return dt.day == 1

def is_month_end(date_value: str) -> bool:
    """월말 여부 판단"""
    dt = parse_date(date_value)
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return dt.day == last_day

def is_holiday_or_weekend(date_value: str) -> bool:
    """해당 날짜가 주말 또는 법정 공휴일인지 여부 판단"""
    dt = parse_date(date_value)
    # 주말 여부 (5: 토요일, 6: 일요일)
    if dt.weekday() in (5, 6):
        return True
    
    # 공휴일 포맷 확인
    formatted_date = dt.strftime("%Y-%m-%d")
    return formatted_date in PUBLIC_HOLIDAYS_2026

def get_day_type(date_value: str) -> str:
    """평일 / 주말 / 공휴일 유형 문자열 반환"""
    dt = parse_date(date_value)
    formatted_date = dt.strftime("%Y-%m-%d")
    if formatted_date in PUBLIC_HOLIDAYS_2026:
        return "공휴일"
    elif dt.weekday() in (5, 6):
        return "주말"
    else:
        return "평일"
