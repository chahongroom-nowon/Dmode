#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import signal

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


