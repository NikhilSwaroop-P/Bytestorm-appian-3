/**
 * Checkout Automation API Integration
 * This library handles communication with the backend API
 * 
 * NOTE: This file is deprecated and will be removed in a future version.
 * The functionality has been moved to the checkout-automation folder.
 */

class CheckoutAutomation {
  constructor(apiUrl = 'http://localhost:5000/api/automation/process') {
    this.apiUrl = apiUrl;
    this.apiKey = null;
    console.warn('This version of CheckoutAutomation is deprecated. Please use the modules in the checkout-automation folder.');
  }

  /**
   * Set the API key for authentication
   * @param {string} apiKey - The API key
   */
  setApiKey(apiKey) {
    this.apiKey = apiKey;
  }

  /**
   * Process a checkout page with AI
   * @param {Object} data - The checkout page data
   * @param {string} data.html - The HTML content of the checkout page
   * @param {string} data.url - The URL of the checkout page
   * @param {Array} data.formElements - The form elements extracted from the page
   * @returns {Promise<Object>} - The automation result
   */
  async processCheckout(data) {
    try {
      // This is a deprecated method - direct to new module
      console.warn('This method is deprecated. Please use the modules in the checkout-automation folder.');
      
      // For backward compatibility, we'll load the JSON directly
      return fetch(chrome.runtime.getURL('/checkout-automation/form_filling_actions.json'))
        .then(response => response.json());
        
    } catch (error) {
      console.error('Error processing checkout:', error);
      throw error;
    }
  }

  /**
   * Apply the form filling actions to the page
   * @param {Object} result - The automation result
   * @param {Array} result.actions - The form filling actions
   * @returns {Object} - Statistics about the applied actions
   */
  applyFormFill(result) {
    console.warn('This method is deprecated. Please use the modules in the checkout-automation folder.');
    
    if (!result || !result.actions || !Array.isArray(result.actions)) {
      throw new Error('Invalid automation result');
    }

    const stats = {
      total: result.actions.length,
      applied: 0,
      failed: 0,
      fields: {}
    };

    // Apply each action to the form
    result.actions.forEach(action => {
      try {
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
      } catch (error) {
        console.error(`Error applying action to ${action.element_id}:`, error);
        stats.failed++;
        stats.fields[action.element_id] = 'error';
      }
    });

    return stats;
  }

  /**
   * Analyze the current page to identify form elements
   * @returns {Array} - The form elements found on the page
   */
  analyzeFormElements() {
    console.warn('This method is deprecated. Please use the modules in the checkout-automation folder.');
    
    const formElements = [];
    
    // Find all interactive elements
    const inputs = document.querySelectorAll('input, select, textarea, button');
    
    inputs.forEach(element => {
      const elementInfo = {
        element_type: element.tagName.toLowerCase(),
        id: element.id || null,
        name: element.name || null,
        classes: Array.from(element.classList),
        value: element.value || null,
        type: element.type || null,
        placeholder: element.placeholder || null
      };
      
      formElements.push(elementInfo);
    });
    
    return formElements;
  }
}

// Export the class for backward compatibility
window.CheckoutAutomation = CheckoutAutomation;
