import gc
import logging
import sys
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

# Configure logging to write to stderr which Vercel can capture
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core import generate_visualization
from data_fetcher import ENTSOEDataFetcher

def handle_request(request_body):
    try:
        # Parse request body
        body = json.loads(request_body)
        start_date = datetime.fromisoformat(body['start_date'])
        end_date = datetime.fromisoformat(body['end_date'])

        # Generate visualization
        message = generate_visualization(
            start_date=start_date,
            end_date=end_date,
            visualize_type="simple"
        )
        
        if message is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Failed to generate visualization'})
            }

        # Return message instead of plot
        return {
            'statusCode': 200,
            'body': json.dumps({'message': message})
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
        logger.error(f"Error handling request: {str(e)}")
        gc.collect()  # Clean up on error too
        return {
            'statusCode': 500, # Internal Server Error
            'body': json.dumps({'error': f'An unexpected error occurred: {e}'})
        }

def check_cache_status():
    import sys
    import os
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Current working directory: {os.getcwd()}")
    logger.debug(f"Directory contents: {os.listdir('.')}")
    
    cache_dir = ENTSOEDataFetcher.CACHE_DIR
    logger.debug(f"Checking cache directory: {cache_dir}")  
    
    # Get absolute path
    abs_cache_dir = os.path.abspath(cache_dir)
    logger.debug(f"Absolute cache path: {abs_cache_dir}")
    
    exists = os.path.exists(abs_cache_dir)
    files = os.listdir(abs_cache_dir) if exists else []
    is_empty = not exists or not files
    
    logger.debug(f"Cache dir exists: {exists}")
    logger.debug(f"Cache files: {files}")
    logger.debug(f"Is empty: {is_empty}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({'is_empty': is_empty})
    }

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/check_cache':
            result = check_cache_status()
            self.send_response(result['statusCode'])
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(result['body'].encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length).decode('utf-8')
        
        result = handle_request(request_body)
        
        response_size = len(result['body'])
        if response_size > 50 * 1024 * 1024:  # 50MB limit
            result = {
                'statusCode': 413,
                'body': json.dumps({'error': 'Response too large'})
            }
        
        self.send_response(result['statusCode'])
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(result['body'].encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
