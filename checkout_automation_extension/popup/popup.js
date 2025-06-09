/**
 * Popup script for AI Checkout Automation
 */

// Get the toggle elements
const enableToggle = document.getElementById('enable-toggle');
const autoDetectToggle = document.getElementById('auto-detect-toggle');
const automateCurrentBtn = document.getElementById('automate-current-btn');
const editProfileBtn = document.getElementById('edit-profile-btn');
const testConnectionBtn = document.getElementById('test-connection-btn');

// Get status elements
const extensionStatus = document.getElementById('extension-status');
const backendStatus = document.getElementById('backend-status');
const contentScriptStatus = document.getElementById('content-script-status');
const healthStatus = document.getElementById('health-status');

// Backend URL configuration
const backendUrlInput = document.getElementById('backend-url');
const saveBackendUrlBtn = document.getElementById('save-backend-url-btn');
const resetBackendUrlBtn = document.getElementById('reset-backend-url-btn');

// Load the current settings and run initial tests
chrome.storage.sync.get(['enabled', 'autoDetect', 'userProfile', 'backendUrl'], (result) => {
  if (enableToggle) enableToggle.checked = result.enabled !== false; // Default to true
  if (autoDetectToggle) autoDetectToggle.checked = result.autoDetect !== false; // Default to true
  
  // Load backend URL
  if (backendUrlInput && result.backendUrl) {
    backendUrlInput.value = result.backendUrl;
  } else if (backendUrlInput) {
    backendUrlInput.value = 'http://localhost:5000'; // Default value
  }
  
  // Update current tab information
  updateCurrentTabInfo();
  
  // Run all connection tests
  runAllConnectionTests();
});

// Function to update status display
function updateStatusDisplay(element, status, message) {
  if (!element) return;
  
  // Remove existing status classes
  element.classList.remove('status-connected', 'status-error', 'status-warning', 'status-checking');
  
  // Add appropriate status class and text
  switch (status) {
    case 'connected':
      element.classList.add('status-connected');
      element.textContent = '✅ ' + message;
      break;
    case 'error':
      element.classList.add('status-error');
      element.textContent = '❌ ' + message;
      break;
    case 'warning':
      element.classList.add('status-warning');
      element.textContent = '⚠️ ' + message;
      break;
    case 'checking':
      element.classList.add('status-checking');
      element.textContent = '🔄 ' + message;
      break;
    default:
      element.textContent = message;
  }
}

// Function to test extension connection
function testExtensionConnection() {
  return new Promise((resolve) => {
    updateStatusDisplay(extensionStatus, 'checking', 'Testing...');
    
    try {
      chrome.runtime.sendMessage({ action: 'testMessage' }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('Extension connection error:', chrome.runtime.lastError);
          updateStatusDisplay(extensionStatus, 'error', 'Connection failed');
          resolve(false);
          return;
        }
        
        if (response && response.success) {
          updateStatusDisplay(extensionStatus, 'connected', 'Connected');
          resolve(true);
        } else {
          updateStatusDisplay(extensionStatus, 'error', 'No response');
          resolve(false);
        }
      });
    } catch (error) {
      console.error('Extension connection exception:', error);
      updateStatusDisplay(extensionStatus, 'error', 'Exception: ' + error.message);
      resolve(false);
    }
  });
}

// Function to test backend connection
function testBackendConnection() {
  return new Promise((resolve) => {
    updateStatusDisplay(backendStatus, 'checking', 'Testing...');
    
    try {
      chrome.runtime.sendMessage({ action: 'checkServerHealth' }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('Backend connection error:', chrome.runtime.lastError);
          updateStatusDisplay(backendStatus, 'error', 'Extension error');
          resolve(false);
          return;
        }
        
        if (response && response.success) {
          updateStatusDisplay(backendStatus, 'connected', 'Server running');
          resolve(true);
        } else {
          updateStatusDisplay(backendStatus, 'error', 'Server not running');
          resolve(false);
        }
      });
    } catch (error) {
      console.error('Backend connection exception:', error);
      updateStatusDisplay(backendStatus, 'error', 'Exception: ' + error.message);
      resolve(false);
    }
  });
}

// Function to test content script connection
function testContentScriptConnection() {
  return new Promise((resolve) => {
    updateStatusDisplay(contentScriptStatus, 'checking', 'Testing...');
    
    try {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (chrome.runtime.lastError || !tabs || !tabs[0]) {
          updateStatusDisplay(contentScriptStatus, 'error', 'No active tab');
          resolve(false);
          return;
        }
        
        const activeTab = tabs[0];
        
        // Check if it's a valid tab for content script injection
        if (activeTab.url.startsWith('chrome://') || activeTab.url.startsWith('chrome-extension://') || activeTab.url.startsWith('edge://') || activeTab.url.startsWith('about:')) {
          updateStatusDisplay(contentScriptStatus, 'warning', 'System page');
          resolve(false);
          return;
        }
        
        chrome.tabs.sendMessage(activeTab.id, { action: 'testConnection' }, (response) => {
          if (chrome.runtime.lastError) {
            console.error('Content script connection error:', chrome.runtime.lastError);
            updateStatusDisplay(contentScriptStatus, 'error', 'Not loaded');
            resolve(false);
            return;
          }
          
          if (response && response.success) {
            updateStatusDisplay(contentScriptStatus, 'connected', 'Ready');
            resolve(true);
          } else {
            updateStatusDisplay(contentScriptStatus, 'error', 'No response');
            resolve(false);
          }
        });
      });
    } catch (error) {
      console.error('Content script connection exception:', error);
      updateStatusDisplay(contentScriptStatus, 'error', 'Exception: ' + error.message);
      resolve(false);
    }
  });
}

// Function to run all connection tests
async function runAllConnectionTests() {
  console.log('Running connection tests...');
  
  // Test extension connection first
  const extensionOk = await testExtensionConnection();
  
  // Test backend connection
  const backendOk = await testBackendConnection();
  
  // Test content script connection
  const contentScriptOk = await testContentScriptConnection();
  
  console.log('Connection test results:', {
    extension: extensionOk,
    backend: backendOk,
    contentScript: contentScriptOk
  });
  
  return { extensionOk, backendOk, contentScriptOk };
}
// Function to update current tab information
function updateCurrentTabInfo() {
  const tabTitleElement = document.getElementById('current-tab-title');
  const tabUrlElement = document.getElementById('current-tab-url');
  
  if (tabTitleElement && tabUrlElement) {
    tabTitleElement.textContent = 'Loading...';
    tabUrlElement.textContent = 'Getting tab information...';
    
    try {
      // Use the background script to get tab info
      chrome.runtime.sendMessage({ action: 'getCurrentTab' }, (response) => {
        if (chrome.runtime.lastError) {
          console.error('Error getting tab info from background:', chrome.runtime.lastError);
          tabTitleElement.textContent = 'Error: ' + chrome.runtime.lastError.message;
          tabUrlElement.textContent = 'Please check extension permissions';
          return;
        }
        
        if (!response || !response.success) {
          tabTitleElement.textContent = 'Error getting tab info';
          tabUrlElement.textContent = response ? response.error : 'Unknown error';
          return;
        }
        
        console.log('Tab info received:', response);
        
        tabTitleElement.textContent = response.tab.title || 'No title';
        tabUrlElement.textContent = response.tab.url || 'No URL';
      });
    } catch (error) {
      console.error('Error in updateCurrentTabInfo:', error);
      tabTitleElement.textContent = 'Error getting tab info';
      tabUrlElement.textContent = error.message;
    }
  }
}

// Function to check backend health
function checkBackendHealth() {
  healthStatus.textContent = 'Checking backend...';
  healthStatus.style.backgroundColor = '#fff3cd';
  healthStatus.style.color = '#856404';
    try {
    chrome.runtime.sendMessage({ action: 'checkServerHealth' }, (response) => {
      // Check for runtime error (connection issue)
      if (chrome.runtime.lastError) {
        console.error('Error checking server health:', chrome.runtime.lastError);
        healthStatus.textContent = '❌ Extension error';
        healthStatus.style.backgroundColor = '#f8d7da';
        healthStatus.style.color = '#721c24';
        
        // Add instructions for extension error
        const instructions = document.createElement('div');
        instructions.style.cssText = 'font-size: 11px; margin-top: 5px;';
        instructions.textContent = 'Background script not running. Try reloading the extension.';
        healthStatus.appendChild(instructions);
        return;
      }
      
      // Process normal response
      if (response && response.success) {
        healthStatus.textContent = '✅ Python backend running';
        healthStatus.style.backgroundColor = '#d4edda';
        healthStatus.style.color = '#155724';
      } else {
        healthStatus.textContent = '❌ Python backend not running';
        healthStatus.style.backgroundColor = '#f8d7da';
        healthStatus.style.color = '#721c24';
        
        // Add instructions
        const instructions = document.createElement('div');
        instructions.style.cssText = 'font-size: 11px; margin-top: 5px;';
        instructions.textContent = 'Run start_server.bat in python-backend folder';
        healthStatus.appendChild(instructions);
      }
    });
  } catch (error) {
    console.error('Exception while checking server health:', error);
    healthStatus.textContent = '❌ Error checking backend';
    healthStatus.style.backgroundColor = '#f8d7da';
    healthStatus.style.color = '#721c24';
  }
}

// Save settings when toggles change
if (enableToggle) {
  enableToggle.addEventListener('change', () => {
    chrome.storage.sync.set({ enabled: enableToggle.checked });
  });
}

if (autoDetectToggle) {
  autoDetectToggle.addEventListener('change', () => {
    chrome.storage.sync.set({ autoDetect: autoDetectToggle.checked });
  });
}

// Save backend URL
if (saveBackendUrlBtn) {
  saveBackendUrlBtn.addEventListener('click', () => {
    const backendUrl = backendUrlInput.value.trim();
    
    if (!backendUrl) {
      showNotification('Please enter a valid URL', 'error');
      return;
    }
    
    // Simple URL validation
    try {
      new URL(backendUrl);
    } catch (e) {
      showNotification('Please enter a valid URL', 'error');
      return;
    }
    
    chrome.storage.sync.set({ backendUrl }, () => {
      showNotification('Backend URL saved successfully');
      // Retest the connection with the new URL
      runAllConnectionTests();
    });
  });
}

// Reset backend URL to default
if (resetBackendUrlBtn) {
  resetBackendUrlBtn.addEventListener('click', () => {
    const defaultUrl = 'http://localhost:5000';
    backendUrlInput.value = defaultUrl;
    chrome.storage.sync.set({ backendUrl: defaultUrl }, () => {
      showNotification('Backend URL reset to default');
      // Retest the connection
      runAllConnectionTests();
    });
  });
}

// Test connection button
if (testConnectionBtn) {
  testConnectionBtn.addEventListener('click', () => {
    console.log('Test connection button clicked');
    runAllConnectionTests();
  });
}
// Automate current page button
if (automateCurrentBtn) {
  automateCurrentBtn.addEventListener('click', async () => {
    console.log('Automate current page button clicked');
    
    // Run connection tests first
    const testResults = await runAllConnectionTests();
    
    if (!testResults.extensionOk) {
      alert('Extension connection failed. Please reload the extension and try again.');
      return;
    }
    
    if (!testResults.backendOk) {
      alert('Python backend is not running. Please start the server first.\n\nRun start_server.bat in the python-backend folder.');
      return;
    }
    
    if (!testResults.contentScriptOk) {
      alert('Content script is not loaded on this page. Please refresh the page and try again.');
      return;
    }
    
    // All tests passed, proceed with automation
    try {
      // Refresh tab info before automation
      updateCurrentTabInfo();
      
      // Get the active tab and inject the automation script
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (chrome.runtime.lastError || !tabs || !tabs[0]) {
          alert('Unable to get active tab information.');
          return;
        }
        
        const activeTab = tabs[0];
        
        // Send a message to the content script to start automation
        chrome.tabs.sendMessage(activeTab.id, { action: 'startAutomation' }, (response) => {
          if (chrome.runtime.lastError) {
            console.error('Error sending message to tab:', chrome.runtime.lastError);
            alert('Unable to communicate with the page. Please refresh and try again.');
            return;
          }
          
          console.log('Automation started successfully');
          // Close the popup
          window.close();
        });
      });
    } catch (error) {
      console.error('Error automating current page:', error);
      alert('An error occurred while trying to automate the current page. Please reload the extension and try again.');
    }
  });
}

// Edit profile button
if (editProfileBtn) {
  editProfileBtn.addEventListener('click', () => {
    // Display current profile info
    chrome.storage.sync.get(['userProfile'], (result) => {
      const profile = result.userProfile || {};
      const profileInfo = `Current Profile:
Name: ${profile.name || 'Not set'}
Email: ${profile.email || 'Not set'}
Address: ${profile.address || 'Not set'}
City: ${profile.city || 'Not set'}

Note: Profile editing UI will be available in a future update.
For now, you can modify the profile in the background.js file.`;
      
      alert(profileInfo);
    });
  });
}

// Add refresh button for health check
const refreshBtn = document.createElement('button');
refreshBtn.textContent = 'Refresh Status';
refreshBtn.style.cssText = `
  font-size: 11px;
  padding: 4px 8px;
  margin-left: 10px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
`;
refreshBtn.onclick = checkBackendHealth;
healthStatus.appendChild(refreshBtn);

// Notification function
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  document.body.appendChild(notification);
  
  // Auto-remove notification after 3 seconds
  setTimeout(() => {
    notification.remove();
  }, 3000);
}

// CSS for notifications
const style = document.createElement('style');
style.textContent = `
  .notification {
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 1000;
    padding: 10px 20px;
    border-radius: 3px;
    font-size: 14px;
    transition: opacity 0.3s;
  }
  .notification-info {
    background-color: #007bff;
    color: white;
  }
  .notification-success {
    background-color: #28a745;
    color: white;
  }
  .notification-error {
    background-color: #dc3545;
    color: white;
  }
`;
document.head.appendChild(style);
