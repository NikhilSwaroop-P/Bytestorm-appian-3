/**
 * Test script for checkout automation
 * This simulates a real checkout page for testing
 */

// Create a mock checkout form
function createMockCheckoutForm() {
  const container = document.createElement('div');
  container.className = 'checkout-container';
  container.innerHTML = `
    <h1>Test Checkout Page</h1>
    <form id="checkout-form">
      <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" name="email" class="form-control">
      </div>
      
      <h2>Shipping Information</h2>
      <div class="form-group">
        <label for="shipping_name">Full Name</label>
        <input type="text" id="shipping_name" name="shipping_name" class="form-control">
      </div>
      
      <div class="form-group">
        <label for="shipping_street">Street Address</label>
        <input type="text" id="shipping_street" name="shipping_street" class="form-control">
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="shipping_city">City</label>
          <input type="text" id="shipping_city" name="shipping_city" class="form-control">
        </div>
        
        <div class="form-group">
          <label for="shipping_state">State</label>
          <input type="text" id="shipping_state" name="shipping_state" class="form-control">
        </div>
        
        <div class="form-group">
          <label for="shipping_zip">ZIP Code</label>
          <input type="text" id="shipping_zip" name="shipping_zip" class="form-control">
        </div>
      </div>
      
      <div class="form-group">
        <label for="shipping_country">Country</label>
        <select id="shipping_country" name="shipping_country" class="form-control">
          <option value="">Select Country</option>
          <option value="US">United States</option>
          <option value="CA">Canada</option>
          <option value="UK">United Kingdom</option>
        </select>
      </div>
      
      <div class="form-group checkbox">
        <input type="checkbox" id="same_as_shipping" name="same_as_shipping">
        <label for="same_as_shipping">Billing address same as shipping</label>
      </div>
      
      <h2>Payment Information</h2>
      <div class="form-group">
        <label for="card_holder">Cardholder Name</label>
        <input type="text" id="card_holder" name="card_holder" class="form-control">
      </div>
      
      <div class="form-group">
        <label for="card_number">Card Number</label>
        <input type="text" id="card_number" name="card_number" class="form-control">
      </div>
      
      <div class="form-row">
        <div class="form-group">
          <label for="card_expiry">Expiration Date</label>
          <input type="text" id="card_expiry" name="card_expiry" class="form-control" placeholder="MM/YY">
        </div>
        
        <div class="form-group">
          <label for="card_cvv">CVV</label>
          <input type="text" id="card_cvv" name="card_cvv" class="form-control">
        </div>
      </div>
      
      <div class="form-group checkbox">
        <input type="checkbox" id="newsletter" name="newsletter" checked>
        <label for="newsletter">Subscribe to newsletter</label>
      </div>
      
      <div class="promo-code">
        <div class="form-group">
          <label for="promo_code">Promo Code</label>
          <input type="text" id="promo_code" name="promo_code" class="form-control">
          <button type="button" id="apply_promo" class="btn btn-primary">Apply</button>
        </div>
      </div>
      
      <button type="submit" id="checkout_submit_button" class="btn btn-primary btn-large checkout-btn">Complete Order</button>
    </form>
  `;
  
  document.body.appendChild(container);
  
  // Add event listener to prevent form submission
  document.getElementById('checkout-form').addEventListener('submit', (event) => {
    event.preventDefault();
    alert('Form submitted!');
  });
}

// Initialize the test page
document.addEventListener('DOMContentLoaded', () => {
  document.body.innerHTML = '<h1>Loading test checkout page...</h1>';
  
  // Create mock checkout form
  createMockCheckoutForm();
  
  // Add styles
  const style = document.createElement('style');
  style.textContent = `
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
      padding: 20px;
      max-width: 800px;
      margin: 0 auto;
    }
    
    .checkout-container {
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
      padding: 30px;
    }
    
    h1, h2 {
      color: #333;
    }
    
    h2 {
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }
    
    .form-group {
      margin-bottom: 20px;
    }
    
    .form-row {
      display: flex;
      gap: 15px;
    }
    
    .form-row .form-group {
      flex: 1;
    }
    
    label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
      color: #555;
    }
    
    .checkbox {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .checkbox label {
      margin-bottom: 0;
    }
    
    .form-control {
      display: block;
      width: 100%;
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 4px;
      font-size: 16px;
    }
    
    .btn {
      padding: 10px 20px;
      background: #4a6fa5;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 16px;
    }
    
    .btn-large {
      padding: 12px 24px;
      font-size: 18px;
      width: 100%;
      margin-top: 20px;
    }
    
    .promo-code {
      margin-top: 20px;
      padding: 15px;
      background: #f8f9fa;
      border-radius: 4px;
    }
    
    .promo-code .form-group {
      display: flex;
      gap: 10px;
      margin-bottom: 0;
    }
    
    .promo-code .btn {
      padding: 10px 15px;
    }
  `;
  
  document.head.appendChild(style);
});

// Export test functions for the extension to use
window.testFunctions = {
  fillFormWithTestData() {
    document.getElementById('email').value = 'test@example.com';
    document.getElementById('shipping_name').value = 'Test User';
    document.getElementById('shipping_street').value = '123 Test St';
    document.getElementById('shipping_city').value = 'Test City';
    document.getElementById('shipping_state').value = 'CA';
    document.getElementById('shipping_zip').value = '12345';
    document.getElementById('shipping_country').value = 'US';
    document.getElementById('same_as_shipping').checked = true;
    document.getElementById('card_holder').value = 'Test User';
    document.getElementById('card_number').value = '4111111111111111';
    document.getElementById('card_expiry').value = '12/25';
    document.getElementById('card_cvv').value = '123';
    document.getElementById('newsletter').checked = false;
    document.getElementById('promo_code').value = 'WELCOME10';
  },
  
  resetForm() {
    document.getElementById('checkout-form').reset();
  }
};
