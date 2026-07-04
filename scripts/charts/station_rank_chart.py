import os
import pandas as pd
import matplotlib.pyplot as plt
from scripts.utils import chart_style

def generate_station_rank_chart(period: str, base_dir: str = "data", output_dir: str = "outputs") -> str:
    """
    역별 이용량 순위를 가로 막대 차트로 시각화하여 저장합니다.
    """
    summary_path = os.path.join(base_dir, "processed", "monthly", period, "station_summary.csv")
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"역별 요약 파일이 존재하지 않습니다: {summary_path}")
        
    df = pd.read_csv(summary_path)
    # 역명이 인덱스가 되거나 정렬된 상태 유지
    # 순위가 높은(이용량이 많은) 역이 위로 오도록 역순 정렬
    df_sorted = df.sort_values(by="total_count", ascending=True)
    
    # 1. 도화지(Figure) 설정 - 800px * 480px = 약 8 * 4.8인치
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # 2. 막대 생성
    # 기본은 accent_blue, 최상위 역(가장 마지막 역)은 primary 컬러로 포인트
    colors = [chart_style.COLORS["accent_blue"]] * len(df_sorted)
    if len(colors) > 0:
        colors[-1] = chart_style.COLORS["primary"] # 1위 역 강조
        
    bars = ax.barh(df_sorted["station"], df_sorted["total_count"], color=colors, height=0.6)
    
    # 막대 끝에 숫자 라벨 추가
    for bar in bars:
        width = bar.get_width()
        ax.text(width + (width * 0.01), bar.get_y() + bar.get_height()/2, 
                f"{int(width):,}", 
                va='center', ha='left', fontsize=8, color=chart_style.COLORS["secondary"])
                
    # 3. 스타일링 적용
    title = f"의정부 경전철 역별 이용량 순위 ({period})"
    chart_style.apply_premium_style(ax, title=title, xlabel="총 이용객 수 (승차+하차, 명)", ylabel="역명")
    
    # X축 범위 조금 넓혀서 숫자 라벨 안잘리게 방지
    max_val = df_sorted["total_count"].max()
    ax.set_xlim(0, max_val * 1.15)
    
    # 천 단위 콤마 포매팅
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    # 4. 저장 처리
    charts_dir = os.path.join(output_dir, "monthly", period, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    output_path = os.path.join(charts_dir, "station_rank.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    
    print(f"[Chart] 역별 순위 차트 저장 완료 -> {output_path}")
    return output_path
