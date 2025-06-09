/**
 * Checkout Form Processor
 * Handles the application of form filling actions to the page
 */

// Process checkout form with form filling actions
function applyFormFill(automationResult) {
  if (!automationResult || !automationResult.actions || !Array.isArray(automationResult.actions)) {
    throw new Error('Invalid automation result');
  }

  const stats = {
    total: automationResult.actions.length,
    applied: 0,
    failed: 0,
    fields: {}
  };

  try {
    // Apply each action to the form
    automationResult.actions.forEach(action => {
      const elementId = action.element_id;
      const actionType = action.action_type;
      const value = action.value;
      
      // Find the element by ID, name, or other selectors
      let element = document.getElementById(elementId);
      
      if (!element) {
        // Try finding by name attribute
        element = document.querySelector(`[name="${elementId}"]`);
      }
      
      if (!element) {
        // Try finding by class if it's unique enough
        element = document.querySelector(`.${elementId}`);
      }
      
      if (!element) {
        // Try finding by placeholder
        element = document.querySelector(`[placeholder*="${elementId}"]`);
      }

      if (element) {
        if (actionType === 'input' || actionType === 'select') {
          // Handle text inputs and selects
          if (element.tagName === 'SELECT') {
            // For select elements, find the option with matching text or value
            const options = Array.from(element.options);
            const option = options.find(opt => 
              opt.text === value || opt.value === value
            );
            
            if (option) {
              element.value = option.value;
              // Trigger change event
              element.dispatchEvent(new Event('change', { bubbles: true }));
              stats.applied++;
              stats.fields[elementId] = 'success';
            } else {
              stats.failed++;
              stats.fields[elementId] = 'option-not-found';
            }
          } else {
            // For input elements
            element.value = value;
            // Trigger input and change events
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));
            stats.applied++;
            stats.fields[elementId] = 'success';
          }
        } else if (actionType === 'checkbox') {
          // Handle checkboxes
          if (value === 'check') {
            element.checked = true;
          } else if (value === 'uncheck') {
            element.checked = false;
          }
          // Trigger change event
          element.dispatchEvent(new Event('change', { bubbles: true }));
          stats.applied++;
          stats.fields[elementId] = 'success';
        } else if (actionType === 'button' || actionType === 'click') {
          // Simulate click for buttons
          element.click();
          stats.applied++;
          stats.fields[elementId] = 'success';
        }
      } else {
        stats.failed++;
        stats.fields[elementId] = 'element-not-found';
      }
    });
  } catch (error) {
    console.error('Error applying form fill:', error);
    stats.error = error.message;
  }

  return stats;
}

// Process form data (calls the local Python backend)
async function processFormData(data) {
  return new Promise((resolve, reject) => {
    // Send message to background script to process the data
    chrome.runtime.sendMessage(
      { action: 'processCheckout', data: data },
      response => {
        if (response && response.success) {
          if (response.fallback) {
            console.warn('Using fallback processing:', response.error);
          }
          resolve(response.result);
        } else {
          reject(new Error(response?.error || 'Failed to process checkout data'));
        }
      }
    );
  });
}

// Analyze form structure (calls the local Python backend)
async function analyzeFormData(data) {
  return new Promise((resolve, reject) => {
    // Send message to background script to analyze the form
    chrome.runtime.sendMessage(
      { action: 'analyzeForm', data: data },
      response => {
        if (response && response.success) {
          resolve(response.result);
        } else {
          reject(new Error(response?.error || 'Failed to analyze form data'));
        }
      }
    );
  });
}

// Check if Python backend server is running
async function checkServerHealth() {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      { action: 'checkServerHealth' },
      response => {
        if (response && response.success) {
          resolve(response.result);
        } else {
          reject(new Error(response?.error || 'Server health check failed'));
        }
      }
    );
  });
}

// Export the functions
export { applyFormFill, processFormData, analyzeFormData, checkServerHealth };
