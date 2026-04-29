import time
import random
import os
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import MIN_DELAY, MAX_DELAY, BROWSER_PROFILE_DIR, TEMP_DIR, CHROME_VERSION_MAIN

def download_image(url: str, filename: str) -> str:
    """이미지 URL을 로컬로 다운로드합니다."""
    filepath = os.path.join(TEMP_DIR, filename)
    try:
        resp = requests.get(url, stream=True, timeout=10)
        resp.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return filepath
    except Exception as e:
        raise Exception(f"이미지 다운로드 실패: {e}")

def random_delay():
    """랜덤 지연 시간 추가"""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

def copy_image_to_clipboard(file_path: str):
    """윈도우 PowerShell을 사용하여 이미지를 클립보드에 복사합니다."""
    import subprocess
    abs_path = os.path.abspath(file_path)
    # PowerShell 명령어로 이미지를 클립보드에 세팅 (System.Windows.Forms 사용)
    cmd = f"powershell -ExecutionPolicy Bypass -Command \"Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile('{abs_path}'))\""
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"[INFO] 이미지를 클립보드에 복사했습니다: {abs_path}")
    except Exception as e:
        print(f"[ERROR] 클립보드 복사 중 오류 발생: {e}")

def post_to_naver_cafe(naver_id: str, naver_pw: str, cafe_id: str, menu_id: str, title: str, content: str, partner_link: str, image_url: str):
    """
    미리 로그인된 브라우저 프로필을 사용하여 네이버 카페에 글을 작성합니다.
    """
    options = uc.ChromeOptions()
    # 사용자 프로필 디렉토리 지정 (세션 유지)
    options.add_argument(f"--user-data-dir={BROWSER_PROFILE_DIR}")
    options.add_argument("--window-size=1280,900")
    
    driver = None
    try:
        step = "크롬 브라우저 시작"
        driver = uc.Chrome(options=options, version_main=CHROME_VERSION_MAIN)
        
        step = "1. 로그인 상태 확인 (세션 유지 체크)"
        driver.get("https://www.naver.com/") # 네이버 메인에서 확인하는 것이 더 정확함
        random_delay()
        
        # '내 정보' 또는 '로그아웃' 버튼이 있으면 이미 로그인된 상태임
        is_logged_in = False
        try:
            # 로그인된 상태에서만 보이는 요소들 (프로필 영역, 로그아웃 버튼 등)
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".gnb_my_interface, .gnb_btn_login_off, #gnb_login_button, .MyView-module__my_info___fP_Yp"))
            )
            is_logged_in = True
            print("[INFO] 기존 세션이 유효합니다. 로그인을 건너뜁니다.")
        except:
            # 로그인 버튼이 보이는지 확인
            login_btns = driver.find_elements(By.XPATH, "//a[contains(@href, 'nidlogin.login')]")
            if not login_btns:
                # 확실치 않을 경우 한 번 더 카페 페이지에서 체크
                driver.get("https://cafe.naver.com/")
                if not driver.find_elements(By.XPATH, "//a[contains(@href, 'nidlogin.login')]"):
                    is_logged_in = True
                    print("[INFO] 카페 페이지에서 로그인 상태 확인됨.")
        
        if not is_logged_in:
            step = "1-1. 네이버 로그인 페이지 접속"
            print("[INFO] 로그인이 필요합니다. 자동 로그인을 시작합니다.")
            driver.get("https://nid.naver.com/nidlogin.login")
            random_delay()
            
            step = "1-2. 아이디 입력"
            pyperclip.copy(naver_id)
            id_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "id")))
            id_input.click()
            id_input.send_keys(Keys.CONTROL, "v")
            time.sleep(1)
            
            step = "1-3. 비밀번호 입력"
            pyperclip.copy(naver_pw)
            pw_input = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "pw")))
            pw_input.click()
            pw_input.send_keys(Keys.CONTROL, "v")
            time.sleep(1)
            
            step = "1-4. 로그인 버튼 클릭"
            login_btn = driver.find_element(By.ID, "log.login")
            login_btn.click()
            time.sleep(3)
            random_delay()
        else:
            print("[INFO] 이미 로그인되어 있어 단계를 생략합니다.")
        
        step = "2. 카페 메인으로 이동하여 clubid 추출"
        driver.get(f"https://cafe.naver.com/{cafe_id}")
        random_delay()
        
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
            
        import re
        match = re.search(r"clubid\s*=?\s*['\"]?([0-9]+)", driver.page_source, re.IGNORECASE)
        if not match:
            match = re.search(r"g_sClubId\s*=\s*['\"]?([0-9]+)", driver.page_source)
            
        if match:
            numeric_clubid = match.group(1)
            # 최신 SPA(ca-fe/f-e) 글쓰기 URL 양식 적용
            write_url = f"https://cafe.naver.com/ca-fe/cafes/{numeric_clubid}/menus/{menu_id}/articles/write?boardType=L"
        else:
            # 구형(전통적) URL 양식
            write_url = f"https://cafe.naver.com/{cafe_id}?iframe_url=/ArticleWrite.nhn%3Fm%3Dwrite%26menuid%3D{menu_id}"
            
        step = "3. 글쓰기 페이지 진입 및 Alert 처리"
        driver.get(write_url)
        random_delay()
        
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        
        step = "4. 글쓰기 메인 프레임 탐색"
        # 구형 UI의 경우 cafe_main iframe이 존재함. 최신 UI는 iframe 없이 직접 렌더링됨.
        try:
            WebDriverWait(driver, 5).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "cafe_main"))
            )
            is_iframe_mode = True
        except:
            is_iframe_mode = False # 최신 UI(ca-fe) 환경
            pass
        
        step = "5. 제목 입력 대기"
        title_selectors = [
            "textarea.textarea_input", 
            "input.textarea_input", 
            "input#subject", 
            ".se-title-text", 
            "textarea[placeholder*='제목']",
            "input[placeholder*='제목']",
            ".title_area input"
        ]
        
        title_input = None
        # 넉넉하게 60초 대기 (네이버 에디터 로딩이나 사용자의 수동 로그인/캡차 해제 시간 고려)
        for _ in range(10): 
            for sel in title_selectors:
                try:
                    # 요소가 화면에 표시될 때까지 대기
                    title_input = driver.find_element(By.CSS_SELECTOR, sel)
                    if title_input and title_input.is_displayed():
                        break
                except:
                    pass
            if title_input and title_input.is_displayed():
                break
            time.sleep(3)
                
        if not title_input:
            raise Exception("제목 입력칸을 찾을 수 없습니다. 메뉴 ID(게시판)가 글쓰기가 불가능한 곳(예: 전체글보기)이거나, 로그인이 안 되어있을 수 있습니다.")
            
        # 제목 입력 (JS로 직접 값을 설정하여 글자 수 제한 팝업 발생 억제)
        driver.execute_script("arguments[0].value = '';", title_input) # 초기화
        driver.execute_script("arguments[0].value = arguments[1];", title_input, title)
        # 리액트/뷰 등 프레임워크 상태 갱신을 위해 input 이벤트 강제 발생
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", title_input)
        driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", title_input)
        
        time.sleep(1)
        # 혹시 모를 Alert 처리 (포커스 이동 전 미리 확인)
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        random_delay()

        step = "6. 스마트에디터 로딩 대기"
        # 에디터 iframe 여부 확인 (최신 UI라도 에디터 자체는 iframe일 수 있음)
        try:
            editor_frame = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#editor_iframe, iframe.se-iframe"))
            )
            driver.switch_to.frame(editor_frame)
            is_editor_iframe = True
        except:
            is_editor_iframe = False
            pass
        
        step = "7. 본문 텍스트 입력 영역 대기 및 클릭"
        body_input = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".se-main-container, .se-component-content, .se-text-paragraph, .se-ff-nanumgothic"))
        )
        
        # JS를 이용한 강제 클릭 및 포커스 지정
        try:
            driver.execute_script("arguments[0].focus(); arguments[0].click();", body_input)
        except:
            body_input.click()
            pass
            
        time.sleep(2) # 경고창이 뜨는 시간을 넉넉히 기다림
        
        # 제목칸에서 포커스가 벗어날 때 발생하는 Alert 무시 (여러 번 뜰 수 있으므로 루프 처리)
        for _ in range(3):
            try:
                alert = driver.switch_to.alert
                alert.accept()
                time.sleep(0.5)
            except:
                break
        
        step = "7-1. 이미지 상단 삽입 (클립보드 방식)"
        if image_url:
            try:
                print(f"[INFO] 이미지 처리 중... URL: {image_url}")
                image_path = download_image(image_url, "temp_upload.jpg")
                copy_image_to_clipboard(image_path)
                
                # 에디터 클릭 후 바로 이미지 붙여넣기
                actions = ActionChains(driver)
                actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                time.sleep(3)
                actions.send_keys(Keys.ENTER).perform() # 이미지 아래로 줄바꿈
                print("[INFO] 이미지 상단 삽입 완료")
            except Exception as img_e:
                print(f"[ERROR] 이미지 삽입 실패: {img_e}")

        step = "7-2. 본문 텍스트 클립보드 붙여넣기"
        pyperclip.copy(content)
        try:
            actions = ActionChains(driver)
            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            actions.send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform() # 본문 뒤 공백 추가
        except Exception as e:
            if "alert" in str(e).lower():
                try:
                    driver.switch_to.alert.accept()
                    time.sleep(0.5)
                    ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                except:
                    pass
        
        step = "7-3. 링크 카드 생성 (URL 입력 + 엔터)"
        pyperclip.copy(partner_link)
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(2)
        actions.send_keys(Keys.ENTER).perform() # 엔터를 쳐야 링크 카드가 생성됨
        print("[INFO] 링크 카드 생성 대기 중 (7초)...")
        time.sleep(7) # 카드 생성을 위해 충분히 대기
        
        # URL 텍스트만 지우고 카드만 남기기
        try:
            actions.send_keys(Keys.ARROW_UP).perform()
            time.sleep(1)
            actions.key_down(Keys.SHIFT).send_keys(Keys.HOME).key_up(Keys.SHIFT).perform()
            actions.send_keys(Keys.BACKSPACE).perform()
            print("[INFO] URL 텍스트 삭제 완료 (카드만 남김)")
        except:
            pass

        # 최종적으로 메인 컨텐츠로 복귀
        driver.switch_to.default_content()
        if is_iframe_mode:
             try:
                 WebDriverWait(driver, 5).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "cafe_main")))
             except:
                 pass

        random_delay()

        step = "8. 등록 버튼 클릭"
        # 등록 버튼은 여러 형태일 수 있으므로 텍스트와 클래스로 검색
        submit_selectors = [
            ".BaseButton.BaseButton--skinGreen",
            "button.BaseButton--skinGreen",
            "a.BaseButton--skinGreen",
            ".tool_area .btn_register",
            "//button[contains(text(),'등록')]",
            "//span[contains(text(),'등록')]/parent::button"
        ]
        
        submit_btn = None
        for sel in submit_selectors:
            try:
                if sel.startswith("//"):
                    submit_btn = driver.find_element(By.XPATH, sel)
                else:
                    submit_btn = driver.find_element(By.CSS_SELECTOR, sel)
                
                if submit_btn and submit_btn.is_displayed():
                    submit_btn.click()
                    break
            except:
                continue
                
        if not submit_btn:
            # 강제 JS 클릭 시도
            try:
                driver.execute_script("document.querySelector('.BaseButton--skinGreen').click();")
            except:
                raise Exception("등록 버튼을 찾을 수 없습니다. 수동으로 등록을 눌러주세요.")

        time.sleep(5) # 등록 후 페이지 전환 대기
        
        return {"success": True, "message": "네이버 카페 포스팅이 성공적으로 완료되었습니다!"}
        
    except Exception as e:
        # 에러 메시지에 어느 단계에서 실패했는지 포함
        return {"success": False, "error": f"[{step}] 중 오류 발생: {str(e)}"}
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
