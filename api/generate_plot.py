from http.server import BaseHTTPRequestHandler
from datetime import datetime
import json
import sys
import os
from data_fetcher import ENTSOEDataFetcher

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core import generate_visualization

def handle_request(request_body):
    try:
        # Parse request body
        body = json.loads(request_body)
        start_date = datetime.fromisoformat(body['start_date'])
        end_date = datetime.fromisoformat(body['end_date'])

        # Generate visualization
        fig = generate_visualization(
            start_date=start_date,
            end_date=end_date,
            visualize_type="simple"
        )
        
        if fig is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Failed to generate visualization'})
            }

        # Convert plot to JSON
        plot_json = fig.to_json()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'figure': json.loads(plot_json)
            })
        }
    except json.JSONDecodeError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Invalid JSON request body: {e}'})
        }
    except KeyError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Missing required field in request body: {e}'})
        }
    except Exception as e:
        return {
            'statusCode': 500, # Internal Server Error
            'body': json.dumps({'error': f'An unexpected error occurred: {e}'})
        }

def check_cache_status():
    import sys
    import os
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Directory contents: {os.listdir('.')}")
    
    cache_dir = ENTSOEDataFetcher.CACHE_DIR
    print(f"Checking cache directory: {cache_dir}")  
    
    # Get absolute path
    abs_cache_dir = os.path.abspath(cache_dir)
    print(f"Absolute cache path: {abs_cache_dir}")
    
    exists = os.path.exists(abs_cache_dir)
    files = os.listdir(abs_cache_dir) if exists else []
    is_empty = not exists or not files
    
    print(f"Cache dir exists: {exists}")
    print(f"Cache files: {files}")
    print(f"Is empty: {is_empty}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({'is_empty': is_empty})
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/check_cache':
            result = check_cache_status()
            
            self.send_response(result['statusCode'])
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(result['body'].encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request_body = self.rfile.read(content_length).decode('utf-8')
        
        result = handle_request(request_body)
        
        self.send_response(result['statusCode'])
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # For development
        self.end_headers()
        self.wfile.write(result['body'].encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET') # Added GET
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
