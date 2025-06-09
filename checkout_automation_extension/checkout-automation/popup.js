/**
 * Popup script for AI Checkout Automation
 */

// Get the toggle elements
const enableToggle = document.getElementById('enable-toggle');
const autoDetectToggle = document.getElementById('auto-detect-toggle');
const automateCurrentBtn = document.getElementById('automate-current-btn');
const editProfileBtn = document.getElementById('edit-profile-btn');

// Load the current settings
chrome.storage.sync.get(['enabled', 'autoDetect', 'userProfile'], (result) => {
  enableToggle.checked = result.enabled !== false; // Default to true
  autoDetectToggle.checked = result.autoDetect !== false; // Default to true
});

// Save settings when toggles change
enableToggle.addEventListener('change', () => {
  chrome.storage.sync.set({ enabled: enableToggle.checked });
});

autoDetectToggle.addEventListener('change', () => {
  chrome.storage.sync.set({ autoDetect: autoDetectToggle.checked });
});

// Automate current page button
automateCurrentBtn.addEventListener('click', () => {
  // Get the active tab and inject the automation script
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const activeTab = tabs[0];
    
    // Send a message to the content script to start automation
    chrome.tabs.sendMessage(activeTab.id, { action: 'startAutomation' }, (response) => {
      // Close the popup
      window.close();
    });
  });
});

// Edit profile button
editProfileBtn.addEventListener('click', () => {
  // In a real implementation, this would open a profile editor
  alert('Profile editing will be available in a future update.');
});
