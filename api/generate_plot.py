from http.server import BaseHTTPRequestHandler
import json
import logging
import sys
import gc
import os
from datetime import datetime
from bokeh.embed import json_item  # Add this import

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
        fig = generate_visualization(
            start_date=start_date,
            end_date=end_date,
            visualize_type="_plot_internal_bokeh_2"
        )
        
        if fig is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Failed to generate visualization'})
            }

        # Convert Bokeh figure to JSON
        plot_json = json_item(fig)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'plot': plot_json})
        }

    except json.JSONDecodeError as e:
        logger.exception(f"Invalid JSON request body: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Invalid JSON request body: {e}'})
        }
    except KeyError as e:
        logger.exception(f"Missing required field in request body: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Missing required field in request body: {e}'})
        }
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        gc.collect()  # Clean up on error too
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'An unexpected error occurred: {e}'})
        }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-type', 'application/json')
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        response = handle_request(post_data)
        self.send_response(response['statusCode'])
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response['body'].encode('utf-8'))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Hello, World!") # Placeholder for GET request

