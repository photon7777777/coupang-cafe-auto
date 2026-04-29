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

def post_to_naver_cafe(naver_id: str, naver_pw: str, cafe_id: str, menu_id: str, title: str, content: str, partner_link: str, image_url: str, product_name: str = ""):
    """
    미리 로그인된 브라우저 프로필을 사용하여 네이버 카페에 글을 작성합니다.
    """
    options = uc.ChromeOptions()
    # 사용자 프로필 디렉토리 지정 (세션 유지)
    options.add_argument(f"--user-data-dir={BROWSER_PROFILE_DIR}")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-popup-blocking")
    
    driver = None
    try:
        step = "크롬 브라우저 시작"
        # headless 모드가 아닐 때 연결 오류가 잦으면 아래와 같이 포트를 고정하기도 함
        # options.add_argument("--remote-debugging-port=9222") 
        driver = uc.Chrome(options=options, version_main=CHROME_VERSION_MAIN)
        
        step = "1. 로그인 상태 확인 (세션 유지 체크)"
        driver.get("https://www.naver.com/") # 네이버 메인에서 확인하는 것이 더 정확함
        random_delay()
        
        # '내 정보' 또는 '로그아웃' 버튼이 있으면 이미 로그인된 상태임
        is_logged_in = False
        try:
            # 로그인된 상태에서만 보이는 요소들 (프로필 영역, 로그아웃 버튼 등)
            # Naver 메인 페이지의 다양한 로그인 상태 지표들
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".gnb_my_interface, .gnb_btn_login_off, #gnb_login_button, .MyView-module__my_info___fP_Yp, .log_out, .btn_logout"))
            )
            is_logged_in = True
            print("[INFO] 기존 세션이 유효합니다. 로그인을 건너뜁니다.")
        except:
            # 쿠키 확인 (NID_AUT 또는 NID_SES 쿠키가 있으면 로그인된 것으로 간주)
            cookies = driver.get_cookies()
            if any(cookie['name'] in ['NID_AUT', 'NID_SES'] for cookie in cookies):
                is_logged_in = True
                print("[INFO] 쿠키 기반으로 로그인 상태 확인됨.")
            else:
                # 확실치 않을 경우 카페 메인에서 로그인 버튼 유무 확인
                driver.get("https://cafe.naver.com/")
                time.sleep(2)
                login_btns = driver.find_elements(By.XPATH, "//a[contains(@href, 'nidlogin.login')]")
                if not login_btns:
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
            
            step = "1-3-1. 로그인 상태 유지 체크"
            try:
                keep_checkbox_selectors = ["#keep", "#login_chk", ".input_keep", "input[name='nvlong']"]
                keep_checkbox = None
                for sel in keep_checkbox_selectors:
                    try:
                        keep_checkbox = driver.find_element(By.CSS_SELECTOR, sel)
                        if keep_checkbox:
                            break
                    except:
                        continue
                
                if keep_checkbox and not keep_checkbox.is_selected():
                    try:
                        driver.execute_script("arguments[0].click();", keep_checkbox)
                        print("[INFO] JS로 '로그인 상태 유지' 체크박스를 클릭했습니다.")
                    except:
                        keep_label = driver.find_element(By.CSS_SELECTOR, f"label[for='{keep_checkbox.get_attribute('id')}']")
                        keep_label.click()
                        print("[INFO] Label을 통해 '로그인 상태 유지' 체크박스를 클릭했습니다.")
                time.sleep(0.5)
            except Exception as e:
                print(f"[WARN] 로그인 상태 유지 체크 실패: {e}")
                
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
        # 더 넓은 범위의 선택자로 본문 영역 탐색
        body_selectors = [
            ".se-main-container",
            ".se-content",
            ".se-component-content",
            ".se-text-paragraph",
            "[contenteditable='true']"
        ]
        
        body_input = None
        for sel in body_selectors:
            try:
                el = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                if el:
                    body_input = el
                    break
            except:
                continue

        if not body_input:
             raise Exception("본문 입력 영역을 찾을 수 없습니다.")
        
        # JS를 이용한 강제 클릭 및 포커스 지정
        driver.execute_script("arguments[0].focus(); arguments[0].click();", body_input)
        time.sleep(2) 
        
        # 제목칸에서 포커스가 벗어날 때 발생하는 Alert 무시 (여러 번 뜰 수 있으므로 루프 처리)
        for _ in range(5):
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
                
                # 에디터 재클릭 후 이미지 붙여넣기
                driver.execute_script("arguments[0].focus(); arguments[0].click();", body_input)
                time.sleep(1)
                actions = ActionChains(driver)
                actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                print("[INFO] 이미지 붙여넣기 완료. 업로드 대기 중 (5초)...")
                time.sleep(5) # 업로드 및 렌더링 대기
                actions.send_keys(Keys.ENTER).perform() 
                print("[INFO] 이미지 상단 삽입 완료")
            except Exception as img_e:
                print(f"[ERROR] 이미지 삽입 실패: {img_e}")

        step = "7-2. 본문 텍스트 클립보드 붙여넣기"
        # 이미지 삽입 후 포커스가 흐트러졌을 수 있으므로 다시 클릭
        driver.execute_script("arguments[0].focus(); arguments[0].click();", body_input)
        time.sleep(1)
        
        pyperclip.copy(content)
        try:
            actions = ActionChains(driver)
            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            time.sleep(1)
            actions.send_keys(Keys.ENTER).send_keys(Keys.ENTER).perform() 
            print("[INFO] 본문 텍스트 삽입 완료")
        except Exception as e:
            print(f"[WARN] 본문 삽입 중 오류(Alert 가능성): {e}")
            try:
                driver.switch_to.alert.accept()
                time.sleep(0.5)
                ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            except:
                pass
        
        step = "7-3. 툴바 '링크' 기능으로 링크 추가"
        link_success = False
        
        # 1. 단축키 (Ctrl + K) 우선 시도 - 가장 안정적임
        try:
            print("[INFO] 단축키(Ctrl+K)로 링크 팝업 호출 시도...")
            ActionChains(driver).key_down(Keys.CONTROL).send_keys('k').key_up(Keys.CONTROL).perform()
            time.sleep(1.5)
        except Exception as e:
            print(f"[WARN] 단축키 시도 실패: {e}")
            
        # 단축키로 안 열렸다면 버튼 찾기
        link_input_selectors = [
            "input.se-popup-link-url",
            "input.se-custom-layer-input",
            "input.se-popup-url",
            "input.se-link-input",
            "input[placeholder*='URL']"
        ]
        
        def is_link_input_visible():
            for sel in link_input_selectors:
                try:
                    el = driver.find_element(By.CSS_SELECTOR, sel)
                    if el and el.is_displayed():
                        return el
                except:
                    pass
            return None

        link_input = is_link_input_visible()
        
        # 2. 단축키로 입력창이 안 열렸다면 버튼 직접 찾아서 클릭
        if not link_input:
            print("[INFO] 툴바의 링크 버튼 탐색 시도...")
            link_btn_selectors = [
                "button.se-popup-button-link",
                "button[data-name='link']",
                "button[title='링크']",
                ".se-btn-tool-link",
                "//button[.//span[contains(text(), '링크')]]",
                "button.se-link"
            ]
            link_btn = None
            for sel in link_btn_selectors:
                try:
                    if sel.startswith("//"):
                        link_btn = driver.find_element(By.XPATH, sel)
                    else:
                        link_btn = driver.find_element(By.CSS_SELECTOR, sel)
                    if link_btn and link_btn.is_displayed():
                        break
                except:
                    continue
                    
            if link_btn:
                try:
                    # JS 강제 클릭
                    driver.execute_script("arguments[0].click();", link_btn)
                    time.sleep(1.5)
                    link_input = is_link_input_visible()
                except Exception as e:
                    print(f"[WARN] 링크 버튼 클릭 실패: {e}")
        
        # 3. 링크 입력창에 URL 입력
        if link_input:
            try:
                pyperclip.copy(partner_link)
                link_input.click()
                link_input.send_keys(Keys.CONTROL, "v")
                time.sleep(1)
                link_input.send_keys(Keys.ENTER)
                time.sleep(1)
                
                try:
                    time.sleep(1.5) # 버튼이 렌더링될 시간 확보
                    confirm_selectors = [
                        "button.se-popup-button-confirm", 
                        "button.se-popup-url-button", 
                        "button[data-name='confirm']",
                        ".se-popup-link button",
                        "button[title='확인']",
                        "button[title='적용']",
                        ".se-popup-button-confirm span"
                    ]
                    confirm_btn = None
                    for sel in confirm_selectors:
                        try:
                            el = driver.find_element(By.CSS_SELECTOR, sel)
                            if el and el.is_displayed():
                                confirm_btn = el
                                break
                        except:
                            pass
                            
                    if confirm_btn:
                        try:
                            driver.execute_script("arguments[0].focus();", confirm_btn)
                            confirm_btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", confirm_btn)
                        print("[INFO] 링크 팝업의 '확인(저장)' 버튼을 클릭했습니다.")
                    else:
                        # 최후의 수단으로 엔터 한 번 더 입력
                        ActionChains(driver).send_keys(Keys.ENTER).perform()
                except:
                    pass
                    
                print("[INFO] 스마트에디터 링크 기능으로 삽입 완료")
                time.sleep(5)
                link_success = True
            except Exception as e:
                print(f"[WARN] 링크 URL 입력 중 오류: {e}")
        
        # 4. 모두 실패 시 폴백(본문에 그냥 입력)
        if not link_success:
            print("[INFO] 스마트에디터 링크 추가 실패. 본문에 직접 URL 입력 후 카드로 변환합니다.")
            pyperclip.copy(partner_link)
            actions = ActionChains(driver)
            actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            time.sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            print("[INFO] 링크 카드 생성 대기 중 (7초)...")
            time.sleep(7)
            
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

        # 등록 후 페이지 전환 대기 및 검증
        is_posted = False
        final_url = ""
        for _ in range(15):
            time.sleep(2)
            current_url = driver.current_url.lower()
            # 성공 시 보통 /articles/ 또는 ArticleRead 형태의 주소로 이동함
            if "write" not in current_url and ("/articles/" in current_url or "articleread" in current_url):
                is_posted = True
                final_url = driver.current_url
                break
            
            # 아직 글쓰기 페이지라면 등록 버튼 다시 시도 (안 눌렸을 가능성 대비)
            if "write" in current_url:
                try:
                    driver.execute_script("document.querySelector('.BaseButton--skinGreen').click();")
                except:
                    pass
        
        if not is_posted:
            print(f"[WARN] 등록 후 페이지 이동이 감지되지 않았습니다. 현재 주소: {driver.current_url}")
            # 이동은 안 됐지만 글쓰기 주소가 아니면 일단 성공으로 간주
            if "write" not in driver.current_url.lower():
                is_posted = True
        else:
            # 게시글이 정상 등록된 경우 댓글 작성 시도
            if product_name:
                try:
                    step = "9. 댓글 작성 시도"
                    print(f"[INFO] 댓글 작성을 시도합니다: {product_name}")
                    
                    # 댓글 입력창 대기
                    comment_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.comment_inbox_text, .CommentWriter textarea"))
                    )
                    
                    comment_text = f"'{product_name}'을 추천드리니 한번 사용해보세요!"
                    
                    # 댓글 입력
                    comment_input.click()
                    time.sleep(1)
                    pyperclip.copy(comment_text)
                    comment_input.send_keys(Keys.CONTROL, "v")
                    time.sleep(1)
                    
                    # 댓글 등록 버튼 클릭
                    comment_submit = driver.find_element(By.CSS_SELECTOR, ".btn_register, .comment_inbox .btn_register, .CommentWriter .btn_register")
                    comment_submit.click()
                    print("[INFO] 댓글 작성을 완료했습니다.")
                    time.sleep(2)
                except Exception as e:
                    print(f"[WARN] 댓글 작성 중 오류 발생 (무시하고 진행): {e}")

        time.sleep(3)
        res_msg = "네이버 카페 포스팅이 완료되었습니다."
        if final_url:
            res_msg += f" (주소: {final_url})"
        else:
            res_msg += " 카페에서 글을 확인해 주세요."
            
        return {"success": True, "message": res_msg}
        
    except Exception as e:
        # 에러 메시지에 어느 단계에서 실패했는지 포함
        return {"success": False, "error": f"[{step}] 중 오류 발생: {str(e)}"}
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
