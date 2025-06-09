document.addEventListener('DOMContentLoaded', function() {
    console.log('CartPage.js loaded');
    const cartItemsContainer = document.getElementById('cart-items-container');
    const emptyCartMessage = document.getElementById('emptyCartMessage');
    const cartSummary = document.getElementById('cartSummary');
    const cartSubtotal = document.getElementById('cart-subtotal');
    const cartTax = document.getElementById('cart-tax');
    const cartTotal = document.getElementById('cart-total');
    const checkoutButton = document.getElementById('checkoutButton');
    const suggestionsContainer = document.getElementById('suggestionsContainer');
    const themeToggle = document.getElementById('themeToggle');
    
    // Theme setup
    function setupTheme() {
        const currentTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        // Update toggle icon based on current theme
        if (currentTheme === 'dark') {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        }
    }
    
    // Initialize theme
    setupTheme();
    
    // Theme toggle event handler
    themeToggle.addEventListener('click', function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update button icon
        if (newTheme === 'dark') {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
        }
    });

    // Format price for display
    function formatPrice(price) {
        return '₹' + Number(price).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }
    
    // Render cart items
    function renderCart() {
        console.log('Rendering cart');
        
        // Ensure cart object exists, if not, try to recreate it
        if (!window.shopsmartCart) {
            console.error("Cart object not found, recreating from localStorage");
            window.shopsmartCart = new Cart();
        }
        
        const cartItems = window.shopsmartCart.getItems();
        console.log('Cart items:', cartItems);
        
        // Show/hide empty cart message
        if (cartItems.length === 0) {
            emptyCartMessage.style.display = 'flex';
            cartSummary.style.display = 'none';
            // Clear cart items
            cartItemsContainer.innerHTML = '';
            cartItemsContainer.appendChild(emptyCartMessage);
            return;
        }
        
        // Hide empty cart message and show summary
        emptyCartMessage.style.display = 'none';
        cartSummary.style.display = 'block';
        
        // Clear existing items
        cartItemsContainer.innerHTML = '';
        
        // Create cart items table
        const cartTable = document.createElement('table');
        cartTable.className = 'cart-table';
        
        // Add table header
        const tableHeader = document.createElement('thead');
        tableHeader.innerHTML = `
            <tr>
                <th class="product-col">Product</th>
                <th class="price-col">Price</th>
                <th class="quantity-col">Quantity</th>
                <th class="total-col">Total</th>
                <th class="actions-col">Actions</th>
            </tr>
        `;
        cartTable.appendChild(tableHeader);
        
        // Add table body
        const tableBody = document.createElement('tbody');
        let allSuggestions = [];
        
        // Add cart items
        cartItems.forEach(item => {
            const itemPrice = typeof item.price === 'string' 
                ? parseFloat(item.price.replace(/[^0-9.]/g, ''))
                : item.price;
            
            const rowTotal = itemPrice * item.quantity;
            
            const row = document.createElement('tr');
            row.className = 'cart-item';
            row.dataset.id = item.id;
            
            // Ensure image_url or image_path exists
            const imageUrl = item.image_url || item.image_path || '/static/img/product-placeholder.svg';
            
            const itemId = String(item.id); // Convert to string to ensure consistent comparison
            console.log('Creating row for item ID:', itemId);
            
            row.innerHTML = `
                <td class="product-info">
                    <img src="${imageUrl}" alt="${item.title}" class="cart-item-image">
                    <div class="product-details">
                        <h3 class="product-title">${item.title}</h3>
                        <p class="product-meta">${item.category || ''}</p>
                        <small class="product-id">ID: ${itemId}</small>
                    </div>
                </td>
                <td class="item-price" data-label="Price:">${formatPrice(itemPrice)}</td>
                <td class="item-quantity" data-label="Quantity:">
                    <div class="quantity-control">
                        <button class="quantity-btn decrease" data-id="${itemId}">-</button>
                        <input type="number" value="${item.quantity}" min="1" class="quantity-input" data-id="${itemId}">
                        <button class="quantity-btn increase" data-id="${itemId}">+</button>
                    </div>
                </td>
                <td class="item-total" data-label="Total:">${formatPrice(rowTotal)}</td>
                <td class="item-actions" data-label="Actions:">
                    <button class="remove-item-btn" data-id="${itemId}" aria-label="Remove item">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            
            tableBody.appendChild(row);
            
            // Get suggestions for this item
            const suggestions = window.shopsmartCart.getSuggestions(item);
            if (suggestions.type === 'category') {
                allSuggestions = [...allSuggestions, ...suggestions.suggestions];
            }
        });
        
        cartTable.appendChild(tableBody);
        cartItemsContainer.appendChild(cartTable);
        
        // Render unique suggestions
        renderSuggestions([...new Set(allSuggestions)]);
        
        // Update summary values
        updateSummary();
        
        // Add event listeners for quantity controls and remove buttons
        addCartItemEventListeners();
    }
    
    // Add event listeners to cart item controls
    function addCartItemEventListeners() {
        console.log('Adding cart item event listeners');
        
        // Direct event delegation approach for cart actions
        cartItemsContainer.addEventListener('click', function(e) {
            // Handle decrease button clicks
            if (e.target.classList.contains('decrease') || 
                (e.target.parentElement && e.target.parentElement.classList.contains('decrease'))) {
                
                const btn = e.target.classList.contains('decrease') ? e.target : e.target.parentElement;
                const id = btn.dataset.id;
                console.log('Decrease button clicked via delegation', id);
                
                if (!id) return;
                
                const inputElement = document.querySelector(`.quantity-input[data-id="${id}"]`);
                if (!inputElement) return;
                
                const currentValue = parseInt(inputElement.value);
                
                if (currentValue > 1) {
                    const newValue = currentValue - 1;
                    inputElement.value = newValue;
                    window.shopsmartCart.updateQuantity(id, newValue);
                    updateRowTotal(id, newValue);
                    updateSummary();
                } else if (currentValue === 1) {
                    // If attempting to go below 1, remove the item
                    const row = document.querySelector(`.cart-item[data-id="${id}"]`);
                    if (!row) return;
                    
                    // Add removal animation
                    row.classList.add('removing');
                    
                    // Remove after animation completes
                    setTimeout(() => {
                        window.shopsmartCart.removeItem(id);
                        renderCart(); // Completely re-render to show empty cart message if needed
                    }, 300);
                }
            }
            
            // Handle increase button clicks
            else if (e.target.classList.contains('increase') || 
                     (e.target.parentElement && e.target.parentElement.classList.contains('increase'))) {
                
                const btn = e.target.classList.contains('increase') ? e.target : e.target.parentElement;
                const id = btn.dataset.id;
                console.log('Increase button clicked via delegation', id);
                
                if (!id) return;
                
                const inputElement = document.querySelector(`.quantity-input[data-id="${id}"]`);
                if (!inputElement) return;
                
                const currentValue = parseInt(inputElement.value);
                const newValue = currentValue + 1;
                
                // Update the input field
                inputElement.value = newValue;
                
                // Update the cart and UI
                window.shopsmartCart.updateQuantity(id, newValue);
                updateRowTotal(id, newValue);
                updateSummary();
                
                // Add a visual feedback for the button click
                btn.classList.add('clicked');
                setTimeout(() => {
                    btn.classList.remove('clicked');
                }, 150);
            }
            
            // Handle remove button clicks
            else if (e.target.classList.contains('remove-item-btn') || 
                     (e.target.parentElement && e.target.parentElement.classList.contains('remove-item-btn')) ||
                     e.target.classList.contains('fa-trash')) {
                
                let btn;
                if (e.target.classList.contains('remove-item-btn')) {
                    btn = e.target;
                } else if (e.target.classList.contains('fa-trash')) {
                    btn = e.target.closest('.remove-item-btn');
                } else {
                    btn = e.target.parentElement;
                }
                
                if (!btn) return;
                
                const id = btn.dataset.id;
                console.log('Remove button clicked via delegation', id);
                
                if (!id) return;
                
                const row = document.querySelector(`.cart-item[data-id="${id}"]`);
                if (!row) return;
                
                // Add removal animation
                row.classList.add('removing');
                
                // Remove after animation completes
                setTimeout(() => {
                    window.shopsmartCart.removeItem(id);
                    
                    // Check if cart is now empty
                    if (window.shopsmartCart.getItems().length === 0) {
                        // Show empty cart message
                        emptyCartMessage.style.display = 'flex';
                        cartSummary.style.display = 'none';
                        cartItemsContainer.innerHTML = '';
                        cartItemsContainer.appendChild(emptyCartMessage);
                    } else {
                        renderCart(); // Re-render the cart
                    }
                }, 300);
            }
        });
        
        // Also keep the individual event listeners as a fallback
        // Quantity decrease buttons
        document.querySelectorAll('.quantity-btn.decrease').forEach(btn => {
            console.log('Adding event listener to decrease button', btn);
            btn.addEventListener('click', function(e) {
                console.log('Decrease button clicked', this.dataset.id);
                e.preventDefault(); // Prevent form submission
                e.stopPropagation(); // Stop event bubbling
                
                const id = this.dataset.id;
                const inputElement = document.querySelector(`.quantity-input[data-id="${id}"]`);
                const currentValue = parseInt(inputElement.value);
                
                if (currentValue > 1) {
                    const newValue = currentValue - 1;
                    inputElement.value = newValue;
                    window.shopsmartCart.updateQuantity(id, newValue);
                    updateRowTotal(id, newValue);
                    updateSummary();
                } else if (currentValue === 1) {
                    // If attempting to go below 1, remove the item
                    const row = document.querySelector(`.cart-item[data-id="${id}"]`);
                    
                    // Add removal animation
                    row.classList.add('removing');
                    
                    // Remove after animation completes
                    setTimeout(() => {
                        window.shopsmartCart.removeItem(id);
                        renderCart(); // Completely re-render to show empty cart message if needed
                    }, 300);
                }
            });
        });
        
        // Quantity increase buttons
        document.querySelectorAll('.quantity-btn.increase').forEach(btn => {
            console.log('Adding event listener to increase button', btn);
            btn.addEventListener('click', function(e) {
                console.log('Increase button clicked', this.dataset.id);
                e.preventDefault(); // Prevent form submission
                e.stopPropagation(); // Stop event bubbling
                
                const id = this.dataset.id;
                const inputElement = document.querySelector(`.quantity-input[data-id="${id}"]`);
                const currentValue = parseInt(inputElement.value);
                const newValue = currentValue + 1;
                
                // Update the input field
                inputElement.value = newValue;
                
                // Update the cart and UI
                window.shopsmartCart.updateQuantity(id, newValue);
                updateRowTotal(id, newValue);
                updateSummary();
                
                // Add a visual feedback for the button click
                this.classList.add('clicked');
                setTimeout(() => {
                    this.classList.remove('clicked');
                }, 150);
            });
        });
        
        // Quantity input fields
        document.querySelectorAll('.quantity-input').forEach(input => {
            console.log('Adding event listener to quantity input', input);
            input.addEventListener('change', function() {
                console.log('Quantity input changed', this.dataset.id);
                const id = this.dataset.id;
                let newValue = parseInt(this.value);
                
                if (isNaN(newValue) || newValue < 1) {
                    newValue = 1; // Reset to minimum value
                    this.value = 1;
                }
                
                if (newValue >= 1) {
                    window.shopsmartCart.updateQuantity(id, newValue);
                    updateRowTotal(id, newValue);
                    updateSummary();
                }
            });
            
            // Prevent non-numeric input
            input.addEventListener('keypress', function(e) {
                if (!/[0-9]/.test(e.key)) {
                    e.preventDefault();
                }
            });
        });
        
        // Remove buttons
        document.querySelectorAll('.remove-item-btn').forEach(btn => {
            console.log('Adding event listener to remove button', btn);
            btn.addEventListener('click', function() {
                console.log('Remove button clicked', this.dataset.id);
                const id = this.dataset.id;
                const row = document.querySelector(`.cart-item[data-id="${id}"]`);
                
                // Add removal animation
                row.classList.add('removing');
                
                // Remove after animation completes
                setTimeout(() => {
                    window.shopsmartCart.removeItem(id);
                    
                    // Check if cart is now empty
                    if (window.shopsmartCart.getItems().length === 0) {
                        // Show empty cart message
                        emptyCartMessage.style.display = 'flex';
                        cartSummary.style.display = 'none';
                        cartItemsContainer.innerHTML = '';
                        cartItemsContainer.appendChild(emptyCartMessage);
                    } else {
                        renderCart(); // Re-render the cart
                    }
                }, 300);
            });
        });
    }
    
    // Update total for a specific row
    function updateRowTotal(id, quantity) {
        const row = document.querySelector(`.cart-item[data-id="${id}"]`);
        if (!row) return;
        
        const priceText = row.querySelector('.item-price').textContent;
        const price = parseFloat(priceText.replace(/[^0-9.]/g, ''));
        const totalCell = row.querySelector('.item-total');
        
        totalCell.textContent = formatPrice(price * quantity);
    }
    
    // Update cart summary values
    function updateSummary() {
        console.log('Updating summary');
        if (!window.shopsmartCart) {
            console.error('Cart object not available for summary update');
            return;
        }
        
        const subtotal = window.shopsmartCart.getTotalPrice();
        const shipping = subtotal > 0 ? 25 : 0; // Free shipping for empty cart
        const tax = subtotal * 0.08; // 8% tax
        const total = subtotal + shipping + tax;
        
        // Format values for display
        cartSubtotal.textContent = formatPrice(subtotal);
        cartTax.textContent = formatPrice(tax);
        cartTotal.textContent = formatPrice(total);
        
        // Enable/disable checkout button based on cart items
        const hasItems = window.shopsmartCart.getItems().length > 0;
        checkoutButton.disabled = !hasItems;
        
        if (!hasItems) {
            checkoutButton.classList.add('disabled');
            cartSummary.style.display = 'none';
            emptyCartMessage.style.display = 'flex';
        } else {
            checkoutButton.classList.remove('disabled');
            cartSummary.style.display = 'block';
            emptyCartMessage.style.display = 'none';
        }
        
        // Update cart count badge
        window.shopsmartCart.updateCartCount();
    }
    
    // Render product suggestions
    function renderSuggestions(suggestions) {
        suggestionsContainer.innerHTML = '';
        
        if (!suggestions || suggestions.length === 0) {
            // Add generic suggestions
            const genericSuggestions = ['Popular items', 'Trending now', 'Top rated products'];
            suggestionsContainer.innerHTML = `
                <div class="suggestion-item">
                    <h3>Check out these popular items:</h3>
                    <ul>
                        ${genericSuggestions.map(item => `<li><a href="/">${item}</a></li>`).join('')}
                    </ul>
                    <a href="/" class="view-all-btn">View all recommendations</a>
                </div>
            `;
            return;
        }
        
        // Render specific suggestions
        const suggestionEl = document.createElement('div');
        suggestionEl.className = 'suggestion-item';
        suggestionEl.innerHTML = `
            <h3>Frequently bought together:</h3>
            <ul>
                ${suggestions.map(item => `<li><a href="/?q=${encodeURIComponent(item)}">${item}</a></li>`).join('')}
            </ul>
            <a href="/" class="view-all-btn">View all recommendations</a>
        `;
        
        suggestionsContainer.appendChild(suggestionEl);
    }
    
    // Checkout button event handler
    checkoutButton.addEventListener('click', function() {
        console.log('Checkout button clicked');
        const cartItems = window.shopsmartCart.getItems();
        if (cartItems.length === 0) {
            alert('Your cart is empty. Please add items before checkout.');
            return;
        }
        
        // Save cart to session storage to ensure it persists across page loads
        sessionStorage.setItem('checkoutCart', JSON.stringify(cartItems));
        
        // Get the first item to create a checkout session
        const firstItem = cartItems[0];
        
        // Create a checkout session first
        fetch('/api/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                product_id: firstItem.id,
                product_data: firstItem,
                cart_items: cartItems
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Redirect to the checkout page with the session ID
                window.location.href = data.checkout_url;
            } else {
                alert('Checkout process failed: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Checkout error:', error);
            alert('Error processing checkout. Please try again.');
        });
    });
    
    // Initialize cart and render on page load
    console.log('Initializing cart page');
    
    // Check if Cart class is available, if not, wait for it
    const initializeCart = () => {
        if (typeof Cart === 'undefined' || !window.shopsmartCart) {
            console.log('Cart class not ready yet, waiting...');
            setTimeout(initializeCart, 100); // Check again in 100ms
            return;
        }
        
        console.log('Cart class is available, rendering cart');
        renderCart();
    };
    
    // Start initialization
    initializeCart();
    
    // Add back to shopping button
    const continueShoppingBtn = document.querySelector('.continue-shopping-btn');
    if (continueShoppingBtn) {
        continueShoppingBtn.addEventListener('click', function(e) {
            // Store cart state in sessionStorage
            sessionStorage.setItem('shopsmartCart', JSON.stringify(window.shopsmartCart.getItems()));
            // Let default action happen (navigate to homepage)
        });
    }

    // Add an extra direct event listener for remove buttons
    document.addEventListener('click', function(e) {
        // Check if the clicked element is a remove button or its child
        const removeBtn = 
            e.target.classList.contains('remove-item-btn') ? e.target : 
            e.target.classList.contains('fa-trash') ? e.target.closest('.remove-item-btn') :
            e.target.closest('.remove-item-btn');
            
        if (!removeBtn) return;
        
        const id = removeBtn.dataset.id;
        console.log('Global remove button click handler triggered for ID:', id);
        
        if (!id) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const row = document.querySelector(`.cart-item[data-id="${id}"]`);
        if (!row) {
            console.error('Could not find row for item', id);
            return;
        }
        
        // Add removal animation
        row.classList.add('removing');
        
        // Remove after animation completes
        setTimeout(() => {
            const removed = window.shopsmartCart.removeItem(id);
            console.log('Item removal result:', removed ? 'Success' : 'Failed');
            
            // Check if cart is now empty
            if (window.shopsmartCart.getItems().length === 0) {
                console.log('Cart is now empty, showing empty cart message');
                // Show empty cart message
                emptyCartMessage.style.display = 'flex';
                cartSummary.style.display = 'none';
                cartItemsContainer.innerHTML = '';
                cartItemsContainer.appendChild(emptyCartMessage);
            } else {
                console.log('Re-rendering cart after item removal');
                renderCart(); // Re-render the cart
            }
        }, 300);
    }, true);
}); 