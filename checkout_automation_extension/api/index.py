"""
Vercel Serverless Function for AI Checkout Automation
====================================================

This file adapts the Flask server to run as a Vercel serverless function.
It provides the same API endpoints as the local server.

Main differences:
- Uses Vercel's serverless architecture
- Environment variables are set in the Vercel dashboard
- Log files are not saved locally (uses Vercel logging)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import logging
from datetime import datetime
import traceback

# Import automation modules - these need to be in the same directory or properly imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from python_backend.checkout_automation import automate_checkout_form, automate_form_filling_with_reanalysis, compare_html_content
from python_backend.process_checkout import process_checkout_page

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for browser extension communication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the server is running."""
    return jsonify({
        "status": "ok",
        "message": "AI Checkout Automation API is running",
        "version": "1.0.0"
    })

@app.route('/process-checkout', methods=['POST'])
def process_checkout():
    """Main endpoint that processes checkout forms and returns filling instructions."""
    try:
        data = request.json
        if not data or 'html' not in data:
            return jsonify({"error": "Missing required data"}), 400
        
        logger.info("Received checkout processing request")
        
        # Process the checkout page
        html_content = data.get('html', '')
        user_profile = data.get('userProfile', {})
        results = process_checkout_page(html_content, user_profile)
        
        return jsonify(results)
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        logger.error(f"Error processing checkout: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/analyze-form', methods=['POST'])
def analyze_form():
    """Endpoint that analyzes a form without filling instructions."""
    try:
        data = request.json
        if not data or 'html' not in data:
            return jsonify({"error": "Missing required data"}), 400
        
        logger.info("Received form analysis request")
        
        # Extract form fields and provide analysis
        html_content = data.get('html', '')
        results = automate_checkout_form(html_content, analysis_only=True)
        
        return jsonify(results)
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        logger.error(f"Error analyzing form: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/process-with-reanalysis', methods=['POST'])
def process_with_reanalysis():
    """Endpoint for form filling with automatic reanalysis capability."""
    try:
        data = request.json
        if not data or 'html' not in data:
            return jsonify({"error": "Missing required data"}), 400
        
        logger.info("Received checkout processing with reanalysis request")
        
        html_content = data.get('html', '')
        user_profile = data.get('userProfile', {})
        previous_actions = data.get('previousActions', [])
        
        results = automate_form_filling_with_reanalysis(
            html_content, 
            user_profile, 
            previous_actions
        )
        
        return jsonify(results)
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        logger.error(f"Error processing with reanalysis: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/compare-html', methods=['POST'])
def compare_html():
    """Endpoint for comparing previous and current HTML to determine if reanalysis is needed."""
    try:
        data = request.json
        if not data or 'previousHtml' not in data or 'currentHtml' not in data:
            return jsonify({"error": "Missing required data"}), 400
        
        logger.info("Received HTML comparison request")
        
        previous_html = data.get('previousHtml', '')
        current_html = data.get('currentHtml', '')
        
        results = compare_html_content(previous_html, current_html)
        
        return jsonify(results)
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        logger.error(f"Error comparing HTML: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

@app.route('/page-change', methods=['POST'])
def page_change():
    """Endpoint for receiving page change notifications from the extension."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Missing required data"}), 400
        
        logger.info("Received page change notification")
        logger.info(f"Page changed to: {data.get('url', 'unknown')}")
        
        return jsonify({"status": "ok", "message": "Page change notification received"})
    except Exception as e:
        error_details = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        logger.error(f"Error handling page change: {error_details}")
        return jsonify({"error": str(e), "details": error_details}), 500

# Required for Vercel serverless function
if __name__ == '__main__':
    # This is used when running locally. Gunicorn uses the app directly
    app.run(host='0.0.0.0', port=5000, debug=True)
