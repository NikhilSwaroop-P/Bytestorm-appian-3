# Bytestorm AI Product Recommendation System

An advanced AI-powered product recommendation and checkout automation system that combines multimodal search capabilities with intelligent form filling.

## Features

### 🔍 Multimodal Search and Recommendations
- **Image + Text Search**: Find products using both images and text queries
- **Semantic Retrieval**: Leverages Jina CLIP embeddings for accurate product matching
- **Hybrid Reranking**: Combines BM25 text scores with visual similarities for optimal results
- **Product History**: Tracks user interactions to improve future recommendations

### 🛒 AI Checkout Automation
- **Browser Extension**: Chrome extension that can be activated on any e-commerce site
- **Form Detection**: Automatically identifies checkout forms and input fields
- **Smart Form Filling**: Uses AI to correctly map user information to the appropriate fields
- **Reanalysis Capability**: Can adjust its strategy if initial form filling attempts are unsuccessful

### 🧠 Core Technologies
- **JINA CLIP API**: For multimodal embeddings (text and image)
- **FAISS**: For efficient similarity search across thousands of products
- **Flask**: Powers the web interface and API endpoints
- **Browser Extension**: Chrome extension for seamless checkout experience

## Installation

### Prerequisites
- Python 3.9+ 
- Node.js (for browser extension development)
- Chrome browser (for extension testing)

### Setting Up the Environment

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/Bytestorm-appian-2-imp.git
   cd Bytestorm-appian-2-imp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up API keys:
   - You need a Jina API key (already configured in the project)
   - Voyage API key is pre-configured, but you can override it by setting:
     ```bash
     # On Windows
     set VOYAGE_API_KEY=your-api-key-here
     # On macOS/Linux
     export VOYAGE_API_KEY=your-api-key-here
     ```

## Running the Application

Hosted the app in website:
https://bytemart-bse2gbgub9acdxbn.canadacentral-01.azurewebsites.net/
-Still the extension server should be run locally and extension should be loaded into the browser

### Option 1: Using the all-in-one launcher (Recommended)

This option automatically starts both the main application and the checkout automation server in separate terminal windows.

#### Windows:
```bash
start_all.bat
```

#### macOS/Linux:
```bash
chmod +x start_all.sh  # Make the script executable (first time only)
./start_all.sh
```

> **Note:** After starting the application with the launcher, you'll still need to install the browser extension. See the [Browser Extension Setup](#browser-extension-setup-required-for-checkout-automation) section below.

### Option 2: Using individual run scripts

#### Windows:
```bash
# Start the main application
run.bat

# In a separate terminal, start the checkout automation server
cd checkout_automation_extension/python-backend
start_server.bat
```

#### macOS/Linux:
```bash
# Start the main application
./run.sh

# In a separate terminal, start the checkout automation server
cd checkout_automation_extension/python-backend
./start_server.sh
```

### Option 3: Manual startup

1. Start the main application:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
   This will start the Flask server on http://localhost:3000

2. In a separate terminal, start the checkout automation API server:
   ```bash
   cd checkout_automation_extension/python-backend
   # On Windows
   start_server.bat
   # On macOS/Linux
   ./start_server.sh
   ```
   This will start the API server on http://localhost:5000

## Browser Extension Setup (Required for Checkout Automation)

After starting both the main application and the checkout automation server, you need to install the browser extension:

1. Open Google Chrome browser

2. Navigate to `chrome://extensions/` in your browser address bar
   - Alternatively, you can access this by clicking the three dots in the top-right corner of Chrome → More tools → Extensions

3. Enable "Developer mode" by toggling the switch in the top-right corner of the Extensions page

4. Click the "Load unpacked" button that appears after enabling Developer mode

5. In the file browser that opens, navigate to your project directory and select the `checkout_automation_extension` folder
   ```
   [Project Directory]/checkout_automation_extension
   ```

6. Click "Select Folder" to install the extension

7. The Bytestorm AI Checkout Assistant extension icon should now appear in your browser toolbar (top-right corner)

8. If you don't see the icon, you might need to pin it by clicking the puzzle piece icon in the toolbar and pinning the extension

## Usage

### Product Search

1. Open your browser and go to http://localhost:3000
2. Search for products using text, images, or both:
   - Type a query in the search box
   - Upload an image for visual search
   - Combine both for more precise results
3. Browse through the recommended products
4. Click on products to view details

### Checkout Automation

1. When shopping on any e-commerce site, click the extension icon
2. Click "Activate Checkout Assistant" 
3. On a checkout page, the extension will detect form fields
4. Click "Fill Form" to automatically complete the checkout form
5. Review the filled information and make any necessary adjustments
6. Complete your purchase!

> **Note:** For more details about the Checkout Automation features, refer to the [Checkout Automation README](checkout_automation_extension/README.md) in the extension folder.

## Project Structure

- `app.py` - Main application entry point
- `blocks/` - Core AI components for search and retrieval
- `checkout_automation_extension/` - Browser extension and API
- `src/frontend/` - Web interface and user experience
- `indexes_final_jina/` - Pre-built indexes for efficient search
- `datasets/` - Product data and images

## Development

### Adding New Products

1. Add product images to `datasets/amazon-2023-all(set)/images/`
2. Update product metadata in the database
3. Rebuild indexes using the indexing scripts if necessary

### Extending the Extension

The checkout automation extension is built with a modular architecture:
- `content.js` - Content script that runs on web pages
- `checkout-automation/` - Core automation logic
- `api/` - Backend API for AI processing

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Jina AI for the CLIP embeddings API
- FAISS for vector similarity search
- All contributors to the project
