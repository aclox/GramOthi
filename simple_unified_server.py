#!/usr/bin/env python3
"""
Simple Unified GramOthi Server
Serves frontend on port 3000 and proxies API calls to backend on port 8000
"""

import os
import sys
import subprocess
import threading
import time
import signal
import requests
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

class SimpleUnifiedHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404, "Not Found")
    
    def do_PUT(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404, "Not Found")
    
    def do_DELETE(self):
        if self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        if self.path.startswith('/api/'):
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
        else:
            super().do_OPTIONS()
    
    def proxy_to_backend(self):
        """Proxy API requests to the FastAPI backend running on port 8000"""
        try:
            # Get the API path
            api_path = self.path[4:]  # Remove '/api' prefix
            
            # Build backend URL
            backend_url = f"http://localhost:8000{api_path}"
            
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Prepare headers for backend request
            headers = {}
            for key, value in self.headers.items():
                if key.lower() not in ['host', 'content-length']:
                    headers[key] = value
            
            # Make request to backend
            if self.command == 'GET':
                response = requests.get(backend_url, headers=headers, timeout=10)
            elif self.command == 'POST':
                response = requests.post(backend_url, data=post_data, headers=headers, timeout=10)
            elif self.command == 'PUT':
                response = requests.put(backend_url, data=post_data, headers=headers, timeout=10)
            elif self.command == 'DELETE':
                response = requests.delete(backend_url, headers=headers, timeout=10)
            else:
                self.send_error(405, "Method Not Allowed")
                return
            
            # Send response
            self.send_response(response.status_code)
            self.send_cors_headers()
            
            # Copy response headers
            for key, value in response.headers.items():
                if key.lower() not in ['content-length', 'transfer-encoding', 'connection']:
                    self.send_header(key, value)
            
            self.end_headers()
            
            # Send response body
            if response.content:
                self.wfile.write(response.content)
                
        except requests.exceptions.ConnectionError:
            self.send_error(503, "Backend service unavailable")
        except Exception as e:
            print(f"Proxy error: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Access-Control-Max-Age', '86400')

def start_backend():
    """Start the FastAPI backend in a separate process"""
    try:
        print("🔧 Starting FastAPI backend...")
        os.chdir('Backend')
        
        # Set environment variables
        env = os.environ.copy()
        env['DATABASE_URL'] = 'sqlite:///./gramothi.db'
        
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'app.main:app', 
            '--reload', 
            '--host', '127.0.0.1', 
            '--port', '8000'
        ], env=env)
    except Exception as e:
        print(f"Backend error: {e}")

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🚀 Starting Unified GramOthi Server...")
    print("=============================================")
    
    # Start backend in background thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend to start
    print("⏳ Waiting for backend to start...")
    for i in range(30):  # Wait up to 30 seconds
        if check_backend_health():
            print("✅ Backend is running!")
            break
        time.sleep(1)
    else:
        print("⚠️  Backend may not be running properly, but continuing...")
    
    # Start unified server
    print("🌐 Starting frontend server...")
    server = HTTPServer(('localhost', 3000), SimpleUnifiedHandler)
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down server...")
        server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("✅ Server running on http://localhost:3000")
        print("   - Frontend: http://localhost:3000")
        print("   - API: http://localhost:3000/api")
        print("   - Backend: http://localhost:8000")
        print("\nPress Ctrl+C to stop the server")
        print("=============================================")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        server.shutdown()

if __name__ == '__main__':
    main()
