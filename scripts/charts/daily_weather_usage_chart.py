import os
import pandas as pd
import matplotlib.pyplot as plt
from scripts.utils import chart_style

def generate_daily_weather_usage_chart(period: str, base_dir: str = "data", output_dir: str = "outputs") -> str:
    """
    일별 경전철 이용객수(꺾은선)와 일강수량(막대)을 이중 축 차트로 비교하여 저장합니다.
    """
    matches_path = os.path.join(base_dir, "processed", "monthly", period, "event_matches.csv")
    if not os.path.exists(matches_path):
        raise FileNotFoundError(f"이벤트 및 날씨 매핑 파일이 존재하지 않습니다: {matches_path}")
        
    df = pd.read_csv(matches_path)
    
    # 날짜를 '일' 단위 숫자로 간소화 (예: 2026-05-01 -> 1)
    df["day"] = df["date"].apply(lambda d: int(d.split("-")[2]))
    df = df.sort_values(by="day")
    
    # 1. 도화지 및 첫 번째 축(이용객 수) 생성
    fig, ax1 = plt.subplots(figsize=(8, 5))
    
    # 2. 이용객 수 꺾은선 플롯
    line = ax1.plot(df["day"], df["total_count"], 
                     color=chart_style.COLORS["accent_blue"], label="일일 이용객 수",
                     linewidth=2.0, marker="o", markersize=4)
                     
    # Y1축 라벨 설정
    ax1.set_ylabel("일일 이용객 수 (명)", color=chart_style.COLORS["accent_blue"], fontsize=11)
    ax1.tick_params(axis='y', labelcolor=chart_style.COLORS["accent_blue"], labelsize=9)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    # Y1축 그리드 제거 (이중축 간 간섭 방지를 위해)
    chart_style.apply_premium_style(ax1, title=f"일별 이용객 추이 및 일강수량 비교 ({period})", 
                                     xlabel="일자 (일)", ylabel="", show_grid=True)
                                     
    # Y1축의 레이블 컬러를 accent_blue로 조정
    ax1.spines["left"].set_color(chart_style.COLORS["accent_blue"])
    ax1.spines["left"].set_linewidth(1.2)
    
    # 3. 두 번째 축(강수량) 생성
    ax2 = ax1.twinx()
    
    # 강수량 막대 플롯
    # 반투명 처리하여 선 그래프와 겹쳐도 보이도록 함
    bars = ax2.bar(df["day"], df["precipitation_sum"], 
                   color=chart_style.COLORS["accent_cyan"], alpha=0.4, 
                   width=0.6, label="일강수량 (mm)")
                   
    # Y2축 라벨 설정
    ax2.set_ylabel("일강수량 (mm)", color=chart_style.COLORS["secondary"], fontsize=11)
    ax2.tick_params(axis='y', labelcolor=chart_style.COLORS["secondary"], labelsize=9)
    ax2.spines["right"].set_color(chart_style.COLORS["accent_cyan"])
    ax2.spines["right"].set_linewidth(1.2)
    ax2.spines["top"].set_visible(False)
    
    # 강수량이 0 이상인 날만 표시하도록 Y2축의 상한 설정 (그 외에는 0~최대강수량)
    max_precip = df["precipitation_sum"].max()
    if max_precip > 0:
        ax2.set_ylim(0, max_precip * 3) # 차트 상단 1/3 영역에만 막대가 오도록 축 밸런싱
    else:
        ax2.set_ylim(0, 10) # 강수량 없어도 고정 범주 제공
        
    # X축 범위 조정 (1일부터 말일까지)
    ax1.set_xlim(0.5, len(df) + 0.5)
    ax1.set_xticks(range(1, len(df) + 1, 2)) # 2일 간격으로 X축 눈금 표시
    
    # 범례 합치기
    lines, labels = ax1.get_legend_handles_labels()
    # bar는 Container 형태이므로 직접 patch를 참조하거나 proxy 사용
    lines2, labels2 = ax2.get_legend_handles_labels()
    
    # custom legend style
    leg = ax1.legend(lines + lines2, labels + labels2, loc="upper right")
    leg.get_frame().set_facecolor(chart_style.COLORS["white"])
    leg.get_frame().set_edgecolor(chart_style.COLORS["grid_color"])
    leg.get_frame().set_alpha(0.9)
    for text in leg.get_texts():
        text.set_color(chart_style.COLORS["primary"])
        text.set_fontsize(9)
        
    # 4. 저장 처리
    charts_dir = os.path.join(output_dir, "monthly", period, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    output_path = os.path.join(charts_dir, "daily_weather_usage.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    
    print(f"[Chart] 일별 날씨/이용객 비교 차트 저장 완료 -> {output_path}")
    return output_path
