# PDF 보고서 변환 모듈 (scripts/renderers/pdf_renderer.py)
import os
from playwright.sync_api import sync_playwright

def convert_html_to_pdf(html_path: str, output_pdf_path: str) -> bool:
    """
    HTML 보고서 파일을 PDF 파일로 컴파일 및 변환합니다.
    Playwright headless 브라우저를 띄워 CSS 및 배경 그래픽이 온전히 렌더링된 PDF를 생성합니다.
    """
    abs_html_path = os.path.abspath(html_path)
    if not os.path.exists(abs_html_path):
        print(f"[PDF Renderer] 변환할 HTML 파일이 존재하지 않습니다: {abs_html_path}")
        return False
        
    print(f"[PDF Renderer] PDF 변환 가동: {abs_html_path} -> {output_pdf_path}")
    
    try:
        with sync_playwright() as p:
            # headless 브라우저 실행
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 로컬 파일 URL
            file_url = f"file://{abs_html_path}"
            
            # 페이지 로드 및 네트워크 유휴 대기
            page.goto(file_url, wait_until="networkidle")
            
            # PDF 출력 옵션: 배경색 출력 보존, 마진 제거하여 HTML 레이아웃 준수
            page.pdf(
                path=output_pdf_path,
                format="A4",
                print_background=True,
                margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"}
            )
            
            browser.close()
        print(f"[PDF Renderer] PDF 보고서 변환 성공: {output_pdf_path}")
        return True
    except Exception as e:
        print(f"[PDF Renderer] PDF 변환 실패: {e}")
        return False
