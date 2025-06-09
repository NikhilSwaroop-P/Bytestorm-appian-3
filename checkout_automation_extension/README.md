# AI Checkout Automation Browser Extension

A self-contained browser extension that uses AI to automatically fill out checkout forms on e-commerce websites. This extension includes its own Python backend for AI processing.

## Features

- 🤖 **AI-Powered Form Analysis**: Automatically detects and understands checkout form fields
- ⚡ **Smart Auto-Fill**: Intelligently fills forms with your saved information
- 🔒 **Local Processing**: All AI processing happens locally on your machine
- 🛡️ **Privacy-First**: Your personal data never leaves your computer
- 🎯 **Form Detection**: Automatically detects checkout forms on any website
- 💳 **Payment Support**: Handles credit card, billing, and shipping information
- 🔧 **Customizable**: Easily configure your personal information

## Architecture

This extension consists of two main components:

1. **Browser Extension** (JavaScript/Chrome Extension APIs)
   - User interface and form interaction
   - Extension popup and content scripts
   - Communication with local Python backend

2. **Python Backend** (Flask API server)
   - AI form processing using Google's Gemini AI
   - Form field analysis and mapping
   - Secure local API endpoints

## Installation & Setup

### Prerequisites

- **Python 3.8+** installed on your system
- **Google Chrome** or **Chromium-based browser** 
- **Google AI API Key** (for Gemini AI processing)

### Step 1: Set Up the Python Backend

1. **Navigate to the python-backend directory:**
   
   Open a terminal/command prompt and go to the python-backend folder:
   
   ```powershell
   cd path\to\checkout_automation\python-backend
   ```
   
   Example (if you downloaded to your desktop):
   ```powershell
   cd C:\Users\username\Desktop\checkout_automation\python-backend
   ```

2. **Get your Google AI API Key:**
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key for the next step

3. **Set up environment variables:**
   
   **On Windows:**
   ```powershell
   $env:GOOGLE_API_KEY="your_api_key_here"
   ```
   
   **On Linux/macOS:**
   ```bash
   export GOOGLE_API_KEY=your_api_key_here
   ```

4. **Start the Python server:**
   
   **On Windows:**
   ```powershell
   .\start_server.bat
   ```
   
   **On Linux/macOS:**
   ```bash
   ./start_server.sh
   ```

   The server will start on `http://localhost:5000` and install all required dependencies automatically.
   
   You should see output indicating the server is running. Leave this terminal window open.

### Step 2: Install the Browser Extension

1. **Open Chrome/Edge and navigate to the extensions page:**
   
   For Chrome:
   ```
   chrome://extensions/
   ```
   
   For Edge:
   ```
   edge://extensions/
   ```

2. **Enable Developer Mode** (toggle in the top right corner)

3. **Click "Load unpacked"** and select the main extension folder (the folder containing manifest.json)

4. **Pin the extension** to your browser toolbar for easy access:
   - Click the puzzle piece icon in the toolbar
   - Find the AI Checkout Automation extension
   - Click the pin icon next to it

The extension should now be installed and visible in your browser toolbar.

## How to Use the Extension

### Basic Usage

1. **Make sure the Python backend is running** (you should have started it in Step 1)

2. **Go to any e-commerce website checkout page**

3. **Click the extension icon** in your browser toolbar to open the popup

4. **Click "Automate Checkout"** button in the popup

5. **Watch as the extension automatically fills out the form** with your saved information

### Configure Your Information

Before using the extension on real checkout pages, you'll need to configure your personal information:

1. **Click the extension icon** in your browser toolbar

2. **Click the "Settings" tab** in the popup

3. **Enter your information** in the provided fields:
   - Name
   - Email
   - Phone number
   - Billing address
   - Shipping address
   - Payment information

4. **Click "Save"** to store your information locally in your browser

### Troubleshooting

If the extension isn't working properly:

1. **Ensure the Python backend is running** - Check the terminal window where you started start_server.bat

2. **Verify your API key** - Make sure you've set the GOOGLE_API_KEY environment variable correctly

3. **Check browser console** - Right-click on the page, select "Inspect", then go to the "Console" tab to check for errors

4. **Reload the extension** - Go to the extensions page, find the AI Checkout Automation extension, and click the refresh icon

## Security & Privacy

- **Local Processing**: All AI processing happens on your local machine through the Python backend
- **No External Servers**: Your personal information is never sent to external servers
- **Data Storage**: Your information is stored locally in your browser's encrypted storage
- **Limited Activation**: The extension only activates on checkout pages
- **Optional Usage**: You control when to trigger the automation through the popup
- **No Tracking**: The extension does not track your browsing history or behavior

### How It Works Behind the Scenes

1. When you click "Automate Checkout":
   - The extension captures the current page's HTML
   - It sends this HTML to the local Python backend (running on your computer)
   
2. The Python backend:
   - Analyzes the form fields using Google's Gemini AI
   - Matches the fields to your saved information
   - Creates a step-by-step plan for filling the form
   - Sends this plan back to the extension
   
3. The extension:
   - Follows the plan to fill out the form
   - Shows you a visual overlay of what's being filled
   - Allows you to confirm before submitting the form

All communication happens locally between the browser extension and the Python server running on your computer, keeping your data secure.

## Development

### Project Structure

```
browser-extension/
├── manifest.json              # Extension manifest
├── background.js              # Background script
├── content.js                 # Content script (runs on checkout pages)
├── popup/                     # Extension popup
│   ├── popup.html            # Popup HTML
│   └── popup.js              # Popup logic
├── checkout-automation/       # Modular automation logic
│   ├── detector.js           # Page detection & form analysis
│   ├── processor.js          # Form filling logic
│   ├── ui-controller.js      # UI overlay management
│   ├── index.js              # Main entry point
│   ├── loader.js             # Module loading coordination
│   ├── form_filling_actions.json  # Predefined form actions
│   ├── test-page.js          # Test utilities
│   └── test.html             # Test page
├── lib/                       # Legacy code (deprecated)
│   └── checkout-automation.js # Deprecated - use modules instead
├── css/                       # Styles
│   └── overlay.css           # Overlay UI styles
└── icons/                     # Extension icons
```

### Modular Architecture

The extension now uses a modular architecture for better maintainability:

- **detector.js**: Detects checkout pages and analyzes form elements
- **processor.js**: Processes and applies form filling actions
- **ui-controller.js**: Manages the automation overlay UI
- **loader.js**: Coordinates module loading for the content script
- **index.js**: Main entry point for importing the complete library

This modular approach allows for easier testing, debugging, and feature additions.

### Local Development

1. Make changes to the code
2. Reload the extension in your browser
3. Test the changes on checkout pages

## Common Examples

### Example 1: Standard E-commerce Checkout

1. Go to an online store and add items to your cart
2. Proceed to checkout
3. Once on the checkout page, click the extension icon
4. Click "Automate Checkout"
5. The extension will fill in your shipping, billing, and payment information
6. Review the information and click the submit button

### Example 2: Multiple Page Checkout

Some websites have multi-page checkout processes:

1. Start on the first page of checkout
2. Click the extension icon and click "Automate Checkout"
3. After the current page is filled, click next/continue
4. On the next page, click the extension icon again and repeat
5. Continue until checkout is complete

### Example 3: Update Information During Checkout

If you need to use different information for a specific order:

1. Click the extension icon on the checkout page
2. Go to the "Settings" tab
3. Update the specific information you want to change
4. Click "Save"
5. Click "Automate Checkout"

## Frequently Asked Questions

### Q: Does this work on all websites?
**A:** The extension works on most standard e-commerce checkout pages. Some highly customized or JavaScript-heavy forms might have limited compatibility.

### Q: Is my credit card information safe?
**A:** Yes. Your payment information is stored locally in your browser's encrypted storage and is never transmitted to external servers. The AI processing happens entirely on your local machine.

### Q: Can I use multiple profiles?
**A:** Currently, the extension supports one profile at a time. You can manually update your information before using the automation on different websites.

### Q: Why do I need to run a Python backend?
**A:** The Python backend provides powerful AI capabilities that aren't available directly in browser extensions. This architecture gives you the benefits of advanced AI without compromising your privacy.

### Q: How do I stop the Python backend?
**A:** You can close the terminal window where the server is running or press Ctrl+C in that window to stop the server.

## Advanced Usage

### Custom API Keys

If you want to use your own Google API key:

1. Get a key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set it as an environment variable before starting the server:
   ```powershell
   $env:GOOGLE_API_KEY="your_key_here"
   .\start_server.bat
   ```

### Multiple Browser Profiles

If you want to use the extension with different profiles:

1. Create separate browser profiles in Chrome/Edge
2. Install the extension in each profile
3. Configure different information in each profile's extension settings

## Deployment Options

### Local Backend (Default)

By default, the extension uses a local Python backend running on your machine. This keeps all processing local for maximum privacy.

Follow the instructions in the [Installation & Setup](#installation--setup) section to set up the local backend.

### Vercel Deployment (Cloud Option)

For users who prefer a cloud-based solution, the Python backend can be deployed to Vercel:

1. Deploy the backend to Vercel following the instructions in [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)

2. Update the extension configuration to use your Vercel deployment URL:
   - Open the extension popup
   - Go to the "Settings" tab
   - Find the "Backend URL" setting
   - Enter your Vercel deployment URL (e.g., `https://your-project-name.vercel.app`)
   - Click "Save"

**Note:** When using the cloud backend, form HTML is sent to your Vercel deployment. While this still keeps your data within your control (your own Vercel account), it's not as private as the fully local setup.

## License

MIT License
