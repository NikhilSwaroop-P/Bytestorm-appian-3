/**
 * Checkout Automation Loader
 * This script loads the checkout automation functionality from modules
 */

// Load dependencies
import { isCheckoutPage, analyzeFormElements, captureHTML } from './detector.js';
import { applyFormFill, processFormData } from './processor.js';

// Export to window so content script can access these functions
window.CheckoutAutomation = {
  isCheckoutPage,
  analyzeFormElements,
  captureHTML,
  applyFormFill,
  processFormData
};

// Log successful loading
console.log('Checkout automation library loaded successfully');
