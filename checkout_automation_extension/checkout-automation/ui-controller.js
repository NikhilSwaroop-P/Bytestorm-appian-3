/**
 * UI Controller for Checkout Automation
 * Handles the creation and management of the automation overlay
 */

import { isCheckoutPage, analyzeFormElements, captureHTML } from './detector.js';
import { applyFormFill, processFormData } from './processor.js';

// Store the automation result
let automationResult = null;

// Create the automation overlay
function createOverlay() {
  const overlay = document.createElement('div');
  overlay.className = 'ai-checkout-overlay';
  overlay.innerHTML = `
    <button id="automation-toggle" class="ai-toggle-btn">
      <span class="ai-icon">🤖</span>
    </button>
    
    <div class="ai-checkout-panel" style="display: none;">
      <div class="ai-checkout-header">
        <h3>AI Checkout Automation</h3>
        <button class="ai-close-btn">&times;</button>
      </div>
      <div class="ai-checkout-content">
        <p>Let AI fill out this checkout form for you!</p>
        <button id="ai-automate-btn" class="ai-primary-btn">Automate Checkout</button>
        <div id="automation-status" style="display: none;">
          <div class="loading-indicator">
            <div class="ai-spinner"></div>
            <span id="status-message">Processing...</span>
          </div>
        </div>
        <button id="apply-form-fill-btn" class="ai-success-btn" style="display: none;">Apply Form Fill</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(overlay);
  
  // Add event listeners for panel toggles
  const toggleBtn = document.getElementById('automation-toggle');
  const closeBtn = document.querySelector('.ai-close-btn');
  const panel = document.querySelector('.ai-checkout-panel');
  
  toggleBtn.addEventListener('click', () => {
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  });
  
  closeBtn.addEventListener('click', () => {
    panel.style.display = 'none';
  });
  
  // Add event listener for automation button
  const automateBtn = document.getElementById('ai-automate-btn');
  automateBtn.addEventListener('click', startAutomation);
  
  // Add event listener for apply button
  const applyBtn = document.getElementById('apply-form-fill-btn');
  applyBtn.addEventListener('click', () => {
    const result = applyFormFill(automationResult);
    updateStatus(`Form fill applied (${result.applied}/${result.total} actions)`, result.applied === result.total ? 'success' : 'warning');
  });
}

// Start the automation process
function startAutomation() {
  const statusDiv = document.getElementById('automation-status');
  const applyBtn = document.getElementById('apply-form-fill-btn');
  
  statusDiv.style.display = 'block';
  applyBtn.style.display = 'none';
  updateStatus('Analyzing page...', 'info');
  
  // Capture the HTML and form elements
  const html = captureHTML();
  const formElements = analyzeFormElements();
  
  // Prepare data for AI processing
  const data = {
    html: html,
    form_elements: formElements,
    url: window.location.href
  };
  
  // Process the data
  processFormData(data)
    .then(result => {
      automationResult = result;
      updateStatus('Checkout form processed successfully!', 'success');
      applyBtn.style.display = 'block';
    })
    .catch(error => {
      updateStatus(`Error: ${error.message}`, 'error');
      console.error('Form processing error:', error);
    });
}

// Update the status message
function updateStatus(message, type = 'info') {
  const statusMessage = document.getElementById('status-message');
  statusMessage.textContent = message;
  
  // Set color based on message type
  switch (type) {
    case 'error':
      statusMessage.style.color = 'red';
      break;
    case 'success':
      statusMessage.style.color = 'green';
      break;
    case 'warning':
      statusMessage.style.color = 'orange';
      break;
    default:
      statusMessage.style.color = 'inherit';
  }
}

// Initialize the checkout automation overlay if on a checkout page
function initCheckoutAutomation() {
  // Check if we're on a checkout page
  if (isCheckoutPage()) {
    // Inject the overlay
    createOverlay();
    
    console.log('Checkout automation initialized');
  }
}

// Initialize when the page is loaded
window.addEventListener('load', initCheckoutAutomation);

// Export the functions
export { initCheckoutAutomation, startAutomation };
