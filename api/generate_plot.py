from http.server import BaseHTTPRequestHandler
import json
import logging
import sys
import gc
import os
from datetime import datetime
import io
import base64
import matplotlib.pyplot as plt

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
            visualize_type="simple"
        )
        
        if fig is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Failed to generate visualization'})
            }

        # Convert Matplotlib figure to base64 encoded PNG
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig) # Close the figure to release resources

        return {
            'statusCode': 200,
            'body': json.dumps({'image': img_base64})
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
            'statusCode': 500, # Internal Server Error
            'body': json.dumps({'error': f'An unexpected error occurred: {e}'})
        }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
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

