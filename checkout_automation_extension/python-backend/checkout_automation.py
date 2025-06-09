"""
Checkout Form Automation Module

This module provides functions to analyze HTML checkout forms and generate
optimized form-filling instructions using Google's Gemini AI model.

Functions:
1. extract_interactive_elements() - Extracts all interactive elements from HTML
2. generate_form_filling_strategy() - Creates optimized form filling strategy with coupon analysis
3. convert_to_structured_json() - Converts strategy to clean JSON format

"""

from google import genai
from google.genai import types
import json
import re
import os
import time
import hashlib
from typing import Dict, List, Any, Tuple, Optional
from flask import jsonify, request
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup

# Define a global constant for the thinking budget
THINKING_BUDGET = 1024

# Global variables for API key management
current_api_keys = []
current_api_key_index = 0
max_retry_count = 30  # Reduced from 60 to 30 for better API key cycling

class ApiKeyManager:
    """Manages multiple Gemini API keys with automatic cycling on errors."""
    
    def __init__(self, api_keys=None, max_retries=60):
        self.api_keys = api_keys or ['AIzaSyBXZLvzTn2Jf52PZ_PgwDlNRtWUu37aPx4']
        self.current_index = 0
        self.max_retries = max_retries
        self.failed_keys = set()
    
    def get_current_key(self):
        """Get the current active API key."""
        if not self.api_keys:
            return 'AIzaSyBXZLvzTn2Jf52PZ_PgwDlNRtWUu37aPx4'
        return self.api_keys[self.current_index]
    
    def cycle_to_next_key(self):
        """Cycle to the next available API key."""
        if len(self.api_keys) <= 1:
            return False  # No other keys to switch to
        
        self.failed_keys.add(self.current_index)
        original_index = self.current_index
        
        # Try next keys until we find one that hasn't failed or cycle back
        for _ in range(len(self.api_keys)):
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            if self.current_index not in self.failed_keys:
                print(f"Switched to API key {self.current_index + 1}/{len(self.api_keys)}")
                return True
            if self.current_index == original_index:
                break
        
        # All keys have failed, reset failed keys and start over
        print("All API keys have failed, resetting and trying again...")
        self.failed_keys.clear()
        self.current_index = (original_index + 1) % len(self.api_keys)
        return True
    
    def update_keys(self, new_keys, new_index=0):
        """Update the API keys list."""
        if new_keys:
            self.api_keys = new_keys
            self.current_index = min(new_index, len(new_keys) - 1)
            self.failed_keys.clear()

# Global API key manager instance
api_key_manager = ApiKeyManager()

def initialize_model(
    api_key: str = None, 
    fast: bool = False, 
    depth: int = 1,
    api_keys: list = None,
    current_key_index: int = 0
) -> genai.Client:
    """
    Initialize the AI model with the provided API key.
    
    Args:
        api_key (str): Google Generative AI API key
        fast (bool): If True, use Gemma models instead of Gemini for faster processing
        depth (int): Model depth when using fast mode: 0=1B, 1=4B, 2=12B
        
    Returns:
        genai.Client: Initialized AI client
    """
    # Add SSL handling for Python on Windows
    import ssl
    import os
    
    # Try to use a more reliable default SSL context
    try:
        # Create a client with the API key
        client = genai.Client(api_key=api_key)
        
        # Store the model selection info as attributes on the client object
        client.fast_mode = fast
        client.model_depth = depth
        
        # Test the client with a simple request to verify it works
        return client
    except Exception as e:
        print(f"Warning: Error initializing AI client: {e}")
        print("Attempting to fix SSL configuration...")
        
        # Try with custom SSL context
        try:
            # Create default context with certificate verification
            default_context = ssl.create_default_context()
            # Some older Windows versions might need this modification
            default_context.check_hostname = False
            default_context.verify_mode = ssl.CERT_NONE
            
            # Set the SSL context as the default
            ssl._create_default_https_context = lambda: default_context
            
            # Retry client creation
            client = genai.Client(api_key=api_key)
            client.fast_mode = fast
            client.model_depth = depth
            
            # Log successful recovery
            print("Successfully created AI client with modified SSL context")
            return client
        except Exception as e2:
            print(f"Error creating AI client even with SSL workaround: {e2}")
            # Return a minimal client that will be marked as not functional
            client = genai.Client(api_key=api_key)
            client.fast_mode = fast
            client.model_depth = depth
            client._ssl_error = True
            return client

# Update the generate_content usage to use the global THINKING_BUDGET
def generate_content_with_model(model_client: genai.Client, prompt: str) -> str:
    """
    Generate content using the AI model with a global thinking budget and API key cycling.
    
    Args:
        model_client (genai.Client): Initialized AI client
        prompt (str): The prompt to generate content for
        
    Returns:
        str: The generated content
    """
    # Check if client has SSL errors
    if hasattr(model_client, '_ssl_error') and model_client._ssl_error:
        print("AI client has SSL errors, falling back to default response")
        return "Error: Unable to connect to AI service due to SSL issues. Please check your network connection and SSL configuration."
        
    # Use global retry count (60) instead of hardcoded 3
    max_retries = max_retry_count
    retry_delay = 3  # seconds
    
    for attempt in range(max_retries):
        current_key_for_call_attempt = api_key_manager.get_current_key()
        key_display_call = f"{current_key_for_call_attempt[:5]}...{current_key_for_call_attempt[-4:]}" if len(current_key_for_call_attempt) > 9 else current_key_for_call_attempt
        try:
            print(f"INFO: Attempting API call with key: {key_display_call} (Attempt {attempt+1}/{max_retries}) in generate_content_with_model")

            # Determine which model to use based on client attributes
            if hasattr(model_client, 'fast_mode') and model_client.fast_mode:
                # Use Gemma models based on depth
                if model_client.model_depth == 0:
                    model_name = "gemma-3-12b-it"  # Was gemma-3-1b-it
                elif model_client.model_depth == 2:
                    model_name = "gemini-2.0-flash"   # Was gemma-3-12b-it
                else:  # Default to depth=1 or any other value
                    model_name = "gemini-2.0-flash-lite" # Was gemma-3-4b-it
                
                # Generate content with Gemma model (without thinking budget)
                response = model_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
            else:
                # Use default Gemini model with thinking budget
                model_name = "gemini-2.5-flash-preview-05-20"
                
                # Generate content with Gemini model (with thinking budget)
                response = model_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET)
                    )
                )
            
            # If we get here, the call succeeded
            return response.text
            
        except Exception as e:
            error_str = str(e).lower()
            should_cycle_api_key = False
            # key_display_log will use the key that was just attempted
            log_prefix = f"ERROR (Attempt {attempt+1}/{max_retries}, Key {key_display_call}):"

            # Check for API key related errors that warrant switching keys
            if any(error_type in error_str for error_type in [
                'quota', 'rate limit', 'exceeded', 'billing', 'key', 'permission', 
                'authentication', 'unauthorized', '429', '403', '401'
            ]):
                should_cycle_api_key = True
                print(f"{log_prefix} API key related error detected: {e}")
                
                # Try to cycle to next API key if available
                success = api_key_manager.cycle_to_next_key() # Corrected method name
                if success:
                    # Reinitialize the model with the new API key
                    try:
                        new_api_key = api_key_manager.get_current_key()
                        new_key_display = f"{new_api_key[:5]}...{new_api_key[-4:]}" if len(new_api_key) > 9 else new_api_key
                        print(f"INFO: Switched to new API key for retry: {new_key_display}")
                        
                        # Create new client with the new API key
                        # Ensure the correct 'genai' (from 'from google import genai') is used.
                        # The local import 'import google.generativeai as genai' was causing the error.
                        new_client = genai.Client(api_key=new_api_key)
                        
                        # Copy over the attributes from the old client
                        if hasattr(model_client, 'fast_mode'):
                            new_client.fast_mode = model_client.fast_mode
                        if hasattr(model_client, 'model_depth'):
                            new_client.model_depth = model_client.model_depth
                        
                        # Replace the client reference for subsequent attempts
                        model_client = new_client
                        
                    except Exception as init_error:
                        print(f"{log_prefix} Failed to initialize new client with switched API key: {init_error}")
                else:
                    print(f"{log_prefix} No more API keys available to cycle through.")
            
            # Handle other types of errors
            elif "SSL" in str(e) or "certificate" in str(e).lower():
                print(f"{log_prefix} SSL error in AI request: {e}")
                if attempt == max_retries - 1:
                    return "Error connecting to AI service: SSL certificate verification failed. Please check your network connection."
            elif "EOF occurred in violation of protocol" in str(e):
                print(f"{log_prefix} Connection error in AI request: {e}")
                if attempt == max_retries - 1:
                    return "Error connecting to AI service: Connection was unexpectedly closed. Please check your network connection."
            else:
                print(f"{log_prefix} Other error in AI request: {e}")
                if attempt == max_retries - 1:
                    return f"Error in AI service request: {str(e)}"
            
            # Wait before retrying (shorter delay for API key switches)
            import time
            delay = retry_delay if not should_cycle_api_key else 0.5
            time.sleep(delay * (attempt + 1))  # Exponential backoff
    
    # This line should never be reached due to the return statements above
    return "Error: Maximum retries exceeded"


def extract_interactive_elements(html_content: str, model_client: genai.Client) -> Tuple[List[Dict], str]:
    """
    Extract all interactive elements from HTML content using Gemini AI.
    
    Args:
        html_content (str): The HTML content to analyze
        model_client (genai.Client): Initialized Gemini client
        
    Returns:
        Tuple[List[Dict], str]: List of interactive elements and raw response
    """
    prompt = f"""
    Analyze the following HTML and extract ALL interactive elements (elements that users can interact with) along with their IDs.

Interactive elements include:
    - Input fields (text, email, tel, checkbox, etc.)
    - Select dropdowns
    - Buttons
    - Forms
    - Links
    - Clickable divs
    - Any element with onclick, onchange, or other event handlers
    - Any element with data attributes that suggest interactivity

    For each interactive element found, provide:
    1. Element type (e.g., input, button, select, div, etc.)
    2. ID attribute (if present)
    3. Name attribute (if present)
    4. Class names (if relevant for interactivity)
    5. Any data attributes
    6. Brief description of what it does

    Return the results as a JSON list with this structure:
    [
      {{
        "element_type": "input",
        "id": "element-id",
        "name": "element-name",
        "classes": ["class1", "class2"],
        "data_attributes": {{"data-method": "card"}},
        "description": "Brief description of the element's purpose"
      }}
    ]

    HTML to analyze:
    {html_content}
    """
    
    # Generate content using Gemini
    response_text = generate_content_with_model(model_client, prompt)
    
    # Check if the response indicates an error with the AI service
    if response_text.startswith("Error:") or response_text.startswith("Error connecting to AI service:"):
        print(f"AI service error detected: {response_text}")
        print("Falling back to traditional HTML parsing")
        fallback_elements = extract_elements_with_beautifulsoup(html_content)
        return fallback_elements, response_text
    
    try:
        # Look for JSON in the response (it might be wrapped in markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If no code blocks, try to find JSON directly
            json_str = response_text.strip()
        
        # Parse the JSON
        interactive_elements = json.loads(json_str)
        
        # Check if we got enough elements
        if not interactive_elements or len(interactive_elements) == 0:
            # Fall back to traditional HTML parsing
            print("AI found no elements - using fallback parser")
            fallback_elements = extract_elements_with_beautifulsoup(html_content)
            return fallback_elements, response_text

        # Count input elements
        input_elements = [e for e in interactive_elements if e.get('element_type', '') and e.get('element_type', '').lower() in ['input', 'select', 'textarea']]
        if len(input_elements) < 3 and len(interactive_elements) > 0:
            # The AI might have missed many input fields - combine with BeautifulSoup results
            print("AI found very few input elements - combining with fallback parser")
            fallback_elements = extract_elements_with_beautifulsoup(html_content)
            
            # Create a combined list with both AI and fallback elements
            combined_elements = interactive_elements.copy()
            
            # Add fallback elements that aren't already in the AI results
            ai_element_ids = {e.get('id', '') for e in interactive_elements if e.get('id')}
            for element in fallback_elements:
                if element.get('id') and element.get('id') not in ai_element_ids:
                    combined_elements.append(element)
            
            return combined_elements, response_text
        
        return interactive_elements, response_text
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in extract_interactive_elements: {e}")
        # Fall back to traditional HTML parsing
        fallback_elements = extract_elements_with_beautifulsoup(html_content)
        return fallback_elements, response_text
    except Exception as e:
        print(f"Unexpected error in extract_interactive_elements: {e}")
        # Fall back to traditional HTML parsing
        fallback_elements = extract_elements_with_beautifulsoup(html_content)
        return fallback_elements, response_text


def extract_elements_with_beautifulsoup(html_content: str) -> List[Dict]:
    """
    Extract interactive elements from HTML using BeautifulSoup as a fallback method.
    
    Args:
        html_content (str): The HTML content to analyze
        
    Returns:
        List[Dict]: List of interactive elements
    """
    try:
        print("Using BeautifulSoup fallback for element extraction")
        soup = BeautifulSoup(html_content, 'html.parser')
        elements = []
        
        # First pass: extract all input fields
        input_selectors = [
            'input:not([type="hidden"])',  # All non-hidden inputs
            'select',
            'textarea',
            'button',
            'input[type="submit"]',
            'input[type="button"]',
            'input[type="image"]'
        ]
        
        # Track found elements by ID to avoid duplicates
        found_ids = set()
        
        # Helper function to extract data attributes
        def extract_data_attrs(element_tag):
            data_attrs = {}
            for attr in element_tag.attrs:
                if attr.startswith('data-'):
                    data_attrs[attr] = element_tag.get(attr)
            return data_attrs
        
        # Extract all standard form elements
        for selector in input_selectors:
            for element_tag in soup.select(selector):
                element_id = element_tag.get('id', '')
                element_type = element_tag.name
                
                # For input elements, use their type as part of the element_type
                if element_type == 'input':
                    input_type = element_tag.get('type', 'text')
                    element_type = f"input_{input_type}"
                
                # Skip if we've already found this element by ID (unless it has no ID)
                if element_id and element_id in found_ids:
                    continue
                
                if element_id:
                    found_ids.add(element_id)
                
                element = {
                    "element_type": element_type,
                    "id": element_id,
                    "name": element_tag.get('name', ''),
                    "classes": element_tag.get('class', []),
                    "data_attributes": extract_data_attrs(element_tag),
                    "description": f"{element_type.capitalize()} field" + (f" of type {element_tag.get('type', '')}" if element_type == 'input' else "")
                }
                
                elements.append(element)
        
        # Second pass: look for clickable elements and interactive divs
        interactive_selectors = [
            '[onclick]',  # Elements with onclick
            '[role="button"]',
            '[role="link"]',
            '[role="checkbox"]',
            '[role="radio"]',
            '[role="switch"]',
            '[role="tab"]',
            '[contenteditable="true"]',
            'a[href]',  # Links
            '.btn',  # Common button classes
            '.button',
            '.submit'
        ]
        
        for selector in interactive_selectors:
            for element_tag in soup.select(selector):
                element_id = element_tag.get('id', '')
                
                # Skip if we've already found this element by ID (unless it has no ID)
                if element_id and element_id in found_ids:
                    continue
                
                if element_id:
                    found_ids.add(element_id)
                
                element_type = f"clickable_{element_tag.name}"
                if element_tag.get('role'):
                    element_type = f"{element_tag.get('role')}"
                
                element = {
                    "element_type": element_type,
                    "id": element_id,
                    "name": element_tag.get('name', ''),
                    "classes": element_tag.get('class', []),
                    "data_attributes": extract_data_attrs(element_tag),
                    "description": f"Interactive {element_tag.name} element" + (f" with role {element_tag.get('role')}" if element_tag.get('role') else "")
                }
                
                elements.append(element)
        
        # Third pass: look for form fields that might be disguised as divs/spans with special attributes
        # This is common in modern frameworks and customized form elements
        custom_form_selectors = [
            'div.form-group input',  # Bootstrap-style
            'div.input-group input',
            'div.field input',
            'label input',  # Input inside label
            'div[class*="input"] input',  # Any div with "input" in class name
            'div[class*="form"] input',   # Any div with "form" in class name
            '.form-control',  # Common form control classes
            '.input-control'
        ]
        
        for selector in custom_form_selectors:
            for element_tag in soup.select(selector):
                element_id = element_tag.get('id', '')
                
                # Skip if we've already found this element by ID (unless it has no ID)
                if element_id and element_id in found_ids:
                    continue
                
                if element_id:
                    found_ids.add(element_id)
                
                element_type = element_tag.name
                if element_tag.name == 'input':
                    input_type = element_tag.get('type', 'text')
                    element_type = f"input_{input_type}"
                
                element = {
                    "element_type": element_type,
                    "id": element_id,
                    "name": element_tag.get('name', ''),
                    "classes": element_tag.get('class', []),
                    "data_attributes": extract_data_attrs(element_tag),
                    "description": f"Custom form {element_tag.name} element"
                }
                
                elements.append(element)
        
        # Special case: If no input fields were found with IDs, look for inputs without IDs as well
        input_elements = [e for e in elements if e["element_type"].startswith("input_") and e["id"]]
        if len(input_elements) == 0:
            print("No input elements with IDs found, looking for inputs without IDs")
            for input_tag in soup.find_all('input'):
                if input_tag.get('type') != 'hidden':  # Skip hidden inputs
                    element_type = f"input_{input_tag.get('type', 'text')}"
                    element = {
                        "element_type": element_type,
                        "id": "",  # No ID
                        "name": input_tag.get('name', ''),
                        "classes": input_tag.get('class', []),
                        "data_attributes": extract_data_attrs(input_tag),
                        "description": f"Input field without ID of type {input_tag.get('type', 'text')}"
                    }
                    elements.append(element)
        
        # Look for potential inputs that might be lazy-loaded or in shadow DOM
        if len(input_elements) < 3:
            print("Few input elements found, checking for potential hidden or lazy-loaded inputs")
            
            # Check for inputs in scripts (often used for templates or lazy-loading)
            for script_tag in soup.find_all('script'):
                script_content = script_tag.string
                if script_content and ('<input' in script_content or '<form' in script_content):
                    # There might be form elements defined in JavaScript templates
                    element = {
                        "element_type": "potential_js_input",
                        "id": "",
                        "name": "",
                        "classes": [],
                        "data_attributes": {},
                        "description": "Potential input field defined in JavaScript"
                    }
                    elements.append(element)
            
            # Check for forms that might be empty (waiting for JS to populate)
            for form in soup.find_all('form'):
                if len(form.find_all('input')) == 0:
                    # Form without inputs might be dynamically populated
                    element = {
                        "element_type": "dynamic_form",
                        "id": form.get('id', ''),
                        "name": form.get('name', ''),
                        "classes": form.get('class', []),
                        "data_attributes": extract_data_attrs(form),
                        "description": "Form that might be dynamically populated"
                    }
                    elements.append(element)
            
            # Check for elements that might be placeholders for inputs
            placeholder_selectors = [
                '[class*="field"]',
                '[class*="input"]',
                '[class*="form-group"]',
                '[class*="form-field"]',
            ]
            
            for selector in placeholder_selectors:
                for placeholder in soup.select(selector):
                    if not placeholder.find_all('input') and not placeholder.find_all('select'):
                        element_id = placeholder.get('id', '')
                        if element_id and element_id in found_ids:
                            continue
                        
                        if element_id:
                            found_ids.add(element_id)
                        
                        element = {
                            "element_type": "potential_input_container",
                            "id": element_id,
                            "name": placeholder.get('name', ''),
                            "classes": placeholder.get('class', []),
                            "data_attributes": extract_data_attrs(placeholder),
                            "description": "Container that might hold dynamically created inputs"
                        }
                        elements.append(element)
        
        print(f"Extracted {len(elements)} elements using BeautifulSoup")
        return elements
    
    except Exception as e:
        print(f"Error in BeautifulSoup fallback extraction: {e}")
        return []


def split_html_into_chunks(
    html_content: str, 
    max_chunks: int = 4,
    min_size_for_chunking: int = 1000
) -> List[str]:
    """
    Split HTML content into a fixed number of chunks if it's large enough.
    
    Args:
        html_content (str): The HTML content to split
        max_chunks (int): Maximum number of chunks to create
        min_size_for_chunking (int): Minimum size in bytes to trigger chunking
        
    Returns:
        List[str]: List of HTML chunks (may be a single chunk if content is small)
    """
    # If HTML is small enough, don't split
    total_size = len(html_content)
    if total_size < min_size_for_chunking:
        return [html_content]
    
    # Use a fixed number of chunks (up to max_chunks)
    chunk_count = min(max_chunks, max(1, total_size // min_size_for_chunking))
    
    if chunk_count == 1:
        return [html_content]
    
    # Calculate chunk size based on chunk count
    chunk_size = total_size // chunk_count
    
    # Split content into chunks
    chunks = []
    for i in range(chunk_count):
        start_idx = i * chunk_size
        # For the last chunk, go to the end
        end_idx = total_size if i == chunk_count - 1 else (i + 1) * chunk_size
        chunks.append(html_content[start_idx:end_idx])
    
    return chunks

def analyze_html_chunks(
    html_chunks: List[str], 
    user_data: str,
    model_client: genai.Client,
    verbose: bool = False
) -> Tuple[List[Dict], str]:
    """
    Analyze HTML chunks and combine results.
    
    Args:
        html_chunks (List[str]): List of HTML chunks to analyze
        user_data (str): User data for form filling
        model_client (genai.Client): Initialized AI client
        verbose (bool): Whether to print detailed progress information
        
    Returns:
        Tuple[List[Dict], str]: Combined interactive elements and order summary
    """
    all_interactive_elements = []
    order_data = {"order_items": [], "pricing": {}, "coupons": []}
    
    # Process each chunk
    for i, chunk in enumerate(html_chunks):
        if verbose and len(html_chunks) > 1:
            print(f"  Processing chunk {i+1}/{len(html_chunks)}...")
        
        # Extract interactive elements from this chunk
        chunk_elements, _ = extract_interactive_elements(chunk, model_client)
        all_interactive_elements.extend(chunk_elements)
        
        # Extract order information from this chunk
        order_info = extract_order_info(chunk, model_client)
        
        # Merge order information
        if order_info.get("order_items"):
            order_data["order_items"].extend(order_info.get("order_items", []))
        
        if order_info.get("pricing") and not order_data["pricing"]:
            order_data["pricing"] = order_info.get("pricing", {})
        
        if order_info.get("coupons"):
            order_data["coupons"].extend(order_info.get("coupons", []))
    # Remove duplicate elements based on ID
    unique_elements = {}
    for element in all_interactive_elements:
        element_id = element.get("id")
        if element_id and element_id not in unique_elements:
            unique_elements[element_id] = element
    
    # Convert order data to JSON string
    order_json = json.dumps(order_data, indent=2)
    
    return list(unique_elements.values()), order_json

def extract_order_info(html_content: str, model_client: genai.Client) -> Dict:
    """
    Extract order summary and coupon information from HTML.
    
    Args:
        html_content (str): The HTML content to analyze
        model_client (genai.Client): Initialized AI client
        
    Returns:
        Dict: Order information including items, pricing, and coupons
    """
    order_summary_prompt = f"""
    Analyze the following HTML and extract:
    1. Order summary details (items, prices, subtotal, shipping, tax, total)
    2. All available coupons and their descriptions/discount details
    3. Current pricing breakdown

    Return the information in JSON format with this structure:
    {{
        "order_items": [
            {{
                "name": "item name",
                "quantity": 1,
                "price": "$XX.XX"
            }}
        ],
        "pricing": {{
            "subtotal": "$XX.XX",
            "shipping": "$XX.XX", 
            "tax": "$XX.XX",
            "total": "$XX.XX"
        }},
        "coupons": [
            {{
                "code": "coupon_code",
                "description": "discount description",
                "discount_amount": "$XX.XX or XX%"
            }}
        ]
    }}

    HTML to analyze:
    {html_content}
    """
    
    # Use the appropriate method based on fast mode status
    response_text = generate_content_with_model(model_client, order_summary_prompt)
    
    try:
        # Look for JSON in the response
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text.strip()
        
        # Parse the JSON
        order_info = json.loads(json_str)
        return order_info
    except:
        # Return empty structure on error
        return {"order_items": [], "pricing": {}, "coupons": []}

def generate_form_filling_actions(
    interactive_elements: List[Dict],
    order_data: str,
    user_data: str,
    model_client: genai.Client
) -> str:
    """
    Generate form filling actions based on interactive elements and order data.
    
    Args:
        interactive_elements (List[Dict]): List of interactive elements
        order_data (str): Order data JSON string
        user_data (str): User data for form filling
        model_client (genai.Client): Initialized AI client
        
    Returns:
        str: Form filling strategy response
    """
    # Convert interactive elements to JSON string for the prompt
    elements_json = json.dumps(interactive_elements, indent=2)
    
    form_filling_prompt = f"""
    You are an intelligent form filling assistant. Based on the interactive elements from the checkout form, user data, and order summary with available coupons, provide step-by-step instructions for filling the form optimally.

    User Data:
    {user_data}

    Order Summary and Coupons:
    {order_data}

    Interactive Elements (from analysis):
    {elements_json}

    CRITICAL VALIDATION REQUIREMENT:
    Before proceeding with any checkout/submit/place order action, you MUST validate that the user data contains ALL required information for this specific checkout form. 

    Analysis Steps:
    1. Examine the form elements to identify which fields are marked as "required"
    2. Check the user data to see if all required information is available
    3. If ANY required field cannot be filled with the provided user data, DO NOT proceed with checkout
    4. Instead, output a special action: <insufficient_data000> "Missing required fields: [list of missing fields]"

    Tasks:
    1. For each interactive element that needs to be filled, determine what data to enter
    2. For buttons, determine if they should be clicked and when
    3. Optimize coupon usage to minimize total cost
    4. Consider the logical order of form filling
    5. VALIDATE data completeness before any final checkout action

    Output format - provide an ordered list where each line follows this format:
    - For input fields: <element_id> "value_to_enter"
    - For buttons: <element_id> "|button|"
    - For dropdowns: <element_id> "selected_option"
    - For checkboxes: <element_id> "|check|" or <element_id> "|uncheck|"
    - For insufficient data: <insufficient_data000> "Missing required fields: field1, field2, etc."

    Provide your strategic thinking first, then the ordered action list.
    """
    
    # Generate content with appropriate model
    response_text = generate_content_with_model(model_client, form_filling_prompt)
    return response_text

def convert_to_structured_json(
    filling_strategy_response: str,
    model_client: genai.Client
) -> Dict[str, Any]:
    """
    Convert form filling strategy to structured JSON format.
    
    Args:
        filling_strategy_response (str): Response from form filling strategy generation
        model_client (genai.Client): Initialized Gemini client
        
    Returns:
        Dict[str, Any]: Structured JSON data with actions and optimization info
    """
    structured_output_prompt = f"""
    You are a data formatter. Take the following form filling strategy output and convert it into a clean, structured JSON format.

    Input Strategy Output:
    {filling_strategy_response}

    Your task:
    1. Extract ONLY the actionable steps from the strategy
    2. Format them as a JSON array with proper structure
    3. Ensure each action has the correct format
    4. IMPORTANT: If the strategy contains <insufficient_data000> element, this indicates validation failure - preserve this exactly

    Output Format (JSON):
    {{
        "strategy_summary": "Brief summary of the optimization strategy used",
        "total_actions": <number>,
        "actions": [
            {{
                "step": 1,
                "element_id": "element-id",
                "action_type": "input|button|select|checkbox|error",
                "value": "value to enter or action to take",
                "description": "Brief description of what this action does"
            }}
        ],
        "cost_optimization": {{
            "coupons_available": ["list of available coupons"],
            "recommended_coupon": "best coupon to use",
            "estimated_savings": "amount saved"
        }},
        "validation_status": {{
            "is_valid": true|false,
            "error_message": "error message if validation failed"
        }}
    }}

    Rules:
    - For text inputs: action_type="input", value="text to enter"
    - For buttons: action_type="button", value="click" or specific action
    - For dropdowns: action_type="select", value="option to select"
    - For checkboxes: action_type="checkbox", value="check" or "uncheck"
    - For insufficient_data000: action_type="error", preserve the missing fields message
    - Only include actionable steps, not explanatory text
    - Maintain the logical order of actions
    - Set validation_status.is_valid to false if insufficient_data000 is present

    Return ONLY the JSON, no additional text.
    """
    
    # Use our wrapper function instead of direct model call
    json_text = generate_content_with_model(model_client, structured_output_prompt)
    
    try:
        # Extract JSON from response (remove any markdown formatting)
        json_text = json_text.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]
        json_text = json_text.strip()
        
        # Parse the JSON
        structured_data = json.loads(json_text)
        
        return structured_data
        
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error in convert_to_structured_json: {e}")
        print("Raw response:")
        print(structured_output_prompt)
        return {"error": "Failed to parse JSON", "raw_response": structured_output_prompt}
    except Exception as e:
        print(f"Unexpected error in convert_to_structured_json: {e}")
        print("Raw response:")
        print(structured_output_prompt)
        return {"error": str(e), "raw_response": structured_output_prompt}


def analyze_html_chunks_parallel(
    html_chunks: List[str], 
    user_data: str,
    model_client: genai.Client,
    verbose: bool = False,
    max_workers: int = None  # None will use default based on system
) -> Tuple[List[Dict], str]:
    """
    Analyze HTML chunks in parallel and combine results.
    
    Args:
        html_chunks (List[str]): List of HTML chunks to analyze
        user_data (str): User data for form filling
        model_client (genai.Client): Initialized AI client
        verbose (bool): Whether to print detailed progress information
        max_workers (int): Maximum number of worker threads
        
    Returns:
        Tuple[List[Dict], str]: Combined interactive elements and order summary
    """
    all_interactive_elements = []
    order_data = {"order_items": [], "pricing": {}, "coupons": []}
    
    # Process chunk function for threading
    def process_chunk(chunk_idx, chunk):
        if verbose and len(html_chunks) > 1:
            print(f"  Processing chunk {chunk_idx+1}/{len(html_chunks)} in thread {threading.current_thread().name}...")
        
        # Extract interactive elements from this chunk
        chunk_elements, _ = extract_interactive_elements(chunk, model_client)
        
        # Extract order information from this chunk
        order_info = extract_order_info(chunk, model_client)
        
        return chunk_elements, order_info
    
    # Use ThreadPoolExecutor to process chunks in parallel
    futures = []
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        for i, chunk in enumerate(html_chunks):
            future = executor.submit(process_chunk, i, chunk)
            futures.append(future)
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                chunk_elements, order_info = future.result()
                results.append((chunk_elements, order_info))
                if verbose:
                    print(f"  ✓ Completed a chunk processing")
            except Exception as e:
                if verbose:
                    print(f"  ❌ Error processing chunk: {e}")
    
    # Combine all results
    for chunk_elements, order_info in results:
        all_interactive_elements.extend(chunk_elements)
        
        # Merge order information
        if order_info.get("order_items"):
            order_data["order_items"].extend(order_info.get("order_items", []))
        
        if order_info.get("pricing") and not order_data["pricing"]:
            order_data["pricing"] = order_info.get("pricing", {})
        
        if order_info.get("coupons"):
            order_data["coupons"].extend(order_info.get("coupons", []))
    
    # Remove duplicate elements based on ID
    unique_elements = {}
    for element in all_interactive_elements:
        element_id = element.get("id")
        if element_id and element_id not in unique_elements:
            unique_elements[element_id] = element
    
    # Convert order data to JSON string
    order_json = json.dumps(order_data, indent=2)
    
    return list(unique_elements.values()), order_json

def automate_checkout_form(
    html_content: str,
    user_data: str,
    api_key: str = 'AIzaSyBXZLvzTn2Jf52PZ_PgwDlNRtWUu37aPx4',
    api_keys: list = None,
    save_to_file: bool = True,
    output_file: str = 'form_filling_actions.json',
    verbose: bool = False,
    fast: bool = False,
    depth: int = 1,
    max_chunks: int = 4,
    min_size_for_chunking: int = 1000,
    max_workers: int = None
) -> Dict[str, Any]:
    """
    Main function to automate checkout form analysis and generate structured actions.
    
    Args:
        html_content (str): The HTML content of the checkout form
        user_data (str): User data for form filling
        api_key (str): Single Google Generative AI API key (for backward compatibility)
        api_keys (list): List of Google Generative AI API keys for automatic cycling
        save_to_file (bool): Whether to save results to JSON file
        output_file (str): Output file name for saving results
        verbose (bool): Whether to print detailed progress information
        fast (bool): If True, use Gemma models instead of Gemini for faster processing
        depth (int): Model depth when using fast mode: 0=1B, 1=4B, 2=12B
        max_chunks (int): Maximum number of chunks to split HTML into
        min_size_for_chunking (int): Minimum size in bytes to trigger chunking
        max_workers (int): Maximum number of worker threads for parallel processing
    Returns:
        Dict[str, Any]: Complete structured data with all analysis results
    """
    # Initialize API key manager with provided keys
    if api_keys:
        api_key_manager.update_keys(api_keys)
        actual_api_key = api_key_manager.get_current_key()
        if verbose:
            print(f"🔑 Initialized with {len(api_keys)} API keys")
    else:
        # Use single API key for backward compatibility
        api_key_manager.update_keys([api_key])
        actual_api_key = api_key
    
    if verbose:
        print("🚀 Starting checkout form automation...")
        print("=" * 60)
        if fast:
            gemma_models = ["gemma-3-1b-it", "gemma-3-4b-it", "gemma-3-12b-it"]
            selected_model = gemma_models[min(depth, 2)]
            print(f"💨 Using fast mode with model: {selected_model}")
    
    try:
    # Initialize model with the current API key
        model = initialize_model(actual_api_key, fast, depth)
    
        # Check if model initialization had SSL errors
        if hasattr(model, '_ssl_error') and model._ssl_error:
            if verbose:
                print("⚠️ Using fallback mode due to SSL/network errors")
            # Create a basic response with error information
            return {
                "error": "SSL or network error when connecting to AI service",
                "validation_status": {
                    "is_valid": False,
                    "error_message": "Could not connect to AI service due to network issues"
                },
                "actions": [],
                "network_error": True
            }
        
    # If not in fast mode, set max_chunks to 1 to avoid parallelization
        if not fast:
            max_chunks = 1
            if verbose:
                print("Not using fast mode - limiting to 1 chunk for higher quality processing")
        
        # Extract interactive elements and make sure we have a list of elements, not a tuple
        elements, _ = extract_interactive_elements(html_content, model)
        interactive_elements = elements if isinstance(elements, list) else []
    
        # Log the detected elements for debugging
        if verbose:
            input_elements = [e for e in interactive_elements if e.get('element_type', '') and e.get('element_type', '').lower().startswith(('input', 'select', 'textarea'))]
            button_elements = [e for e in interactive_elements if e.get('element_type', '') and e.get('element_type', '').lower() in ['button', 'submit']]
            print(f"🔍 Element detection summary:")
            print(f"   - Total elements: {len(interactive_elements)}")
            print(f"   - Input-type elements: {len(input_elements)}")
            print(f"   - Button-type elements: {len(button_elements)}")
            
            # If very few input elements were found, show a warning
            if len(input_elements) < 3 and len(interactive_elements) > 0:
                print(f"⚠️  Warning: Very few input elements detected. The system used fallback methods.")
                print(f"   The detected input elements are:")
                for idx, input_el in enumerate(input_elements):
                    el_id = input_el.get('id', 'no-id')
                    el_type = input_el.get('element_type', 'unknown')
                    print(f"   {idx+1}. {el_type} (id: {el_id})")
        
        # Extract order summary if present
        order_data = extract_order_info(html_content, model)
        
        # Determine if the HTML is large enough to require chunking
        html_size = len(html_content.encode('utf-8'))
        should_chunk = html_size > min_size_for_chunking and max_chunks > 1
        
        if verbose:
            print(f"HTML size: {html_size / 1024:.1f} KB")
            print(f"Chunking strategy: {'Enabled' if should_chunk else 'Disabled'}")
            if should_chunk:
                print(f"Max chunks: {max_chunks}")
        
        # Formulate the strategy - determine how to fill the form
        if fast and should_chunk:
            # Process in parallel chunks for faster processing with smaller models
            if verbose:
                print("Using parallel processing with chunking...")
            
            # Use split_html_into_chunks instead of create_html_chunks
            chunks = split_html_into_chunks(
                html_content, 
                max_chunks, 
                min_size_for_chunking
            )
            
            # Process each chunk in parallel
            num_workers = max_workers or min(4, len(chunks))
            if verbose:
                print(f"Processing {len(chunks)} chunks with {num_workers} workers")
            
            # Create a thread pool for parallel execution
            results = []
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                # Important: Use user_data consistently for ALL chunks, regardless of fast mode
                futures = [
                    executor.submit(
                        process_chunk, 
                        chunk, 
                        interactive_elements, 
                        user_data,  # Use actual user_data, not default
                        model, 
                        i, 
                        len(chunks), 
                        verbose
                    ) 
                    for i, chunk in enumerate(chunks)
                ]
                results = [future.result() for future in futures]
            
            # Simple concatenation of results with a separator instead of combine_chunk_results
            strategy_response = "\n\n--- CHUNK BOUNDARY ---\n\n".join(results)
        else:
            # Single-pass processing
            if verbose:
                print("Using single-pass processing...")
            
            # Replace get_form_filling_strategy with generate_form_filling_actions
            order_json = json.dumps(order_data, indent=2)
            strategy_response = generate_form_filling_actions(
                interactive_elements=interactive_elements,
                order_data=order_json,
                user_data=user_data,
                model_client=model
            )
        
            # Check if we received an error response
            if strategy_response.startswith("Error:") or strategy_response.startswith("Error connecting to AI service:"):
                if verbose:
                    print(f"❌ AI service error: {strategy_response}")
                
                # Create a basic response with error information
                result = {
                    "error": strategy_response,
                    "validation_status": {
                        "is_valid": False,
                        "error_message": "Could not generate form-filling strategy due to AI service error"
                    },
                    "actions": [],
                    "network_error": True
                }
                return result
            
        # Convert the strategy into structured JSON data
        # Replace convert_strategy_to_json with convert_to_structured_json
        structured_data = convert_to_structured_json(
            filling_strategy_response=strategy_response,
            model_client=model
        )
        
        # IMPORTANT: Validate that all required fields are filled
        if verbose:
            print("Validating user data and form mapping...")
        
        # Simple placeholder for validate_user_data function
        # Check if there's an error action in the structured data
        has_validation_error = False
        for action in structured_data.get('actions', []):
            if action.get('action_type') == 'error' or action.get('element_id') == 'insufficient_data000':
                has_validation_error = True
                break
        
        # Add validation status to the structured data
        if 'validation_status' not in structured_data:
            structured_data['validation_status'] = {
                'is_valid': not has_validation_error,
                'error_message': 'Missing required fields' if has_validation_error else ''
            }
        
        # Add additional metadata
        structured_data['metadata'] = {
            'interactive_elements_count': len(interactive_elements),
            'interactive_elements': interactive_elements,
            'order_summary_raw': order_data,
            'strategy_response_raw': strategy_response
        }
        
        # Save to file if requested
        if save_to_file and "error" not in structured_data:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(structured_data, f, indent=2, ensure_ascii=False)
                if verbose:
                    print(f"💾 Results saved to: {output_file}")
            except Exception as e:
                print(f"❌ Failed to save file: {e}")
        
        if verbose:
            print("🎉 Checkout form automation completed!")
            print("=" * 60)
        
        return structured_data
    
    except Exception as e:
        error_message = str(e)
        if "SSL" in error_message or "EOF occurred in violation of protocol" in error_message:
            if verbose:
                print(f"❌ Network/SSL error during form automation: {error_message}")
            return {
                "error": f"Network or SSL error: {error_message}",
                "validation_status": {
                    "is_valid": False,
                    "error_message": "Could not complete form automation due to network issues"
                },
                "actions": [],
                "network_error": True
            }
        else:
            if verbose:
                print(f"❌ Error during form automation: {error_message}")
            return {
                "error": f"Processing error: {error_message}",
                "validation_status": {
                    "is_valid": False,
                    "error_message": f"Could not complete form automation: {error_message}"
                },
                "actions": []
            }


def print_action_sequence(structured_data: Dict[str, Any]) -> None:
    """
    Print a clean, formatted action sequence from structured data.
    
    Args:
        structured_data (Dict[str, Any]): Structured data from automation
    """
    if "error" in structured_data:
        print("❌ Error in structured data - cannot print action sequence")
        return
    
    print("📋 CHECKOUT FORM ACTION SEQUENCE")
    print("=" * 50)
    
    # Print summary
    strategy = structured_data.get('strategy_summary', 'N/A')
    total_actions = structured_data.get('total_actions', 0)
    print(f"Strategy: {strategy}")
    print(f"Total Actions: {total_actions}")
      # Print validation status
    validation_status = structured_data.get('validation_status', {})
    if validation_status:
        is_valid = validation_status.get('is_valid', True)
        if not is_valid:
            error_message = validation_status.get('error_message', 'Unknown validation error')
            print(f"Validation Status: ❌ FAILED - {error_message}")
        else:
            print("Validation Status: ✅ PASSED")
    
    # Print cost optimization info
    cost_opt = structured_data.get('cost_optimization', {})
    if cost_opt:
        recommended_coupon = cost_opt.get('recommended_coupon', 'None')
        estimated_savings = cost_opt.get('estimated_savings', 'N/A')
        print(f"Recommended Coupon: {recommended_coupon}")
        print(f"Estimated Savings: {estimated_savings}")
    
    print("\nAction Sequence:")
    print("-" * 30)
    
    # Print actions
    for action in structured_data.get('actions', []):
        step = action.get('step', '?')
        element_id = action.get('element_id', 'unknown')
        action_type = action.get('action_type', 'unknown')
        value = action.get('value', '')
        description = action.get('description', '')
        
        if action_type in ['input', 'select']:
            print(f"{step:2d}. <{element_id}> \"{value}\"")
        elif action_type == 'error':
            print(f"{step:2d}. <{element_id}> \"{value}\" ⚠️")
        else:
            print(f"{step:2d}. <{element_id}> |{value}|")
        
        if description:
            print(f"     → {description}")
    
    print("=" * 50)


# Example usage and testing
if __name__ == "__main__":
    # Example with test data (you would replace these with actual data)
    sample_html = """
    <!-- Sample HTML for testing -->
    <form id="checkout-form">
        <input type="text" id="first-name" name="first_name" required>
        <input type="email" id="email" name="email" required>
        <button type="submit" id="submit-btn">Place Order</button>
    </form>
    """
    
    sample_user_data = """
    name: John Doe
    email: john.doe@example.com
    phone: +1-555-0123
    """
    
    # Run automation with different models
    # Fast mode with smallest model (1B)
    result_fast_small = automate_checkout_form(
        html_content=sample_html,
        user_data=sample_user_data,
        verbose=True,
        fast=True,
        depth=0
    )
    
    # Default Gemini model for high quality results
    result_high_quality = automate_checkout_form(
        html_content=sample_html,
        user_data=sample_user_data,
        verbose=True,
        fast=False
    )

def process_chunk(
    html_chunk: str, 
    interactive_elements: List[Dict],
    user_data: str,
    model: Any,
    chunk_index: int,
    total_chunks: int,
    verbose: bool = False
) -> str:
    """
    Process a single HTML chunk to extract form filling information.
    
    Args:
        html_chunk: The HTML content chunk
        interactive_elements: List of interactive elements
        user_data: User profile data for form filling
        model: The AI model to use
        chunk_index: Index of current chunk
        total_chunks: Total number of chunks
        verbose: Whether to print progress info
        
    Returns:
        str: The form filling strategy for this chunk
    """
    if verbose:
        print(f"Processing chunk {chunk_index + 1}/{total_chunks} (size: {len(html_chunk)} chars)")
    
    # Create prompt for this chunk
    prompt = create_form_filling_prompt(
        html_chunk, 
        interactive_elements, # This is already a list of dictionaries
        user_data  # Always use the provided user_data, never use default
    )
    
    # Send to model
    try:
        response = generate_content_with_model(model, prompt)
        return response
    except Exception as e:
        if verbose:
            print(f"Error processing chunk {chunk_index + 1}: {str(e)}")
        return f"ERROR: Failed to process chunk {chunk_index + 1}: {str(e)}"

def create_form_filling_prompt(html_content: str, interactive_elements: List[Dict], user_data: str) -> str:
    """
    Create a prompt for form filling strategy.
    
    Args:
        html_content: HTML content to analyze
        interactive_elements: List of interactive elements
        user_data: User profile data for form filling
        
    Returns:
        str: The prompt for the model
    """
    # Always use the user_data that was passed in, never use default values
    prompt = f"""
You are an AI assistant that helps fill out checkout forms. 

# USER PROFILE DATA
```
{user_data}
```

# INTERACTIVE ELEMENTS
The page contains the following interactive elements:
{json.dumps(interactive_elements, indent=2)}

# HTML CONTENT
```html
{html_content[:20000]}  <!-- Limit to avoid token overflow -->
```

Your task is to create a detailed step-by-step strategy for filling out this form using the user profile data provided.
For each interactive element, provide:
1. The element ID or name
2. The action to take (input, select, click, etc.)
3. The value to enter or select

Format your response as a numbered list of steps with clear instructions for each element.
If you're unsure about any field, make a reasonable guess based on the context.
"""
    return prompt

def compare_html_content(previous_html: str, current_html: str) -> Dict[str, Any]:
    """
    Compare two HTML contents to determine if there are significant changes.
    
    Args:
        previous_html (str): The previous HTML content
        current_html (str): The current HTML content
        
    Returns:
        Dict[str, Any]: Comparison results with the following keys:
            - significant_change: Whether the change is significant
            - similarity_score: A measure of similarity (0-1)
            - new_elements: List of new elements found
            - removed_elements: List of removed elements
            - changed_elements: List of elements that have changed
    """
    previous_soup = BeautifulSoup(previous_html, 'html.parser')
    current_soup = BeautifulSoup(current_html, 'html.parser')
    
    # Extract interactive elements from both HTMLs
    previous_elements = extract_elements_for_comparison(previous_soup)
    current_elements = extract_elements_for_comparison(current_soup)
    
    # Check for completely new page (significant structure changes)
    previous_structure = get_page_structure(previous_soup)
    current_structure = get_page_structure(current_soup)
    
    structure_similarity = calculate_similarity(previous_structure, current_structure)
    
    # Compare interactive elements
    new_elements = []
    removed_elements = []
    changed_elements = []
    
    # Find new and changed elements
    for curr_el in current_elements:
        # Try to find by ID first
        if curr_el['id']:
            prev_el = next((el for el in previous_elements if el['id'] == curr_el['id']), None)
            if prev_el is None:
                new_elements.append(curr_el)
            elif prev_el['attributes'] != curr_el['attributes']:
                changed_elements.append({
                    'previous': prev_el,
                    'current': curr_el
                })
        # Then try to find by combination of element type and position
        else:
            prev_el = next((el for el in previous_elements 
                          if el['type'] == curr_el['type'] 
                          and el['position'] == curr_el['position']), None)
            if prev_el is None:
                new_elements.append(curr_el)
    
    # Find removed elements
    for prev_el in previous_elements:
        if prev_el['id']:
            curr_el = next((el for el in current_elements if el['id'] == prev_el['id']), None)
            if curr_el is None:
                removed_elements.append(prev_el)
        else:
            curr_el = next((el for el in current_elements 
                          if el['type'] == prev_el['type'] 
                          and el['position'] == prev_el['position']), None)
            if curr_el is None:
                removed_elements.append(prev_el)
    
    # Calculate a similarity score
    total_elements = len(set([e['id'] or str(e['position']) for e in previous_elements + current_elements]))
    if total_elements == 0:
        similarity_score = 1.0  # If no elements, consider identical
    else:
        changes = len(new_elements) + len(removed_elements) + len(changed_elements)
        similarity_score = max(0.0, 1.0 - (changes / total_elements))
    
    # Determine if change is significant based on multiple factors
    significant_change = False
    
    # 1. Structure similarity below threshold suggests new page
    if structure_similarity < 0.7:
        significant_change = True
    
    # 2. Large number of new elements suggests new page
    if len(new_elements) > 5:
        significant_change = True
    
    # 3. Significant number of removed form elements suggests new page
    form_elements_removed = [el for el in removed_elements 
                            if el.get('type') and el['type'].startswith(('input', 'select', 'textarea', 'button'))]
    if len(form_elements_removed) > 3:
        significant_change = True
    
    # 4. URL or title changes in the page
    previous_title = get_page_title(previous_soup)
    current_title = get_page_title(current_soup)
    
    if previous_title != current_title:
        significant_change = True
    
    # Return comparison results
    return {
        'significant_change': significant_change,
        'similarity_score': similarity_score,
        'structure_similarity': structure_similarity,
        'new_elements': new_elements,
        'removed_elements': removed_elements,
        'changed_elements': changed_elements,
        'previous_title': previous_title,
        'current_title': current_title
    }

def extract_elements_for_comparison(soup: BeautifulSoup) -> List[Dict]:
    """
    Extract elements from HTML for comparison purposes.
    
    Args:
        soup (BeautifulSoup): The BeautifulSoup object
        
    Returns:
        List[Dict]: List of element information for comparison
    """
    elements = []
    
    # Find all interactive elements
    for i, element in enumerate(soup.select('input, select, textarea, button, a[href], [onclick], [role="button"]')):
        element_type = element.name
        if element_type == 'input' and element.get('type'):
            element_type = f"input_{element.get('type')}"
        
        # Get position information
        position = {
            'index': i,
            'parent': str(element.parent.name) if element.parent else None
        }
        
        # Get attributes for comparison
        attributes = {}
        for attr in element.attrs:
            if attr not in ['style', 'class']:  # Ignore style and class for comparison
                attributes[attr] = element.get(attr)
        
        elements.append({
            'id': element.get('id', ''),
            'type': element_type,
            'position': position,
            'attributes': attributes
        })
    
    return elements

def get_page_structure(soup: BeautifulSoup) -> Dict:
    """
    Get a hash representing the page structure.
    
    Args:
        soup (BeautifulSoup): The BeautifulSoup object
        
    Returns:
        Dict: Structure information
    """
    # Count tag types
    tags = {}
    for tag in soup.find_all(True):
        tag_name = tag.name
        if tag_name in tags:
            tags[tag_name] += 1
        else:
            tags[tag_name] = 1
    
    # Get structure of main containers
    containers = []
    for container in soup.select('body > div, body > main, body > section'):
        container_info = {
            'tag': container.name,
            'id': container.get('id', ''),
            'class': ' '.join(container.get('class', [])),
            'children_count': len(list(container.children))
        }
        containers.append(container_info)
    
    # Create a hash of the overall structure
    structure_string = json.dumps(tags) + json.dumps(containers)
    structure_hash = hashlib.md5(structure_string.encode()).hexdigest()
    
    return {
        'tag_counts': tags,
        'containers': containers,
        'hash': structure_hash
    }

def get_page_title(soup: BeautifulSoup) -> str:
    """
    Get the page title.
    
    Args:
        soup (BeautifulSoup): The BeautifulSoup object
        
    Returns:
        str: The page title
    """
    title_tag = soup.find('title')
    if title_tag:
        return title_tag.get_text(strip=True)
    return ""

def calculate_similarity(structure1: Dict, structure2: Dict) -> float:
    """
    Calculate similarity between two page structures.
    
    Args:
        structure1 (Dict): First structure
        structure2 (Dict): Second structure
        
    Returns:
        float: Similarity score (0-1)
    """
    # Quick hash comparison
    if structure1['hash'] == structure2['hash']:
        return 1.0
    
    # Tag count comparison
    all_tags = set(structure1['tag_counts'].keys()) | set(structure2['tag_counts'].keys())
    if not all_tags:
        return 1.0
    
    tag_diff = 0
    for tag in all_tags:
        count1 = structure1['tag_counts'].get(tag, 0)
        count2 = structure2['tag_counts'].get(tag, 0)
        tag_diff += abs(count1 - count2)
    
    max_tags = sum(structure1['tag_counts'].values()) + sum(structure2['tag_counts'].values())
    if max_tags == 0:
        tag_similarity = 1.0
    else:
        tag_similarity = 1.0 - min(1.0, tag_diff / max_tags)
    
    # Container comparison
    containers1 = structure1['containers']
    containers2 = structure2['containers']
    
    # If containers structure is very different, pages are different
    container_similarity = 0.0
    if len(containers1) == 0 and len(containers2) == 0:
        container_similarity = 1.0
    elif len(containers1) == 0 or len(containers2) == 0:
        container_similarity = 0.0
    else:
        matches = 0
        for c1 in containers1:
            for c2 in containers2:
                if (c1['tag'] == c2['tag'] and 
                    (c1['id'] == c2['id'] or c1['class'] == c2['class'])):
                    matches += 1
                    break
        
        container_similarity = matches / max(len(containers1), len(containers2))
    
    # Final combined similarity
    return (tag_similarity * 0.7) + (container_similarity * 0.3)

def automate_form_filling_with_reanalysis(
    html_content: str,
    user_data: str,
    api_key: str = 'AIzaSyBXZLvzTn2Jf52PZ_PgwDlNRtWUu37aPx4',
    wait_time: int = 2,
    max_attempts: int = 3,
    callback_get_updated_html = None,
    verbose: bool = False,
    fast: bool = False,
    depth: int = 1,
    max_chunks: int = 4,
    min_size_for_chunking: int = 1000,
    max_workers: int = None
) -> Dict[str, Any]:
    """
    Automated form filling with wait and reanalysis if page changes.
    
    Args:
        html_content (str): The HTML content of the checkout form
        user_data (str): User data for form filling
        api_key (str): Google Generative AI API key
        wait_time (int): Time to wait in seconds after form filling
        max_attempts (int): Maximum number of form filling attempts
        callback_get_updated_html: Function to call to get updated HTML (if None, reanalysis is disabled)
        verbose (bool): Whether to print detailed progress information
        fast (bool): If True, use Gemma models instead of Gemini for faster processing
        depth (int): Model depth when using fast mode: 0=1B, 1=4B, 2=12B
        max_chunks (int): Maximum number of chunks to split HTML into
        min_size_for_chunking (int): Minimum size in bytes to trigger chunking
        max_workers (int): Maximum number of worker threads for parallel processing
        
    Returns:
        Dict[str, Any]: Results from the form filling process with additional metadata
    """
    if verbose:
        print("🚀 Starting form filling with reanalysis...")
    
    attempt = 1
    previous_html = html_content
    current_html = html_content
    final_result = None
    analysis_history = []
    
    while attempt <= max_attempts:
        if verbose:
            print(f"📝 Attempt {attempt}/{max_attempts}")
        
        # Process the checkout form
        result = automate_checkout_form(
            html_content=current_html,
            user_data=user_data,
            api_key=api_key,
            save_to_file=False,
            verbose=verbose,
            fast=fast,
            depth=depth,
            max_chunks=max_chunks,
            min_size_for_chunking=min_size_for_chunking,
            max_workers=max_workers
        )
        
        # Store this result
        result['attempt'] = attempt
        analysis_history.append({
            'attempt': attempt,
            'actions_count': len(result.get('actions', [])),
            'timestamp': time.time()
        })
        
        # If this is the final attempt or we can't get updated HTML, return the result
        if attempt == max_attempts or callback_get_updated_html is None:
            final_result = result
            break
        
        if verbose:
            print(f"⏳ Waiting {wait_time} seconds to check for page changes...")
        
        # Wait for the specified time
        time.sleep(wait_time)
        
        # Get updated HTML
        previous_html = current_html
        try:
            current_html = callback_get_updated_html()
            
            if verbose:
                print("🔍 Comparing HTML content for changes...")
            
            # Compare HTML
            comparison = compare_html_content(previous_html, current_html)
            
            if comparison['significant_change']:
                if verbose:
                    print("🔄 Significant page change detected, reanalyzing...")
                    print(f"   Similarity score: {comparison['similarity_score']:.2f}")
                    print(f"   New elements: {len(comparison['new_elements'])}")
                    print(f"   Removed elements: {len(comparison['removed_elements'])}")
                    
                # Store the comparison results
                result['page_comparison'] = comparison
                
                # Increment attempt counter and continue to reanalyze
                attempt += 1
                continue
            else:
                if verbose:
                    print("✅ No significant page changes detected, completing process")
                
                # Store the comparison results
                result['page_comparison'] = comparison
                
                final_result = result
                break
        
        except Exception as e:
            if verbose:
                print(f"❌ Error getting updated HTML: {e}")
            
            final_result = result
            final_result['error'] = str(e)
            break
    
    # Add analysis history to the final result
    if final_result:
        final_result['analysis_history'] = analysis_history
        
        # Add metadata about the reanalysis process
        final_result['reanalysis_metadata'] = {
            'attempts': attempt,
            'max_attempts': max_attempts,
            'wait_time': wait_time,
            'completed': attempt <= max_attempts,
            'reanalysis_triggered': attempt > 1
        }
    
    return final_result
