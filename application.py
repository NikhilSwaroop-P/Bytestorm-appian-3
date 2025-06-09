#!/usr/bin/env python
"""
Vercel entry point for the Product Recommendation System.
"""
import os
import sys
from flask import Flask, render_template, redirect, url_for

# Add the root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Create a minimal Flask application for Vercel deployment
app = Flask(__name__, 
           static_folder='src/frontend/static',
           template_folder='src/frontend/templates')

# Set secret key
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_session')

@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html', ai_checkout_enabled=False)

@app.route('/cart')
def cart():
    """Render the shopping cart page."""
    return render_template('cart.html')

@app.route('/login')
def login():
    """Placeholder login route"""
    return render_template('login.html')

@app.route('/register')
def register():
    """Placeholder register route"""
    return render_template('register.html')

# Add more routes as needed

if __name__ == "__main__":
    # This block only runs when the script is executed directly
    port = int(os.environ.get('PORT', 3000))
    app.run(debug=False, host='0.0.0.0', port=port) 