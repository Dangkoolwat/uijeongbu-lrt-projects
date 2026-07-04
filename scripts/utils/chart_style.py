import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# templates/design.md에 기술된 프리미엄 색상 시스템 정의
COLORS = {
    "primary": "#0f172a",       # Slate 900
    "secondary": "#64748b",     # Slate 500
    "accent_blue": "#3b82f6",    # Blue 500
    "accent_cyan": "#06b6d4",    # Cyan 500
    "success": "#10b981",        # Emerald 500
    "danger": "#ef4444",         # Red 500
    "light_bg": "#f8fafc",       # Slate 50
    "grid_color": "#e2e8f0",     # Slate 200 (라이트 모드 그리드용)
    "white": "#ffffff"
}

def setup_korean_font():
    """시스템 내 한글 폰트를 검색하여 matplotlib에 설정하고 폰트명을 반환합니다."""
    # Mac OS 환경의 물리적 폰트 직접 등록을 통해 한글 Glyph 깨짐 경고 해결
    mac_font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
    if os.path.exists(mac_font_path):
        try:
            fm.fontManager.addfont(mac_font_path)
            plt.rcParams["font.family"] = "AppleGothic"
            plt.rcParams["axes.unicode_minus"] = False
            return "AppleGothic"
        except Exception:
            pass

    # 일반적인 시스템 폰트 탐색 우선순위
    target_fonts = ["Apple SD Gothic Neo", "AppleGothic", "NanumGothic", "Malgun Gothic", "Noto Sans CJK KR", "NanumBarunGothic"]
    
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    selected_font = "sans-serif"
    
    for font_name in target_fonts:
        if font_name in available_fonts:
            selected_font = font_name
            break
            
    plt.rcParams["font.family"] = selected_font
    plt.rcParams["axes.unicode_minus"] = False  # 마이너스 기호 깨짐 방지
    return selected_font

def get_font_properties():
    """한글 처리를 위해 물리적 폰트 경로를 가리키는 FontProperties를 반환합니다."""
    mac_font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
    if os.path.exists(mac_font_path):
        return fm.FontProperties(fname=mac_font_path)
    win_font_path = "C:/Windows/Fonts/malgun.ttf"
    if os.path.exists(win_font_path):
        return fm.FontProperties(fname=win_font_path)
    return fm.FontProperties(family="sans-serif")

def apply_premium_style(ax, title: str = "", xlabel: str = "", ylabel: str = "", show_grid: bool = True):
    """
    matplotlib Axes에 design.md 가이드에 따른 프리미엄 스타일을 적용합니다.
    """
    font_name = setup_korean_font()
    font_prop = get_font_properties()
    
    # 1. 배경색 및 선 스타일 설정
    ax.set_facecolor(COLORS["light_bg"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLORS["secondary"])
    ax.spines["bottom"].set_color(COLORS["secondary"])
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)
    
    # 2. 타이틀 및 라벨 폰트 설정
    if title:
        font_prop_title = get_font_properties()
        font_prop_title.set_size(14)
        font_prop_title.set_weight("bold")
        ax.set_title(title, color=COLORS["primary"], pad=15, fontproperties=font_prop_title)
    if xlabel:
        font_prop_label = get_font_properties()
        font_prop_label.set_size(11)
        ax.set_xlabel(xlabel, color=COLORS["secondary"], labelpad=8, fontproperties=font_prop_label)
    if ylabel:
        font_prop_label = get_font_properties()
        font_prop_label.set_size(11)
        ax.set_ylabel(ylabel, color=COLORS["secondary"], labelpad=8, fontproperties=font_prop_label)
        
    # 3. 축 눈금 한글 폰트 설정
    font_prop_tick = get_font_properties()
    font_prop_tick.set_size(9)
    for label in ax.get_xticklabels():
        label.set_fontproperties(font_prop_tick)
    for label in ax.get_yticklabels():
        label.set_fontproperties(font_prop_tick)
    ax.tick_params(colors=COLORS["secondary"])
    
    # 4. 그리드 설정
    if show_grid:
        ax.grid(True, linestyle="--", linewidth=0.5, color=COLORS["grid_color"], alpha=0.7)
        ax.set_axisbelow(True)  # 그리드를 차트 뒤로 보냄
        
    # 5. 범례 스타일 설정
    legend = ax.get_legend()
    if legend:
        legend.get_frame().set_facecolor(COLORS["white"])
        legend.get_frame().set_edgecolor(COLORS["grid_color"])
        legend.get_frame().set_boxstyle("round,pad=0.4")
        legend.get_frame().set_alpha(0.9)
        font_prop_leg = get_font_properties()
        font_prop_leg.set_size(9)
        for text in legend.get_texts():
            text.set_color(COLORS["primary"])
            text.set_fontproperties(font_prop_leg)
