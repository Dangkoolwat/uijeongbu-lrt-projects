import os
import csv
import random
from datetime import datetime, timedelta

def generate_sample_ridership_data(period: str = "2026-05", output_dir: str = "data/raw/ridership"):
    """
    분석 시나리오에 부합하는 정밀한 의정부 경전철 승하차 가상 CSV 데이터를 생성합니다.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 20260531 형식의 파일명 지정
    file_name = f"경기도_의정부시_경전철_승하차_현황_{period.replace('-', '')}31.csv"
    output_path = os.path.join(output_dir, file_name)
    
    # 공식 역 리스트
    stations = [
        "발곡", "회룡", "범골", "경전철의정부", "의정부시청", "흥선", "의정부중앙", 
        "동오", "새말", "경기도청북부청사", "효자", "곤제", "어룡", "송산", "탑석"
    ]
    
    # 시간대별 컬럼 정의 (00시~01시부터 23시~24시까지)
    hour_cols = [f"{h:02d}시~{h+1:02d}시" for h in range(24)]
    header = ["일자", "역명", "구분"] + hour_cols
    
    # 2026-05 날짜 범위 생성
    start_date = datetime.strptime(f"{period}-01", "%Y-%m-%d")
    days_in_month = 31 # 5월
    
    # 공휴일 매핑
    holidays = {
        "2026-05-05",  # 어린이날 (행사 있음)
        "2026-05-24",  # 부처님오신날 (비 옴)
        "2026-05-25"   # 대체공휴일
    }
    
    random.seed(42) # 동일한 테스트 데이터를 얻기 위한 시드 고정
    
    rows = []
    
    for day_offset in range(days_in_month):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        
        is_weekend = current_date.weekday() in (5, 6)
        is_holiday = date_str in holidays
        day_type = "weekend" if (is_weekend or is_holiday) else "weekday"
        
        # 시나리오 요인들
        weather_factor = 1.0
        # 5월 24일은 강수가 심해서 수송객 감소 시나리오 (0.75 배)
        if date_str == "2026-05-24":
            weather_factor = 0.72
        # 5월 5일은 어린이날 축제 행사로 이용객 증가 시나리오 (1.28 배)
        elif date_str == "2026-05-05":
            weather_factor = 1.30
            
        for station in stations:
            # 역별 가중치 (회룡역이 환승역이므로 압도적으로 많음)
            station_factor = 1.0
            if station == "회룡":
                station_factor = 3.5
            elif station in ["경기도청북부청사", "탑석", "의정부시청"]:
                station_factor = 1.5
            elif station in ["곤제", "효자"]:
                station_factor = 0.5
                
            for ride_type in ["승차", "하차"]:
                row_data = {"일자": date_str, "역명": station, "구분": ride_type}
                
                # 시간대별 승객수 산출
                for h in range(24):
                    base_count = 50.0
                    
                    # 시간대별 분산 패턴 (통근 노선 시나리오)
                    if day_type == "weekday":
                        # 평일 출퇴근 피크
                        if h == 8:  # 오전 출근
                            base_count = 950.0 if ride_type == "승차" else 450.0
                        elif h == 7:
                            base_count = 650.0 if ride_type == "승차" else 300.0
                        elif h == 18: # 오후 퇴근
                            base_count = 450.0 if ride_type == "승차" else 980.0
                        elif h == 19:
                            base_count = 350.0 if ride_type == "승차" else 620.0
                        else:
                            # 낮 및 심야 시간
                            if 9 <= h <= 16:
                                base_count = 180.0
                            else:
                                base_count = 40.0
                    else:
                        # 주말/공휴일 패턴 (완만하게 분산)
                        if 11 <= h <= 17:
                            base_count = 350.0
                        elif 8 <= h <= 10 or 18 <= h <= 20:
                            base_count = 200.0
                        else:
                            base_count = 30.0
                            
                    # 랜덤 노이즈 추가 및 각종 가중치 반영
                    noise = random.uniform(0.9, 1.1)
                    final_count = int(base_count * station_factor * weather_factor * noise)
                    # 심야 미운행 시간 보정 (01시 ~ 04시)
                    if 1 <= h <= 4:
                        final_count = random.randint(0, 5)
                        
                    row_data[f"{h:02d}시~{h+1:02d}시"] = max(0, final_count)
                    
                rows.append(row_data)
                
    # CSV 저장
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"[Generator] 테스트용 경전철 승하차 데이터 생성 완료 -> {output_path} (총 {len(rows)}행)")
    return output_path

if __name__ == "__main__":
    generate_sample_ridership_data()
