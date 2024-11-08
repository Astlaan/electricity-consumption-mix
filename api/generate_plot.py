from http.server import BaseHTTPRequestHandler
import json
import logging
import sys
import gc
import os
from datetime import datetime
from bokeh.embed import json_item  # type: ignore # Add this import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import utils as utils
from time_pattern import TimePatternValidator
from utils import SimpleInterval, AdvancedPattern
from core import generate_visualization

# Configure logging to write to stderr which Vercel can capture
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def handle_request(request_body):
    try:
        # Parse request body
        body = json.loads(request_body)
        
        if body['mode'] == 'simple':
            # Simple mode - single interval
            start_date = datetime.fromisoformat(body['start_date'])
            end_date = datetime.fromisoformat(body['end_date'])
            try:
                data_request = SimpleInterval(start_date, end_date)
                # Add validation here
                utils.validate_inputs(start_date, end_date)
            except AssertionError as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Invalid date range: Dates must be whole hours and within available range'})
                }
        else:
            # Advanced mode - pattern-based
            try:
                data_request = AdvancedPattern(
                    years=body["years"],
                    months=body["months"],
                    days=body["days"],
                    hours=body["hours"])
                TimePatternValidator.validate_pattern(data_request)
            except ValueError as e:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': str(e)})
                }
            
        fig = generate_visualization(data_request, backend="_plot_internal_bokeh_2")
        
        if fig is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No data available for the specified time range'})
            }

        # Convert Bokeh figure to JSON
        plot_json = json_item(fig) # type: ignore
        
        return {
            'statusCode': 200,
            'body': json.dumps({'plot': plot_json})
        }

    except json.JSONDecodeError as e:
        logger.exception(f"Invalid JSON request body: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Invalid JSON format: {str(e)}'})
        }
    except KeyError as e:
        logger.exception(f"Missing required field in request body: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Missing required field: {str(e)}'})
        }
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Server error: {str(e)}'})
        }
    except ValueError as e:
        logger.exception(f"Error processing data request: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(e)}) # Return the detailed ValueError message
        }
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Server error: {str(e)}'})
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

