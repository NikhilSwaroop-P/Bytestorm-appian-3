/**
 * Checkout Page Detector
 * Responsible for detecting checkout pages and relevant form elements
 */

// Check if the current page is a checkout page
function isCheckoutPage() {
  const url = window.location.href.toLowerCase();
  const title = document.title.toLowerCase();
  
  // URL patterns that indicate checkout pages
  const urlPatterns = ['checkout', 'payment', 'billing', 'cart', 'order'];
  
  // Form elements that indicate checkout pages
  const hasPaymentForms = document.querySelectorAll('input[type="credit-card"], input[name*="card"], input[id*="card"]').length > 0;
  const hasAddressForms = document.querySelectorAll('input[name*="address"], input[id*="address"], input[name*="zip"], input[id*="zip"]').length > 0;
  
  // Check URL patterns
  const matchesUrlPattern = urlPatterns.some(pattern => url.includes(pattern));
  
  // Check title patterns
  const matchesTitlePattern = urlPatterns.some(pattern => title.includes(pattern));
  
  return matchesUrlPattern || matchesTitlePattern || (hasPaymentForms && hasAddressForms);
}

// Extract and analyze form elements from the page
function analyzeFormElements() {
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
      placeholder: element.placeholder || null,
      is_required: element.required || false,
      has_required_attr: element.hasAttribute('required'),
      aria_required: element.getAttribute('aria-required') === 'true'
    };
    
    formElements.push(elementInfo);
  });
  
  return formElements;
}

// Capture the HTML of the current page
function captureHTML() {
  return document.documentElement.outerHTML;
}

// Export the functions
export { isCheckoutPage, analyzeFormElements, captureHTML };
