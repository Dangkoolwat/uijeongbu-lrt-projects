import os
import pandas as pd
import matplotlib.pyplot as plt
from scripts.utils import chart_style

def generate_hourly_pattern_chart(period: str, base_dir: str = "data", output_dir: str = "outputs") -> str:
    """
    시간대별 이용량 패턴(승차/하차)을 선 차트로 시각화하여 저장합니다.
    """
    summary_path = os.path.join(base_dir, "processed", "monthly", period, "hourly_summary.csv")
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"시간대별 요약 파일이 존재하지 않습니다: {summary_path}")
        
    df = pd.read_csv(summary_path)
    
    # 1. 도화지 및 축 눈금 설정
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # 2. 꺾은선 그래프 플롯
    ax.plot(df["hour"], df["ride_count"], 
            color=chart_style.COLORS["accent_blue"], label="승차", 
            linewidth=2.5, marker="o", markersize=5)
            
    ax.plot(df["hour"], df["alight_count"], 
            color=chart_style.COLORS["accent_cyan"], label="하차", 
            linewidth=2.5, marker="s", markersize=5)
            
    # 3. 스타일링 적용
    title = f"시간대별 이용객 분산 패턴 ({period})"
    chart_style.apply_premium_style(ax, title=title, xlabel="시간대 (시)", ylabel="이용객 수 (명)")
    
    # X축 24시간 눈금 세밀 조정
    ax.set_xticks(range(0, 24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)])
    
    # Y축 포매팅
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    # 범례 활성화
    ax.legend(loc="upper right")
    
    # 4. 저장 처리
    charts_dir = os.path.join(output_dir, "monthly", period, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    output_path = os.path.join(charts_dir, "hourly_pattern.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()
    
    print(f"[Chart] 시간대별 패턴 차트 저장 완료 -> {output_path}")
    return output_path
