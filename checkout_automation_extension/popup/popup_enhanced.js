/**
 * Popup script for AI Checkout Automation
 */

// Get the toggle elements
const enableToggle = document.getElementById('enable-toggle');
const autoDetectToggle = document.getElementById('auto-detect-toggle');
const automateCurrentBtn = document.getElementById('automate-current-btn');
const editProfileBtn = document.getElementById('edit-profile-btn');
const testConnectionBtn = document.getElementById('test-connection-btn');

// Advanced settings elements
const advancedToggle = document.getElementById('advanced-toggle');
const advancedSettingsSection = document.getElementById('advanced-settings-section');
const fastModeToggle = document.getElementById('fast-mode-toggle');
const fastModeSettings = document.getElementById('fast-mode-settings');
const geminiSettings = document.getElementById('gemini-settings');
const modelDepth = document.getElementById('model-depth');
const maxChunks = document.getElementById('max-chunks');
const minChunkSize = document.getElementById('min-chunk-size');
const thinkingBudget = document.getElementById('thinking-budget');

// API Management elements
const retryCount = document.getElementById('retry-count');
const addApiKeyBtn = document.getElementById('add-api-key-btn');
const newApiKeyInput = document.getElementById('new-api-key');
const saveApiKeyBtn = document.getElementById('save-api-key-btn');
const apiKeysList = document.getElementById('api-keys-list');

// Get status elements
const extensionStatus = document.getElementById('extension-status');
const backendStatus = document.getElementById('backend-status');
const contentScriptStatus = document.getElementById('content-script-status');

// Load the current settings and run initial tests
chrome.storage.sync.get([
  'enabled', 
  'autoDetect', 
  'userProfile', 
  'advancedSettingsEnabled',
  'fastMode',
  'modelDepth',
  'thinkingBudget',
  'maxChunks',
  'minChunkSize',
  'geminiApiKeys',
  'retryCount',
  'currentApiKeyIndex'
], (result) => {
  if (enableToggle) enableToggle.checked = result.enabled !== false; // Default to true
  if (autoDetectToggle) autoDetectToggle.checked = result.autoDetect !== false; // Default to true
    // Set advanced settings
  if (advancedToggle) advancedToggle.checked = result.advancedSettingsEnabled === true;
  if (fastModeToggle) fastModeToggle.checked = result.fastMode === true;
  if (modelDepth) modelDepth.value = result.modelDepth !== undefined ? result.modelDepth : 1;
  if (thinkingBudget) thinkingBudget.value = result.thinkingBudget || 1024;
  if (maxChunks) maxChunks.value = result.maxChunks || 4;
  if (minChunkSize) minChunkSize.value = result.minChunkSize || 1000;
  
  // Set API management settings
  if (retryCount) retryCount.value = result.retryCount || 60;
  
  // Initialize API keys with default if none exist
  const apiKeys = result.geminiApiKeys || ['AIzaSyBXZLvzTn2Jf52PZ_PgwDlNRtWUu37aPx4'];
  const currentIndex = result.currentApiKeyIndex || 0;
  renderApiKeysList(apiKeys, currentIndex);
  
  // Toggle visibility of advanced settings
  if (advancedSettingsSection) {
    advancedSettingsSection.style.display = result.advancedSettingsEnabled ? 'block' : 'none';
  }
  
  // Toggle visibility of fast mode settings
  if (fastModeSettings && geminiSettings) {
    fastModeSettings.style.display = result.fastMode ? 'block' : 'none';
    geminiSettings.style.display = result.fastMode ? 'none' : 'block';
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

// Advanced settings event listeners
if (advancedToggle) {
  advancedToggle.addEventListener('change', function() {
    const isEnabled = this.checked;
    if (advancedSettingsSection) {
      advancedSettingsSection.style.display = isEnabled ? 'block' : 'none';
    }
    
    // Save the setting
    chrome.storage.sync.set({ advancedSettingsEnabled: isEnabled });
  });
}

if (fastModeToggle) {
  fastModeToggle.addEventListener('change', function() {
    const isEnabled = this.checked;
    if (fastModeSettings) {
      fastModeSettings.style.display = isEnabled ? 'block' : 'none';
    }
    if (geminiSettings) {
      geminiSettings.style.display = isEnabled ? 'none' : 'block';
    }
    
    // Save the setting
    chrome.storage.sync.set({ fastMode: isEnabled });
  });
}

// Save advanced settings when changed
if (modelDepth) {
  modelDepth.addEventListener('change', function() {
    chrome.storage.sync.set({ modelDepth: this.value });
  });
}

if (thinkingBudget) {
  thinkingBudget.addEventListener('change', function() {
    chrome.storage.sync.set({ thinkingBudget: parseInt(this.value) });
  });
}

if (maxChunks) {
  maxChunks.addEventListener('change', function() {
    chrome.storage.sync.set({ maxChunks: parseInt(this.value) });
  });
}

if (minChunkSize) {
  minChunkSize.addEventListener('change', function() {
    chrome.storage.sync.set({ minChunkSize: parseInt(this.value) });
  });
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
        
        // Get advanced settings from storage
        chrome.storage.sync.get([
          'advancedSettingsEnabled',
          'fastMode',
          'modelDepth',
          'thinkingBudget',
          'maxChunks',
          'minChunkSize'
        ], (settings) => {
          // Only use advanced settings if they're enabled
          const advancedSettings = settings.advancedSettingsEnabled ? {
            fast_mode: settings.fastMode || false,
            model_depth: parseInt(settings.modelDepth || 1),
            thinking_budget: parseInt(settings.thinkingBudget || 1024),
            max_chunks: parseInt(settings.maxChunks || 4),
            min_size_for_chunking: parseInt(settings.minChunkSize || 1000)
          } : null;
          
          // Send a message to the content script to start automation
          chrome.tabs.sendMessage(activeTab.id, { 
            action: 'startAutomation',
            advancedSettings: advancedSettings
          }, (response) => {
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
    // Show edit profile modal
    const modal = document.getElementById('edit-profile-modal');
    if (!modal) return;
    
    // Get current profile data
    chrome.storage.sync.get(['userProfile'], (result) => {
      const profile = result.userProfile || {};
      
      // Fill form with current profile data
      document.getElementById('profile-name').value = profile.name || '';
      document.getElementById('profile-email').value = profile.email || '';
      document.getElementById('profile-phone').value = profile.phone || '';
      document.getElementById('profile-address').value = profile.address || '';
      document.getElementById('profile-city').value = profile.city || '';
      document.getElementById('profile-state').value = profile.state || '';
      document.getElementById('profile-zip').value = profile.zip || '';
      document.getElementById('profile-country').value = profile.country || '';
      document.getElementById('profile-card-number').value = profile.card_number || '';
      document.getElementById('profile-card-expiry').value = profile.card_expiry || '';
      document.getElementById('profile-card-cvv').value = profile.card_cvv || '';
      
      // Show the modal
      modal.style.display = 'flex';
    });
  });
}

// Handle close modal
const closeModal = document.querySelector('.close-modal');
if (closeModal) {
  closeModal.addEventListener('click', () => {
    document.getElementById('edit-profile-modal').style.display = 'none';
  });
}

// Handle cancel profile edit
const cancelProfileBtn = document.getElementById('cancel-profile-btn');
if (cancelProfileBtn) {
  cancelProfileBtn.addEventListener('click', () => {
    document.getElementById('edit-profile-modal').style.display = 'none';
  });
}

// Handle save profile
const saveProfileBtn = document.getElementById('save-profile-btn');
if (saveProfileBtn) {
  saveProfileBtn.addEventListener('click', () => {
    // Get form values
    const name = document.getElementById('profile-name').value.trim();
    const email = document.getElementById('profile-email').value.trim();
    const phone = document.getElementById('profile-phone').value.trim();
    const address = document.getElementById('profile-address').value.trim();
    const city = document.getElementById('profile-city').value.trim();
    const state = document.getElementById('profile-state').value.trim();
    const zip = document.getElementById('profile-zip').value.trim();
    const country = document.getElementById('profile-country').value.trim();
    const cardNumber = document.getElementById('profile-card-number').value.trim().replace(/\s+/g, '');
    const cardExpiry = document.getElementById('profile-card-expiry').value.trim();
    const cardCvv = document.getElementById('profile-card-cvv').value.trim();
    
    // Basic validation
    if (!name) {
      alert('Please enter your name');
      return;
    }
    
    if (!email || !email.includes('@')) {
      alert('Please enter a valid email address');
      return;
    }
    
    if (!address) {
      alert('Please enter your address');
      return;
    }
    
    if (!city) {
      alert('Please enter your city');
      return;
    }
    
    // Card validation
    if (cardNumber) {
      // Check that card number is numeric and 13-19 digits
      if (!/^\d{13,19}$/.test(cardNumber)) {
        alert('Please enter a valid card number (13-19 digits)');
        return;
      }
    }
    
    // Validate card expiry (MM/YY format)
    if (cardExpiry) {
      if (!/^\d{2}\/\d{2}$/.test(cardExpiry)) {
        alert('Please enter card expiry in MM/YY format');
        return;
      }
      
      // Check that expiry date is not in the past
      const [month, year] = cardExpiry.split('/');
      const expiryDate = new Date(2000 + parseInt(year), parseInt(month) - 1);
      const today = new Date();
      if (expiryDate < today) {
        alert('Card expiry date is in the past');
        return;
      }
    }
    
    // Validate CVV (3-4 digits)
    if (cardCvv) {
      if (!/^\d{3,4}$/.test(cardCvv)) {
        alert('Please enter a valid CVV (3-4 digits)');
        return;
      }
    }
    
    // Create user profile object
    const userProfile = {
      name,
      email,
      phone,
      address,
      city,
      state,
      zip,
      country,
      card_number: cardNumber,
      card_expiry: cardExpiry,
      card_cvv: cardCvv
    };
    
    // Save to storage
    chrome.storage.sync.set({ userProfile }, () => {
      // Update displayed profile info
      updateProfileDisplay();
      
      // Close modal
      document.getElementById('edit-profile-modal').style.display = 'none';
      
      // Show success notification
      const notification = document.getElementById('success-notification');
      notification.style.display = 'block';
      
      // Auto-hide notification after animation completes
      setTimeout(() => {
        notification.style.display = 'none';
      }, 5000);
    });
  });
}

// API Management Functions
function renderApiKeysList(apiKeys, currentIndex = 0) {
  if (!apiKeysList) return;
  
  apiKeysList.innerHTML = '';
  
  if (apiKeys.length === 0) {
    apiKeysList.innerHTML = '<div style="color: #6c757d; font-size: 12px; text-align: center; padding: 8px;">No API keys added</div>';
    return;
  }
  
  apiKeys.forEach((key, index) => {
    const keyItem = document.createElement('div');
    keyItem.className = 'api-key-item';
    
    const isActive = index === currentIndex;
    const maskedKey = key.length > 20 ? key.substr(0, 10) + '...' + key.substr(-6) : key;
    
    keyItem.innerHTML = `
      <div class="api-key-text" title="${key}">${maskedKey}</div>
      <div class="api-key-status ${isActive ? 'api-key-active' : 'api-key-inactive'}">${isActive ? 'Active' : 'Standby'}</div>
      <button class="api-key-remove" data-index="${index}">×</button>
    `;
    
    apiKeysList.appendChild(keyItem);
  });
  
  // Add event listeners for remove buttons
  apiKeysList.querySelectorAll('.api-key-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const index = parseInt(e.target.dataset.index);
      removeApiKey(index);
    });
  });
}

function addApiKey(key) {
  if (!key || key.trim().length === 0) {
    alert('Please enter a valid API key');
    return;
  }
  
  chrome.storage.sync.get(['geminiApiKeys', 'currentApiKeyIndex'], (result) => {
    const apiKeys = result.geminiApiKeys || [];
    const currentIndex = result.currentApiKeyIndex || 0;
    
    // Check if key already exists
    if (apiKeys.includes(key.trim())) {
      alert('This API key already exists');
      return;
    }
    
    apiKeys.push(key.trim());
    
    chrome.storage.sync.set({
      geminiApiKeys: apiKeys
    }, () => {
      renderApiKeysList(apiKeys, currentIndex);
      if (newApiKeyInput) newApiKeyInput.value = '';
    });
  });
}

function removeApiKey(index) {
  chrome.storage.sync.get(['geminiApiKeys', 'currentApiKeyIndex'], (result) => {
    const apiKeys = result.geminiApiKeys || [];
    let currentIndex = result.currentApiKeyIndex || 0;
    
    if (index < 0 || index >= apiKeys.length) return;
    if (apiKeys.length === 1) {
      alert('Cannot remove the last API key. Please add another key first.');
      return;
    }
    
    apiKeys.splice(index, 1);
    
    // Adjust current index if necessary
    if (currentIndex >= apiKeys.length) {
      currentIndex = 0;
    } else if (currentIndex > index) {
      currentIndex--;
    }
    
    chrome.storage.sync.set({
      geminiApiKeys: apiKeys,
      currentApiKeyIndex: currentIndex
    }, () => {
      renderApiKeysList(apiKeys, currentIndex);
    });
  });
}

function cycleToNextApiKey() {
  chrome.storage.sync.get(['geminiApiKeys', 'currentApiKeyIndex'], (result) => {
    const apiKeys = result.geminiApiKeys || [];
    const currentIndex = result.currentApiKeyIndex || 0;
    
    if (apiKeys.length <= 1) return; // No point cycling with only one key
    
    const nextIndex = (currentIndex + 1) % apiKeys.length;
    
    chrome.storage.sync.set({
      currentApiKeyIndex: nextIndex
    }, () => {
      renderApiKeysList(apiKeys, nextIndex);
      console.log(`Switched to API key ${nextIndex + 1}/${apiKeys.length}`);
    });
  });
}

// Event listeners for API management
if (addApiKeyBtn) {
  addApiKeyBtn.addEventListener('click', () => {
    if (newApiKeyInput) {
      newApiKeyInput.style.display = 'block';
      newApiKeyInput.focus();
    }
  });
}

if (saveApiKeyBtn) {
  saveApiKeyBtn.addEventListener('click', () => {
    if (newApiKeyInput) {
      addApiKey(newApiKeyInput.value);
    }
  });
}

if (newApiKeyInput) {
  newApiKeyInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      addApiKey(newApiKeyInput.value);
    }
  });
}

if (retryCount) {
  retryCount.addEventListener('change', () => {
    chrome.storage.sync.set({
      retryCount: parseInt(retryCount.value) || 60
    });
  });
}

// Add to existing settings save functions
if (thinkingBudget) {
  thinkingBudget.addEventListener('change', () => {
    chrome.storage.sync.set({
      thinkingBudget: parseInt(thinkingBudget.value) || 1024,
      retryCount: retryCount ? parseInt(retryCount.value) || 60 : 60
    });
  });
}

// Function to update profile display
function updateProfileDisplay() {
  chrome.storage.sync.get(['userProfile', 'cardDetailsVisible'], (result) => {
    const profile = result.userProfile || {};
    const isVisible = result.cardDetailsVisible || false;
    
    // Update profile display in popup
    const profileValueElements = document.querySelectorAll('.profile-value');
    if (profileValueElements.length >= 4) {
      profileValueElements[0].textContent = profile.name || 'Not set';
      profileValueElements[1].textContent = profile.email || 'Not set';
      document.getElementById('profile-phone-display').textContent = profile.phone || 'Not set';
      profileValueElements[3].textContent = profile.address || 'Not set';
      
      // Update city, state/zip, country
      document.getElementById('profile-city-display').textContent = profile.city || 'Not set';
      document.getElementById('profile-state-zip-display').textContent = 
        (profile.state ? profile.state + ' ' : '') + (profile.zip || 'Not set');
      document.getElementById('profile-country-display').textContent = profile.country || 'Not set';
      
      // Update card details with visibility setting
      updateCardDisplay(profile, isVisible);
      
      // Update toggle button text
      const toggleCardVisibilityBtn = document.getElementById('toggle-card-visibility');
      if (toggleCardVisibilityBtn) {
        toggleCardVisibilityBtn.textContent = isVisible ? 'Hide' : 'Show';
      }
    }
  });
}

// Call updateProfileDisplay on page load
updateProfileDisplay();

// Handle toggle card visibility
const toggleCardVisibilityBtn = document.getElementById('toggle-card-visibility');
if (toggleCardVisibilityBtn) {
  toggleCardVisibilityBtn.addEventListener('click', () => {
    chrome.storage.sync.get(['userProfile', 'cardDetailsVisible'], (result) => {
      const profile = result.userProfile || {};
      const isVisible = result.cardDetailsVisible || false;
      
      // Toggle visibility state
      const newVisibility = !isVisible;
      chrome.storage.sync.set({ cardDetailsVisible: newVisibility });
      
      // Update display
      updateCardDisplay(profile, newVisibility);
      
      // Update button text
      toggleCardVisibilityBtn.textContent = newVisibility ? 'Hide' : 'Show';
    });
  });
}

// Function to update card display based on visibility setting
function updateCardDisplay(profile, isVisible) {
  const cardNumber = profile.card_number || '';
  const cardExpiry = profile.card_expiry || 'Not set';
  const cardCvv = profile.card_cvv || 'Not set';
  
  // Get card display elements
  const cardNumberElement = document.querySelector('.section:nth-of-type(2) .profile-info .profile-row:nth-of-type(1) .profile-value');
  const cardExpiryElement = document.getElementById('card-expiry-display');
  const cardCvvElement = document.getElementById('card-cvv-display');
  
  if (isVisible) {
    // Show actual card details
    cardNumberElement.textContent = cardNumber ? formatCardNumber(cardNumber) : 'Not set';
    cardExpiryElement.textContent = cardExpiry;
    cardCvvElement.textContent = cardCvv;
  } else {
    // Show masked card details
    const formattedCardNumber = cardNumber.length > 4 
      ? '•••• •••• •••• ' + cardNumber.slice(-4) 
      : (cardNumber ? '•••• •••• •••• ••••' : 'Not set');
    cardNumberElement.textContent = formattedCardNumber;
    cardExpiryElement.textContent = cardExpiry !== 'Not set' ? 'XX/XX' : 'Not set';
    cardCvvElement.textContent = cardCvv !== 'Not set' ? '•••' : 'Not set';
  }
}

// Helper function to format card number with spaces
function formatCardNumber(cardNumber) {
  let formattedValue = '';
  for (let i = 0; i < cardNumber.length; i++) {
    if (i > 0 && i % 4 === 0) {
      formattedValue += ' ';
    }
    formattedValue += cardNumber[i];
  }
  return formattedValue;
}

// Add input formatting for card number and expiry
const cardNumberInput = document.getElementById('profile-card-number');
if (cardNumberInput) {
  cardNumberInput.addEventListener('input', (e) => {
    // Remove all non-numeric characters
    let value = e.target.value.replace(/\D/g, '');
    
    // Add a space after every 4 digits
    let formattedValue = '';
    for (let i = 0; i < value.length; i++) {
      if (i > 0 && i % 4 === 0) {
        formattedValue += ' ';
      }
      formattedValue += value[i];
    }
    
    // Update the input value
    e.target.value = formattedValue;
  });
}

// Add phone number formatting
const phoneInput = document.getElementById('profile-phone');
if (phoneInput) {
  phoneInput.addEventListener('input', (e) => {
    // Get only numbers from input
    let input = e.target.value.replace(/\D/g, '');
    
    // Format as XXX-XXX-XXXX
    let formattedPhone = input;
    if (input.length <= 3) {
      formattedPhone = input;
    } else if (input.length <= 6) {
      formattedPhone = input.slice(0, 3) + '-' + input.slice(3);
    } else if (input.length <= 10) {
      formattedPhone = input.slice(0, 3) + '-' + input.slice(3, 6) + '-' + input.slice(6);
    } else {
      formattedPhone = input.slice(0, 3) + '-' + input.slice(3, 6) + '-' + input.slice(6, 10);
    }
    
    e.target.value = formattedPhone;
  });
}

const cardExpiryInput = document.getElementById('profile-card-expiry');
if (cardExpiryInput) {
  cardExpiryInput.addEventListener('input', (e) => {
    // Remove all non-numeric characters
    let value = e.target.value.replace(/\D/g, '');
    
    // Format as MM/YY
    if (value.length > 2) {
      e.target.value = value.substring(0, 2) + '/' + value.substring(2, 4);
    } else {
      e.target.value = value;
    }
    
    // Limit to MM/YY format (5 characters)
    if (e.target.value.length > 5) {
      e.target.value = e.target.value.substring(0, 5);
    }
  });
}

// Add input constraint for CVV (limit to 4 digits)
const cardCvvInput = document.getElementById('profile-card-cvv');
if (cardCvvInput) {
  cardCvvInput.addEventListener('input', (e) => {
    // Remove all non-numeric characters
    let value = e.target.value.replace(/\D/g, '');
    
    // Limit to 4 digits
    if (value.length > 4) {
      value = value.substring(0, 4);
    }
    
    e.target.value = value;
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

// Close modal when clicking outside
const modal = document.getElementById('edit-profile-modal');
if (modal) {
  modal.addEventListener('click', (e) => {
    // Close the modal if the user clicks outside the modal content
    if (e.target === modal) {
      modal.style.display = 'none';
    }
  });
}

// Prevent modal from closing when pressing Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && modal && modal.style.display === 'flex') {
    e.preventDefault();
    e.stopPropagation();
  }
});
