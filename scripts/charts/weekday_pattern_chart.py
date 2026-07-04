import os
import pandas as pd
import matplotlib.pyplot as plt
from scripts.utils import chart_style

def generate_weekday_pattern_chart(period: str, base_dir: str = "data", output_dir: str = "outputs") -> str:
    """
    요일별 일평균 이용량을 세로 막대 차트로 시각화하여 저장합니다.
    (평일과 주말을 다른 색상으로 표현하여 시인성을 높임)
    """
    summary_path = os.path.join(base_dir, "processed", "monthly", period, "weekday_summary.csv")
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"요일별 요약 파일이 존재하지 않습니다: {summary_path}")
        
    df = pd.read_csv(summary_path)
    
    # 요일 순서(월~일) 확인 (0~6)
    df = df.sort_values(by="weekday")
    
    # 1. 도화지 설정
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # 2. 평일(월~금)과 주말(토~일) 막대 색상 구분
    colors = []
    for w in df["weekday"]:
        if w in (5, 6): # 토요일, 일요일
            colors.append(chart_style.COLORS["secondary"]) # 주말은 차분한 슬레이트 그레이
        else:
            colors.append(chart_style.COLORS["accent_blue"]) # 평일은 블루 강조
            
    bars = ax.bar(df["weekday_ko"], df["average_daily_count"], color=colors, width=0.55)
    
    # 막대 상단에 값 수치 표시
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + (height * 0.01),
                f"{int(height):,}",
                ha='center', va='bottom', fontsize=9, color=chart_style.COLORS["primary"])
                
    # 3. 스타일링 적용
    title = f"요일별 하루 평균 이용객 추이 ({period})"
    chart_style.apply_premium_style(ax, title=title, xlabel="요일", ylabel="일평균 이용객 수 (명)")
    
    # Y축 포매팅 및 범위 마진 확보
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    max_val = df["average_daily_count"].max()
    ax.set_ylim(0, max_val * 1.12)
    
    # 4. 저장 처리
    charts_dir = os.path.join(output_dir, "monthly", period, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    output_path = os.path.join(charts_dir, "weekday_pattern.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    
    print(f"[Chart] 요일별 패턴 차트 저장 완료 -> {output_path}")
    return output_path
