from http.server import BaseHTTPRequestHandler
import json
import logging
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "core"))
from data_fetcher import SimpleInterval
from time_pattern import AdvancedPattern  # type: ignore # Add this import
import utils as utils
from core import generate_visualization

# Configure logging to write to stderr which Vercel can capture
logger = logging.getLogger(__name__)


def sanitize_exception(e):
    # Convert exception to string
    error_message = str(e)
    # Check if the API key is in the error message
    api_key = os.getenv("ENTSOE_API_KEY")
    if api_key:
        if api_key in error_message:
            error_message = error_message.replace(api_key, "<API-KEY>")
    return error_message


def handle_request(request_body):
    body = json.loads(request_body)
    try:
        if body["mode"] == "simple":
            data_request = SimpleInterval(
                start_date=datetime.fromisoformat(body["start_date"]),
                end_date=datetime.fromisoformat(body["end_date"]),
            )
        else:
            data_request = AdvancedPattern(
                years=body["years"],
                months=body["months"],
                days=body["days"],
                hours=body["hours"],
            )

        aggregated, contributions = generate_visualization(
            data_request,
            config=body,
        )
    except Exception as e:
        # Sanitize the exception message
        sanitized_error = sanitize_exception(e)
        logger.error("An unexpected error occurred: %s", sanitized_error, exc_info=True)

        # Return the sanitized error to the client
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Error: {sanitized_error}"}),
        }

    if aggregated is None or contributions is None:
        return {
            "statusCode": 400,
            "body": json.dumps(
                {"error": "No data available for the specified time interval(s)"}
            ),
        }

    # Serialize the dataframes
    aggregated_json = aggregated.to_json(orient="split")
    contributions_json = {
        country: df.to_json(orient="split") for country, df in contributions.items()
    }

    # Create the response body
    response_data = {
        "aggregated": aggregated_json,
        "contributions": contributions_json,
    }

    return {"statusCode": 200, "body": json.dumps({"data": response_data})}


class handler(BaseHTTPRequestHandler):
    
    # def do_GET(self):
    #     response = {"statusCode": 200, "body": json.dumps({"plot": "test"})}
    #     self.send_response(response['statusCode'])
    #     self.send_header('Content-type', 'application/json')
    #     self.end_headers()
    #     self.wfile.write(response['body'].encode('utf-8'))
    #     return
    
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode("utf-8")

        response = handle_request(post_data)

        self.send_response(int(response['statusCode']))
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(str(response['body']).encode('utf-8'))
        return
