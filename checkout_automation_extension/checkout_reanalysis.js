/**
 * Checkout Reanalysis Module
 * 
 * This module provides functionality for handling form-filling with automatic reanalysis
 * when the page changes after form interactions.
 */

class CheckoutReanalysis {
  /**
   * Initialize the reanalysis handler
   * 
   * @param {Object} options - Configuration options
   * @param {string} options.apiUrl - Base URL of the API server
   * @param {number} options.waitTime - Time to wait in seconds between attempts
   * @param {number} options.maxAttempts - Maximum number of attempts
   * @param {Function} options.onSuccess - Callback when form filling succeeds
   * @param {Function} options.onError - Callback when an error occurs
   * @param {Function} options.onNewAttempt - Callback when a new attempt is started
   */
  constructor(options = {}) {
    this.apiUrl = options.apiUrl || 'http://localhost:5000';
    this.waitTime = options.waitTime || 2; // seconds
    this.maxAttempts = options.maxAttempts || 3;
    this.onSuccess = options.onSuccess || (() => {});
    this.onError = options.onError || (() => {});
    this.onNewAttempt = options.onNewAttempt || (() => {});
    
    // State variables
    this.currentAttempt = 1;
    this.sessionId = null;
    this.previousHtml = null;
    this.reanalysisTimer = null;
    this.lastFormActions = null;
  }
  
  /**
   * Process a checkout form with reanalysis support
   * 
   * @param {Object} formData - Data about the form
   * @param {string} formData.html - HTML content of the form
   * @param {string} formData.url - URL of the page with the form
   * @param {Object} userData - User profile data for form filling
   * @returns {Promise<Object>} - Results from the form processing
   */  async processCheckoutForm(formData, userData) {
    try {
      // Store the initial HTML
      this.previousHtml = formData.html;
      
      // Reset state
      this.currentAttempt = 1;
      this.sessionId = null;
      
      // Clear any existing timers
      if (this.reanalysisTimer) {
        clearTimeout(this.reanalysisTimer);
        this.reanalysisTimer = null;
      }
      
      // Get API settings from storage
      const settings = await chrome.storage.sync.get([
        'geminiApiKeys', 
        'retryCount', 
        'currentApiKeyIndex'
      ]);
      const apiKeys = settings.geminiApiKeys || [];
      const retryCount = settings.retryCount || 60;
      const currentApiKeyIndex = settings.currentApiKeyIndex || 0;
      
      // Create request data
      const requestData = {
        form_data: formData,
        user_profile: userData,
        api_keys: apiKeys,
        retry_count: retryCount,
        current_api_key_index: currentApiKeyIndex,
        reanalysis_settings: {
          wait_time: this.waitTime,
          max_attempts: this.maxAttempts
        }
      };
      
      // Call the API
      console.log('Submitting form data for processing with reanalysis...');
      const response = await fetch(`${this.apiUrl}/process-with-reanalysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }
      
      // Parse response
      const result = await response.json();
      
      // Store session ID for future requests
      if (result.reanalysis_instructions && result.reanalysis_instructions.session_id) {
        this.sessionId = result.reanalysis_instructions.session_id;
      }
      
      // Store the form actions
      this.lastFormActions = result.actions;
      
      // Start the reanalysis process if needed
      if (result.reanalysis_instructions && result.reanalysis_instructions.should_wait) {
        this._scheduleReanalysis(result.reanalysis_instructions.wait_time);
      }
      
      return result;
    } catch (error) {
      console.error('Error processing checkout form:', error);
      this.onError(error);
      throw error;
    }
  }
  
  /**
   * Schedule a reanalysis after the specified wait time
   * 
   * @param {number} waitTime - Time to wait in seconds
   * @private
   */
  _scheduleReanalysis(waitTime) {
    console.log(`Scheduling reanalysis after ${waitTime} seconds...`);
    
    // Clear any existing timer
    if (this.reanalysisTimer) {
      clearTimeout(this.reanalysisTimer);
    }
    
    // Set a new timer
    this.reanalysisTimer = setTimeout(() => {
      this._checkForPageChanges();
    }, waitTime * 1000);
  }
  
  /**
   * Check for page changes and determine if reanalysis is needed
   * 
   * @private
   */
  async _checkForPageChanges() {
    try {
      // Get current HTML
      const currentHtml = document.documentElement.outerHTML;
      
      // Compare with previous HTML
      console.log('Comparing current page with previous state...');
      const comparisonData = {
        previous_html: this.previousHtml,
        current_html: currentHtml,
        session_id: this.sessionId,
        attempt: this.currentAttempt,
        reanalysis_settings: {
          wait_time: this.waitTime,
          max_attempts: this.maxAttempts
        }
      };
      
      // Call the comparison API
      const response = await fetch(`${this.apiUrl}/compare-html`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(comparisonData)
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }
      
      // Parse response
      const result = await response.json();
      
      // Check if reanalysis is needed
      if (result.reanalysis_instructions.should_reanalyze) {
        // Update current attempt
        this.currentAttempt = result.reanalysis_instructions.next_attempt;
        
        // Store new HTML as previous
        this.previousHtml = currentHtml;
        
        // Notify that a new attempt is starting
        console.log(`Significant page changes detected, starting reanalysis (attempt ${this.currentAttempt})...`);
        
        // Trigger reanalysis
        await this._reanalyzeForm();
        
        // Schedule next check if needed
        if (result.reanalysis_instructions.should_wait) {
          this._scheduleReanalysis(result.reanalysis_instructions.wait_time);
        }
      } else {
        // No reanalysis needed
        console.log('No significant page changes detected, form filling complete.');
        this.onSuccess({
          message: 'Form filling completed successfully',
          actions: this.lastFormActions,
          reanalysis: {
            attempts: this.currentAttempt,
            maxAttempts: this.maxAttempts
          }
        });
      }
    } catch (error) {
      console.error('Error checking for page changes:', error);
      this.onError(error);
    }
  }
  
  /**
   * Reanalyze the form with the current page state
   * 
   * @private
   */
  async _reanalyzeForm() {
    try {
      // Get current HTML
      const currentHtml = document.documentElement.outerHTML;
      
      // Create request data for a new analysis
      const formData = {
        html: currentHtml,
        url: window.location.href
      };
      
      // Call the onNewAttempt callback
      this.onNewAttempt({
        attempt: this.currentAttempt,
        maxAttempts: this.maxAttempts
      });
      
      // Process the form again
      const result = await this.processCheckoutForm(formData, {});
      
      return result;
    } catch (error) {
      console.error('Error reanalyzing form:', error);
      this.onError(error);
      throw error;
    }
  }
  
  /**
   * Cancel any pending reanalysis
   */
  cancel() {
    if (this.reanalysisTimer) {
      clearTimeout(this.reanalysisTimer);
      this.reanalysisTimer = null;
    }
    
    console.log('Reanalysis process cancelled');
  }
}

// Export the class for use in the extension
if (typeof module !== 'undefined') {
  module.exports = { CheckoutReanalysis };
} 