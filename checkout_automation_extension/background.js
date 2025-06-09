/**
 * Background script for AI Checkout Automation
 * This script runs in the background and manages extension state
 */

// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  // Initialize extension settings
  chrome.storage.sync.set({
    enabled: true,
    backendUrl: 'http://localhost:5000', // Default to local backend
    userProfile: {
      name: "Test User",
      email: "test@example.com",
      address: "123 Test St",
      city: "Test City",
      state: "CA",
      zip: "12345",
      country: "US",
      card_number: "4111111111111111",
      card_expiry: "12/25",
      card_cvv: "123"
    }
  });
  
  console.log('AI Checkout Automation extension installed');
});

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'processCheckout') {
    console.log('Processing checkout:', message.data);
    processCheckoutWithPythonBackend(message.data, sendResponse);
    return true; // Indicates we will respond asynchronously
  }
  
  if (message.action === 'analyzeForm') {
    console.log('Analyzing form:', message.data);
    analyzeFormWithPythonBackend(message.data, sendResponse);
    return true; // Indicates we will respond asynchronously
  }
    if (message.action === 'checkServerHealth') {
    console.log('Checking Python server health');
    checkPythonServerHealth(sendResponse);
    return true; // Indicates we will respond asynchronously
  }
  
  // Debug handler for test messages
  if (message.action === 'testMessage') {
    console.log('Received test message in background script:', message.data);
    // Echo back the message with a timestamp
    sendResponse({
      success: true,
      echo: message.data,
      timestamp: new Date().toISOString(),
      from: 'background.js'
    });
    return true;
  }
  
  // Get current tab information
  if (message.action === 'getCurrentTab') {
    console.log('Getting current tab information');
    getCurrentTabInfo(sendResponse);
    return true; // Indicates we will respond asynchronously
  }
  
  // Handle page state changes after form filling
  if (message.action === 'pageStateChange') {
    console.log('Page state change detected:', message.data);
    // Store the page change event
    chrome.storage.local.get(['pageChanges'], result => {
      const pageChanges = result.pageChanges || [];
      pageChanges.push(message.data);
      chrome.storage.local.set({ pageChanges }, () => {
        console.log('Page change event stored');
        sendResponse({ success: true, message: 'Page change recorded' });
      });
    });
    return true; // Indicates we will respond asynchronously
  }
});

// Process checkout form using local Python backend
async function processCheckoutWithPythonBackend(formData, sendResponse) {
  try {
    // Get user profile and API settings from storage
    const settings = await chrome.storage.sync.get([
      'userProfile', 
      'geminiApiKeys', 
      'retryCount', 
      'currentApiKeyIndex'
    ]);
    const userProfile = settings.userProfile || getDefaultUserProfile();
    const apiKeys = settings.geminiApiKeys || [];
    const retryCount = settings.retryCount || 60;
    const currentApiKeyIndex = settings.currentApiKeyIndex || 0;
    
    const payload = {
      form_data: formData,
      user_profile: userProfile,
      url: formData.url || '',
      page_title: formData.page_title || '',
      api_keys: apiKeys,
      retry_count: retryCount,
      current_api_key_index: currentApiKeyIndex
    };
    
    // Include advanced settings if available
    if (formData.advanced_settings) {
      payload.advanced_settings = formData.advanced_settings;
      console.log('Including advanced settings in backend request:', formData.advanced_settings);
    }
    
    const backendUrl = await getBackendUrl();
    
    console.log('Sending to Python backend:', payload);
    console.log('JSON payload:', JSON.stringify(payload));
    
    // Debug time
    console.log('Request time:', new Date().toISOString());
    
    const response = await fetch(`${backendUrl}/process-checkout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });
    
    console.log('Response status:', response.status);
    console.log('Response headers:', response.headers);
    
    if (!response.ok) {
      throw new Error(`Server responded with status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('Python backend response:', result);
    
    // Validate result before sending
    if (!result || typeof result !== 'object') {
      console.error('Invalid result from Python backend - not an object:', result);
      throw new Error('Invalid result format from server');
    }
    
    if (!result.actions || !Array.isArray(result.actions)) {
      console.error('Invalid result from Python backend - no actions array:', result);
      throw new Error('Invalid actions format from server');
    }
    
    console.log('Sending valid result to content script with', result.actions.length, 'actions');
    
    // Store the result in local storage for debugging
    chrome.storage.local.set({
      lastProcessingResult: {
        timestamp: new Date().toISOString(),
        result: result
      }
    });
    
    sendResponse({ 
      success: true, 
      result: result
    });
    
  } catch (error) {
    console.error('Error communicating with Python backend:', error);
    
    // Fallback to static JSON file if Python server is not available
    try {
      console.log('Attempting to load fallback data');
      const fallbackResponse = await fetch(chrome.runtime.getURL('checkout-automation/form_filling_actions.json'));
      
      if (!fallbackResponse.ok) {
        throw new Error(`Failed to fetch fallback data: ${fallbackResponse.status}`);
      }
      
      const fallbackData = await fallbackResponse.json();
      console.log('Using fallback form filling actions:', fallbackData);
      
      // Validate fallback data
      if (!fallbackData || !fallbackData.actions || !Array.isArray(fallbackData.actions)) {
        throw new Error('Invalid fallback data format');
      }
      
      console.log('Fallback data valid with', fallbackData.actions.length, 'actions');
      
      // Store the fallback result in local storage for debugging
      chrome.storage.local.set({
        lastFallbackResult: {
          timestamp: new Date().toISOString(),
          result: fallbackData
        }
      });
      
      sendResponse({ 
        success: true, 
        result: fallbackData,
        fallback: true,
        error: `Python server unavailable: ${error.message}`
      });
    } catch (fallbackError) {
      console.error('Fallback also failed:', fallbackError);
      sendResponse({ 
        success: false,
        error: `Python server unavailable and fallback failed: ${error.message}, Fallback error: ${fallbackError.message}`
      });
    }
  }
}

// Analyze form using local Python backend
async function analyzeFormWithPythonBackend(formData, sendResponse) {
  try {
    // Get API settings from storage
    const settings = await chrome.storage.sync.get([
      'geminiApiKeys', 
      'retryCount', 
      'currentApiKeyIndex'
    ]);
    const apiKeys = settings.geminiApiKeys || [];
    const retryCount = settings.retryCount || 60;
    const currentApiKeyIndex = settings.currentApiKeyIndex || 0;
    
    // Get the current backend URL
    const backendUrl = await getBackendUrl();
    console.log('Using backend URL for form analysis:', backendUrl);
    
    const response = await fetch(`${backendUrl}/analyze-form`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        form_data: formData,
        url: formData.url || '',
        page_title: formData.page_title || '',
        api_keys: apiKeys,
        retry_count: retryCount,
        current_api_key_index: currentApiKeyIndex
      })
    });
    
    if (!response.ok) {
      throw new Error(`Server responded with status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('Form analysis response:', result);
    
    sendResponse({ 
      success: true, 
      result: result
    });
    
  } catch (error) {
    console.error('Error analyzing form with Python backend:', error);
    sendResponse({ 
      success: false,
      error: error.message
    });
  }
}

// Check if Python server is running
async function checkPythonServerHealth(sendResponse) {
  try {
    console.log('Making server health request at:', new Date().toISOString());
    
    // Get the current backend URL
    const backendUrl = await getBackendUrl();
    console.log('Using backend URL for health check:', backendUrl);
    
    const response = await fetch(`${backendUrl}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Server responded with status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('Python server health:', result);
    
    // Save the health check result to storage for troubleshooting
    chrome.storage.local.set({
      lastHealthCheck: {
        timestamp: new Date().toISOString(),
        result: result,
        success: true
      }
    });
    
    sendResponse({ 
      success: true, 
      result: result
    });
    
  } catch (error) {
    console.error('Python server health check failed:', error);
    
    // Save the error to storage for troubleshooting
    chrome.storage.local.set({
      lastHealthCheck: {
        timestamp: new Date().toISOString(),
        error: error.message,
        success: false
      }
    });
    
    sendResponse({ 
      success: false,
      error: error.message
    });
  }
}

// Get default user profile if none exists
function getDefaultUserProfile() {
  return {
    name: "Test User",
    email: "test@example.com",
    address: "123 Test St",
    city: "Test City",
    state: "CA",
    zip: "12345",
    country: "US",
    card_number: "4111111111111111",
    card_expiry: "12/25",
    card_cvv: "123",
    phone: "900-000-0000"
  };
}

// Load the form filling actions from the predefined file
function loadFormFillingActions() {
  // In a real implementation, this would come from an API call
  // For demonstration, we're using a static JSON file
  return {
    "strategy_summary": "Optimal form filling strategy applied by identifying required fields, validating user data, leveraging 'same as shipping' for billing, optimizing coupon usage for maximum savings, and filling fields in a logical order.",
    "total_actions": 16,
    "actions": [
      {
        "step": 1,
        "element_id": "email",
        "action_type": "input",
        "value": "test@example.com",
        "description": "Enter user email address"
      },
      {
        "step": 2,
        "element_id": "shipping_name",
        "action_type": "input",
        "value": "Test User",
        "description": "Enter shipping recipient name"
      },
      {
        "step": 3,
        "element_id": "shipping_street",
        "action_type": "input",
        "value": "123 Test St",
        "description": "Enter shipping street address"
      },
      {
        "step": 4,
        "element_id": "shipping_city",
        "action_type": "input",
        "value": "Test City",
        "description": "Enter shipping city"
      },
      {
        "step": 5,
        "element_id": "shipping_state",
        "action_type": "input",
        "value": "CA",
        "description": "Enter shipping state"
      },
      {
        "step": 6,
        "element_id": "shipping_zip",
        "action_type": "input",
        "value": "12345",
        "description": "Enter shipping zip code"
      },
      {
        "step": 7,
        "element_id": "shipping_country",
        "action_type": "input",
        "value": "US",
        "description": "Enter shipping country"
      },
      {
        "step": 8,
        "element_id": "same_as_shipping",
        "action_type": "checkbox",
        "value": "check",
        "description": "Check checkbox to use shipping address as billing address"
      },
      {
        "step": 9,
        "element_id": "card_holder",
        "action_type": "input",
        "value": "Test User",
        "description": "Enter cardholder's name"
      },
      {
        "step": 10,
        "element_id": "card_number",
        "action_type": "input",
        "value": "4111111111111111",
        "description": "Enter credit card number"
      },
      {
        "step": 11,
        "element_id": "card_expiry",
        "action_type": "input",
        "value": "12/25",
        "description": "Enter card expiry date"
      },
      {
        "step": 12,
        "element_id": "card_cvv",
        "action_type": "input",
        "value": "123",
        "description": "Enter card CVV"
      },
      {
        "step": 13,
        "element_id": "newsletter",
        "action_type": "checkbox",
        "value": "uncheck",
        "description": "Uncheck newsletter subscription based on user preference"
      },
      {
        "step": 14,
        "element_id": "promo_code",
        "action_type": "input",
        "value": "WELCOME10",
        "description": "Enter optimal promo code for maximum discount"
      },
      {
        "step": 15,
        "element_id": "apply_promo",
        "action_type": "button",
        "value": "click",
        "description": "Click to apply the entered promo code"
      },
      {
        "step": 16,
        "element_id": "checkout_submit_button",
        "action_type": "button",
        "value": "click",
        "description": "Click to submit the order and proceed to payment"
      }
    ]
  };
}

// Get current tab information
function getCurrentTabInfo(sendResponse) {
  try {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs || tabs.length === 0) {
        console.error('No active tab found');
        sendResponse({
          success: false,
          error: 'No active tab found',
          timestamp: new Date().toISOString()
        });
        return;
      }

      const activeTab = tabs[0];
      console.log('Active tab found:', activeTab);

      // Save the current tab info to storage for troubleshooting
      chrome.storage.local.set({
        lastActiveTab: {
          id: activeTab.id,
          url: activeTab.url,
          title: activeTab.title,
          timestamp: new Date().toISOString()
        }
      });

      sendResponse({
        success: true,
        tab: {
          id: activeTab.id,
          url: activeTab.url,
          title: activeTab.title
        },
        timestamp: new Date().toISOString()
      });
    });
  } catch (error) {
    console.error('Error getting active tab:', error);
    sendResponse({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
}

// Get the backend URL from settings, with a fallback to localhost
async function getBackendUrl() {
  try {
    const settings = await chrome.storage.sync.get(['backendUrl']);
    return settings.backendUrl || 'http://localhost:5000';
  } catch (error) {
    console.error('Error getting backend URL:', error);
    return 'http://localhost:5000'; // Default fallback
  }
}
