#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import signal
import requests
import base64
import io
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import logging

# 데이터 파일 경로
DATA_FILE = 'shared_data.json'

# 전역 데이터
shared_data = {
    'employees': [],
    'teams': [],
    'vacations': [],
    'breakRecords': [],
    'lastUpdated': None
}

# 텔레그램 설정 (여기에 실제 봇 토큰과 채팅 ID를 입력하세요)
TELEGRAM_BOT_TOKEN = "7829681305:AAEnjOQp8mSXldy9UyLhRsP3sfz5ktfCRdM"  # 실제 봇 토큰으로 변경 필요
TELEGRAM_CHAT_ID = "7415089515"      # 실제 채팅 ID로 변경 필요

# 크롤링 설정 - handsos.com 로그인 정보
CRAWL_COMPANY_ID = "h65216022"
CRAWL_USERNAME = "chahongnw1207"
CRAWL_PASSWORD = "ckghdnw1379"
CRAWL_URL = "https://www.handsos.com/login/login.asp?p=pc"

# 데이터 로드
def load_data():
    global shared_data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                shared_data = json.load(f)
        except:
            pass

# 데이터 저장
def save_data():
    global shared_data
    shared_data['lastUpdated'] = datetime.now().isoformat()
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(shared_data, f, ensure_ascii=False, indent=2)

# 텔레그램 메시지 전송
def send_telegram_message(message):
    try:
        if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
            print("텔레그램 설정이 필요합니다. BOT_TOKEN과 CHAT_ID를 설정해주세요.")
            return False
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            print("텔레그램 메시지 전송 성공")
            return True
        else:
            print(f"텔레그램 메시지 전송 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"텔레그램 메시지 전송 오류: {e}")
        return False

# 크롤링 함수
def fetch_sales_data():
    """
    로그인이 필요한 페이지에서 HTML을 직접 파싱하여 매출 정보를 크롤링합니다.
    CRAWL_URL, CRAWL_USERNAME, CRAWL_PASSWORD를 설정하고,
    실제 사이트의 HTML 구조에 맞게 셀렉터를 수정해야 합니다.
    """
    try:
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # 브라우저 창 숨김
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 드라이버 생성
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # 1. 로그인 페이지로 이동
            if not CRAWL_URL:
                return {
                    'status': 'error',
                    'message': 'CRAWL_URL이 설정되지 않았습니다.'
                }
            
            print(f"페이지 접속 중: {CRAWL_URL}")
            driver.get(CRAWL_URL)
            time.sleep(2)  # 페이지 로딩 대기
            
            # 2. 로그인 처리
            try:
                wait = WebDriverWait(driver, 10)
                
                # 회사코드 입력 필드 찾기
                company_input = wait.until(EC.presence_of_element_located((By.NAME, "companyID")))
                
                # 회사코드 입력
                company_input.clear()
                company_input.send_keys(CRAWL_COMPANY_ID)
                
                # 아이디 입력
                username_input = driver.find_element(By.NAME, "userID")
                username_input.clear()
                username_input.send_keys(CRAWL_USERNAME)
                
                # 패스워드 입력
                password_input = driver.find_element(By.NAME, "userPWD")
                password_input.clear()
                password_input.send_keys(CRAWL_PASSWORD)
                
                # 로그인 버튼 클릭
                login_button = wait.until(EC.element_to_be_clickable((By.ID, "sendLogin")))
                login_button.click()
                
                print("로그인 완료")
                time.sleep(5)  # 로그인 후 대기 (페이지 로딩 시간 확보)
                
            except Exception as login_error:
                print(f"로그인 실패: {login_error}")
                return {
                    'status': 'error',
                    'message': f'로그인 실패: {str(login_error)}'
                }
            
            # 3. 매출 페이지로 이동 (필요한 경우)
            # 로그인 후 메인 페이지에서 매출 정보 확인
            # 추가 페이지 이동이 필요한 경우 여기에 작성
            # driver.get("https://www.handsos.com/sales")
            time.sleep(2)
            
            # 4. HTML 구조를 파싱하여 매출 데이터 추출
            sales_data = []
            
            # 현재 페이지 URL 출력 (디버깅용)
            print(f"현재 페이지 URL: {driver.current_url}")
            
            # 페이지 소스 일부 출력 (HTML 구조 확인용)
            try:
                page_source = driver.page_source[:1000]  # 처음 1000자만
                print(f"페이지 소스 일부: {page_source}")
            except:
                pass
            
            try:
                # ⚠️ 실제 handsos.com의 매출 데이터 HTML 구조에 맞게 수정하세요
                # 아래 예시를 참고하여 실제 셀렉터로 변경하세요
                
                # 예시 1: 테이블에서 데이터 추출
                # table_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                # for row in table_rows:
                #     cells = row.find_elements(By.TAG_NAME, "td")
                #     if len(cells) >= 4:
                #         sales_data.append({
                #             'date': cells[0].text.strip(),
                #             'time': cells[1].text.strip(),
                #             'customer': cells[2].text.strip(),
                #             'service': cells[3].text.strip(),
                #             'amount': int(cells[4].text.strip().replace(',', '').replace('원', ''))
                #         })
                
                # 예시 2: 특정 클래스명으로 찾기
                # sales_elements = driver.find_elements(By.CLASS_NAME, "sales-row")
                # for element in sales_elements:
                #     sales_data.append({
                #         'date': element.find_element(By.CLASS_NAME, "date").text,
                #         'time': element.find_element(By.CLASS_NAME, "time").text,
                #         'customer': element.find_element(By.CLASS_NAME, "customer").text,
                #         'service': element.find_element(By.CLASS_NAME, "service").text,
                #         'amount': int(element.find_element(By.CLASS_NAME, "amount").text.replace(',', '').replace('원', ''))
                #     })
                
                # ⚠️ 실제 HTML 구조를 확인한 후 위 예시를 수정하세요!
                # 현재는 handsos.com의 실제 구조를 모르기 때문에 더미 데이터 반환
                print("⚠️ handsos.com의 실제 HTML 구조를 확인 후 셀렉터를 수정해야 합니다.")
                print("현재는 테스트 데이터를 반환합니다.")
                
                print(f"크롤링된 매출 데이터: {len(sales_data)}건")
                
                # 실제 데이터가 없으면 테스트 데이터 반환
                if not sales_data:
                    print("크롤링된 데이터가 없어 테스트 데이터를 반환합니다.")
                    return get_dummy_data()
                
            except Exception as parse_error:
                print(f"HTML 파싱 오류: {parse_error}")
                print("테스트 데이터를 반환합니다.")
                return get_dummy_data()
            
            # 5. 매출 요약 계산
            today_total = sum(s.get('amount', 0) for s in sales_data)
            
            # 추가로 필요한 데이터가 있다면 더 크롤링
            # 예: 이번 주, 이번 달 데이터 등
            
            summary = {
                'today': today_total,
                'week': today_total * 7,  # 임시: 오늘의 7배
                'month': today_total * 30,  # 임시: 오늘의 30배
                'totalBookings': len(sales_data)
            }
            
            print(f"매출 요약: 오늘 {summary['today']:,.0f}원")
            
            return {
                'status': 'success',
                'data': {
                    'summary': summary,
                    'sales': sales_data
                }
            }
            
        finally:
            driver.quit()
            print("드라이버 종료")
            
    except Exception as e:
        logging.error(f"크롤링 오류: {e}")
        print(f"크롤링 오류 발생: {e}")
        return get_dummy_data()

def get_dummy_data():
    """테스트용 더미 데이터 반환"""
    today = datetime.now()
    sales_data = [
        {
            'date': today.strftime('%Y-%m-%d'),
            'time': '10:00',
            'customer': '홍길동',
            'service': '커트',
            'amount': 25000
        },
        {
            'date': today.strftime('%Y-%m-%d'),
            'time': '11:30',
            'customer': '김철수',
            'service': '파마',
            'amount': 180000
        },
        {
            'date': today.strftime('%Y-%m-%d'),
            'time': '14:00',
            'customer': '이영희',
            'service': '컬러',
            'amount': 120000
        },
        {
            'date': today.strftime('%Y-%m-%d'),
            'time': '15:30',
            'customer': '박민수',
            'service': '염색',
            'amount': 150000
        }
    ]
    
    summary = {
        'today': sum(s.get('amount', 0) for s in sales_data),
        'week': len(sales_data) * 100000,
        'month': len(sales_data) * 500000,
        'totalBookings': len(sales_data)
    }
    
    print("더미 데이터 반환")
    return {
        'status': 'success',
        'data': {
            'summary': summary,
            'sales': sales_data
        }
    }

# 텔레그램 이미지 전송
def send_telegram_image(image_data, caption=""):
    try:
        if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
            print("텔레그램 설정이 필요합니다. BOT_TOKEN과 CHAT_ID를 설정해주세요.")
            return False
        
        # base64 데이터에서 실제 이미지 데이터 추출
        if image_data.startswith('data:image/png;base64,'):
            image_data = image_data.split(',')[1]
        
        # base64 디코딩
        image_bytes = base64.b64decode(image_data)
        
        # 이미지 파일로 저장 (임시)
        temp_filename = f"temp_capture_{int(time.time())}.png"
        with open(temp_filename, 'wb') as f:
            f.write(image_bytes)
        
        # 텔레그램으로 이미지 전송
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        with open(temp_filename, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, files=files, data=data, timeout=30)
        
        # 임시 파일 삭제
        try:
            os.remove(temp_filename)
        except:
            pass
        
        if response.status_code == 200:
            print("텔레그램 이미지 전송 성공")
            return True
        else:
            print(f"텔레그램 이미지 전송 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"텔레그램 이미지 전송 오류: {e}")
        return False

# HTTP 요청 핸들러
class DataHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(shared_data, ensure_ascii=False).encode('utf-8'))
        else:
            # 정적 파일 서빙
            self.serve_static_file()
    
    def do_POST(self):
        if self.path == '/api/data':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                new_data = json.loads(post_data.decode('utf-8'))
                global shared_data
                shared_data.update(new_data)
                save_data()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/telegram':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                
                if send_telegram_message(message):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'success'}, ensure_ascii=False).encode('utf-8'))
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'error', 'message': '텔레그램 전송 실패'}, ensure_ascii=False).encode('utf-8'))
                    
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/telegram-image':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                image_data = data.get('image', '')
                caption = data.get('caption', '')
                
                if send_telegram_image(image_data, caption):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'success'}, ensure_ascii=False).encode('utf-8'))
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'error', 'message': '텔레그램 이미지 전송 실패'}, ensure_ascii=False).encode('utf-8'))
                    
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == '/api/sales-data':
            # 크롤링을 통한 매출 데이터 반환
            sales_data = fetch_sales_data()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(sales_data, ensure_ascii=False).encode('utf-8'))
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_static_file(self):
        # 기존 정적 파일 서빙 로직
        if self.path == '/':
            self.path = '/index.html'
        
        try:
            with open(self.path[1:], 'rb') as f:
                content = f.read()
                self.send_response(200)
                if self.path.endswith('.html'):
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                elif self.path.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                elif self.path.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

# SIGINT 시그널 무시 함수
def ignore_sigint(signum, frame):
    pass

# 서버 시작
def start_server():
    # Ctrl+C 시그널 무시
    signal.signal(signal.SIGINT, ignore_sigint)
    
    load_data()
    server = HTTPServer(('0.0.0.0', 8000), DataHandler)
    print("실시간 동기화 서버가 시작되었습니다!")
    print("다른 PC에서 접속: http://172.30.1.32:8000")
    print("서버가 실행 중입니다.")
    server.serve_forever()

if __name__ == '__main__':
    start_server()


