"""
Health Check Endpoint for Deployment Monitoring
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check HTTP handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'AlphaAlgo Trading Bot'
            }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def start_health_check_server(port=8080):
    """Start health check server in background thread"""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

if __name__ == '__main__':
    print("Starting health check server on port 8080...")
    start_health_check_server(8080)
    print("Health check available at http://localhost:8080/health")
    
    # Keep running
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
