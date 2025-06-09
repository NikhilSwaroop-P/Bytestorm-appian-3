/**
 * Debug script for testing extension communication
 * Load this file in the background script console to test message passing
 */

// Test sending a message from background to content script
async function testContentScriptCommunication() {
  console.log('Testing communication with content script...');
  
  try {
    // Get the current active tab
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tabs || tabs.length === 0) {
      console.error('No active tab found');
      return;
    }
    
    const activeTab = tabs[0];
    console.log('Active tab:', activeTab);
    
    // Send a test message to the content script
    chrome.tabs.sendMessage(
      activeTab.id, 
      { action: 'testMessage', data: 'Hello from background' },
      (response) => {
        if (chrome.runtime.lastError) {
          console.error('Error sending message to content script:', chrome.runtime.lastError);
          return;
        }
        
        console.log('Response from content script:', response);
      }
    );
  } catch (error) {
    console.error('Error in testContentScriptCommunication:', error);
  }
}

// Test the server health check endpoint
async function testServerHealth() {
  console.log('Testing server health check...');
  
  try {
    const response = await fetch('http://localhost:5000/health', {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    if (!response.ok) {
      console.error(`Server responded with status: ${response.status}`);
      return;
    }
    
    const result = await response.json();
    console.log('Server health response:', result);
  } catch (error) {
    console.error('Error checking server health:', error);
  }
}

// Add a test message handler to the content script
function addTestMessageHandlerToContentScript() {
  console.log('Adding test message handler to content script...');
  
  chrome.scripting.executeScript({
    target: { tabId: activeTab.id },
    function: () => {
      // This function runs in the content script context
      console.log('Adding test message handler');
      
      chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        console.log('Test message handler received:', message);
        
        if (message.action === 'testMessage') {
          console.log('Received test message:', message.data);
          sendResponse({ success: true, echo: message.data });
        }
        
        return true;
      });
    }
  });
}

// Exports
window.debugExtension = {
  testContentScriptCommunication,
  testServerHealth,
  addTestMessageHandlerToContentScript
};

console.log('Debug utilities loaded. Use window.debugExtension.testContentScriptCommunication() to test.');
