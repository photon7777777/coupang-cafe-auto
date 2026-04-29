from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os

from scraper import scrape_coupang
from gemini_helper import generate_blog_post
from naver_cafe import post_to_naver_cafe

app = FastAPI(title="쿠팡 카페 포스팅 자동화")

# 디렉토리 설정
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

class WorkflowRequest(BaseModel):
    coupang_url: str
    partners_id: str
    gemini_key: str
    guidelines: str
    naver_id: str
    naver_pw: str
    cafe_id: str
    menu_id: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/run-workflow")
async def run_workflow(req: WorkflowRequest):
    try:
        # Step 1: 데이터 추출
        scrape_result = scrape_coupang(req.coupang_url)
        if not scrape_result.get("success"):
            return JSONResponse(status_code=400, content={"success": False, "step": "scraping", "error": scrape_result.get("error")})
            
        if scrape_result.get("product_name") == "제품명 알 수 없음":
            return JSONResponse(status_code=400, content={"success": False, "step": "scraping", "error": "쿠팡 상품 정보를 정상적으로 가져오지 못했습니다. 입력하신 URL이 정확한 모바일/PC 상품 주소인지 확인해 주세요."})

        # Step 2: 파트너스 링크 생성 (가상)
        # 실제 API가 없으므로 간단히 쿼리 파라미터 조합으로 모사
        partner_link = f"{req.coupang_url}&af_id={req.partners_id}"
        
        # Step 3: AI 콘텐츠 생성
        content_full = generate_blog_post(
            api_key=req.gemini_key,
            product_info=scrape_result,
            guidelines=req.guidelines,
            partner_link=partner_link
        )
        
        # 빈 줄 제거 및 첫 번째 텍스트를 제목으로
        lines = [line for line in content_full.split('\n') if line.strip()]
        title = lines[0].replace("#", "").replace("*", "").strip()
        if len(title) > 40:
            title = title[:40] + "..."
            
        body = '\n'.join(lines[1:]).strip()

        # Step 4: 네이버 카페 포스팅
        post_result = post_to_naver_cafe(
            naver_id=req.naver_id,
            naver_pw=req.naver_pw,
            cafe_id=req.cafe_id,
            menu_id=req.menu_id,
            title=title,
            content=body,
            partner_link=partner_link, # 링크 별도 전달
            image_url=scrape_result.get("image_url", "")
        )
        
        if not post_result.get("success"):
            return JSONResponse(status_code=500, content={"success": False, "step": "posting", "error": post_result.get("error")})

        return JSONResponse(content={
            "success": True,
            "product_name": scrape_result["product_name"],
            "title": title,
            "content_preview": body[:100] + "...",
            "message": "워크플로우가 성공적으로 완료되었습니다."
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
