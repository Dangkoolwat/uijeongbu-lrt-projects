import os
import json
from jinja2 import Template

def render_html_report(period: str, base_dir: str = "data", template_dir: str = "templates", output_dir: str = "outputs") -> str:
    """
    정제된 3종의 JSON 분석 데이터를 읽어 Jinja2 템플릿에 매핑하고 
    최종 프리미엄 HTML 보고서를 렌더링합니다.
    """
    processed_dir = os.path.join(base_dir, "processed", "monthly", period)
    data_json_path = os.path.join(processed_dir, "report_data.json")
    context_json_path = os.path.join(processed_dir, "external_context.json")
    narrative_json_path = os.path.join(processed_dir, "report_narrative.json")
    
    # 1. 파일 검증
    for p in [data_json_path, context_json_path, narrative_json_path]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"필수 렌더링 데이터가 존재하지 않습니다: {p}")
            
    # 2. JSON 로드
    with open(data_json_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)
    with open(context_json_path, "r", encoding="utf-8") as f:
        external_context = json.load(f)
    with open(narrative_json_path, "r", encoding="utf-8") as f:
        report_narrative = json.load(f)
        
    # 3. 템플릿 로드
    template_path = os.path.join(template_dir, "monthly_report.html.j2")
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"HTML 템플릿 파일이 없습니다: {template_path}")
        
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    # 4. Jinja2 템플릿 컴파일 및 렌더링
    template = Template(template_content)
    rendered_html = template.render(
        report_data=report_data,
        external_context=external_context,
        report_narrative=report_narrative
    )
    
    # 5. 저장 처리
    out_dir = os.path.join(output_dir, "monthly", period)
    os.makedirs(out_dir, exist_ok=True)
    
    out_path = os.path.join(out_dir, "report.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rendered_html)
        
    print(f"[Renderer] HTML 보고서 생성 완료 -> {out_path}")
    return out_path
