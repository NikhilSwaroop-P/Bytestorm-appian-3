"""
Standalone Flask Server for Browser Extension
============================================

This Flask server provides AI-powered checkout automation services
for the browser extension. It runs locally and processes HTML forms
to generate optimized form-filling instructions.

Endpoints:
- /health - Health check endpoint
- /process-checkout - Main checkout processing endpoint
- /analyze-form - Form analysis endpoint
- /process-with-reanalysis - Form filling with automatic reanalysis
- /compare-html - Endpoint for comparing previous and current HTML to determine if reanalysis is needed
- /page-change - Endpoint for receiving page change notifications from the extension

"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import os
import sys
from typing import Dict, Any
import logging
from datetime import datetime

# Import our automation modules
from checkout_automation import automate_checkout_form, automate_form_filling_with_reanalysis, compare_html_content
from process_checkout import process_checkout_page

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for browser extension communication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Function to save request data to file
def save_request_to_file(endpoint: str, data: Dict[str, Any]) -> str:
    """Save the request data to a text file for debugging purposes.
    
    Args:
        endpoint: The endpoint that received the request
        data: The request data to save
    
    Returns:
        The path to the saved file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{endpoint}_{timestamp}.txt"
    filename = 'html_log.txt'
    filepath = os.path.join(LOGS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"=== Request to {endpoint} at {datetime.now().isoformat()} ===\n\n")
        
        # Extract and save the most important parts separately at the top
        if 'url' in data:
            f.write(f"URL: {data['url']}\n")
        if 'page_title' in data:
            f.write(f"Page Title: {data['page_title']}\n")
        
        # If user profile is present, save it in a readable format
        if 'user_profile' in data:
            f.write("\n=== User Profile ===\n")
            for key, value in data['user_profile'].items():
                f.write(f"{key}: {value}\n")
        
        # For form data, save a summary
        if 'form_data' in data:
            f.write("\n=== Form Data Summary ===\n")
            form_data = data['form_data']
            if isinstance(form_data, dict):
                if 'html' in form_data:
                    html_length = len(form_data['html'])
                    f.write(f"HTML Content Length: {html_length} characters\n")
                # Include other form metadata but not the full HTML
                for key, value in form_data.items():
                    if key != 'html':
                        f.write(f"{key}: {value}\n")
        
        # Save the full JSON data at the end
        f.write("\n=== Full Request JSON ===\n")
        f.write(json.dumps(data, indent=2))
    
    logger.info(f"Request data saved to {filepath}")
    return filepath

# Default user data for testing
DEFAULT_USER_DATA = """
name: John Doe
email: john.doe@example.com
phone: +1-555-0123
address: 123 Main St
city: New York
state: NY
zip: 10001
country: United States
card_number: 4111111111111111
card_expiry: 12/25
card_cvv: 123
"""

@app.route('/')
def home():
    """Home page with API documentation."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Checkout Automation API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .endpoint { background: #f4f4f4; padding: 15px; margin: 15px 0; border-radius: 5px; }
            .method { color: #007acc; font-weight: bold; }
            .status { padding: 5px 10px; border-radius: 3px; color: white; }
            .running { background: #28a745; }
            .code { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }
        </style>
    </head>
    <body>
        <h1>🤖 Checkout Automation API</h1>
        <p><span class="status running">RUNNING</span> Local server for browser extension</p>
        
        <h2>📡 Available Endpoints</h2>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /health</h3>
            <p>Health check endpoint to verify server status</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /process-checkout</h3>
            <p>Main endpoint for processing checkout forms with AI analysis</p>
            <p><strong>Body:</strong></p>
            <div class="code">
            {
                "html_content": "&lt;form&gt;...&lt;/form&gt;",
                "user_data": "name: John...",
                "checkout_url": "https://example.com/checkout"
            }
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /analyze-form</h3>
            <p>Basic form analysis without full processing</p>
            <p><strong>Body:</strong></p>
            <div class="code">
            {
                "html_content": "&lt;form&gt;...&lt;/form&gt;"
            }
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /process-with-reanalysis</h3>
            <p>Form filling with automatic reanalysis</p>
            <p><strong>Body:</strong></p>
            <div class="code">
            {
                "form_data": {
                    "html": "HTML content of the form",
                    "url": "URL of the page"
                },
                "user_profile": {
                    "name": "User name",
                    "email": "User email",
                    ...
                },
                "reanalysis_settings": {
                    "wait_time": 2,  // seconds to wait before reanalyzing
                    "max_attempts": 3  // maximum number of form filling attempts
                }
            }
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /compare-html</h3>
            <p>Endpoint for comparing previous and current HTML to determine if reanalysis is needed</p>
            <p><strong>Body:</strong></p>
            <div class="code">
            {
                "previous_html": "Previous HTML content",
                "current_html": "Current HTML content",
                "session_id": "Session ID from reanalysis_instructions",
                "attempt": 1
            }
            </div>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /page-change</h3>
            <p>Handle page change notifications from the extension after form filling</p>
            <p><strong>Body:</strong></p>
            <div class="code">
            {
                "url": "current page URL",
                "timestamp": "ISO timestamp of when the change occurred"
            }
            </div>
        </div>
        
        <h2>🚀 Usage</h2>
        <p>This server is designed to work with the Checkout Automation browser extension. 
        The extension sends checkout page HTML to these endpoints and receives structured 
        form-filling instructions powered by Google's Gemini AI.</p>
        
        <h2>⚡ Status</h2>
        <p>Server is running on <strong>localhost:5000</strong></p>
        <p>Started: {{ timestamp }}</p>
    </body>
    </html>
    """
    return render_template_string(html_content, timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/health')
def health_check():
    """Health check endpoint."""
    logger.info("Health check endpoint called")
    
    # Debug: Log health check
    debug_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_file = os.path.join(LOGS_DIR, f"health_check_{debug_timestamp}.txt")
    
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write("=== HEALTH CHECK REQUEST ===\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"Headers: {dict(request.headers)}\n")
        f.write(f"Remote address: {request.remote_addr}\n")
    
    logger.info(f"Health check request logged to {debug_file}")
    
    return jsonify({
        'status': 'healthy',
        'message': 'Checkout Automation API is running',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/process-checkout', methods=['POST'])
def process_checkout():
    """
    Main endpoint for processing checkout forms.
    
    Expected JSON payload:
    {
        "form_data": {
            "html": "HTML content of the checkout form",
            "url": "URL of the checkout page"
        },
        "user_profile": {
            "name": "User name",
            "email": "User email",
            ...
        }
    }
    """
    try:
        logger.info("Process checkout endpoint called")
        
        # Get request data
        data = request.get_json()
        logger.info(f"Received data type: {type(data)}")
        
        # Debug: Write raw request data to a file regardless of format
        debug_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = os.path.join(LOGS_DIR, f"debug_raw_request_{debug_timestamp}.txt")
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("=== RAW REQUEST DATA ===\n")
            f.write(f"Headers: {dict(request.headers)}\n\n")
            f.write(f"Request Method: {request.method}\n")
            f.write(f"Request URL: {request.url}\n\n")
            
            # Try to get the raw data in case JSON parsing failed
            raw_data = request.get_data(as_text=True)
            f.write(f"Raw request body:\n{raw_data}\n\n")
            
            # If JSON data is available, also log that
            if data:
                f.write(f"Parsed JSON data:\n{json.dumps(data, indent=2)}\n")
        
        logger.info(f"Debug raw request data saved to {debug_file}")
        
        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Save all incoming data to file for debugging
        log_file = save_request_to_file('process-checkout', data)
        logger.info(f"Request data saved to {log_file}")
        
        # Extract form data
        form_data = data.get('form_data', {})
        if not form_data:
            logger.error("form_data is missing in the request")
            return jsonify({'error': 'form_data is required'}), 400
            
        html_content = form_data.get('html')
        if not html_content:
            return jsonify({'error': 'html content is required in form_data'}), 400
          # Get optional parameters
        user_profile = data.get('user_profile', {})
        if user_profile:
            # Convert user profile to format expected by processor
            user_data = "\n".join([f"{key}: {value}" for key, value in user_profile.items()])
        else:
            user_data = DEFAULT_USER_DATA
            
        checkout_url = form_data.get('url')
        # Ensure checkout_url is not an empty string
        if checkout_url == "":
            checkout_url = None
            
        # Handle both single API key and multiple API keys
        api_key = data.get('api_key', os.environ.get('GOOGLE_API_KEY'))
        api_keys = data.get('api_keys', None)  # List of API keys for cycling
        
        # Get advanced parameters
        advanced_settings = data.get('advanced_settings', {})
        fast_mode = advanced_settings.get('fast_mode', False)
        model_depth = advanced_settings.get('model_depth', 1)
        thinking_budget = advanced_settings.get('thinking_budget', 1024)
        max_chunks = advanced_settings.get('max_chunks', 4)
        min_size_for_chunking = advanced_settings.get('min_size_for_chunking', 1000)
        
        logger.info(f"Processing checkout form from URL: {checkout_url or 'unknown'}")
        if api_keys:
            logger.info(f"Using {len(api_keys)} API keys for automatic cycling")
        logger.info(f"Advanced settings: fast_mode={fast_mode}, " +
                   f"model_depth={model_depth}, thinking_budget={thinking_budget}, " +
                   f"max_chunks={max_chunks}, min_size_for_chunking={min_size_for_chunking}")
        
        # Process the checkout page
        result = process_checkout_page(
            html_content=html_content,
            checkout_url=checkout_url,
            user_data=user_data,
            api_key=api_key,
            api_keys=api_keys,
            save_to_file=False,  # Don't save files in server mode
            verbose=False,  # Don't print to console in server mode
            fast=fast_mode,
            depth=model_depth,
            thinking_budget=thinking_budget,
            max_chunks=max_chunks,
            min_size_for_chunking=min_size_for_chunking
        )
        
        # Add processing metadata
        result['processing_info'] = {
            'timestamp': datetime.now().isoformat(),
            'server_version': '1.0.0',
            'processing_mode': 'enhanced'
        }
        
        logger.info("Checkout form processed successfully")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing checkout form: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/analyze-form', methods=['POST'])
def analyze_form():
    """
    Basic form analysis endpoint (lighter processing).
    
    Expected JSON payload:
    {
        "form_data": {
            "html": "HTML content of the form",
            "url": "URL of the page"
        }
    }
    """
    try:
        logger.info("Analyze form endpoint called")
        
        # Get request data
        data = request.get_json()
        logger.info(f"Received data type: {type(data)}")
        
        # Debug: Write raw request data to a file regardless of format
        debug_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = os.path.join(LOGS_DIR, f"debug_raw_request_{debug_timestamp}.txt")
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("=== RAW REQUEST DATA ===\n")
            f.write(f"Headers: {dict(request.headers)}\n\n")
            f.write(f"Request Method: {request.method}\n")
            f.write(f"Request URL: {request.url}\n\n")
            
            # Try to get the raw data in case JSON parsing failed
            raw_data = request.get_data(as_text=True)
            f.write(f"Raw request body:\n{raw_data}\n\n")
            
            # If JSON data is available, also log that
            if data:
                f.write(f"Parsed JSON data:\n{json.dumps(data, indent=2)}\n")
        
        logger.info(f"Debug raw request data saved to {debug_file}")
        
        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Save all incoming data to file for debugging
        log_file = save_request_to_file('analyze-form', data)
        logger.info(f"Request data saved to {log_file}")
        
        # Extract form data
        form_data = data.get('form_data', {})
        if not form_data:
            logger.error("form_data is missing in the request")
            return jsonify({'error': 'form_data is required'}), 400
            
        html_content = form_data.get('html')
        if not html_content:
            return jsonify({'error': 'html content is required in form_data'}), 400
          # Get optional parameters - support both single and multiple API keys
        api_key = data.get('api_key', os.environ.get('GOOGLE_API_KEY'))
        api_keys = data.get('api_keys', None)  # List of API keys for cycling
        
        # Get advanced parameters
        advanced_settings = data.get('advanced_settings', {})
        fast_mode = advanced_settings.get('fast_mode', False)
        model_depth = advanced_settings.get('model_depth', 1)
        thinking_budget = advanced_settings.get('thinking_budget', 1024)
        max_chunks = advanced_settings.get('max_chunks', 4)
        min_size_for_chunking = advanced_settings.get('min_size_for_chunking', 1000)
        
        logger.info("Analyzing form structure")
        if api_keys:
            logger.info(f"Using {len(api_keys)} API keys for automatic cycling")
        logger.info(f"Advanced settings: fast_mode={fast_mode}, " +
                   f"model_depth={model_depth}, thinking_budget={thinking_budget}, " +
                   f"max_chunks={max_chunks}, min_size_for_chunking={min_size_for_chunking}")
        
        # Use basic automation (faster processing)
        # CRITICAL FIX: Use user profile data even in fast mode
        # Convert user profile to format expected by processor
        user_profile = data.get('user_profile', {})
        if user_profile:
            user_data = "\n".join([f"{key}: {value}" for key, value in user_profile.items()])
        else:
            user_data = DEFAULT_USER_DATA
            
        # Get checkout URL and ensure it's not an empty string
        checkout_url = form_data.get('url')
        if checkout_url == "":
            checkout_url = None
            
        result = automate_checkout_form(
            html_content=html_content,
            user_data=user_data,  # Use actual user data instead of DEFAULT_USER_DATA
            api_key=api_key,
            api_keys=api_keys,
            save_to_file=False,
            verbose=False,
            fast=fast_mode,
            depth=model_depth,
            max_chunks=max_chunks,
            min_size_for_chunking=min_size_for_chunking
        )
        
        # Add processing metadata
        result['processing_info'] = {
            'timestamp': datetime.now().isoformat(),
            'server_version': '1.0.0',
            'processing_mode': 'basic'
        }
        
        logger.info("Form analysis completed successfully")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error analyzing form: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/process-with-reanalysis', methods=['POST'])
def process_with_reanalysis():
    """
    Endpoint for form filling with automatic reanalysis.
    
    Expected JSON payload:
    {
        "form_data": {
            "html": "HTML content of the form",
            "url": "URL of the page"
        },
        "user_profile": {
            "name": "User name",
            "email": "User email",
            ...
        },
        "reanalysis_settings": {
            "wait_time": 2,  // seconds to wait before reanalyzing
            "max_attempts": 3  // maximum number of form filling attempts
        }
    }
    
    Note: This endpoint doesn't actually fetch new HTML itself - the extension
    must provide new HTML through the callback URL provided in the response.
    """
    try:
        logger.info("Process with reanalysis endpoint called")
        
        # Get request data
        data = request.get_json()
        logger.info(f"Received data type: {type(data)}")
        
        # Debug: Write raw request data to a file regardless of format
        debug_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = os.path.join(LOGS_DIR, f"debug_raw_request_{debug_timestamp}.txt")
        
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("=== RAW REQUEST DATA ===\n")
                f.write(f"Headers: {dict(request.headers)}\n\n")
                f.write(f"Request Method: {request.method}\n")
                f.write(f"Request URL: {request.url}\n\n")
                
                # Try to get the raw data in case JSON parsing failed
                raw_data = request.get_data(as_text=True)
                f.write(f"Raw request body:\n{raw_data}\n\n")
                
                # If JSON data is available, also log that
                if data:
                    f.write(f"Parsed JSON data:\n{json.dumps(data, indent=2)}\n")
            
            logger.info(f"Debug raw request data saved to {debug_file}")
        except Exception as write_error:
            logger.warning(f"Could not write debug file: {write_error}")
        
        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided', 'details': 'Request body must be valid JSON'}), 400
        
        # Extract form data
        form_data = data.get('form_data', {})
        if not form_data:
            logger.error("form_data is missing in the request")
            return jsonify({'error': 'form_data is required', 'details': 'The form_data object is missing from the request'}), 400
            
        html_content = form_data.get('html')
        if not html_content:
            return jsonify({'error': 'html content is required in form_data', 'details': 'The html field is missing from form_data'}), 400
          
        # Get optional parameters
        user_profile = data.get('user_profile', {})
        if user_profile:
            # Convert user profile to format expected by processor
            user_data = "\n".join([f"{key}: {value}" for key, value in user_profile.items()])
        else:
            user_data = DEFAULT_USER_DATA
            
        # Get checkout URL and ensure it's not an empty string
        checkout_url = form_data.get('url')
        if checkout_url == "":
            checkout_url = None
            
        # Handle both single API key and multiple API keys
        api_key = data.get('api_key', os.environ.get('GOOGLE_API_KEY'))
        api_keys = data.get('api_keys', None)  # List of API keys for cycling
        if not api_key and not api_keys:
            # Use a default API key if none provided
            api_key = 'AIzaSyBXZLvzTn2Jf52PZ_PgwDlNRtWUu37aPx4'
        
        # Get advanced parameters
        advanced_settings = data.get('advanced_settings', {})
        fast_mode = advanced_settings.get('fast_mode', False)
        model_depth = advanced_settings.get('model_depth', 1)
        thinking_budget = advanced_settings.get('thinking_budget', 1024)
        max_chunks = advanced_settings.get('max_chunks', 4)
        min_size_for_chunking = advanced_settings.get('min_size_for_chunking', 1000)
        
        # Get reanalysis settings
        reanalysis_settings = data.get('reanalysis_settings', {})
        wait_time = reanalysis_settings.get('wait_time', 2)  # Default 2 seconds
        max_attempts = reanalysis_settings.get('max_attempts', 3)  # Default 3 attempts
        
        logger.info("Processing form with automatic reanalysis")
        if api_keys:
            logger.info(f"Using {len(api_keys)} API keys for automatic cycling")
        logger.info(f"Reanalysis settings: wait_time={wait_time}s, max_attempts={max_attempts}")
        logger.info(f"Advanced settings: fast_mode={fast_mode}, " +
                   f"model_depth={model_depth}, thinking_budget={thinking_budget}, " +
                   f"max_chunks={max_chunks}, min_size_for_chunking={min_size_for_chunking}")
        
        # For server-side processing, we can't wait for updated HTML from the client
        # So we'll do a single pass and return instructions to the client on how to handle reanalysis
        try:
            # Configure SSL for Python
            import ssl
            ssl_context = ssl.create_default_context()
            if sys.platform == 'win32':
                # Windows often has SSL verification issues - disable strict checking
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                ssl._create_default_https_context = lambda: ssl_context
                logger.info("Modified SSL context for Windows platform")
                
            result = automate_checkout_form(
                html_content=html_content,
                user_data=user_data,
                api_key=api_key,
                api_keys=api_keys,
                save_to_file=False,
                verbose=False,
                fast=fast_mode,
                depth=model_depth,
                max_chunks=max_chunks,
                min_size_for_chunking=min_size_for_chunking
            )
            
            # Handle network errors in the result
            if isinstance(result, dict) and result.get("error", "").startswith("Network or SSL error:"):
                logger.error(f"Network/SSL error in API call: {result.get('error')}")
                return jsonify({
                    'error': 'SSL/Network error', 
                    'message': result.get('error', 'Connection to AI service failed'),
                    'timestamp': datetime.now().isoformat()
                }), 503  # Service Unavailable
                
        except Exception as proc_error:
            error_message = str(proc_error)
            logger.error(f"Error in API processing: {error_message}")
            
            if "SSL" in error_message or "EOF occurred in violation of protocol" in error_message:
                return jsonify({
                    'error': 'SSL/Network error',
                    'message': error_message,
                    'timestamp': datetime.now().isoformat()
                }), 503  # Service Unavailable
            else:
                return jsonify({
                    'error': 'Processing error',
                    'message': error_message,
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        # Add reanalysis instructions to the result
        result['reanalysis_instructions'] = {
            'wait_time': wait_time,
            'max_attempts': max_attempts,
            'current_attempt': 1,
            'should_wait': True,
            'callback_endpoint': '/compare-html',
            'session_id': debug_timestamp  # Use the debug timestamp as a session ID
        }
        
        # Add processing metadata
        result['processing_info'] = {
            'timestamp': datetime.now().isoformat(),
            'server_version': '1.0.0',
            'processing_mode': 'reanalysis-enabled'
        }
        
        logger.info("Form processing with reanalysis instructions completed successfully")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing form with automatic reanalysis: {str(e)}")
        
        error_message = str(e)
        if "SSL" in error_message or "EOF occurred in violation of protocol" in error_message:
            return jsonify({
                'error': 'SSL/Network error',
                'message': error_message,
                'timestamp': datetime.now().isoformat()
            }), 503  # Service Unavailable
        else:
            return jsonify({
                'error': 'Internal server error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500


@app.route('/compare-html', methods=['POST'])
def compare_html():
    """
    Endpoint for comparing previous and current HTML to determine if reanalysis is needed.
    
    Expected JSON payload:
    {
        "previous_html": "Previous HTML content",
        "current_html": "Current HTML content",
        "session_id": "Session ID from reanalysis_instructions",
        "attempt": 1
    }
    
    Returns:
        JSON response with comparison results and reanalysis instructions
    """
    try:
        logger.info("Compare HTML endpoint called")
        
        # Get request data
        data = request.get_json()
        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({'error': 'No JSON data provided', 'details': 'Request body must be valid JSON'}), 400
        
        # Extract HTML content
        previous_html = data.get('previous_html')
        current_html = data.get('current_html')
        session_id = data.get('session_id')
        attempt = data.get('attempt', 1)
        
        if not previous_html:
            logger.error("previous_html is missing")
            return jsonify({'error': 'previous_html is required', 'details': 'The previous_html field is missing from the request'}), 400
        
        if not current_html:
            logger.error("current_html is missing")
            return jsonify({'error': 'current_html is required', 'details': 'The current_html field is missing from the request'}), 400
        
        # Get reanalysis settings
        reanalysis_settings = data.get('reanalysis_settings', {})
        wait_time = reanalysis_settings.get('wait_time', 2)  # Default 2 seconds
        max_attempts = reanalysis_settings.get('max_attempts', 3)  # Default 3 attempts
        
        # Configure SSL for Python to avoid SSL errors
        try:
            import ssl
            ssl_context = ssl.create_default_context()
            if sys.platform == 'win32':
                # Windows often has SSL verification issues - disable strict checking
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                ssl._create_default_https_context = lambda: ssl_context
                logger.info("Modified SSL context for Windows platform")
        except Exception as ssl_error:
            logger.warning(f"Could not configure SSL context: {ssl_error}")
        
        # Import the comparison function
        try:
            from checkout_automation import compare_html_content
            
            # Compare HTML content
            logger.info("Comparing HTML content")
            comparison = compare_html_content(previous_html, current_html)
            
            # Determine if reanalysis is needed
            should_reanalyze = comparison['significant_change']
            next_attempt = attempt + 1 if should_reanalyze else attempt
            should_wait = should_reanalyze and next_attempt <= max_attempts
            
            # Log comparison results
            logger.info(f"HTML comparison results: significant_change={comparison['significant_change']}, " +
                      f"similarity_score={comparison['similarity_score']:.2f}")
            
            # Create response
            response = {
                'comparison': {
                    'significant_change': comparison['significant_change'],
                    'similarity_score': comparison['similarity_score'],
                    'structure_similarity': comparison['structure_similarity'],
                    'new_elements_count': len(comparison['new_elements']),
                    'removed_elements_count': len(comparison['removed_elements']),
                    'changed_elements_count': len(comparison['changed_elements']),
                    'previous_title': comparison['previous_title'],
                    'current_title': comparison['current_title']
                },
                'reanalysis_instructions': {
                    'should_reanalyze': should_reanalyze,
                    'should_wait': should_wait,
                    'wait_time': wait_time,
                    'max_attempts': max_attempts,
                    'current_attempt': attempt,
                    'next_attempt': next_attempt,
                    'session_id': session_id
                }
            }
            
            # If significant change detected and more attempts are available, tell client to reanalyze
            if should_reanalyze and next_attempt <= max_attempts:
                logger.info(f"Significant HTML changes detected, instructing client to reanalyze (attempt {next_attempt})")
                response['reanalysis_instructions']['message'] = "Significant page changes detected, please reanalyze"
            else:
                if should_reanalyze:
                    logger.info("Significant changes detected but max attempts reached")
                    response['reanalysis_instructions']['message'] = "Max reanalysis attempts reached"
                else:
                    logger.info("No significant HTML changes detected")
                    response['reanalysis_instructions']['message'] = "No significant changes detected"
            
            return jsonify(response)
            
        except Exception as compare_error:
            error_msg = str(compare_error)
            logger.error(f"Error in compare_html_content: {error_msg}")
            
            if "SSL" in error_msg or "EOF occurred in violation of protocol" in error_msg:
                return jsonify({
                    'error': 'SSL/Network error',
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                }), 503  # Service Unavailable
            else:
                return jsonify({
                    'error': 'HTML comparison error',
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                }), 500
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error comparing HTML: {error_message}")
        
        if "SSL" in error_message or "EOF occurred in violation of protocol" in error_message:
            return jsonify({
                'error': 'SSL/Network error',
                'message': error_message,
                'timestamp': datetime.now().isoformat()
            }), 503  # Service Unavailable
        else:
            return jsonify({
                'error': 'Internal server error',
                'message': error_message,
                'timestamp': datetime.now().isoformat()
            }), 500


# Store the URL where form automation was last performed
last_form_url = None

@app.route('/page-change', methods=['POST'])
def handle_page_change():
    """Handle page change notifications from the extension after form filling.
    
    Expected POST data:
    {
        "previousUrl": "URL where form automation was performed",
        "currentUrl": "current page URL",
        "timestamp": "ISO timestamp of when the change occurred"
    }
    """
    try:
        # Log the start of the request processing
        logger.info("=== Processing Page Change Request ===")
        req_timestamp = datetime.now()
        
        # Parse JSON data
        try:
            data = request.get_json()
            if not data:
                logger.error("No JSON data in request")
                return jsonify({
                    "success": False,
                    "error": "No JSON data provided",
                    "timestamp": req_timestamp.isoformat()
                }), 400
        except Exception as json_error:
            logger.error(f"JSON parsing error: {str(json_error)}")
            return jsonify({
                "success": False,
                "error": f"Invalid JSON: {str(json_error)}",
                "timestamp": req_timestamp.isoformat()
            }), 400
        
        # Get and validate URLs
        current_url = data.get('currentUrl')
        previous_url = data.get('previousUrl')
        client_timestamp = data.get('timestamp')
        is_checkout_page = data.get('isCheckoutPage', False)
        
        # Validate required fields
        if not current_url:
            logger.error("Missing currentUrl in request")
            return jsonify({
                "success": False,
                "error": "Current URL is required",
                "timestamp": req_timestamp.isoformat()
            }), 400
            
        if not previous_url:
            logger.error("Missing previousUrl in request")
            return jsonify({
                "success": False,
                "error": "Previous URL is required",
                "timestamp": req_timestamp.isoformat()
            }), 400
        
        # Check if the page has actually changed
        url_changed = current_url != previous_url
        
        # Determine if automation should restart
        # MODIFIED: Always restart automation on ANY page change, regardless of checkout detection
        # This treats any page change as a potential checkout page that should be processed
        should_restart = url_changed
        
        # Log additional analysis for debugging
        restart_reason = ""
        if url_changed:
            restart_reason = "Page URL changed - treating as checkout page"
        else:
            restart_reason = "No page change detected"
            
        logger.info(
            f"\nURL Change Analysis:\n" +
            f"Previous URL: {previous_url}\n" +
            f"Current URL: {current_url}\n" +
            f"Changed: {url_changed}\n" +
            f"Is Checkout Page: {is_checkout_page}\n" +
            f"Should Restart: {should_restart}\n" +
            f"Restart Reason: {restart_reason}\n" +
            f"Client Timestamp: {client_timestamp}\n" +
            f"Server Timestamp: {req_timestamp.isoformat()}"
        )
        
        # Log the page change to a file with more detailed information
        timestamp = req_timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"page_change_{timestamp}.txt"
        filepath = os.path.join(LOGS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=== Page Change Event ===\n")
            f.write(f"Server Timestamp: {req_timestamp.isoformat()}\n")
            f.write(f"Client Timestamp: {client_timestamp}\n")
            f.write("\nURL Information:\n")
            f.write(f"Previous URL: {previous_url}\n")
            f.write(f"Current URL: {current_url}\n")
            f.write(f"URL Changed: {url_changed}\n")
            f.write(f"Is Checkout Page: {is_checkout_page}\n")
            f.write(f"Should Restart: {should_restart}\n")
            f.write("\nRequest Details:\n")
            f.write(f"Remote IP: {request.remote_addr}\n")
            f.write(f"User Agent: {request.headers.get('User-Agent', 'Unknown')}\n")
            f.write(f"Content Type: {request.headers.get('Content-Type', 'Unknown')}\n")
        
        logger.info(f"Page change details logged to: {filename}")
        
        # Send success response with detailed information
        return jsonify({
            "success": True,
            "shouldRestart": should_restart,
            "message": "Page change recorded successfully",
            "data": {
                "urlChanged": url_changed,
                "isCheckoutPage": is_checkout_page,
                "shouldRestart": should_restart,
                "previousUrl": previous_url,
                "currentUrl": current_url,
                "clientTimestamp": client_timestamp,
                "serverTimestamp": req_timestamp.isoformat(),
                "logFile": filename
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing page change: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': ['/health', '/process-checkout', '/analyze-form', '/process-with-reanalysis', '/compare-html']
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    print("🚀 Starting Checkout Automation API Server...")
    print("=" * 50)
    print("📡 Server will be available at: http://localhost:5000")
    print("🤖 Ready to process checkout forms!")
    print(" Use Ctrl+C to stop the server")
    print("=" * 50)
    
    # Run the Flask server
    app.run(
        host='localhost',
        port=5000,
        debug=True,  # Enable debug mode for development
        threaded=True  # Enable threading for concurrent requests
    )
