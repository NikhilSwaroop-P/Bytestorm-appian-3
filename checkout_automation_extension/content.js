/**
 * Content script for AI Checkout Automation
 * This script is injected into checkout pages and adds the automation overlay
 */

// Global reference to checkout automation module
let CheckoutAutomation = null;

// Keep track of last URL for page change detection
let lastUrl = window.location.href;

// Flag to track if automatic page change detection is active
let autoPageChangeDetection = false;

// Page state for change detection and handling
let lastPageState = {
    url: window.location.href,
    title: document.title,
    html: document.documentElement.outerHTML,
    timestamp: new Date().getTime()
};

// Watch for page changes
setInterval(async () => {
    const currentUrl = window.location.href;
    if (currentUrl !== lastPageState.url) {
        console.log('Page change detected:', currentUrl);
        
        try {
            // Get the current backend URL
            const backendUrl = await getBackendUrl();
            
            // Validate page change with backend
            const response = await fetch(`${backendUrl}/page-change`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    previousUrl: lastPageState.url,
                    currentUrl: currentUrl,
                    isCheckoutPage: CheckoutAutomation && typeof CheckoutAutomation.isCheckoutPage === 'function' ? CheckoutAutomation.isCheckoutPage() : false,
                    timestamp: new Date().toISOString()
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.shouldRestart) {
                console.log('Backend validated page change, restarting automation...');
                restartAutomation();
            }
        } catch (error) {
            console.error('Error validating page change:', error);
        }
        
        // Update last page state
        lastPageState = {
            url: currentUrl,
            timestamp: new Date().getTime()
        };
    }
}, 1000);

// Initialize the checkout automation when the page loads
window.addEventListener('load', initializeExtension);

// Create MutationObserver to monitor for page changes
const observer = new MutationObserver((mutations) => {
  if (window.location.href !== lastUrl) {
    console.log('Page changed from', lastUrl, 'to', window.location.href);
    lastUrl = window.location.href;
  } else {
    console.log('Page did not change');
  }
});

// Start observing once the document loads
window.addEventListener('load', () => {
  observer.observe(document, {
    subtree: true,
    childList: true
  });
});

// Add listener for messages from the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content script received message:', message);
  console.log('Message sender:', sender);
  console.log('Current URL:', window.location.href);
  console.log('Document readyState:', document.readyState);
  
  // Debug: Show message in page (only during testing)
  if (window.location.href.includes('test-extension.html')) {
    const debugDiv = document.createElement('div');
    debugDiv.style.cssText = 'position: fixed; top: 10px; right: 10px; background: #fff3cd; padding: 10px; border-radius: 4px; z-index: 10000; font-size: 12px;';
    debugDiv.innerHTML = `<strong>Message received:</strong> ${JSON.stringify(message)}`;
    document.body.appendChild(debugDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
      debugDiv.remove();
    }, 5000);
  }
    if (message.action === 'startAutomation') {
    console.log('Starting automation from popup message');
    try {
      // Store advanced settings globally if provided
      if (message.advancedSettings) {
        console.log('Advanced settings received:', message.advancedSettings);
        window.automationAdvancedSettings = message.advancedSettings;
      }
      
      startAutomation();
      sendResponse({ success: true });
    } catch (error) {
      console.error('Error in startAutomation:', error);
      sendResponse({ success: false, error: error.message });
    }
  }
    // Debug test message handler
  if (message.action === 'testMessage') {
    console.log('Received test message:', message.data);
    sendResponse({ success: true, echo: message.data });
  }
  
  // Connection test handler
  if (message.action === 'testConnection') {
    console.log('Content script connection test');
    sendResponse({ success: true, status: 'Content script loaded and ready' });
  }
  
  // Return true to indicate we'll send a response asynchronously
  return true;
});

// Initialize the extension
async function initializeExtension() {
  try {
    // Load the checkout automation module first
    await loadCheckoutAutomation();
    
    console.log('Extension loaded, checking if this is a checkout page...');
    
    // Debug: Check what CheckoutAutomation contains
    console.log('CheckoutAutomation module:', CheckoutAutomation);
    
    // Only add the overlay if this is a checkout page
    if (CheckoutAutomation && CheckoutAutomation.isCheckoutPage()) {
      console.log('✅ Checkout page detected, initializing automation UI');
      createOverlay();
      
      // Start monitoring for page changes
      startPageChangeDetection();
    } else {
      console.log('❌ Not a checkout page, extension inactive');
      console.log('Page URL:', window.location.href);
      console.log('Page title:', document.title);
      
      // Force overlay for test-extension.html
      if (window.location.href.includes('test-extension.html')) {
        console.log('⚠️ Test page detected, forcing automation UI');
        createOverlay();
        
        // Start monitoring for page changes in test mode
        startPageChangeDetection();
      }
    }
  } catch (error) {
    console.error('Failed to initialize extension:', error);
  }
}

// Load the checkout automation module
function loadCheckoutAutomation() {
  return new Promise((resolve, reject) => {
    // Import the checkout automation module
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('checkout-automation/loader.js');
    script.type = 'module';
    script.onload = function() {
      // Wait for the module to be available on window
      const checkModule = () => {
        if (window.CheckoutAutomation) {
          CheckoutAutomation = window.CheckoutAutomation;
          console.log('Checkout automation module loaded');
          resolve();
        } else {
          setTimeout(checkModule, 50);
        }
      };
      checkModule();
    };
    script.onerror = function() {
      console.error('Failed to load checkout automation module');
      reject(new Error('Module loading failed'));
    };
    (document.head || document.documentElement).appendChild(script);
  });
}

// Create the automation overlay
function createOverlay() {
  // Remove any existing overlay
  const existingOverlay = document.querySelector('.ai-checkout-overlay');
  if (existingOverlay) {
    existingOverlay.remove();
  }

  const overlay = document.createElement('div');
  overlay.className = 'ai-checkout-overlay';
  
  const button = document.createElement('button');
  button.className = 'ai-checkout-button';
  button.innerHTML = '<i class="ai-icon"></i> AI Checkout';
  button.addEventListener('click', toggleAutomationPanel);
  
  const panel = document.createElement('div');
  panel.className = 'ai-checkout-panel';
  panel.style.display = 'none';
  panel.innerHTML = `
    <div class="ai-checkout-header">
      <h3>AI Checkout Automation</h3>
      <button class="ai-close-btn">&times;</button>
    </div>
    <div class="ai-checkout-content">
      <p>Let AI fill out this checkout form for you!</p>
      <div id="automation-status">
        <div class="loading-indicator">
          <div class="ai-spinner"></div>
          <span id="status-message">Analyzing page...</span>
        </div>
      </div>
      <button id="apply-form-fill-btn" class="ai-success-btn" style="display: none;">Apply Form Fill</button>
    </div>
  `;
  
  overlay.appendChild(button);
  overlay.appendChild(panel);
  document.body.appendChild(overlay);
  
  // Add event listeners with direct element references and stopPropagation
  const closeBtn = panel.querySelector('.ai-close-btn');
  closeBtn.addEventListener('click', (event) => {
    event.stopPropagation();
    panel.style.display = 'none';
    console.log('Close button clicked');
  });
  
  const applyFillBtn = document.getElementById('apply-form-fill-btn');
  if (applyFillBtn) {
    applyFillBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      console.log('Apply Form Fill button clicked');
      applyFormFill();
    });
  }
  
  // Ensure the button is always visible
  button.style.display = 'flex';
}

// Toggle the automation panel
function toggleAutomationPanel() {
  const panel = document.querySelector('.ai-checkout-panel');
  if (panel.style.display === 'none') {
    panel.style.display = 'block';
    
    // Make sure panel has proper pointer events
    panel.style.pointerEvents = 'auto';
    
    // Ensure all buttons in the panel are clickable
    const buttons = panel.querySelectorAll('button');
    buttons.forEach(btn => {
      btn.style.pointerEvents = 'auto';
      btn.style.cursor = 'pointer';
    });
    
    // Start automation immediately when panel is opened
    startAutomation();
  } else {
    panel.style.display = 'none';
  }
}

// Store the automation result
let automationResult = null;
let isAnimationRunning = false;

// Detect navigation buttons (Next, Continue, Complete Order, etc.)
function detectNavigationButtons() {
  // Patterns for navigation buttons (both text content and button attributes)
  const nextPatterns = [
    'next', 'continue', 'proceed', 'siguiente', 'weiter', 'suivant', 'avançar',
    'next step', 'continue to', 'proceed to', 'go to'
  ];
  
  const completePatterns = [
    'complete', 'finish', 'submit', 'place order', 'confirm', 'pay', 'purchase',
    'buy now', 'complete order', 'place your order', 'confirm order',
    'complete purchase', 'finalizar', 'bestellen', 'commander', 'completar'
  ];
  
  // Look for buttons, inputs, and anchors that could be navigation elements
  const potentialButtons = [
    ...document.querySelectorAll('button'),
    ...document.querySelectorAll('input[type="button"]'),
    ...document.querySelectorAll('input[type="submit"]'),
    ...document.querySelectorAll('a.button'),
    ...document.querySelectorAll('a.btn'),
    ...document.querySelectorAll('[role="button"]'),
    ...document.querySelectorAll('.button'),
    ...document.querySelectorAll('.btn')
  ];
  
  // Find the first matching navigation button of each type
  const nextButton = potentialButtons.find(button => {
    const text = (button.textContent || button.value || button.innerText || '').toLowerCase();
    const ariaLabel = (button.getAttribute('aria-label') || '').toLowerCase();
    const name = (button.getAttribute('name') || '').toLowerCase();
    const id = (button.id || '').toLowerCase();
    
    return nextPatterns.some(pattern => 
      text.includes(pattern) || 
      ariaLabel.includes(pattern) || 
      name.includes(pattern) || 
      id.includes(pattern)
    ) && !completePatterns.some(pattern => 
      text.includes(pattern) || 
      ariaLabel.includes(pattern) || 
      name.includes(pattern) || 
      id.includes(pattern)
    );
  });
  
  const completeButton = potentialButtons.find(button => {
    const text = (button.textContent || button.value || button.innerText || '').toLowerCase();
    const ariaLabel = (button.getAttribute('aria-label') || '').toLowerCase();
    const name = (button.getAttribute('name') || '').toLowerCase();
    const id = (button.id || '').toLowerCase();
    
    return completePatterns.some(pattern => 
      text.includes(pattern) || 
      ariaLabel.includes(pattern) || 
      name.includes(pattern) || 
      id.includes(pattern)
    );
  });
  
  return { nextButton, completeButton };
}

// Create a visual cursor element
function createVisualCursor() {
  // Remove any existing cursor
  const existingCursor = document.getElementById('ai-visual-cursor-container');
  if (existingCursor) {
    existingCursor.remove();
  }
  
  // Create new cursor element with container for animations
  const cursorContainer = document.createElement('div');
  cursorContainer.id = 'ai-visual-cursor-container';
  cursorContainer.style.cssText = `
    position: fixed;
    width: 40px;
    height: 40px;
    pointer-events: none;
    z-index: 99999;
    transition: transform 0.3s cubic-bezier(0.215, 0.610, 0.355, 1.000);
    transform: translate(-50%, -50%);
  `;
  
  // Create the actual cursor pointer with directional arrow
  const cursor = document.createElement('div');
  cursor.id = 'ai-visual-cursor';
  cursor.innerHTML = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
      <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="0" stdDeviation="2" flood-color="#000" flood-opacity="0.3"/>
      </filter>
      <path fill="#4a6fa5" d="M12,3l12,12l-6,1l3,10l-3,2l-3.5-10L8,22V3" filter="url(#shadow)"/>
      <circle cx="16" cy="16" r="5" fill="#4a6fa5" fill-opacity="0.2" />
    </svg>
    <div class="ai-cursor-pulse"></div>
  `;
  
  cursorContainer.appendChild(cursor);
  document.body.appendChild(cursorContainer);
  
  // Initially hide cursor until it's moved to a target
  cursorContainer.style.display = 'none';
  
  return cursorContainer;
}

// Move cursor to element with animation
function moveCursorToElement(element, callback) {
  if (!element) {
    console.warn('Cannot move cursor to undefined element');
    if (callback) callback();
    return;
  }
  
  // Create cursor if it doesn't exist
  let cursorContainer = document.getElementById('ai-visual-cursor-container');
  if (!cursorContainer) {
    cursorContainer = createVisualCursor();
  }
  
  // Get element position
  const rect = element.getBoundingClientRect();
  const targetX = rect.left + rect.width / 2;
  const targetY = rect.top + rect.height / 2;
  
  // Ensure element is in view
  if (rect.bottom < 0 || rect.top > window.innerHeight) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    });
    
    // Wait for scrolling to complete
    setTimeout(() => {
      moveCursorToElement(element, callback);
    }, 500);
    return;
  }
  
  // Add directional animation - show where cursor is moving
  const currentTransform = cursorContainer.style.transform;
  let currentX = window.innerWidth / 2;
  let currentY = window.innerHeight / 2;
  
  if (currentTransform && currentTransform.includes('translate')) {
    try {
      const matches = currentTransform.match(/translate\(([\d.-]+)px,\s*([\d.-]+)px\)/);
      if (matches && matches.length >= 3) {
        currentX = parseFloat(matches[1]);
        currentY = parseFloat(matches[2]);
      }
    } catch (e) {
      console.log('Error parsing transform:', e);
    }
  }
  
  // Add trailing effect to show direction
  if (cursorContainer.style.display !== 'none') {
    const trail = document.createElement('div');
    trail.className = 'ai-cursor-trail';
    trail.style.cssText = `
      position: fixed;
      left: ${currentX}px;
      top: ${currentY}px;
      width: 8px;
      height: 8px;
      background-color: rgba(74, 111, 165, 0.5);
      border-radius: 50%;
      z-index: 99998;
      pointer-events: none;
      animation: fade-out 0.8s forwards;
    `;
    document.body.appendChild(trail);
    
    // Remove trail after animation
    setTimeout(() => {
      trail.remove();
    }, 800);
  }
  
  // Set cursor position with animation
  cursorContainer.style.display = 'block';
  cursorContainer.style.transform = `translate(${targetX}px, ${targetY}px)`;
  
  // Add click animation effect
  setTimeout(() => {
    const clickEffect = document.createElement('div');
    clickEffect.className = 'ai-cursor-click';
    cursorContainer.appendChild(clickEffect);
    
    // Remove click effect after animation
    setTimeout(() => {
      clickEffect.remove();
      if (callback) callback();
    }, 300);
  }, 300);
}

// Simulate typing animation
function simulateTyping(element, text, callback) {
  if (!element) {
    console.warn('Cannot type in undefined element');
    if (callback) callback();
    return;
  }
  
  let i = 0;
  element.focus();
  element.value = '';
  
  // Add typing indicator
  const typingIndicator = document.createElement('div');
  typingIndicator.style.cssText = `
    position: absolute;
    background: rgba(74, 111, 165, 0.1);
    border: 1px solid #4a6fa5;
    border-radius: 4px;
    padding: 5px;
    font-size: 12px;
    color: #4a6fa5;
    z-index: 99998;
  `;
  typingIndicator.textContent = 'AI typing...';
  
  // Position the indicator near the element
  const rect = element.getBoundingClientRect();
  typingIndicator.style.left = `${rect.left}px`;
  typingIndicator.style.top = `${rect.bottom + 5}px`;
  
  document.body.appendChild(typingIndicator);
  
  // Type characters with delay
  function typeNextChar() {
    if (i < text.length) {
      element.value += text.charAt(i);
      element.dispatchEvent(new Event('input', { bubbles: true }));
      i++;
      setTimeout(typeNextChar, 30 + Math.random() * 50);
    } else {
      element.dispatchEvent(new Event('change', { bubbles: true }));
      typingIndicator.remove();
      if (callback) {
        setTimeout(callback, 200);
      }
    }
  }
  
  typeNextChar();
}

// Select option from dropdown with visual feedback
function selectOptionWithAnimation(element, value, callback) {
  if (!element || element.tagName !== 'SELECT') {
    console.warn('Element is not a select dropdown');
    if (callback) callback();
    return;
  }
  
  // Find the matching option
  const options = Array.from(element.options);
  const option = options.find(opt => 
    opt.text === value || opt.value === value
  );
  
  if (!option) {
    console.warn(`Option with value "${value}" not found`);
    if (callback) callback();
    return;
  }
  
  // Focus and click to open dropdown
  element.focus();
  element.click();
  
  // Highlight the selecting process
  const selectingIndicator = document.createElement('div');
  selectingIndicator.style.cssText = `
    position: absolute;
    background: rgba(74, 111, 165, 0.1);
    border: 1px solid #4a6fa5;
    border-radius: 4px;
    padding: 5px;
    font-size: 12px;
    color: #4a6fa5;
    z-index: 99998;
  `;
  selectingIndicator.textContent = `Selecting: ${value}`;
  
  // Position the indicator near the element
  const rect = element.getBoundingClientRect();
  selectingIndicator.style.left = `${rect.left}px`;
  selectingIndicator.style.top = `${rect.bottom + 5}px`;
  
  document.body.appendChild(selectingIndicator);
  
  // Select the option after a short delay
  setTimeout(() => {
    element.value = option.value;
    element.dispatchEvent(new Event('change', { bubbles: true }));
    selectingIndicator.remove();
    
    if (callback) {
      setTimeout(callback, 200);
    }
  }, 500);
}

// Simulate checkbox checking with animation
function simulateCheckboxClick(element, shouldCheck, callback) {
  if (!element || (element.type !== 'checkbox' && element.type !== 'radio')) {
    console.warn('Element is not a checkbox or radio');
    if (callback) callback();
    return;
  }
  
  // Visual click effect
  const clickEffect = document.createElement('div');
  clickEffect.style.cssText = `
    position: absolute;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: rgba(74, 111, 165, 0.3);
    transform: translate(-50%, -50%);
    pointer-events: none;
    z-index: 99997;
    animation: click-ripple 0.5s ease-out forwards;
  `;
  
  // Add animation keyframes
  const style = document.createElement('style');
  style.textContent = `
    @keyframes click-ripple {
      0% { transform: translate(-50%, -50%) scale(0.5); opacity: 1; }
      100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
    }
  `;
  document.head.appendChild(style);
  
  // Position click effect
  const rect = element.getBoundingClientRect();
  clickEffect.style.left = `${rect.left + rect.width/2}px`;
  clickEffect.style.top = `${rect.top + rect.height/2}px`;
  
  document.body.appendChild(clickEffect);
  
  // Set checkbox state after animation
  setTimeout(() => {
    element.checked = shouldCheck;
    element.dispatchEvent(new Event('change', { bubbles: true }));
    
    // Remove click effect
    setTimeout(() => {
      clickEffect.remove();
      if (callback) callback();
    }, 300);
  }, 200);
}

// Add diagnostic debugging function
function debugAutomationResult() {
  console.log("Debugging automation result");
  console.log("automationResult value:", automationResult);
  
  if (!automationResult) {
    console.error("automationResult is null or undefined");
    return "automationResult is null or undefined";
  }
  
  if (!automationResult.actions) {
    console.error("automationResult exists but has no actions property");
    console.log("automationResult keys:", Object.keys(automationResult));
    return "automationResult exists but has no actions property";
  }
  
  console.log("automationResult actions count:", automationResult.actions.length);
  return "automationResult looks valid with " + automationResult.actions.length + " actions";
}

// Start monitoring for page changes
function startPageChangeDetection() {
  if (autoPageChangeDetection) {
    console.log('Page change detection already active');
    return;
  }
  
  console.log('Starting page change detection');
  autoPageChangeDetection = true;
  
  // Store the current URL to detect changes
  let lastUrl = window.location.href;
  let lastTitle = document.title;
  let lastHtml = document.documentElement.outerHTML;
  
  // Create a MutationObserver to monitor DOM changes
  const observer = new MutationObserver((mutations) => {
    // Check if we're already in an automation process
    if (isAnimationRunning) {
      return;
    }
    
    // Only check for page changes if not in the middle of form filling
    if (!isAnimationRunning) {
      const currentState = {
        url: window.location.href,
        title: document.title,
        html: document.documentElement.outerHTML
      };

      if (currentState.url !== lastPageState.url) {
        console.log('====== PAGE CHANGED (NAVIGATION) ======');
        console.log('Previous URL:', lastPageState.url);
        console.log('Current URL:', currentState.url);
        console.log('====================================');
        
        // Update stored values
      lastUrl = window.location.href;
      lastTitle = document.title;
      lastHtml = document.documentElement.outerHTML;
      
      // Wait for page to stabilize
      setTimeout(() => {
        // MODIFIED: Always trigger automation on page change, treating any page as potential checkout
        console.log('Page changed - treating as checkout page and triggering automatic analysis');
        
        // Create overlay if it doesn't exist
        const existingOverlay = document.querySelector('.ai-checkout-overlay');
        if (!existingOverlay) {
          createOverlay();
        }
        
        // Start automation process
        startAutomation();
        
        // Show notification to user
        const notification = document.createElement('div');
        notification.className = 'ai-page-change-notification';
        notification.textContent = 'Page changed! Starting automatic checkout...';
        notification.style.cssText = `
          position: fixed;
          top: 20px;
          right: 20px;
          background: rgba(0, 128, 0, 0.8);
          color: white;
          padding: 10px 15px;
          border-radius: 5px;
          z-index: 10000;
          box-shadow: 0 0 10px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(notification);
        
        // Remove notification after 5 seconds
        setTimeout(() => notification.remove(), 5000);
      }, 1000);
    } 
    // Check for significant DOM changes that might indicate page content changed without URL change
    else {
      // Only run this check occasionally to avoid performance issues
      if (Math.random() < 0.1) { // 10% chance on each mutation batch
        const currentHtml = document.documentElement.outerHTML;
        
        // Simple check for significant changes - compare HTML length
        const lengthDiff = Math.abs(currentHtml.length - lastHtml.length);
        const significantChange = lengthDiff > 5000; // Consider 5KB change as significant
        
        if (significantChange) {
          console.log('Significant page content change detected!');
          console.log('HTML length change:', lengthDiff);
          
          // Update stored HTML
          lastHtml = currentHtml;
          
          // If we're on a checkout page, trigger automation
          if (CheckoutAutomation && CheckoutAutomation.isCheckoutPage()) {
            console.log('Page content changed significantly, triggering automatic analysis');
            
            // Create overlay if it doesn't exist
            const existingOverlay = document.querySelector('.ai-checkout-overlay');
            if (!existingOverlay) {
              createOverlay();
            }
            
            // Start automation process
            startAutomation();
            
            // Show notification to user
            const notification = document.createElement('div');
            notification.className = 'ai-page-change-notification';
            notification.textContent = 'Page updated! Starting automatic checkout...';
            notification.style.cssText = `
              position: fixed;
              top: 20px;
              right: 20px;
              background: rgba(0, 128, 0, 0.8);
              color: white;
              padding: 10px 15px;
              border-radius: 5px;
              z-index: 10000;
              box-shadow: 0 0 10px rgba(0,0,0,0.2);
            `;
            document.body.appendChild(notification);
            
            // Remove notification after 5 seconds
            setTimeout(() => notification.remove(), 5000);
          }
        }
      }
      }
    }
  });
  
  // Start observing document for changes
  observer.observe(document.documentElement, { 
    childList: true, 
    subtree: true,
    attributes: true,
    characterData: true
  });
  
  // Also listen for history API changes (SPA navigation)
  const originalPushState = history.pushState;
  const originalReplaceState = history.replaceState;
  
  history.pushState = function() {
    originalPushState.apply(this, arguments);
    console.log('pushState called, page might be changing');
    
    // Dispatch a custom event
    dispatchEvent(new Event('locationchange'));
  };
  
  history.replaceState = function() {
    originalReplaceState.apply(this, arguments);
    console.log('replaceState called, page might be changing');
    
    // Dispatch a custom event
    dispatchEvent(new Event('locationchange'));
  };
  
  // Listen for location changes
  window.addEventListener('locationchange', function() {
    console.log('Location changed event detected');
    
    // Wait for the page to update
    setTimeout(() => {
      // MODIFIED: Always trigger automation on location change, treating any page as potential checkout
      console.log('Location changed - treating as checkout page and triggering automation');
      
      // Create overlay if it doesn't exist
      const existingOverlay = document.querySelector('.ai-checkout-overlay');
      if (!existingOverlay) {
        createOverlay();
      }
      
      // Start automation process
      startAutomation();
    }, 1000);
  });
  
  // Listen for standard navigation events
  window.addEventListener('popstate', function() {
    console.log('popstate event detected');
    
    // Wait for page to update
    setTimeout(() => {
      // MODIFIED: Always trigger automation on popstate, treating any page as potential checkout
      console.log('Popstate detected - treating as checkout page and triggering automation');
      
      // Create overlay if it doesn't exist
      const existingOverlay = document.querySelector('.ai-checkout-overlay');
      if (!existingOverlay) {
        createOverlay();
      }
      
      // Start automation
      startAutomation();
    }, 1000);
  });
}

// Function to check page changes after form fill
function checkPageChanges() {
  const currentState = {
    url: window.location.href,
    title: document.title,
    html: document.documentElement.outerHTML
  };

  if (currentState.url !== lastPageState.url) {
    console.log('====== PAGE CHANGED ======');
    console.log('Previous URL:', lastPageState.url);
    console.log('Current URL:', currentState.url);
    console.log('========================');

    // Send URL change data to background script
    chrome.runtime.sendMessage({
      action: 'pageStateChange',
      data: {
        previousUrl: lastPageState.url,
        currentUrl: currentState.url,
        changed: true,
        timestamp: new Date().toISOString()
      }
    }, response => {
      if (chrome.runtime.lastError) {
        console.error('Error sending page change:', chrome.runtime.lastError);
      } else {
        console.log('Page change sent to background script:', response);
      }
    });
  } else {
    console.log('====== PAGE DID NOT CHANGE ======');
    console.log('URL remained:', currentState.url);
    console.log('===============================');
  }

  // Update the stored state
  lastPageState = currentState;
}

// Apply form filling with the automation result
function applyFormFill() {
  const statusMessage = document.getElementById('status-message');
  
  // Add debugging
  console.log("Apply Form Fill called");
  const debugResult = debugAutomationResult();
  console.log("Debug result:", debugResult);
  
  if (!automationResult || !automationResult.actions) {
    statusMessage.textContent = 'No automation result available';
    statusMessage.style.color = 'red';
    hideLoadingSpinner();
    
    // Try to use fallback data if main result failed
    console.log("Attempting to use fallback data");
    tryLoadFallbackData().then(success => {
      if (success) {
        console.log("Fallback data loaded successfully");
        statusMessage.textContent = 'Using fallback data. Retry the form fill.';
        statusMessage.style.color = 'orange';
        
        // Show Apply Form Fill button again with proper styling
        const applyBtn = document.getElementById('apply-form-fill-btn');
        if (applyBtn) {
          applyBtn.style.display = 'block';
          applyBtn.style.pointerEvents = 'auto';
          applyBtn.style.cursor = 'pointer';
          applyBtn.style.position = 'relative';
          applyBtn.style.zIndex = '10001';
          
          // Ensure event listener is properly set for manual clicks
          applyBtn.onclick = (event) => {
            event.stopPropagation();
            console.log('Apply Form Fill button clicked (via onclick)');
            applyFormFill();
          };
        }
      } else {
        console.error("Failed to load fallback data");
      }
    });
    
    return;
  }
  
  if (isAnimationRunning) {
    console.log('Animation already running');
    return;
  }
  
  isAnimationRunning = true;
  statusMessage.textContent = 'Filling form...';
  
  // Create the visual cursor
  createVisualCursor();
  
  // Add progress indicator
  const progressIndicator = document.createElement('div');
  progressIndicator.className = 'ai-progress-indicator';
  progressIndicator.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: white;
    border: 1px solid #4a6fa5;
    border-radius: 4px;
    padding: 10px;
    font-size: 14px;
    color: #4a6fa5;
    z-index: 99999;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  `;
  document.body.appendChild(progressIndicator);
  
  // Process actions sequentially
  let actionsApplied = 0;
  const totalActions = automationResult.actions.length;
  
  function processNextAction(index) {
    if (index >= totalActions) {
      // All actions completed
      console.log('Form filling completed');
      
      // Update status message to show completion and countdown
      const statusMessage = document.getElementById('status-message');
      if (statusMessage) {
        statusMessage.textContent = `Form fill completed (${totalActions}/${totalActions})`;
        statusMessage.style.color = 'green';
      }
      
      // Create countdown display
      const countdownDisplay = document.createElement('div');
      countdownDisplay.style.cssText = `
        color: #4a6fa5;
        font-size: 16px;
        font-weight: bold;
        margin-top: 10px;
      `;
      statusMessage.parentElement.appendChild(countdownDisplay);
      
      // Manually run the countdown instead of using setInterval to avoid syntax issues
      function runCountdown() {
        let count = 2;
        
        function updateCountdown() {
          countdownDisplay.textContent = `Sending data in ${count}s...`;
          
          if (count <= 0) {
            countdownDisplay.remove();
            
            // Send request after countdown
            getBackendUrl().then(function(backendUrl) {
              fetch(`${backendUrl}/page-change`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  previousUrl: lastPageState.url,
                  currentUrl: window.location.href,
                  timestamp: new Date().toISOString()
                })
              })
              .then(function(response) { return response.json(); })
              .then(function(data) {
                if (data.success) {
                  const successNotification = document.createElement('div');
                  successNotification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: rgba(40, 167, 69, 0.9);
                    color: white;
                    padding: 12px 20px;
                    border-radius: 6px;
                    font-size: 14px;
                    z-index: 10000;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    transition: opacity 0.3s ease;
                  `;
                  successNotification.textContent = 'Page change recorded successfully';
                  document.body.appendChild(successNotification);
                  
                  // Remove success notification after 2 seconds
                  setTimeout(function() {
                    successNotification.style.opacity = '0';
                    setTimeout(function() { successNotification.remove(); }, 300);
                  }, 2000);
  
                  // Send page change to backend and handle automation restart based on response
                  if (window.location.href !== lastPageState.url) {
                    console.log('Page URL changed, sending to backend for analysis...');
                    
                    // Get backend URL and send page change data to backend for analysis
                    getBackendUrl().then(function(backendUrl) {
                      fetch(`${backendUrl}/page-change`, {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                          previousUrl: lastPageState.url,
                          currentUrl: window.location.href,
                          isCheckoutPage: CheckoutAutomation && typeof CheckoutAutomation.isCheckoutPage === 'function' ? CheckoutAutomation.isCheckoutPage() : false,
                          timestamp: new Date().toISOString()
                        })
                      })
                      .then(function(response) { return response.json(); })
                      .then(function(data) {
                        if (data.success && data.shouldRestart) {
                          console.log('Backend confirmed page change, preparing to restart automation...');
                          
                          // Call the main restart function
                          restartAutomation();
                        } else {
                          console.log('Backend indicated no need to restart automation');
                        }
                      })
                      .catch(function(error) {
                        console.error('Error analyzing page change:', error);
                        // On error, fall back to always restarting automation on ANY page change
                        console.log('Falling back to client-side detection, restarting automation on page change...');
                        const panel = document.querySelector('.ai-checkout-panel');
                        if (panel && panel.style.display !== 'none') {
                          panel.style.display = 'none';
                        }
                        const existingOverlay = document.querySelector('.ai-checkout-overlay');
                        if (existingOverlay) {
                          existingOverlay.remove();
                        }
                        createOverlay();
                        setTimeout(function() {
                          const button = document.querySelector('.ai-checkout-button');
                          if (button) button.click();
                        }, 1000);
                      });
                    });
                  }
                }
              })
              .catch(function(error) {
                console.error('Error sending page change:', error);
                const errorNotification = document.createElement('div');
                errorNotification.style.cssText = `
                  position: fixed;
                  top: 20px;
                  right: 20px;
                  background: rgba(220, 53, 69, 0.9);
                  color: white;
                  padding: 12px 20px;
                  border-radius: 6px;
                  font-size: 14px;
                  z-index: 10000;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                  transition: opacity 0.3s ease;
                `;
                errorNotification.textContent = 'Error recording page change';
                document.body.appendChild(errorNotification);
                
                // Remove error notification after 3 seconds
                setTimeout(function() {
                  errorNotification.style.opacity = '0';
                  setTimeout(function() { errorNotification.remove(); }, 300);
                }, 3000);
              });
            });
          } else {
            count--;
            setTimeout(updateCountdown, 1000);
          }
        }
        
        // Start the countdown
        updateCountdown();
      }
      
      // Run the countdown
      runCountdown();

      // Continue with navigation buttons check
      const { nextButton, completeButton } = detectNavigationButtons();
      
      if (completeButton) {
        // Found Complete Order button, finish the process by clicking it
        progressIndicator.textContent = 'Completing order...';
        
        moveCursorToElement(completeButton, () => {
          // Show completion message
          const completionMessage = document.createElement('div');
          completionMessage.className = 'ai-completion-message';
          completionMessage.textContent = 'Order process completed!';
          document.body.appendChild(completionMessage);
          
          // Add visual click effect before clicking
          const clickEffect = document.createElement('div');
          clickEffect.className = 'ai-click-ripple';
          const rect = completeButton.getBoundingClientRect();
          clickEffect.style.left = `${rect.left + rect.width/2}px`;
          clickEffect.style.top = `${rect.top + rect.height/2}px`;
          document.body.appendChild(clickEffect);
          
          // Click the complete button after a delay
          setTimeout(() => {
            completeButton.click();
            progressIndicator.remove();
            
            const statusMessage = document.getElementById('status-message');
            if (statusMessage) {
              statusMessage.textContent = 'Order successfully completed!';
              statusMessage.style.color = 'green';
              
              // Hide the loading spinner
              hideLoadingSpinner();
            }
            
            // Remove cursor after completion
            setTimeout(() => {
              const cursor = document.getElementById('ai-visual-cursor-container');
              if (cursor) cursor.remove();
              clickEffect.remove();
              
              // Remove completion message after a few seconds
              setTimeout(() => {
                completionMessage.remove();
                
                // Make sure the main button remains visible
                const button = document.querySelector('.ai-checkout-button');
                if (button) button.style.display = 'flex';
                
                isAnimationRunning = false;
              }, 3000);
            }, 1000);
          }, 500);
        });
      } else if (nextButton) {
        // Found Next button, continue to next page
        progressIndicator.textContent = 'Moving to next step...';
        
        moveCursorToElement(nextButton, () => {
          // Add visual click effect
          const clickEffect = document.createElement('div');
          clickEffect.className = 'ai-click-ripple';
          const rect = nextButton.getBoundingClientRect();
          clickEffect.style.left = `${rect.left + rect.width/2}px`;
          clickEffect.style.top = `${rect.top + rect.height/2}px`;
          document.body.appendChild(clickEffect);
          
          // Click the next button after a delay
          setTimeout(() => {
            nextButton.click();
            
            // Set up a listener to detect page load/change
            const pageChangeListener = () => {
              // Clean up
              progressIndicator.remove();
              clickEffect.remove();
              
              // Show navigation message
              const navigationMessage = document.createElement('div');
              navigationMessage.className = 'ai-navigation-message';
              navigationMessage.textContent = 'Moving to next step...';
              document.body.appendChild(navigationMessage);
              
              // Wait for page to stabilize
              setTimeout(() => {
                navigationMessage.remove();
                
                // Restart the automation process on the new page
                startAutomation();
                
                // Since we've detected a page change and started automation,
                // automatically apply form fill after a delay to give time for analysis
                setTimeout(() => {
                  const applyBtn = document.getElementById('apply-form-fill-btn');
                  if (applyBtn && applyBtn.style.display !== 'none') {
                    console.log('Automatically applying form fill after page change');
                    applyFormFill();
                  }
                }, 5000); // Wait 5 seconds for analysis to complete
                
                // Make sure the main button remains visible
                const button = document.querySelector('.ai-checkout-button');
                if (button) button.style.display = 'flex';
              }, 1500);
            };
            
            // Set up detection of page changes
            setTimeout(pageChangeListener, 1000);
          }, 500);
        });
      } else {
        // No navigation buttons found, end the process
        progressIndicator.remove();
        const cursor = document.getElementById('ai-visual-cursor-container');
        if (cursor) cursor.remove();
        
        const statusMessage = document.getElementById('status-message');
        if (statusMessage) {
          statusMessage.textContent = `Form fill completed (${actionsApplied}/${totalActions} actions)`;
          statusMessage.style.color = 'green';
          
          // Hide the loading spinner
          hideLoadingSpinner();
        }
        
        // Make sure the main button remains visible
        const button = document.querySelector('.ai-checkout-button');
        if (button) button.style.display = 'flex';
        
        isAnimationRunning = false;
      }
      return;
    }
    
    // Update progress
    progressIndicator.textContent = `Filling form: ${index + 1}/${totalActions}`;
    
    const action = automationResult.actions[index];
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
      // Move cursor to element first
      moveCursorToElement(element, () => {
        if (actionType === 'input') {
          // Handle text inputs
          simulateTyping(element, value, () => {
            actionsApplied++;
            setTimeout(() => processNextAction(index + 1), 300);
          });
        } else if (actionType === 'select') {
          // Handle select dropdowns
          selectOptionWithAnimation(element, value, () => {
            actionsApplied++;
            setTimeout(() => processNextAction(index + 1), 300);
          });
        } else if (actionType === 'checkbox') {
          // Handle checkboxes
          const shouldCheck = value === 'check';
          simulateCheckboxClick(element, shouldCheck, () => {
            actionsApplied++;
            setTimeout(() => processNextAction(index + 1), 300);
          });
        } else if (actionType === 'button' || actionType === 'click') {
          // Simulate click for buttons or clickable elements
          const clickEffect = document.createElement('div');
          clickEffect.className = 'ai-click-ripple';
          const rect = element.getBoundingClientRect();
          clickEffect.style.left = `${rect.left + rect.width/2}px`;
          clickEffect.style.top = `${rect.top + rect.height/2}px`;
          document.body.appendChild(clickEffect);
          
          setTimeout(() => {
            element.click();
            clickEffect.remove();
            actionsApplied++;
            setTimeout(() => processNextAction(index + 1), 500);
          }, 300);
        } else {
          // Unknown action type, skip
          console.warn(`Unknown action type: ${actionType}`);
          setTimeout(() => processNextAction(index + 1), 100);
        }
      });
    } else {
      console.warn(`Element not found: ${elementId}`);
      setTimeout(() => processNextAction(index + 1), 100);
    }
  }
  
  // Start processing actions
  setTimeout(() => {
    processNextAction(0);
  }, 500);
}

// Function to try loading fallback data
async function tryLoadFallbackData() {
  try {
    // Try different possible locations for the fallback data
    const possiblePaths = [
      'checkout-automation/form_filling_actions.json',
      'form_filling_actions.json',
      'checkout-automation/checkout-automation/form_filling_actions.json'
    ];
    
    for (const path of possiblePaths) {
      try {
        const url = chrome.runtime.getURL(path);
        console.log(`Attempting to fetch fallback data from: ${url}`);
        
        const response = await fetch(url);
        if (response.ok) {
          const fallbackData = await response.json();
          console.log(`Fallback data loaded from ${path}:`, fallbackData);
          
          if (fallbackData && fallbackData.actions && Array.isArray(fallbackData.actions)) {
            automationResult = fallbackData;
            return true;
          } else {
            console.warn(`Invalid data structure in ${path}`);
          }
        }
      } catch (e) {
        console.warn(`Failed to load from ${path}:`, e);
      }
    }
    
    // Create an embedded fallback as last resort
    console.log("Using embedded fallback data");
    automationResult = {
      "strategy_summary": "Basic form filling with default values",
      "total_actions": 16,
      "actions": [
        {
          "step": 1,
          "element_id": "email",
          "action_type": "input",
          "value": "test@example.com",
          "description": "Enter user email address"
        },
        {
          "step": 2,
          "element_id": "shipping_name",
          "action_type": "input",
          "value": "Test User",
          "description": "Enter shipping recipient name"
        },
        {
          "step": 3,
          "element_id": "shipping_street",
          "action_type": "input",
          "value": "123 Test St",
          "description": "Enter shipping street address"
        },
        {
          "step": 4,
          "element_id": "shipping_city",
          "action_type": "input",
          "value": "Test City",
          "description": "Enter shipping city"
        },
        {
          "step": 5,
          "element_id": "shipping_state",
          "action_type": "input",
          "value": "CA",
          "description": "Enter shipping state"
        },
        {
          "step": 6,
          "element_id": "shipping_zip",
          "action_type": "input",
          "value": "12345",
          "description": "Enter shipping zip code"
        },
        {
          "step": 7,
          "element_id": "shipping_country",
          "action_type": "input",
          "value": "US",
          "description": "Enter shipping country"
        },
        {
          "step": 8,
          "element_id": "same_as_shipping",
          "action_type": "checkbox",
          "value": "check",
          "description": "Check checkbox to use shipping address as billing address"
        },
        {
          "step": 9,
          "element_id": "card_holder",
          "action_type": "input",
          "value": "Test User",
          "description": "Enter cardholder's name"
        },
        {
          "step": 10,
          "element_id": "card_number",
          "action_type": "input",
          "value": "4111111111111111",
          "description": "Enter credit card number"
        },
        {
          "step": 11,
          "element_id": "card_expiry",
          "action_type": "input",
          "value": "12/25",
          "description": "Enter card expiry date"
        },
        {
          "step": 12,
          "element_id": "card_cvv",
          "action_type": "input",
          "value": "123",
          "description": "Enter card CVV"
        },
        {
          "step": 13,
          "element_id": "newsletter",
          "action_type": "checkbox",
          "value": "uncheck",
          "description": "Uncheck newsletter subscription based on user preference"
        },
        {
          "step": 14,
          "element_id": "promo_code",
          "action_type": "input",
          "value": "WELCOME10",
          "description": "Enter optimal promo code for maximum discount"
        },
        {
          "step": 15,
          "element_id": "apply_promo",
          "action_type": "button",
          "value": "click",
          "description": "Click to apply the entered promo code"
        },
        {
          "step": 16,
          "element_id": "checkout_submit_button",
          "action_type": "button",
          "value": "click",
          "description": "Click to submit the order and proceed to payment"
        }
      ]
    };
    
    return true;
  } catch (error) {
    console.error("Error in tryLoadFallbackData:", error);
    return false;
  }
}

// Listen for test events from the test page
window.addEventListener('test_content_script', (event) => {
  console.log('Content script received test event:', event.detail);
  
  // Show a visual confirmation
  const confirmDiv = document.createElement('div');
  confirmDiv.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #d4edda; color: #155724; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); z-index: 10000;';
  confirmDiv.innerHTML = `
    <div style="font-weight: bold; margin-bottom: 10px;">✅ Content Script Active!</div>
    <div>Message received: ${JSON.stringify(event.detail)}</div>
    <div style="margin-top: 15px; font-size: 12px;">This message will disappear in 3 seconds</div>
  `;
  document.body.appendChild(confirmDiv);
  
  // Remove after 3 seconds
  setTimeout(() => {
    confirmDiv.remove();
  }, 3000);
  
  // Update the test result element if it exists
  const testResult = document.getElementById('test_result');
  if (testResult) {
    testResult.textContent = 'Content script responded: ' + new Date().toLocaleTimeString();
  }
});

// Function to hide loading spinner
function hideLoadingSpinner() {
  const statusDiv = document.getElementById('automation-status');
  if (statusDiv) {
    const spinner = statusDiv.querySelector('.ai-spinner');
    if (spinner) {
      spinner.style.display = 'none';
    }
    const loadingIndicator = statusDiv.querySelector('.loading-indicator');
    if (loadingIndicator) {
      loadingIndicator.style.display = 'none';
    }
  }
}

// Function to show loading spinner
function showLoadingSpinner() {
  const statusDiv = document.getElementById('automation-status');
  if (statusDiv) {
    const spinner = statusDiv.querySelector('.ai-spinner');
    if (spinner) {
      spinner.style.display = 'block';
    }
    const loadingIndicator = statusDiv.querySelector('.loading-indicator');
    if (loadingIndicator) {
      loadingIndicator.style.display = 'block';
    }
  }
}

// Start the automation process
function startAutomation() {
  console.log('startAutomation function called');
  
  // Try to find status elements
  let statusDiv = document.getElementById('automation-status');
  let statusMessage = document.getElementById('status-message');
  let applyBtn = document.getElementById('apply-form-fill-btn');
  
  // Check if we have the UI elements (they may not exist if createOverlay wasn't called)
  if (!statusDiv || !statusMessage) {
    console.warn('Status elements not found, creating overlay first');
    createOverlay();
    
    // Try to get elements again after creating overlay
    statusDiv = document.getElementById('automation-status');
    statusMessage = document.getElementById('status-message');
    applyBtn = document.getElementById('apply-form-fill-btn');
    
    if (statusDiv && statusMessage) {
      console.log('Status elements created successfully');
    } else {
      console.error('Failed to create status elements even after creating overlay');
      alert('Error: Could not initialize automation UI. Please refresh and try again.');
      
      // Ensure main button is visible
      const button = document.querySelector('.ai-checkout-button');
      if (button) button.style.display = 'flex';
      
      return;
    }
  }
    try {
    // Status div is already visible in the new UI
    if (applyBtn) applyBtn.style.display = 'none';
    statusMessage.textContent = 'Analyzing page...';
    
    // Use the CheckoutAutomation module to capture HTML
    const html = CheckoutAutomation ? CheckoutAutomation.captureHTML() : document.documentElement.outerHTML;
    console.log('HTML captured, length:', html.length);
      const data = {
      html: html,
      url: window.location.href,
      page_title: document.title
    };
    
    // Add advanced settings if available
    if (window.automationAdvancedSettings) {
      data.advanced_settings = window.automationAdvancedSettings;
      console.log('Including advanced settings in request:', window.automationAdvancedSettings);
    }
    
    console.log('Sending data to background script:', {
      url: data.url,
      htmlLength: data.html.length,
      page_title: data.page_title
    });
  
    // Process with background script
    chrome.runtime.sendMessage(
      { 
        action: 'processCheckout', 
        data: data
      },
      response => {
        console.log('Received response from background script:', response);
        
        if (response && response.success) {
          // Save automation result to global variable and localStorage for persistence
          if (response.result && response.result.actions && Array.isArray(response.result.actions)) {
            console.log('Setting automationResult with valid actions array, length:', response.result.actions.length);
            automationResult = response.result;
            
            // Also save to localStorage for persistence across page refreshes
            try {
              localStorage.setItem('lastAutomationResult', JSON.stringify(automationResult));
              console.log('Saved automationResult to localStorage');
            } catch (e) {
              console.warn('Failed to save to localStorage:', e);
            }
          } else {
            console.error('Invalid response.result structure:', response.result);
            statusMessage.textContent = 'Error: Invalid data received';
            statusMessage.style.color = 'red';
            
            // Try to load from fallback
            tryLoadFallbackData();
            return;
          }
          
          statusMessage.textContent = 'Checkout form processed successfully!';
          statusMessage.style.color = 'green';
          hideLoadingSpinner();

          // Set default auto-fill behavior to true
          window.automationAdvancedSettings = {
            ...window.automationAdvancedSettings,
            auto_fill_forms: true
          };

          // Show Apply Form Fill button with proper styling
          if (applyBtn) {
            applyBtn.style.display = 'block';
            applyBtn.style.pointerEvents = 'auto';
            applyBtn.style.cursor = 'pointer';
            applyBtn.style.position = 'relative';
            applyBtn.style.zIndex = '10001';
            
            // Ensure event listener is properly set for manual clicks
            applyBtn.onclick = (event) => {
              event.stopPropagation();
              console.log('Apply Form Fill button clicked (via onclick)');
              applyFormFill();
            };
            
            // Auto-apply form fill after a short delay
            console.log('Auto-fill is enabled by default, applying form fill automatically');
            setTimeout(() => {
              applyFormFill();
            }, 1000);
          }
        } else {
          statusMessage.textContent = 'Failed to process checkout data';
          statusMessage.style.color = 'red';
          hideLoadingSpinner();
          console.error('Error from background script:', response ? response.error : 'No response');
          
          // Try to recover from localStorage or fallback
          console.log('Trying to recover from localStorage or fallback');
          try {
            const savedResult = localStorage.getItem('lastAutomationResult');
            if (savedResult) {
              automationResult = JSON.parse(savedResult);
              console.log('Recovered automationResult from localStorage');
              
              if (automationResult && automationResult.actions && Array.isArray(automationResult.actions)) {
                              statusMessage.textContent = 'Using previously saved form data';
              statusMessage.style.color = 'orange';
              hideLoadingSpinner();
                
                if (applyBtn) {
                  applyBtn.style.display = 'block';
                  applyBtn.style.pointerEvents = 'auto';
                  applyBtn.style.cursor = 'pointer';
                  applyBtn.style.position = 'relative';
                  applyBtn.style.zIndex = '10001';
                  
                  // Ensure event listener is properly set for manual clicks
                  applyBtn.onclick = (event) => {
                    event.stopPropagation();
                    console.log('Apply Form Fill button clicked (via onclick)');
                    applyFormFill();
                  };
                }
                return;
              }
            }
          } catch (e) {
            console.warn('Failed to recover from localStorage:', e);
          }
          
          // Try fallback as last resort
          tryLoadFallbackData().then(success => {
            if (success) {
              statusMessage.textContent = 'Using fallback form data';
              statusMessage.style.color = 'orange';
              hideLoadingSpinner();
              
              if (applyBtn) {
                applyBtn.style.display = 'block';
                applyBtn.style.pointerEvents = 'auto';
                applyBtn.style.cursor = 'pointer';
                applyBtn.style.position = 'relative';
                applyBtn.style.zIndex = '10001';
                
                // Ensure event listener is properly set for manual clicks
                applyBtn.onclick = (event) => {
                  event.stopPropagation();
                  console.log('Apply Form Fill button clicked (via onclick)');
                  applyFormFill();
                };
              }
            }
          });
          
          // Ensure main button is visible on error
          const button = document.querySelector('.ai-checkout-button');
          if (button) button.style.display = 'flex';
        }
      }
    );
  } catch (error) {
    console.error('Error in automation process:', error);
    if (statusMessage) {
      statusMessage.textContent = 'Error: ' + error.message;
      statusMessage.style.color = 'red';
      hideLoadingSpinner();
    } else {
      alert('Error: ' + error.message);
    }
    
    // Try to recover from localStorage or fallback
    tryLoadFallbackData();
    
    // Ensure main button is visible on error
    const button = document.querySelector('.ai-checkout-button');
    if (button) button.style.display = 'flex';
  }
}

// Get the backend URL from settings
async function getBackendUrl() {
    return new Promise((resolve) => {
        chrome.storage.sync.get(['backendUrl'], (settings) => {
            resolve(settings.backendUrl || 'http://localhost:5000');
        });
    });
}

// Function to handle automation restart with proper sequencing
function restartAutomation() {
  console.log('Restarting automation with proper sequencing...');
  
  // Get panel and add transition styles
  const panel = document.querySelector('.ai-checkout-panel');
  if (panel && panel.style.display !== 'none') {
    // Panel is visible, close it with animation first
    panel.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    panel.style.opacity = '0';
    panel.style.transform = 'translateY(-20px)';
    
    // Wait for panel closing animation
    setTimeout(() => {
      panel.style.display = 'none';
      panel.style.opacity = '1';
      panel.style.transform = 'none';
      
      // Remove existing overlay after panel is closed
      const existingOverlay = document.querySelector('.ai-checkout-overlay');
      if (existingOverlay) {
        existingOverlay.remove();
      }
      
      // Create new overlay
      createOverlay();
      
      // Wait for overlay creation and DOM update
      setTimeout(() => {
        console.log('Clicking AI Checkout button to restart automation...');
        const button = document.querySelector('.ai-checkout-button');
        if (button) {
          button.click();
        }
      }, 1500); // Wait 1.5s for overlay to be ready
      
    }, 300); // Wait for panel closing animation
  } else {
    // No panel visible, restart directly
    console.log('No panel to close, restarting directly...');
    
    // Remove existing overlay
    const existingOverlay = document.querySelector('.ai-checkout-overlay');
    if (existingOverlay) {
      existingOverlay.remove();
    }
    
    // Create new overlay
    createOverlay();
    
    // Wait for overlay creation
    setTimeout(() => {
      console.log('Clicking AI Checkout button to restart automation...');
      const button = document.querySelector('.ai-checkout-button');
      if (button) {
        button.click();
      }
    }, 1000);
  }
}
