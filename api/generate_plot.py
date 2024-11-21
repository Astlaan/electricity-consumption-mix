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


def handle_request(request_body):
    backend="_plot_internal_plotly_2"
    # Parse request body
    body = json.loads(request_body)
    
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

    try:    
        fig = generate_visualization(
            data_request, 
            backend=backend,
            plot_calc_function=body["plot_calc_function"])  # Default to 'plot' if not specified
            plot_mode=body["plot_mode"]  # Default to 'plot' if not specified
        )
    except AssertionError as e: # TODO fix
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid date range: Dates must be whole hours and within available range'})
        }
    
    if fig is None: # TODO fix
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No data available for the specified time range'})
        }

    # Convert Plotly figure to JSON
    if "bokeh" in backend:
        from bokeh.embed import json_item
        plot_json = json_item(fig)
    elif "plotly" in backend:
        plot_json = fig.to_json()
    else:
        raise ValueError(f"Backend {backend} not supported")
    
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
