/**
 * Main entry point for the checkout automation library
 * This file exports the main functionality for use in content.js
 */

import { isCheckoutPage, analyzeFormElements, captureHTML } from './detector.js';
import { applyFormFill, processFormData } from './processor.js';
import { initCheckoutAutomation } from './ui-controller.js';

// Export everything in a single object
const CheckoutAutomation = {
  isCheckoutPage,
  analyzeFormElements,
  captureHTML,
  applyFormFill,
  processFormData,
  initCheckoutAutomation
};

export default CheckoutAutomation;
