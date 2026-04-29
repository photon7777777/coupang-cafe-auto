"""
쿠팡 카페 자동화 - 전역 설정
"""
import os

# 프로젝트 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp_images")

# 한글 경로 문제를 방지하기 위해 프로필 경로는 시스템 로컬 앱 데이터 폴더 사용
import os
local_app_data = os.environ.get('LOCALAPPDATA', BASE_DIR)
BROWSER_PROFILE_DIR = os.path.join(local_app_data, "CoupangAutoBot", "profile")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 필요한 디렉토리 생성
for d in [TEMP_DIR, BROWSER_PROFILE_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)

# 브라우저 설정
CHROME_VERSION_MAIN = 147
DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# 지연 시간 설정 (초)
MIN_DELAY = 3
MAX_DELAY = 7
PAGE_LOAD_WAIT = 5

# 네이버 카페 관련
NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"
NAVER_CAFE_BASE = "https://cafe.naver.com"

# 쿠팡 파트너스
COUPANG_PARTNERS_BASE = "https://partners.coupang.com"
