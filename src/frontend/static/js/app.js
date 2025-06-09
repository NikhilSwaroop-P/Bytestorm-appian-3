document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatMessages = document.getElementById('chatMessages');
    const uploadBtn = document.getElementById('uploadBtn');
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const removeImage = document.getElementById('removeImage');
    const productsContainer = document.getElementById('productsContainer');
    const themeToggle = document.getElementById('themeToggle');
    const chatbotContainer = document.getElementById('chatbotContainer');
    const collapseBtn = document.getElementById('collapseBtn');
    const helpButton = document.getElementById('helpButton');
    const helpBox = document.getElementById('helpBox');
    const closeHelp = document.getElementById('closeHelp');
    const sortingContainer = document.getElementById('sortingContainer');
    const sortingDropdown = document.getElementById('sortingDropdown');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const startShoppingBtn = document.getElementById('startShoppingBtn');
    const categoryPills = document.querySelectorAll('.category-pill');
    const recentlyViewedSection = document.getElementById('recentlyViewedSection');
    const recentlyViewedProducts = document.getElementById('recentlyViewedProducts');
    
    // Create a container for suggested questions that will appear after user messages
    let suggestedQuestionsContainer = document.createElement('div');
    suggestedQuestionsContainer.className = 'suggested-queries-container';
    suggestedQuestionsContainer.style.display = 'none';
    suggestedQuestionsContainer.innerHTML = `
        <div class="suggested-queries-header">Try searching for:</div>
        <div class="suggested-queries-list"></div>
    `;
    chatMessages.parentNode.insertBefore(suggestedQuestionsContainer, chatMessages.nextSibling);
    
    // Add CSS styles for suggested questions
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .suggested-queries-container {
            padding: 10px 20px;
            background-color: var(--secondary-color);
            border-top: 1px solid var(--divider-color);
        }
        .suggested-queries-header {
            font-size: 13px;
            font-weight: 500;
            color: var(--primary-color);
            margin-bottom: 8px;
        }
        .suggested-queries-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .suggested-query {
            background-color: var(--bg-color);
            padding: 8px 12px;
            border-radius: 18px;
            font-size: 14px;
            color: var(--text-color);
            cursor: pointer;
            border: 1px solid var(--border-color);
            transition: all 0.2s ease;
            text-align: left;
            white-space: nowrap;
        }
        .suggested-query:hover {
            background-color: var(--primary-color);
            color: white;
        }
        /* Tags display styling */
        .tags-filter {
            display: flex;
            flex-direction: column;
            padding: 12px 15px;
            background-color: var(--card-bg);
            border-radius: 6px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            width: 100%;
        }
        .tags-header {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-color);
            margin-bottom: 8px;
        }
        .tags-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        .filter-tag {
            background-color: rgba(var(--primary-color-rgb), 0.1);
            color: var(--primary-color);
            padding: 5px 12px;
            border-radius: 16px;
            font-size: 13px;
            font-weight: 400;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid rgba(var(--primary-color-rgb), 0.2);
        }
        .filter-tag:hover, .filter-tag.active {
            background-color: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }
        /* Product tags styling - keeping for reference but not using anymore */
        .product-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }
        .product-tag {
            background-color: rgba(var(--primary-color-rgb), 0.1);
            color: var(--primary-color);
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .product-description-hover .product-tags {
            margin: 10px 0;
        }
    `;
    document.head.appendChild(styleElement);
    
    // Create reset button
    const resetButton = document.createElement('button');
    resetButton.id = 'resetSearchBtn';
    resetButton.innerHTML = '<i class="fas fa-trash"></i> Clear search';
    resetButton.className = 'reset-search-btn';
    resetButton.style.marginLeft = '10px';
    resetButton.style.padding = '8px 12px';
    resetButton.style.backgroundColor = '#dc3545';
    resetButton.style.color = 'white';
    resetButton.style.border = 'none';
    resetButton.style.borderRadius = '4px';
    resetButton.style.cursor = 'pointer';
    resetButton.style.display = 'none'; // Hide by default
    
    // Add reset button to sorting container
    sortingContainer.appendChild(resetButton);
    
    // Recently viewed products tracking
    let recentlyViewed = [];
    const MAX_RECENT_ITEMS = 8;
    
    // Category pills event listeners
    categoryPills.forEach(pill => {
        pill.addEventListener('click', function() {
            // Only do something if image is already uploaded
            if (!imagePreview.classList.contains('hidden')) {
                const category = this.textContent.trim();
                userInput.value = `Show me ${category} products`;
                chatForm.dispatchEvent(new Event('submit'));
                
                // Highlight the selected pill
                categoryPills.forEach(p => p.classList.remove('active'));
                this.classList.add('active');
            } else {
                // Prompt to upload image first
                const messageElement = document.createElement('div');
                messageElement.className = 'message bot-message';
                messageElement.innerHTML = `
                    <div class="message-content">
                        Please upload an image first, then I can help you find ${this.textContent.trim()} products.
                    </div>
                `;
                chatMessages.appendChild(messageElement);
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                // Highlight the upload button with pulse animation
                uploadBtn.classList.add('pulse-animation');
                setTimeout(() => {
                    uploadBtn.classList.remove('pulse-animation');
                }, 2000);
            }
        });
    });
    
    // Reset button event listener
    resetButton.addEventListener('click', function() {
        // Clear localStorage data
        localStorage.removeItem('shopsmartProducts');
        localStorage.removeItem('shopsmartIndices');
        localStorage.removeItem('shopsmartChatMessages');
        localStorage.removeItem('shopsmartSortOrder');
        
        // Reset state variables
        currentProducts = [];
        retrievedIdx = null;
        currentSortOrder = 'default';
        lastUserQuery = '';
        
        // Clear chat messages
        chatMessages.innerHTML = '';
        
        // Hide suggested queries
        suggestedQuestionsContainer.style.display = 'none';
        
        // Reset UI
        productsContainer.innerHTML = '';
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <div class="empty-state-animation">
                <lottie-player src="https://assets3.lottiefiles.com/packages/lf20_yvkrcogf.json" background="transparent" speed="1" style="width: 200px; height: 200px;" loop autoplay></lottie-player>
            </div>
            <h3>Ready to discover amazing products?</h3>
            <p>Upload an image or ask a question to find what you're looking for</p>
            <div class="empty-state-steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-text">Upload a product image</div>
                </div>
                <div class="step-arrow"><i class="fas fa-arrow-right"></i></div>
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-text">Refine with text queries</div>
                </div>
                <div class="step-arrow"><i class="fas fa-arrow-right"></i></div>
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-text">Discover perfect matches</div>
                </div>
            </div>
        `;
        productsContainer.appendChild(emptyState);
        
        // Add welcome message
        addMessage('Hello! I need an image to help you find products. Please upload an image to start.', 'bot');
        
        // Hide sorting options and reset button
        sortingContainer.style.display = 'none';
        resetButton.style.display = 'none';
        
        // Clear userInput if there's text
        userInput.value = '';
        
        // Reset recently viewed section
        recentlyViewed = [];
        updateRecentlyViewedSection();
        
        // Reset to initial state with the backend too
        fetch('/api/reset', {
            method: 'POST'
        }).catch(error => {
            console.error('Error resetting search state:', error);
        });
    });
    
    // Set placeholder image
    const PLACEHOLDER_IMAGE = 'https://via.placeholder.com/150?text=No+Image';
    
    // State
    let currentImageFile = null;
    let retrievedIdx = null;
    let isReset = true;
    let currentProducts = [];
    let currentSortOrder = 'default';
    let lastUserQuery = ''; // Track the last user query for suggested questions
    
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
    
    // Load saved state from localStorage
    function loadSavedState() {
        // Load chat messages
        const savedMessages = localStorage.getItem('shopsmartChatMessages');
        if (savedMessages) {
            try {
                const messages = JSON.parse(savedMessages);
                
                // Clear existing messages
                chatMessages.innerHTML = '';
                
                // Rebuild messages
                messages.forEach(msg => {
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${msg.sender}-message`;
                    
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'message-content';
                    contentDiv.innerHTML = msg.content;
                    
                    messageDiv.appendChild(contentDiv);
                    chatMessages.appendChild(messageDiv);
                });
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } catch (error) {
                console.error('Error restoring chat messages:', error);
                // Add a default welcome message if there's an error
                addMessage('Hello! I need an image to help you find products. Please upload an image to start, then you can refine your search with text.', 'bot');
            }
        } else {
            // Add default welcome message if no saved messages
            addMessage('Hello! I need an image to help you find products. Please upload an image to start, then you can refine your search with text.', 'bot');
        }
        
        // Load products and display them
        const savedProducts = localStorage.getItem('shopsmartProducts');
        const savedIndices = localStorage.getItem('shopsmartIndices');
        
        if (savedProducts) {
            try {
                currentProducts = JSON.parse(savedProducts);
                if (savedIndices) {
                    retrievedIdx = JSON.parse(savedIndices);
                }
                
                if (currentProducts.length > 0) {
                    // Load sort order
                    const savedSortOrder = localStorage.getItem('shopsmartSortOrder');
                    if (savedSortOrder) {
                        currentSortOrder = savedSortOrder;
                        sortingDropdown.value = currentSortOrder;
                    }
                    
                    // Show sorting options
                    sortingContainer.style.display = 'flex';
                    resetButton.style.display = 'inline-block';
                    
                    // Update product grid
                    updateProductGrid();
                } else {
                    // Show empty state
                    showEmptyState();
                }
            } catch (error) {
                console.error('Error restoring saved products:', error);
                showEmptyState();
            }
        } else {
            showEmptyState();
        }
    }
    
    function showEmptyState() {
        productsContainer.innerHTML = '';
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <div class="empty-state-animation">
                <lottie-player src="https://assets3.lottiefiles.com/packages/lf20_yvkrcogf.json" background="transparent" speed="1" style="width: 200px; height: 200px;" loop autoplay></lottie-player>
            </div>
            <h3>Ready to discover amazing products?</h3>
            <p>Upload an image or ask a question to find what you're looking for</p>
            <div class="empty-state-steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <div class="step-text">Upload a product image</div>
                </div>
                <div class="step-arrow"><i class="fas fa-arrow-right"></i></div>
                <div class="step">
                    <div class="step-number">2</div>
                    <div class="step-text">Refine with text queries</div>
                </div>
                <div class="step-arrow"><i class="fas fa-arrow-right"></i></div>
                <div class="step">
                    <div class="step-number">3</div>
                    <div class="step-text">Discover perfect matches</div>
                </div>
            </div>
        `;
        productsContainer.appendChild(emptyState);
        
        // Hide sorting options
        sortingContainer.style.display = 'none';
        resetButton.style.display = 'none';
    }
    
    // Save current state to localStorage
    function saveCurrentState() {
        // Save products and indices
        if (currentProducts && currentProducts.length > 0) {
            localStorage.setItem('shopsmartProducts', JSON.stringify(currentProducts));
        }
        
        if (retrievedIdx) {
            localStorage.setItem('shopsmartIndices', JSON.stringify(retrievedIdx));
        }
        
        // Save chat messages
        const savedMessages = [];
        const messageElements = chatMessages.querySelectorAll('.message');
        
        messageElements.forEach(msg => {
            const content = msg.querySelector('.message-content').innerHTML;
            const sender = msg.classList.contains('user-message') ? 'user' : 'bot';
            const imageElement = msg.querySelector('img');
            const imageUrl = imageElement ? imageElement.src : null;
            
            savedMessages.push({
                content,
                sender,
                imageUrl
            });
        });
        
        localStorage.setItem('shopsmartChatMessages', JSON.stringify(savedMessages));
        
        // Save current sort order
        localStorage.setItem('shopsmartSortOrder', currentSortOrder);
    }
    
    // Load saved state on page load
    loadSavedState();
    
    // Save state when user navigates away
    window.addEventListener('beforeunload', saveCurrentState);
    
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
    
    // Function to update product grid based on available space
    function updateProductGrid() {
        const containerWidth = productsContainer.offsetWidth;
        const baseCardWidth = 220; // Base card width including padding and margins
        
        // Calculate how many cards can fit per row
        let cardsPerRow = Math.floor(containerWidth / baseCardWidth);
        
        // Cap at 5 cards per row maximum, minimum 1
        cardsPerRow = Math.min(Math.max(cardsPerRow, 1), 5);
        
        // Update card width to fit exactly the number of cards per row
        // Each card has 2% total margin (1% on each side)
        const cardWidthPercent = (100 / cardsPerRow) - 2;
        document.documentElement.style.setProperty('--cards-per-row', cardsPerRow);
        document.documentElement.style.setProperty('--card-width-percent', cardWidthPercent + '%');
    }
    
    // Collapse functionality
    collapseBtn.addEventListener('click', function() {
        chatbotContainer.classList.toggle('chatbot-collapsed');
        
        // Update product grid after collapse animation completes
        setTimeout(updateProductGrid, 300);
    });
    
    // Help box functionality
    helpButton.addEventListener('click', function() {
        helpBox.classList.toggle('visible');
    });
    
    closeHelp.addEventListener('click', function() {
        helpBox.classList.remove('visible');
    });
    
    // Call updateProductGrid on window resize
    window.addEventListener('resize', updateProductGrid);
    
    // Initialize grid on page load
    updateProductGrid();
    
    // Event Listeners
    chatForm.addEventListener('submit', handleChatSubmit);
    uploadBtn.addEventListener('click', () => imageUpload.click());
    imageUpload.addEventListener('change', handleImageUpload);
    removeImage.addEventListener('click', clearImagePreview);
    
    // Add sorting event listener
    sortingDropdown.addEventListener('change', function() {
        currentSortOrder = this.value;
        sortProducts(currentProducts);
    });
    
    // Display bot typing indication
    function showBotTyping() {
        const typingElement = document.createElement('div');
        typingElement.className = 'message bot-message typing';
        typingElement.innerHTML = `
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        typingElement.id = 'botTyping';
        chatMessages.appendChild(typingElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Remove bot typing indication
    function hideBotTyping() {
        const typingElement = document.getElementById('botTyping');
        if (typingElement) {
            typingElement.remove();
        }
    }
    
    // Render star ratings based on a number (0-5)
    function renderStars(rating) {
        const fullStars = Math.floor(rating);
        const halfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
        
        let starsHTML = '';
        // Full stars
        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<i class="fas fa-star"></i>';
        }
        // Half star if needed
        if (halfStar) {
            starsHTML += '<i class="fas fa-star-half-alt"></i>';
        }
        // Empty stars
        for (let i = 0; i < emptyStars; i++) {
            starsHTML += '<i class="far fa-star"></i>';
        }
        
        return starsHTML;
    }
    
    // Add a new message to the chat
    function addMessage(text, sender, imageUrl = null) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        let messageContent = `<div class="message-content">`;
        
        if (imageUrl) {
            messageContent += `<img src="${imageUrl}" alt="Uploaded image" onerror="this.onerror=null; this.src='${PLACEHOLDER_IMAGE}';">`;
        }
        
        messageContent += `${text}</div>`;
        messageElement.innerHTML = messageContent;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Handle file upload
    function handleImageUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        currentImageFile = file;
        const fileReader = new FileReader();
        
        fileReader.onload = function(e) {
            previewImg.src = e.target.result;
            imagePreview.classList.remove('hidden');
        };
        
        fileReader.readAsDataURL(file);
    }
    
    // Clear image preview
    function clearImagePreview() {
        imagePreview.classList.add('hidden');
        imageUpload.value = '';
        currentImageFile = null;
    }
    
    // Handle image error by replacing with placeholder
    function handleImageError(img) {
        console.log('Image failed to load:', img.src);
        img.onerror = null; // Prevent infinite loop
        img.src = PLACEHOLDER_IMAGE;
    }
    
    // Get suggested search queries based on user query
    async function fetchSuggestedQuestions(query) {
        try {
            const response = await fetch('/api/suggest-questions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get suggestions');
            }
            
            const data = await response.json();
            
            if (data.success && data.suggestions && data.suggestions.length > 0) {
                return data.suggestions;
            } else {
                return [];
            }
        } catch (error) {
            console.error('Error fetching suggested queries:', error);
            return [];
        }
    }
    
    // Display suggested queries in the UI
    function displaySuggestedQuestions(suggestions) {
        const suggestionsList = document.querySelector('.suggested-queries-list');
        
        if (!suggestions || suggestions.length === 0) {
            suggestedQuestionsContainer.style.display = 'none';
            return;
        }
        
        // Clear previous suggestions
        suggestionsList.innerHTML = '';
        
        // Add new suggestions
        suggestions.forEach(suggestion => {
            const button = document.createElement('button');
            button.className = 'suggested-query';
            button.textContent = suggestion;
            
            // When clicked, fill the input with the suggestion and submit
            button.addEventListener('click', () => {
                userInput.value = suggestion;
                chatForm.dispatchEvent(new Event('submit'));
            });
            
            suggestionsList.appendChild(button);
        });
        
        // Show suggestions container
        suggestedQuestionsContainer.style.display = 'block';
    }
    
    // Handle checkout process
    async function handleCheckout(product) {
        // Show loading in chat
        addMessage(`Processing your purchase for ${product.title || 'this product'}...`, 'bot');
        
        try {
            // Call the checkout API
            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    product_id: product.id,
                    product_data: product  // Pass the complete product data to be stored in session
                })
            });
            
            if (!response.ok) {
                throw new Error('Checkout process failed');
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Open Stripe checkout in a new window/tab
                window.open(data.checkout_url, '_blank');
                addMessage('You have been redirected to the payment page. Complete your purchase there.', 'bot');
            } else {
                throw new Error(data.error || 'Checkout process failed');
            }
            
        } catch (error) {
            console.error('Checkout error:', error);
            addMessage('Sorry, there was an error processing your checkout. Please try again.', 'bot');
        }
    }
    
    // Handle buy now button click
    function handleBuyNowClick(event, product) {
        event.preventDefault();
        event.stopPropagation();
        
        // Show confirmation in chat
        addMessage(`You selected: ${product.title || 'Product'}`, 'user');
        
        // Process checkout
        handleCheckout(product);
    }
    
    // Handle add to cart button click
    function handleAddToCartClick(event, product) {
        event.preventDefault();
        event.stopPropagation();
        
        // Add to cart
        if (window.shopsmartCart) {
            window.shopsmartCart.addItem(product);
            
            // Show confirmation in chat
            addMessage(`Added to cart: ${product.title || 'Product'}`, 'user');
            
            // Update cart count
            const cartCountElement = document.getElementById('cart-count');
            if (cartCountElement) {
                const count = window.shopsmartCart.getTotalItems();
                cartCountElement.textContent = count;
                cartCountElement.style.display = count > 0 ? 'flex' : 'none';
            }
        } else {
            addMessage('Sorry, the cart functionality is not available.', 'bot');
        }
    }
    
    // Sort products based on selected option
    function sortProducts(products) {
        if (!products || products.length === 0) return products;
        
        let sortedProducts = [...products];
        
        switch(currentSortOrder) {
            case 'price_asc':
                sortedProducts.sort((a, b) => {
                    const priceA = parseFloat(a.price.replace(/[^0-9.]/g, ''));
                    const priceB = parseFloat(b.price.replace(/[^0-9.]/g, ''));
                    return priceA - priceB;
                });
                break;
            case 'price_desc':
                sortedProducts.sort((a, b) => {
                    const priceA = parseFloat(a.price.replace(/[^0-9.]/g, ''));
                    const priceB = parseFloat(b.price.replace(/[^0-9.]/g, ''));
                    return priceB - priceA;
                });
                break;
            case 'rating_desc':
                sortedProducts.sort((a, b) => {
                    const ratingA = parseFloat(a.rating || 0);
                    const ratingB = parseFloat(b.rating || 0);
                    return ratingB - ratingA;
                });
                break;
            case 'rating_count_desc':
                sortedProducts.sort((a, b) => {
                    const countA = parseInt(a.rating_count || 0);
                    const countB = parseInt(b.rating_count || 0);
                    return countB - countA;
                });
                break;
            case 'default':
            default:
                // Keep original order
                break;
        }
        
        displayProducts(sortedProducts);
        return sortedProducts;
    }
    
    async function handleChatSubmit(event) {
        event.preventDefault();
        
        const text = userInput.value.trim();
        if (!text && !currentImageFile) return;
        
        // Save the user query for suggestions if it's not empty
        if (text) {
            lastUserQuery = text;
        }
        
        // Clear input
        userInput.value = '';
        
        // Add user message to chat
        if (text) {
            addMessage(text, 'user');
        }
        
        // Hide suggested queries when a new message is sent
        suggestedQuestionsContainer.style.display = 'none';
        
        // Show bot typing indicator
        showBotTyping();
        
        try {
            // Create form data for uploading
            const formData = new FormData();
            if (text) {
                formData.append('text', text);
            }
            
            // Append any uploaded image
            if (currentImageFile) {
                formData.append('image', currentImageFile);
                
                // Display image in chat if not already shown
                if (imagePreview.classList.contains('hidden') === false) {
                    addMessage('', 'user', previewImg.src);
                    clearImagePreview();
                }
            }
            
            // Append previous search context if applicable
            if (retrievedIdx !== null) {
                formData.append('retrieved_idx', JSON.stringify(retrievedIdx));
                formData.append('reset', 'false');
            }
            
            // Send the search request
            const response = await fetch('/api/search', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error('Search failed');
            }
            
            const data = await response.json();
            
            if (data.success) {
            retrievedIdx = data.indices;
                const products = data.products;
                currentProducts = products;
            
                // Hide bot typing indicator
            hideBotTyping();
            
                if (products && products.length > 0) {
                    // Show sorting options if we have products
                    sortingContainer.style.display = 'flex';
                    
                    // Show reset button
                    resetButton.style.display = 'inline-block';
                    
                    // Add message about search results
                    addMessage(`Here are ${products.length} products that match your search:`, 'bot');
                    
                    // Display the products
                    sortProducts(products);
                    
                    // Save the updated state to localStorage
                    saveCurrentState();
                    
                    // Fetch and display suggested queries based on the user's query
                    if (lastUserQuery) {
                        try {
                            const suggestions = await fetchSuggestedQuestions(lastUserQuery);
                            if (suggestions && suggestions.length > 0) {
                                displaySuggestedQuestions(suggestions);
                            }
                        } catch (err) {
                            console.error("Error fetching suggested queries:", err);
                        }
                    }
                } else {
                    // Hide sorting if no products
                    sortingContainer.style.display = 'none';
                    
                    // Hide reset button if no products
                    resetButton.style.display = 'none';
                    
                    addMessage('Sorry, I couldn\'t find any products matching your search. Please try again with different criteria.', 'bot');
                    
                    // Save chat messages even if no products found
                    saveCurrentState();
                }
            } else {
                hideBotTyping();
                addMessage('Sorry, there was an error processing your search. Please try again.', 'bot');
                
                // Save chat messages even if there was an error
                saveCurrentState();
            }
            
        } catch (error) {
            console.error('Search error:', error);
            hideBotTyping();
            addMessage('Sorry, there was an error processing your request. Please try again.', 'bot');
            
            // Save chat messages even if there was an error
            saveCurrentState();
        }
    }
    
    function displayProducts(products) {
        // Clear current products
        productsContainer.innerHTML = '';
        
        if (!products || products.length === 0) {
            // Show empty state
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.innerHTML = `
                <div class="empty-state-animation">
                    <lottie-player src="https://assets3.lottiefiles.com/packages/lf20_yvkrcogf.json" background="transparent" speed="1" style="width: 200px; height: 200px;" loop autoplay></lottie-player>
                </div>
                <h3>No products found</h3>
                <p>Try searching with different criteria</p>
            `;
            productsContainer.appendChild(emptyState);
            return;
        }
        
        // Create a row to hold sorting and tags together
        const filterRow = document.createElement('div');
        filterRow.className = 'products-filter-row';
        
        // Add the sortingContainer to the filter row
        if (sortingContainer) {
            sortingContainer.style.display = 'flex';
            filterRow.appendChild(sortingContainer);
        }
        
        // Collect all unique tags from products
        const allTags = new Set();
        products.forEach(product => {
            if (product.tags && Array.isArray(product.tags)) {
                product.tags.forEach(tag => allTags.add(tag));
            }
        });
        
        // Create tags container if we have tags
        if (allTags.size > 0) {
            const tagsContainer = document.createElement('div');
            tagsContainer.className = 'tags-filter';
            tagsContainer.innerHTML = '<div class="tags-header">Popular filters:</div>';
            
            const tagsListContainer = document.createElement('div');
            tagsListContainer.className = 'tags-list';
            
            // Add tags to container
            Array.from(allTags).forEach(tag => {
                const tagElement = document.createElement('span');
                tagElement.className = 'filter-tag';
                tagElement.textContent = tag;
                
                // Add click event to append or remove tag to/from prompt text input
                tagElement.addEventListener('click', function() {
                    this.classList.toggle('active');
                    
                    // Get reference to userInput element
                    const userInput = document.getElementById('userInput');
                    
                    // Format the tag text to append
                    const tagText = `, ${tag} is optional`;
                    
                    // Check if the tagText is already in the input
                    if (userInput.value.includes(tagText)) {
                        // Tag is already in the input, remove it
                        userInput.value = userInput.value.replace(tagText, '');
                        
                        // Handle edge case: if we removed a tag that was at the beginning and started with a comma
                        if (userInput.value.startsWith(', ')) {
                            userInput.value = userInput.value.substring(2);
                        }
                        
                        // Clean up any double commas that might result from removing a middle tag
                        userInput.value = userInput.value.replace(/,\s*,/g, ',');
                        
                        // Clean up trailing comma
                        userInput.value = userInput.value.replace(/,\s*$/, '');
                    } else {
                        // Tag is not in the input, add it
                        if (userInput.value.trim() !== '') {
                            userInput.value += tagText;
                        } else {
                            userInput.value = tag + ' is optional'; // No leading comma for first tag
                        }
                    }
                    
                    // Focus on the input after modifying
                    userInput.focus();
                });
                
                tagsListContainer.appendChild(tagElement);
            });
            
            tagsContainer.appendChild(tagsListContainer);
            filterRow.appendChild(tagsContainer);
        }
        
        // Add the filter row to the products container
        productsContainer.appendChild(filterRow);
        
        // Create a grid container for products
        const productsGrid = document.createElement('div');
        productsGrid.className = 'products-grid';
        
        // Add products to grid
        products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'product-card';
            card.dataset.id = product.id;
            
            // Get image URL from various possible sources
            const imageUrl = product.image_url || product.image_path || PLACEHOLDER_IMAGE;
            
            // Create card HTML (removed tags from individual cards)
            card.innerHTML = `
                <img src="${imageUrl}" alt="${product.title}" class="product-image" onerror="this.onerror=null; this.src='${PLACEHOLDER_IMAGE}';">
                <div class="product-details">
                    <h3 class="product-title">${product.title}</h3>
                    <div class="product-rating">
                        <div class="stars">${renderStars(product.rating || 0)}</div>
                        <span class="rating-count">(${product.rating_count || 0})</span>
                    </div>
                    <div class="product-price-container">
                        <span class="current-price">${product.price}</span>
                        ${product.actual_price ? `<span class="original-price">${product.actual_price}</span>` : ''}
                        ${product.discount ? `<span class="discount-badge">-${product.discount}%</span>` : ''}
                    </div>
                </div>
                <div class="product-meta">
                    <div class="product-actions">
                        <button class="add-to-cart-btn">Add to Cart</button>
                        <button class="buy-now-btn">Buy Now</button>
                    </div>
                </div>
                <div class="product-description-hover">
                    <h4>${product.title}</h4>
                    <p>${product.description || 'No description available'}</p>
                    <div class="hover-actions">
                        <button class="add-to-cart-btn">Add to Cart</button>
                        <button class="buy-now-btn">Buy Now</button>
                    </div>
                </div>
            `;
            
            // Add click event to view product details
            card.addEventListener('click', () => {
                // Track view in analytics
                trackProductView(product);
                
                // Navigate to product page
                window.location.href = `/product/${product.id}`;
            });
            
            // Add event listeners for add to cart and buy now buttons
            const buyNowButtons = card.querySelectorAll('.buy-now-btn');
            buyNowButtons.forEach(btn => {
                btn.addEventListener('click', (e) => handleBuyNowClick(e, product));
            });
            
            const addToCartButtons = card.querySelectorAll('.add-to-cart-btn');
            addToCartButtons.forEach(btn => {
                btn.addEventListener('click', (e) => handleAddToCartClick(e, product));
            });
            
            productsGrid.appendChild(card);
        });
        
        // Add grid to container
        productsContainer.appendChild(productsGrid);
        
        // Track product view for analytics
        function trackProductView(product) {
            fetch('/api/view-product', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    product_id: product.id,
                    product_data: product
                })
            }).catch(error => {
                console.error('Error tracking product view:', error);
            });
        }
    }
    
    // Clear chat button event listener
    clearChatBtn.addEventListener('click', function() {
        // Clear chat messages
        chatMessages.innerHTML = '';
        
        // Hide suggested queries
        suggestedQuestionsContainer.style.display = 'none';
        
        // Add welcome message
        addMessage('Hello! I need an image to help you find products. Please upload an image to start, then you can refine your search with text.', 'bot');
        
        // Save the cleared chat state
        localStorage.removeItem('shopsmartChatMessages');
        
        // Clear userInput if there's text
        userInput.value = '';
    });
}); 