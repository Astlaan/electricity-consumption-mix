from http.server import BaseHTTPRequestHandler
import json
import logging
import sys
import gc
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from data_fetcher import SimpleInterval
from time_pattern import AdvancedPattern  # type: ignore # Add this import
import utils as utils
from core import generate_visualization

# Configure logging to write to stderr which Vercel can capture
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)




def sanitize_exception(e):
    # Convert exception to string
    error_message = str(e)
    # Check if the API key is in the error message
    api_key = os.getenv("ENTSOE_API_KEY") 
    if api_key:
        if api_key in error_message:
            error_message = error_message.replace(api_key, '<API-KEY>')
    return error_message


def handle_request(request_body):
    body = json.loads(request_body)
    
    try:    
        if body['mode'] == 'simple':
            data_request = SimpleInterval(
                start_date=datetime.fromisoformat(body['start_date']), 
                end_date=datetime.fromisoformat(body['end_date'])
                )
        else:
            data_request = AdvancedPattern(
                years=body["years"],
                months=body["months"],
                days=body["days"],
                hours=body["hours"])

        fig = generate_visualization(
                data_request, 
                config=body  # Default to 'plot' if not specified
            )
    except Exception as e:
            # Sanitize the exception message
            sanitized_error = sanitize_exception(e)
            logger.error("An unexpected error occurred: %s", sanitized_error, exc_info=True)
            
            # Return the sanitized error to the client
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'Error: {sanitized_error}'
                })
            }
    
    if fig is None: # TODO fix
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No data available for the specified time interval(s)'})
        }

    # Convert Plotly figure to JSON
    if "backend" in body:
        if "bokeh" in body["backend"]:
            from bokeh.embed import json_item
            plot_json = json_item(fig)  # type: ignore
        elif "plotly" in body["backend"]:
            plot_json = fig.to_json()
        else:
            raise ValueError(f"Backend {body["backend"]} not supported")
    else: # Assume plotly
        plot_json = fig.to_json()

    
    return {
        'statusCode': 200,
        'body': json.dumps({'plot': plot_json})
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
