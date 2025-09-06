#!/usr/bin/env python3
"""
Unified GramOthi Server
Serves both frontend and backend API on port 3000
"""

import os
import sys
import subprocess
import threading
import time
import signal
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

# Add Backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Backend'))

class UnifiedRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def do_GET(self):
        # Handle API requests
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.send_error(404, "Not Found")
    
    def do_PUT(self):
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.send_error(404, "Not Found")
    
    def do_DELETE(self):
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            self.send_error(404, "Not Found")
    
    def handle_api_request(self):
        """Proxy API requests to the FastAPI backend"""
        try:
            # Import FastAPI app
            from app.main import app
            from fastapi.testclient import TestClient
            
            # Create test client
            client = TestClient(app)
            
            # Parse the API path
            api_path = self.path[4:]  # Remove '/api' prefix
            
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Prepare headers
            headers = dict(self.headers)
            if 'host' in headers:
                del headers['host']
            
            # Make request to FastAPI
            if self.command == 'GET':
                response = client.get(api_path, headers=headers)
            elif self.command == 'POST':
                response = client.post(api_path, data=post_data, headers=headers)
            elif self.command == 'PUT':
                response = client.put(api_path, data=post_data, headers=headers)
            elif self.command == 'DELETE':
                response = client.delete(api_path, headers=headers)
            else:
                self.send_error(405, "Method Not Allowed")
                return
            
            # Send response
            self.send_response(response.status_code)
            
            # Copy headers
            for key, value in response.headers.items():
                if key.lower() not in ['content-length', 'transfer-encoding']:
                    self.send_header(key, value)
            
            self.end_headers()
            
            # Send response body
            if response.content:
                self.wfile.write(response.content)
                
        except Exception as e:
            print(f"API Error: {e}")
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def start_backend():
    """Start the FastAPI backend in a separate process"""
    try:
        os.chdir('Backend')
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'app.main:app', 
            '--reload', 
            '--host', '127.0.0.1', 
            '--port', '8001'  # Use different port for internal backend
        ])
    except Exception as e:
        print(f"Backend error: {e}")

def main():
    print("Starting Unified GramOthi Server...")
    print("Frontend: http://localhost:3000")
    print("API: http://localhost:3000/api")
    
    # Start backend in background thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend to start
    time.sleep(3)
    
    # Start unified server
    server = HTTPServer(('localhost', 3000), UnifiedRequestHandler)
    
    def signal_handler(sig, frame):
        print("\nShutting down server...")
        server.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("Server running on http://localhost:3000")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == '__main__':
    main()
