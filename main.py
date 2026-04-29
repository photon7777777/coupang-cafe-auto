from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import os
import time
import asyncio

from scraper import scrape_coupang
from gemini_helper import generate_blog_post
from naver_cafe import post_to_naver_cafe

app = FastAPI(title="쿠팡 카페 포스팅 자동화")

# 전역 상태 관리
task_control = {
    "is_paused": False,
    "should_stop": False
}

# 디렉토리 설정
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

class WorkflowRequest(BaseModel):
    coupang_url: str
    partners_id: str
    gemini_key: str
    naver_id: str
    naver_pw: str
    cafe_id: str
    menu_id: str

class BulkWorkflowRequest(BaseModel):
    coupang_urls: List[str]
    partners_id: str
    gemini_key: str
    naver_id: str
    naver_pw: str
    cafe_id: str
    menu_id: str
    interval_minutes: int

def execute_single_posting(url: str, req_data: dict):
    """단일 상품에 대한 스크래핑-AI생성-포스팅 워크플로우를 실행합니다."""
    try:
        print(f"\n[INFO] 작업 시작: {url}")
        # Step 1: 데이터 추출
        scrape_result = scrape_coupang(url)
        if not scrape_result.get("success"):
            print(f"[ERROR] 스크래핑 실패: {scrape_result.get('error')}")
            return False
            
        # Step 2: 파트너스 링크 생성
        partner_link = f"{url}&af_id={req_data['partners_id']}"
        
        # Step 3: AI 콘텐츠 생성
        content_full = generate_blog_post(
            api_key=req_data['gemini_key'],
            product_info=scrape_result,
            partner_link=partner_link
        )
        
        lines = [line for line in content_full.split('\n') if line.strip()]
        title = lines[0].replace("#", "").replace("*", "").strip()
        body = '\n'.join(lines[1:]).strip()

        # Step 4: 네이버 카페 포스팅
        post_result = post_to_naver_cafe(
            naver_id=req_data['naver_id'],
            naver_pw=req_data['naver_pw'],
            cafe_id=req_data['cafe_id'],
            menu_id=req_data['menu_id'],
            title=title,
            content=body,
            partner_link=partner_link,
            image_url=scrape_result.get("image_url", ""),
            product_name=scrape_result.get("product_name", "")
        )
        
        if post_result.get("success"):
            print(f"[SUCCESS] 포스팅 완료: {title}")
            return True
        else:
            print(f"[ERROR] 포스팅 실패: {post_result.get('error')}")
            return False
    except Exception as e:
        print(f"[ERROR] 예외 발생: {str(e)}")
        return False

async def process_bulk_posting(req: BulkWorkflowRequest):
    """백그라운드에서 일정 간격으로 대량 포스팅을 수행합니다."""
    global task_control
    task_control["should_stop"] = False
    task_control["is_paused"] = False
    
    req_dict = req.dict()
    total = len(req.coupang_urls)
    
    for i, url in enumerate(req.coupang_urls):
        # 정지 요청 체크
        if task_control["should_stop"]:
            print("[BULK] 작업이 중단되었습니다.")
            break
            
        # 일시중지 체크 루프
        while task_control["is_paused"]:
            await asyncio.sleep(1)
            if task_control["should_stop"]:
                break
        
        if task_control["should_stop"]: break

        print(f"\n[BULK] 전체 {total}개 중 {i+1}번째 진행 중...")
        execute_single_posting(url, req_dict)
        
        # 마지막 아이템이 아니면 대기
        if i < total - 1:
            wait_seconds = req.interval_minutes * 60
            print(f"[BULK] 다음 포스팅까지 {req.interval_minutes}분 대기합니다...")
            
            # 대기 시간 동안에도 일시중지/정지 체크를 위해 1초씩 나눠서 대기
            for _ in range(wait_seconds):
                if task_control["should_stop"]: break
                while task_control["is_paused"]:
                    await asyncio.sleep(1)
                    if task_control["should_stop"]: break
                await asyncio.sleep(1)
    
    print("\n[BULK] 모든 예약 포스팅 작업이 완료되었습니다.")

@app.post("/api/pause")
async def toggle_pause():
    global task_control
    task_control["is_paused"] = not task_control["is_paused"]
    return JSONResponse(content={"is_paused": task_control["is_paused"]})

@app.post("/api/stop")
async def stop_task():
    global task_control
    task_control["should_stop"] = True
    task_control["is_paused"] = False
    return JSONResponse(content={"success": True})

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/run-workflow")
async def run_workflow(req: WorkflowRequest):
    # 기존 단일 포스팅 API (호환성 유지)
    success = execute_single_posting(req.coupang_url, req.dict())
    if success:
        return JSONResponse(content={"success": True, "message": "포스팅 성공"})
    else:
        return JSONResponse(status_code=500, content={"success": False, "message": "포스팅 실패"})

@app.post("/api/run-bulk-workflow")
async def run_bulk_workflow(req: BulkWorkflowRequest, background_tasks: BackgroundTasks):
    # 백그라운드 작업으로 등록하고 즉시 응답
    background_tasks.add_task(process_bulk_posting, req)
    return JSONResponse(content={
        "success": True, 
        "message": f"총 {len(req.coupang_urls)}개의 상품 포스팅 예약이 완료되었습니다. {req.interval_minutes}분 간격으로 진행됩니다."
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
