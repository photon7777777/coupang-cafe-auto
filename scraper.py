import re
import time
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from config import CHROME_VERSION_MAIN, DESKTOP_UA, TEMP_DIR

def fix_image_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        return "https:" + url
    if not url.startswith("http"):
        return "https://" + url
    return url

def scrape_coupang(url: str) -> dict:
    """쿠팡 URL에서 상품 정보를 스크래핑합니다."""
    options = uc.ChromeOptions()
    options.add_argument("--window-position=-2000,0")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={DESKTOP_UA}")
    
    driver = None
    try:
        driver = uc.Chrome(options=options, version_main=CHROME_VERSION_MAIN)
        driver.get(url)
        
        # 아카마이 챌린지 및 단축 URL 리다이렉션을 넉넉히 대기 (최대 15초)
        # 페이지 소스에 akamai가 있거나 상품 관련 태그가 없으면 더 대기합니다.
        for _ in range(15):
            html = driver.page_source
            if ("akamai" not in html.lower()) and ("sec-if-cpt-container" not in html) and ("link.coupang.com" not in driver.current_url):
                # 쿠팡 상품 요소가 보이기 시작하면 통과
                if "prod-buy-header__title" in html or "pdp-name" in html or "제품이 존재하지 않습니다" in html:
                    break
            time.sleep(1)
            
        time.sleep(2)
        
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(0.5)
            
        driver.execute_script("window.scrollTo(0, 0)")
        time.sleep(1)

        html = driver.page_source
        if "Access Denied" in html or "방문하신 사이트의 이용이 일시적으로 제한" in html:
            return {"success": False, "error": "봇 탐지 시스템에 의해 차단되었습니다."}

        soup = BeautifulSoup(html, 'html.parser')

        product_name = ""
        price_formatted = ""
        image_url = ""
        
        # 1. JSON-LD 파싱 시도 (가장 정확하고 레이아웃 변경에 강함)
        import json
        ld_json_scripts = soup.find_all("script", {"type": "application/ld+json"})
        for script in ld_json_scripts:
            try:
                data = json.loads(script.string)
                if data.get("@type") == "Product":
                    if not product_name:
                        product_name = data.get("name", "")
                    if not image_url and data.get("image"):
                        images = data.get("image")
                        image_url = images[0] if isinstance(images, list) else images
                    if not price_formatted and data.get("offers"):
                        offers = data.get("offers")
                        raw_price = offers.get("price") if isinstance(offers, dict) else (offers[0].get("price") if isinstance(offers, list) else None)
                        if raw_price:
                            price_formatted = f"{int(raw_price):,}원"
            except:
                continue

        # 2. JSON-LD에서 못 찾은 경우 기존 CSS 셀렉터 폴백
        if not product_name:
            for sel in [
                "h2.prod-buy-header__title", "span.prod-buy-header__title", "h1.prod-buy-header__title", 
                ".prod-buy-header__title", "span.identity-primary-item", 
                "div.pdp-name", "h1.pdp-name", ".pdp-product-name", ".product-name", "h1.product-title"
            ]:
                el = soup.select_one(sel)
                if el:
                    product_name = el.get_text(strip=True)
                    break
                    
        if not price_formatted:
            price = ""
            for sel in [
                "span.total-price strong", "strong.prod-sale-price", "span.price-value", 
                "strong.price-value", ".prod-price .total-price strong", 
                ".pdp-price", "span.sale-price"
            ]:
                el = soup.select_one(sel)
                if el:
                    price = el.get_text(strip=True)
                    break
            price_num = re.sub(r"[^\d]", "", price)
            price_formatted = f"{int(price_num):,}원" if price_num else price

        if not image_url:
            for sel in [
                "img.prod-image__detail", "img.prod-image-detail", "#repImageContainer img", 
                ".prod-image img", "img.pdp-image", ".pdp-image-container img", ".pdp-main-image img"
            ]:
                el = soup.select_one(sel)
                if el:
                    image_url = el.get("src") or el.get("data-img-src") or ""
                    break
                    
        image_url = fix_image_url(image_url)

        # 특징 텍스트 (단순화된 스크래핑)
        features = []
        feature_els = soup.select(".prod-description li, .prod-description p")
        for el in feature_els[:5]:
            text = el.get_text(strip=True)
            if text:
                features.append(text)

        if not product_name:
            import os
            debug_path = os.path.join(TEMP_DIR, "error_page.html")
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"[ERROR] 상품명을 찾을 수 없습니다. 현재 URL: {driver.current_url}")
            print(f"[ERROR] 페이지 제목: {soup.title.string if soup.title else '없음'}")

        return {
            "success": True,
            "product_name": product_name or "제품명 알 수 없음",
            "price": price_formatted,
            "image_url": image_url,
            "features": features,
            "url": driver.current_url, # 리다이렉트된 최종 주소 반환
        }
    except Exception as e:
        return {"success": False, "error": f"스크래핑 오류: {str(e)}"}
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
