import os
import sys
import json
import glob
import uuid
import time
import numpy as np
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session, flash
import werkzeug.utils
import tempfile
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# Function to log user interactions
def log_interaction(interaction_type, product_info):
    """
    Log user interactions with products.
    
    Args:
        interaction_type (str): Type of interaction (purchased, view, search)
        product_info (dict): Information about the product or search query
    """
    try:
        # Create logs directory if it doesn't exist
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logs_path = os.path.join(project_root, 'logs.txt')
        
        # Format the log entry based on the interaction type
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if interaction_type == 'search':
            log_entry = f"{timestamp},{interaction_type},{product_info.get('query', '')},{product_info.get('filters', '')}"
        else:  # purchased or view
            log_entry = (f"{timestamp},{interaction_type},{product_info.get('title', '')},"
                        f"{product_info.get('color', '')},"
                        f"{product_info.get('specs', '')},"
                        f"{product_info.get('price', '')},"
                        f"ratings:{product_info.get('rating', '')},"
                        f"{product_info.get('rating_count', '')}")
        
        # Print log entry for debugging
        print(f"Logging interaction: {log_entry}")
        
        # Read existing logs
        existing_logs = []
        if os.path.exists(logs_path):
            with open(logs_path, 'r', encoding='utf-8') as f:
                existing_logs = f.readlines()
        
        # Add new log at the beginning (reverse chronological order)
        with open(logs_path, 'w', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")
            f.writelines(existing_logs)
            
        return True
    except Exception as e:
        print(f"Error logging interaction: {e}")
        return False

# Custom JSON encoder to handle NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)

# Add the root directory to path so we can import from project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from blocks import image_extractions, suggested_prompts
from main_pipeline import main_pipeline

# Global variable to track if automation is available
HAS_AUTOMATION = False

# Database setup
db = SQLAlchemy()

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Card details
    card_number = db.Column(db.String(16))  # In production, this should be encrypted
    card_expiry = db.Column(db.String(5))
    card_holder = db.Column(db.String(100))
    card_cvv = db.Column(db.String(4))  # In production, this should never be stored
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_card_details(self):
        return bool(self.card_number and self.card_expiry and self.card_holder)

def create_app():
    global HAS_AUTOMATION
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
    app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_session')  # Required for sessions
    app.json.encoder = NumpyEncoder  # Use custom JSON encoder for NumPy types

    # Import checkout automation controller if available
    try:
        automation_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'automation')
        sys.path.append(automation_dir)
        
        # Now import directly
        from checkout_controller import router as checkout_automation_router, registerTestRoutes
        print(f"Successfully imported checkout_controller from {automation_dir}")
        HAS_AUTOMATION = True
    except ImportError as e:
        print(f"Checkout automation controller not found. AI Checkout features will be disabled. Error: {e}")
        HAS_AUTOMATION = False

    # Database setup
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(project_root, "database", "appain.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Login manager setup
    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create a temporary directory for uploaded images
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'appain_uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Dataset images folder - ensure it's an absolute path
    DATASET_IMAGES = os.path.join(project_root, 'datasets', 'amazon-2023-all(set)', 'images')
    print(f"Loading images from: {DATASET_IMAGES}")
    if not os.path.exists(DATASET_IMAGES):
        print(f"WARNING: Dataset images directory does not exist: {DATASET_IMAGES}")
        print("Creating directory...")
        os.makedirs(DATASET_IMAGES, exist_ok=True)
    
    # Register checkout automation routes if available
    if HAS_AUTOMATION:
        try:
            app.register_blueprint(checkout_automation_router, url_prefix='/api/automation')
            registerTestRoutes(app)
            print("AI Checkout automation routes registered successfully")
            print(f"HAS_AUTOMATION is set to: {HAS_AUTOMATION}")
        except Exception as e:
            print(f"Error registering checkout automation routes: {e}")
            HAS_AUTOMATION = False
    else:
        print("AI Checkout automation is disabled because HAS_AUTOMATION is False")
    
    # Check for automation scripts directory
    automation_dir = os.path.join(project_root, 'src', 'frontend', 'scripts', 'automation')
    if os.path.exists(automation_dir):
        print(f"AI Checkout automation directory found: {automation_dir}")
    else:
        print(f"WARNING: AI Checkout automation directory not found: {automation_dir}")
    
    # Mock Stripe checkout sessions (for demo purposes)
    mock_checkout_sessions = {}

    # Helper function to make objects JSON serializable
    def make_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.number, np.integer, np.floating, np.bool_)):
            return obj.item()
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(item) for item in obj]
        elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32, np.float16)):
            return float(obj)
        else:
            return obj

    @app.route('/')
    def index():
        """Render the main application page."""
        return render_template('index.html', ai_checkout_enabled=HAS_AUTOMATION)

    @app.route('/cart')
    def cart():
        """Render the shopping cart page."""
        return render_template('cart.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration page."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists. Please choose a different one.', 'error')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered. Please use a different one.', 'error')
                return redirect(url_for('register'))
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login page."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        """Log out the current user."""
        logout_user()
        return redirect(url_for('index'))

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        """User profile page for managing personal info and card details."""
        if request.method == 'POST':
            # Update card details
            current_user.card_number = request.form.get('card_number')
            current_user.card_expiry = request.form.get('card_expiry')
            current_user.card_holder = request.form.get('card_holder')
            # Note: CVV is typically not stored for security reasons
            # But for demo purposes, we'll update it if provided
            if request.form.get('card_cvv'):
                current_user.card_cvv = request.form.get('card_cvv')
            
            db.session.commit()
            flash('Card details updated successfully.', 'success')
            return redirect(url_for('profile'))
        
        return render_template('profile.html')

    @app.route('/test-images')
    def test_images():
        """Test route to check image availability."""
        image_files = []
        
        try:
            # List all files in the dataset images directory
            pattern = os.path.join(DATASET_IMAGES, '*.*')
            image_files = glob.glob(pattern)
            
            # Format them for display
            files = []
            for img in image_files:
                basename = os.path.basename(img)
                files.append({'path': img, 'name': basename, 'url': f'/dataset-images/{basename}'})
            
            # Just return the first 20 files
            return jsonify({
                'directory': DATASET_IMAGES,
                'exists': os.path.exists(DATASET_IMAGES),
                'file_count': len(image_files),
                'files': files[:20] if files else []
            })
        except Exception as e:
            return jsonify({'error': str(e)})

    @app.route('/dataset-images/<path:filename>')
    def dataset_image(filename):
        """Serve images from the dataset directory."""
        print(f"Requested image: {filename}")
        print(f"Looking in: {DATASET_IMAGES}")
        try:
            # Check if the file exists
            file_path = os.path.join(DATASET_IMAGES, filename)
            if os.path.isfile(file_path):
                return send_from_directory(DATASET_IMAGES, filename)
            else:
                print(f"Image file does not exist: {file_path}")
                return "", 404
        except Exception as e:
            print(f"Error serving image {filename}: {e}")
            return "", 404

    @app.route('/static/img/<path:filename>')
    def serve_static_image(filename):
        """Serve static images."""
        return app.send_static_file(f'img/{filename}')

    @app.route('/api/search', methods=['POST'])
    def search():
        """Handle search requests with text and/or image input."""
        try:
            # Get text query if any
            text_query = request.form.get('text', '')
            reset = request.form.get('reset', 'true').lower() == 'true'
            
            # Check for retrieved indices from previous search
            retrieved_idx = None
            if 'retrieved_idx' in request.form and request.form['retrieved_idx']:
                try:
                    retrieved_idx = json.loads(request.form['retrieved_idx'])
                except json.JSONDecodeError:
                    pass
            
            # Process uploaded image if any
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    filename = werkzeug.utils.secure_filename(file.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(image_path)
                    # Store image path in session for future searches
                    session['last_image_path'] = image_path
            
            # Always use the last uploaded image (from session) or a default one
            image_path = session.get('last_image_path')
            
            # If no image has been uploaded yet, return an error
            if not image_path:
                return jsonify({
                    'success': False,
                    'error': 'Image input is required. Please upload an image.'
                }), 400
            
            # Log the search interaction
            if text_query:
                search_info = {
                    'query': text_query,
                    'filters': request.form.get('filters', '')
                }
                log_interaction('search', search_info)
            
            # Call the main pipeline
            indices, metadata = main_pipeline(
                modification_text=text_query,
                reset=reset,
                image_path=image_path,
            )
            
            # Format products for display
            products = []
            
            # Calculate discount percentage helper function
            def calculate_discount(price, actual_price):
                try:
                    # Remove currency symbols and commas
                    price_clean = price.replace('₹', '').replace(',', '').strip() if isinstance(price, str) else price
                    actual_price_clean = actual_price.replace('₹', '').replace(',', '').strip() if isinstance(actual_price, str) else actual_price
                    
                    # Convert to float
                    price_value = float(price_clean)
                    actual_price_value = float(actual_price_clean)
                    
                    if actual_price_value > 0:
                        discount = ((actual_price_value - price_value) / actual_price_value) * 100
                        return round(discount)
                    return 0
                except (ValueError, TypeError, AttributeError):
                    return 0
                    
            for idx in indices[:20]:  # Limit to top 20 results
                item = metadata[idx]
                
                # Extract product title from metadata
                title = make_serializable(item.get('name', ''))
                
                # Make product data serializable
                product = {
                    'image_path': image_path,
                    'image_url': make_serializable(item.get('image_url', '')),
                    'title': title,
                    'description': make_serializable(item.get('discription', '')),
                    'price': make_serializable(item.get('price', '')),
                    'actual_price': make_serializable(item.get('actual_price', '')),
                    'rating': make_serializable(item.get('rating', 0)),
                    'rating_count': make_serializable(item.get('rating_count', 0)),
                    'discount': calculate_discount(item.get('price', ''), item.get('actual_price', '')),
                    'id': make_serializable(idx),
                    'tags': make_serializable(item.get('tags', []))
                }
                products.append(product)
        
            # Create response data
            response_data = {
                'success': True,
                'indices': indices.tolist() if isinstance(indices, np.ndarray) else indices,
                'products': products
            }
            
            # Return the response using flask.Response directly with our custom encoder
            return app.response_class(
                response=json.dumps(response_data, cls=NumpyEncoder),
                status=200,
                mimetype='application/json'
            )
        
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/view-product', methods=['POST'])
    def view_product():
        """Track when a user views a product's details."""
        try:
            data = request.json
            product_id = data.get('product_id')
            
            if not product_id:
                return jsonify({
                    'success': False,
                    'error': 'Product ID is required'
                }), 400
            
            # Get product details - in a real app, this would come from a database
            # For now, we'll use the metadata from the search session
            product_info = {}
            
            if 'product_data' in data:
                product_info = data.get('product_data', {})
                
                # Log the product view
                view_info = {
                    'title': product_info.get('title', ''),
                    'color': product_info.get('color', ''),
                    'specs': product_info.get('specs', ''),
                    'price': product_info.get('price', ''),
                    'rating': product_info.get('rating', ''),
                    'rating_count': product_info.get('rating_count', '')
                }
                log_interaction('view', view_info)
                
            return jsonify({
                'success': True,
                'message': 'Product view tracked'
            })
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/checkout', methods=['POST'])
    def create_checkout():
        """Create a checkout session for the selected product."""
        try:
            data = request.json
            product_id = data.get('product_id')
            product_data = data.get('product_data', {})
            cart_items = data.get('cart_items', [])
            
            if not product_id:
                return jsonify({
                    'success': False,
                    'error': 'Product ID is required'
                }), 400
            
            # Create a mock checkout session ID
            session_id = str(uuid.uuid4())
            
            # Make sure image URL is properly set
            if 'image_url' in product_data and product_data['image_url']:
                # Image URL already exists and is valid
                pass
            elif 'image_path' in product_data and product_data['image_path']:
                # If no image_url but image_path exists, use it as a fallback
                if product_data['image_path'].startswith('http'):
                    # If it's already a URL, use it directly
                    product_data['image_url'] = product_data['image_path']
                else:
                    # If it's a local path, we need to handle it differently
                    # For demonstration, we'll just note this in logs
                    print(f"Local image path detected: {product_data['image_path']}")
                    # Could serve this through a local route if needed
            
            # Debug log
            print(f"Checkout session created with product data: {product_data}")
            
            # Store session information (in a real app, this would be in a database)
            mock_checkout_sessions[session_id] = {
                'product_id': product_id,
                'product_data': product_data,  # Store the product data from the request
                'cart_items': cart_items,      # Store all cart items
                'status': 'pending',
                'created_at': time.time()
            }
            
            # In a real app, we would create a Stripe checkout session here
            # For demo purposes, we'll redirect to our mock checkout page
            checkout_url = url_for('checkout_page', session_id=session_id, _external=True)
            
            return jsonify({
                'success': True,
                'checkout_url': checkout_url,
                'session_id': session_id
            })
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/checkout/<session_id>', methods=['GET'])
    def checkout_page(session_id):
        """Render the checkout page for the given session."""
        # In a real app, we would fetch session details from Stripe or our database
        session_data = mock_checkout_sessions.get(session_id)
        if not session_data:
            return render_template('error.html', message='Checkout session not found'), 404
        
        # Get the product information
        product_id = session_data.get('product_id')
        product_info = None
        
        # Print debug info about the session data
        print(f"DEBUG - Checkout session data: {session_data}")
        
        # Process all cart items to ensure they have proper image URLs
        if 'cart_items' in session_data and session_data['cart_items']:
            for item in session_data['cart_items']:
                # Make sure image_url is properly formatted
                if 'image_url' in item and item['image_url']:
                    if not item['image_url'].startswith(('http://', 'https://', '/')):
                        # This is a local file path, not a web URL
                        print(f"DEBUG - Converting local path to URL for cart item: {item['image_url']}")
                        # Extract just the filename from the path
                        image_filename = os.path.basename(item['image_url'])
                        item['local_image_path'] = item['image_url']  # Save original path
                        # Use a route that can serve this file
                        item['image_url'] = f"/dataset-images/{image_filename}"
                elif 'image_path' in item and item['image_path']:
                    # If no image_url but image_path exists, use it
                    if not item['image_path'].startswith(('http://', 'https://', '/')):
                        # Extract just the filename
                        image_filename = os.path.basename(item['image_path'])
                        item['image_url'] = f"/dataset-images/{image_filename}"
                    else:
                        item['image_url'] = item['image_path']
                else:
                    # Set a default image if none exists
                    item['image_url'] = "/static/img/product-placeholder.svg"
        
        # In a real app, this would fetch from a database
        # For demo, we'll generate mock product data
        if product_id:
            try:
                # Check if we have product data in the session
                if 'product_data' in session_data and session_data['product_data']:
                    print(f"DEBUG - Using product data from session: {session_data['product_data']}")
                    product_info = session_data['product_data']
                    
                    # Make sure image_url is properly formatted
                    if 'image_url' in product_info and product_info['image_url']:
                        if not product_info['image_url'].startswith(('http://', 'https://', '/')):
                            # This is a local file path, not a web URL
                            print(f"DEBUG - Converting local path to URL: {product_info['image_url']}")
                            # For demonstration, we'll convert to a web URL (in real app, serve through a local route)
                            # Extract just the filename from the path
                            image_filename = os.path.basename(product_info['image_url'])
                            product_info['local_image_path'] = product_info['image_url']  # Save original path
                            # Use a route that can serve this file
                            product_info['image_url'] = f"/dataset-images/{image_filename}"
                    
                    elif 'image_path' in product_info and product_info['image_path']:
                        # If no image_url but image_path exists, use it
                        if not product_info['image_path'].startswith(('http://', 'https://', '/')):
                            # Extract just the filename
                            image_filename = os.path.basename(product_info['image_path'])
                            product_info['image_url'] = f"/dataset-images/{image_filename}"
                        else:
                            product_info['image_url'] = product_info['image_path']
                else:
                    # For demo purposes, create mock product data
                    print("DEBUG - No product data in session, using mock data")
                    product_info = {
                        'id': product_id,
                        'title': f"Product #{product_id}",
                        'price': "₹499",
                        'actual_price': "₹599",
                        'image_url': "/static/img/product-placeholder.svg",
                        'description': "Product description not available",
                        'quantity': 1
                    }
                
                # Store product data in session for later use
                session_data['product_data'] = product_info
                print(f"DEBUG - Final product info for checkout: {product_info}")
                
            except Exception as e:
                print(f"Error getting product info: {e}")
                # Fallback product data
                product_info = {
                    'id': product_id,
                    'title': f"Product #{product_id}",
                    'price': "₹499",
                    'image_url': "/static/img/product-placeholder.svg",
                    'quantity': 1
                }
        
        # Calculate order totals
        subtotal = 0
        shipping = 25  # Default shipping cost in rupees
        tax = 0
        
        # Calculate subtotal from all cart items
        if 'cart_items' in session_data and session_data['cart_items']:
            for item in session_data['cart_items']:
                price_str = item.get('price', '0')
                quantity = int(item.get('quantity', 1))
                
            # Clean price string and convert to float
                if isinstance(price_str, str):
                    price_str = price_str.replace('₹', '').replace(',', '').strip()
                try:
                    price = float(price_str)
                    subtotal += price * quantity
                except (ValueError, TypeError):
                    # Skip if price can't be converted
                    pass
        elif product_info and 'price' in product_info:
            # Fallback to single product if no cart items
            price_str = product_info['price']
            if isinstance(price_str, str):
                price_str = price_str.replace('₹', '').replace(',', '').strip()
            try:
                price = float(price_str)
                quantity = int(product_info.get('quantity', 1))
                subtotal = price * quantity
            except (ValueError, TypeError):
                subtotal = 499  # Default if conversion fails
        else:
            subtotal = 499  # Default value
        
        # Calculate tax
        tax = round(subtotal * 0.08)  # 8% tax rate, rounded to nearest rupee
            
        order_total = subtotal + shipping + tax
        
        # Format currency values with Rupee symbol
        def format_price(value):
            return f"₹{value}"
        
        order_summary = {
            'subtotal': format_price(subtotal),
            'shipping': format_price(shipping),
            'tax': format_price(tax),
            'total': format_price(order_total)
        }
        
        # Get card details for autofill if user is logged in
        card_details = None
        if current_user.is_authenticated and current_user.has_card_details():
            card_details = {
                'number': current_user.card_number,
                'expiry': current_user.card_expiry,
                'holder': current_user.card_holder,
                'cvv': current_user.card_cvv
            }
        
        # Get address from user profile if available
        shipping_address = None
        if current_user.is_authenticated:
            # In a real app, this would come from the user's saved addresses
            shipping_address = {
                'name': current_user.username,
                'street': '123 Main St',
                'city': 'Anytown',
                'state': 'CA',
                'zip': '12345',
                'country': 'United States'
            }
        
        # Print debug info
        print(f"Rendering checkout page with ai_checkout_enabled={HAS_AUTOMATION}")
        
        # Render the checkout template with all data
        return render_template(
            'checkout.html',
            session_id=session_id,
            session_data=session_data,
            product=product_info,
            order_summary=order_summary,
            card_details=card_details,
            shipping_address=shipping_address,
            ai_checkout_enabled=True  # Force enable for testing
        )

    @app.route('/checkout/complete/<session_id>', methods=['POST'])
    def complete_checkout(session_id):
        """Process the checkout form submission."""
        try:
            # In a real app, we would verify payment with Stripe or another payment processor
            session_data = mock_checkout_sessions.get(session_id)
            if not session_data:
                return render_template('error.html', message='Checkout session not found'), 404
            
            # Get form data
            form_data = request.form
            
            # Extract shipping info
            shipping_info = {
                'name': form_data.get('shipping_name', ''),
                'street': form_data.get('shipping_street', ''),
                'city': form_data.get('shipping_city', ''),
                'state': form_data.get('shipping_state', ''),
                'zip': form_data.get('shipping_zip', ''),
                'country': form_data.get('shipping_country', '')
            }
            
            # Extract billing info
            same_as_shipping = form_data.get('same_as_shipping') == 'on'
            
            billing_info = {}
            if same_as_shipping:
                billing_info = shipping_info
            else:
                billing_info = {
                    'name': form_data.get('billing_name', ''),
                    'street': form_data.get('billing_street', ''),
                    'city': form_data.get('billing_city', ''),
                    'state': form_data.get('billing_state', ''),
                    'zip': form_data.get('billing_zip', ''),
                    'country': form_data.get('billing_country', '')
                }
            
            # Extract payment info
            payment_info = {
                'card_number': form_data.get('card_number', ''),
                'card_name': form_data.get('card_name', ''),
                'card_expiry': form_data.get('card_expiry', ''),
                'card_cvv': form_data.get('card_cvv', '')
            }
            
            # Save card details if user is logged in and checked save_card
            save_card = form_data.get('save_card') == 'on'
            if current_user.is_authenticated and save_card:
                current_user.card_number = payment_info['card_number'].replace(' ', '')
                current_user.card_holder = payment_info['card_name']
                current_user.card_expiry = payment_info['card_expiry']
                current_user.card_cvv = payment_info['card_cvv']
                db.session.commit()
            
            # Get ordered items from session
            ordered_items = []
            order_total = 0
            
            # Use cart items if available
            if 'cart_items' in session_data and session_data['cart_items']:
                # Process all items in the cart
                for item in session_data['cart_items']:
                    price_str = item.get('price', '0')
                if isinstance(price_str, str):
                    price_str = price_str.replace('₹', '').replace(',', '').strip()
                    
                    try:
                        price = float(price_str)
                        quantity = int(item.get('quantity', 1))
                        item_total = price * quantity
                        order_total += item_total
                        
                        ordered_items.append({
                            'id': item.get('id', 'unknown'),
                            'title': item.get('title', 'Unknown Product'),
                            'price': price,
                            'quantity': quantity,
                            'total': item_total,
                            'image_url': item.get('image_url', '/static/img/product-placeholder.svg')
                        })
                    except (ValueError, TypeError) as e:
                        print(f"Error processing cart item: {e}")
                        # Skip invalid items
            else:
                    # Fallback to the primary product if no cart items
                product_info = session_data.get('product_data', {})
                price_str = product_info.get('price', '499')
                if isinstance(price_str, str):
                    price_str = price_str.replace('₹', '').replace(',', '').strip()
            
                try:
                    price = float(price_str)
                    quantity = int(product_info.get('quantity', 1))
                    item_total = price * quantity
                    order_total += item_total
                    
                    ordered_items.append({
                        'id': product_info.get('id', 'unknown'),
                        'title': product_info.get('title', 'Unknown Product'),
                        'price': price,
                        'quantity': quantity,
                        'total': item_total,
                        'image_url': product_info.get('image_url', '/static/img/product-placeholder.svg')
                    })
                except (ValueError, TypeError) as e:
                    print(f"Error processing primary product: {e}")
                    # Create a default item
                    ordered_items.append({
                        'id': 'default',
                        'title': 'Default Product',
                        'price': 499,
                        'quantity': 1,
                        'total': 499,
                        'image_url': '/static/img/product-placeholder.svg'
                    })
                    order_total = 499
            
            # Calculate order summary
            shipping_cost = 25  # Default shipping cost
            shipping_method = form_data.get('shipping_method', 'standard')
            
            if shipping_method == 'express':
                shipping_cost = 50
            elif shipping_method == 'next_day':
                shipping_cost = 100
            
            tax = round(order_total * 0.08)  # 8% tax rate
            
            # Check if a promo code was used
            promo_code = form_data.get('promo_code', '').strip().upper()
            discount = 0
            
            if promo_code == 'WELCOME10':
                discount = round(order_total * 0.1)  # 10% discount
            elif promo_code == 'FREESHIP':
                shipping_cost = 0
            elif promo_code == 'SAVE20' and order_total >= 100:
                discount = 20
            
            final_total = order_total + shipping_cost + tax - discount
            
            # Create order summary object
            order_summary = {
                'subtotal': order_total,
                'shipping': shipping_cost,
                'tax': tax,
                'discount': discount,
                'total': final_total,
                'items': ordered_items,
                'shipping_method': shipping_method,
                'promo_code': promo_code if promo_code else None
            }
            
            # In a real app, we would create an order in the database
            # For demo purposes, we'll just update the mock session
            session_data['status'] = 'completed'
            session_data['shipping_info'] = shipping_info
            session_data['billing_info'] = billing_info
            session_data['payment_info'] = {
                'last4': payment_info['card_number'][-4:] if payment_info['card_number'] else 'XXXX',
                'exp_month': payment_info['card_expiry'].split('/')[0] if '/' in payment_info['card_expiry'] else '',
                'exp_year': payment_info['card_expiry'].split('/')[1] if '/' in payment_info['card_expiry'] else '',
                'name': payment_info['card_name']
            }
            session_data['order_summary'] = order_summary
            session_data['order_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            session_data['order_number'] = f"ORD-{int(time.time())}"
            
            # Log the purchase for analytics
            for item in ordered_items:
                log_interaction('purchased', {
                    'title': item['title'],
                    'price': item['price'],
                    'quantity': item['quantity']
                })
            
            # Clear the cart in session storage
            session['cart'] = []
            
            # Return success response
            return redirect(url_for('checkout_success', session_id=session_id))
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return render_template('error.html', message=f'Error processing checkout: {str(e)}'), 500

    @app.route('/checkout/success/<session_id>')
    def checkout_success(session_id):
        """Render the success page after checkout."""
        session_data = mock_checkout_sessions.get(session_id)
        if not session_data:
            return render_template('error.html', message='Order not found'), 404
            
        # Get order information for display
        form_data = session_data.get('form_data', {})
        shipping_method = form_data.get('shipping_method', 'standard')
        
        # Determine shipping cost based on method
        shipping_cost = 25  # Default standard shipping
        if shipping_method == 'express':
            shipping_cost = 50
        elif shipping_method == 'next_day':
            shipping_cost = 100
        
        # Check for free shipping coupon
        promo_code = form_data.get('promo_code', '')
        if promo_code and promo_code.upper() == 'FREESHIP':
            shipping_cost = 0
        
        order_info = {
            'order_number': session_data.get('order_number', f"ORD-{session_id[:8]}"),
            'date': datetime.utcnow().strftime('%B %d, %Y'),
            'status': 'Processing',
            'payment_method': 'Credit Card',
            'shipping_method': shipping_method.capitalize() + ' Shipping',
            'shipping_cost': shipping_cost,
            'discount': session_data.get('discount', 0),
            'promo_code': form_data.get('promo_code', '')
        }
        
        # Get shipping address if available
        shipping_info = None
        if 'form_data' in session_data and session_data['form_data'].get('shipping_name'):
            form_data = session_data['form_data']
            shipping_info = {
                'name': form_data.get('shipping_name', ''),
                'street': form_data.get('shipping_street', ''),
                'city': form_data.get('shipping_city', ''),
                'state': form_data.get('shipping_state', ''),
                'zip': form_data.get('shipping_zip', ''),
                'country': form_data.get('shipping_country', '')
            }
        
        # Get product information if available
        product_info = session_data.get('product_data', {
            'title': 'Your product',
            'price': '₹499',
            'quantity': 1,
            'image_url': '/static/img/product-placeholder.jpg'
        })
        
        # Calculate order summary
        subtotal = 0
        if 'price' in product_info:
            price_str = product_info['price']
            if isinstance(price_str, str):
                price_str = price_str.replace('₹', '').replace(',', '').strip()
            try:
                subtotal = float(price_str)
            except (ValueError, TypeError):
                subtotal = 499
        
        tax = round(subtotal * 0.08)  # 8% tax
        discount = session_data.get('discount', 0)
        total = subtotal + shipping_cost + tax - discount
        
        # Format currency values
        order_summary = {
            'subtotal': f"₹{subtotal}",
            'shipping': f"₹{shipping_cost}",
            'tax': f"₹{tax}",
            'discount': f"₹{discount}" if discount > 0 else "",
            'total': f"₹{total}"
        }
        
        # Calculate estimated delivery date (5-7 business days from now)
        delivery_days = 7
        if shipping_method == 'express':
            delivery_days = 3
        elif shipping_method == 'next_day':
            delivery_days = 1
        
        delivery_date = (datetime.utcnow() + timedelta(days=delivery_days)).strftime('%B %d, %Y')
        
        return render_template(
            'checkout_success.html', 
            session_id=session_id,
            order=order_info,
            shipping=shipping_info,
            product=product_info,
            order_summary=order_summary,
            delivery_date=delivery_date
        )

    @app.route('/reset', methods=['POST'])
    def reset():
        """Reset the chat state."""
        # Clear the stored image path
        if 'last_image_path' in session:
            session.pop('last_image_path')
        return jsonify({'success': True})
        
    @app.route('/ai-checkout.js')
    def ai_checkout_js():
        """Serve the AI checkout JavaScript."""
        return app.send_static_file('js/ai-checkout.js')
        
    @app.route('/api/automation/checkout', methods=['POST'])
    def start_automation():
        """Start a checkout automation process."""
        try:
            data = request.json
            checkout_url = data.get('checkout_url')
            product_info = data.get('product_info', {})
            
            if not checkout_url:
                return jsonify({
                    'success': False,
                    'error': 'Checkout URL is required'
                }), 400
                
            # Generate a job ID
            job_id = str(uuid.uuid4())
            
            # Log the automation attempt
            automation_log_dir = os.path.join(project_root, 'src', 'frontend', 'scripts', 'automation')
            os.makedirs(os.path.join(automation_log_dir, 'screenshots'), exist_ok=True)
            
            log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: Starting automation for {product_info.get('title', 'Unknown Product')} at {checkout_url}"
            try:
                with open(os.path.join(automation_log_dir, 'automation.log'), 'a') as f:
                    f.write(log_entry + '\n')
            except Exception as e:
                print(f"Error writing to automation log: {e}")
            
            return jsonify({
                'success': True,
                'job_id': job_id,
                'message': 'Checkout automation started. Check logs for progress.'
            })
            
        except Exception as e:
            print(f"Error starting automation: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            
    @app.route('/api/automation/status/<job_id>', methods=['GET'])
    def automation_status(job_id):
        """Get the status of a checkout automation job."""
        # In a real implementation, we would fetch status from a database or the Node.js service
        # For this demo, we'll return a simulated status
        
        # Simulate a random progress amount based on the job ID
        progress = int(int(job_id.replace('-', '')[0:8], 16) % 100)
        
        return jsonify({
            'success': True,
            'status': 'running' if progress < 100 else 'completed',
            'progress': progress,
            'logs': [
                'Started checkout automation',
                'Analyzed checkout form',
                'Filling out customer information',
                'Entering payment details' if progress > 50 else None,
                'Confirming order' if progress > 80 else None,
                'Order completed successfully!' if progress == 100 else None
            ]
        })

    @app.route('/ai-checkout-status')
    def ai_checkout_status():
        """Return the status of the AI checkout system."""
        return jsonify({
            'enabled': HAS_AUTOMATION,
            'version': '1.0.0',
            'status': 'active' if HAS_AUTOMATION else 'disabled'
        })

    @app.route('/api/product/suggest', methods=['POST'])
    def product_suggestions():
        """Get product suggestions based on a product."""
        try:
            data = request.json
            product = data.get('product', {})
            
            if not product:
                return jsonify({
                    'success': False,
                    'error': 'Product data is required'
                }), 400
                
            # For a real application, you would query your database or recommendation engine
            # For this demo, we'll return dummy suggestions
            suggestions = []
            
            # Get the product category or use title for matching
            category = product.get('category', '').lower()
            title = product.get('title', '').lower()
            
            # Define relationship mappings for related products
            relationship_map = {
                'mobile phone': ['phone case', 'screen guard', 'earphone', 'charger', 'power bank'],
                'laptop': ['laptop bag', 'mouse', 'keyboard', 'cooling pad', 'laptop stand'],
                'camera': ['memory card', 'camera bag', 'tripod', 'lens', 'camera battery'],
                'headphone': ['headphone case', 'audio splitter', 'headphone stand'],
                'smartwatch': ['watch strap', 'screen protector', 'charger']
            }
            
            # Find suggestions based on category or title
            for key, related_items in relationship_map.items():
                if key in category or key in title:
                    suggestions = related_items
                    break
            
            # If no category match, provide generic suggestions
            if not suggestions:
                suggestions = ['popular items', 'trending now', 'recommended for you']
                
            return jsonify({
                'success': True,
                'suggestions': suggestions
            })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/suggest-questions', methods=['POST'])
    def suggest_followup_questions():
        """Generate suggested search queries based on user's previous query or uploaded image."""
        try:
            data = request.json
            user_query = data.get('query', '')
            
            if not user_query:
                return jsonify({
                    'success': False,
                    'error': 'Query is required'
                }), 400
            
            # Import here to avoid circular imports
            import sys
            sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
            from main_pipeline import current_text, back_bone
            
            # Get suggested search queries from our module with additional context
            suggestions = suggested_prompts.get_suggested_prompts(
                user_query, 
                current_text=current_text, 
                back_bone=back_bone
            )
            
            return jsonify({
                'success': True,
                'suggestions': suggestions
            })
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 