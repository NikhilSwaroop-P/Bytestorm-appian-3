// Cart functionality for ShopSmart
window.Cart = class Cart {
    constructor() {
        this.items = [];
        this.loadFromStorage();
        this.updateCartCount();
    }

    // Load cart from localStorage
    loadFromStorage() {
        // First try sessionStorage (higher priority - used for transfers between pages)
        const sessionCart = sessionStorage.getItem('shopsmartCart');
        if (sessionCart) {
            try {
                this.items = JSON.parse(sessionCart);
                console.log("Cart loaded from sessionStorage", this.items);
                // Clear sessionStorage after loading to avoid stale data
                sessionStorage.removeItem('shopsmartCart');
                // Save to localStorage for persistence
                localStorage.setItem('shopsmartCart', sessionCart);
                return;
            } catch (e) {
                console.error('Failed to parse cart from sessionStorage', e);
            }
        }
        
        // Fall back to localStorage
        const savedCart = localStorage.getItem('shopsmartCart');
        if (savedCart) {
            try {
                this.items = JSON.parse(savedCart);
                console.log("Cart loaded from localStorage", this.items);
            } catch (e) {
                console.error('Failed to parse cart from localStorage', e);
                this.items = [];
            }
        }
    }

    // Save cart to localStorage
    saveToStorage() {
        localStorage.setItem('shopsmartCart', JSON.stringify(this.items));
        this.updateCartCount();
    }

    // Add item to cart
    addItem(product, quantity = 1) {
        // Check if item already exists in cart
        const existingItem = this.items.find(item => item.id === product.id);
        
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            // Ensure required properties exist
            const safeProduct = {
                id: product.id || `prod_${Date.now()}`,
                title: product.title || 'Unknown Product',
                price: product.price || 0,
                image_url: product.image_url || product.image_path || '/static/img/product-placeholder.svg',
                quantity: quantity,
                category: product.category || '',
                ...product // Include all other properties from product
            };
            
            this.items.push(safeProduct);
        }
        
        this.saveToStorage();
        return this.getSuggestions(product);
    }

    // Update item quantity
    updateQuantity(productId, quantity) {
        const item = this.items.find(item => item.id === productId);
        
        if (item) {
            if (quantity > 0) {
                item.quantity = quantity;
            } else {
                // Remove item if quantity is 0 or negative
                this.removeItem(productId);
                return;
            }
            
            this.saveToStorage();
        }
    }

    // Remove item from cart
    removeItem(productId) {
        console.log('Attempting to remove item with ID:', productId);
        console.log('Cart before removal:', JSON.parse(JSON.stringify(this.items)));
        
        // Make sure productId is a string for consistent comparison
        const idToRemove = String(productId);
        
        // Check if the item exists in cart before removal
        const itemToRemove = this.items.find(item => String(item.id) === idToRemove);
        if (!itemToRemove) {
            console.error('Item with ID', idToRemove, 'not found in cart');
            return false;
        }
        
        // Filter out the item with the given ID
        const prevLength = this.items.length;
        this.items = this.items.filter(item => String(item.id) !== idToRemove);
        
        // Verify removal was successful
        if (prevLength === this.items.length) {
            console.error('Failed to remove item with ID', idToRemove);
            console.log('Item IDs in cart:', this.items.map(item => String(item.id)));
            return false;
        }
        
        console.log('Item removed successfully. Cart after removal:', this.items);
        
        // Save the updated cart to storage
        this.saveToStorage();
        return true;
    }

    // Clear the entire cart
    clearCart() {
        this.items = [];
        this.saveToStorage();
    }

    // Get cart total price
    getTotalPrice() {
        return this.items.reduce((total, item) => {
            // Parse price string to number
            let itemPrice = item.price;
            if (typeof itemPrice === 'string') {
                itemPrice = parseFloat(itemPrice.replace(/[^0-9.]/g, ''));
            }
            return total + (itemPrice * item.quantity);
        }, 0);
    }

    // Get total number of items in cart
    getTotalItems() {
        return this.items.reduce((total, item) => total + item.quantity, 0);
    }

    // Update cart count badge
    updateCartCount() {
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            const count = this.getTotalItems();
            cartCountElement.textContent = count;
            cartCountElement.style.display = count > 0 ? 'flex' : 'none';
        }
    }

    // Get product suggestions based on cart items (cross-selling)
    getSuggestions(product) {
        // Define relationship mappings for related products
        const relationshipMap = {
            'mobile phone': ['phone case', 'screen guard', 'earphone', 'charger', 'power bank'],
            'laptop': ['laptop bag', 'mouse', 'keyboard', 'cooling pad', 'laptop stand'],
            'camera': ['memory card', 'camera bag', 'tripod', 'lens', 'camera battery'],
            'headphone': ['headphone case', 'audio splitter', 'headphone stand'],
            'smartwatch': ['watch strap', 'screen protector', 'charger'],
            'shoe': ['shoe cleaner', 'socks', 'shoe horn', 'insoles'],
            'shirt': ['pants', 'tie', 'belt', 'cufflinks'],
            'dress': ['handbag', 'jewelry', 'scarf']
        };

        // Find suggested categories based on product's category or title
        const productCategory = (product.category || '').toLowerCase();
        const productTitle = (product.title || '').toLowerCase();
        
        // Check direct matches for product category
        for (const [category, suggestions] of Object.entries(relationshipMap)) {
            if (productCategory.includes(category) || productTitle.includes(category)) {
                return {
                    type: 'category',
                    category: category,
                    suggestions: suggestions
                };
            }
        }

        // If no direct match, use generic suggestions
        return {
            type: 'generic',
            suggestions: ['popular items', 'trending now', 'recommended for you']
        };
    }

    // Get the cart items
    getItems() {
        return this.items;
    }
}

// Initialize cart on page load and make it globally available
console.log('Initializing cart...');
try {
    // Make cart a global variable so it can be accessed by event handlers
    window.cart = new Cart();
    // Export cart object for use in other scripts
    window.shopsmartCart = window.cart;
    console.log('Cart initialized successfully', window.shopsmartCart);
} catch (e) {
    console.error('Error initializing cart:', e);
}

// Store cart in sessionStorage before leaving the page
window.addEventListener('beforeunload', function() {
    if (window.shopsmartCart && window.shopsmartCart.getItems().length > 0) {
        console.log('Saving cart to sessionStorage before unload');
        sessionStorage.setItem('shopsmartCart', JSON.stringify(window.shopsmartCart.getItems()));
    }
});

// Add event listener for back/forward navigation
window.addEventListener('popstate', function() {
    // Reload cart from storage when navigating with browser buttons
    if (window.shopsmartCart) {
        console.log('Reloading cart from storage due to navigation');
        window.shopsmartCart.loadFromStorage();
        window.shopsmartCart.updateCartCount();
    }
}); 