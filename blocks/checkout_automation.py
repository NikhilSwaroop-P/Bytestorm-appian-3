"""
Checkout Form Automation Module

This module provides functions to analyze HTML checkout forms and generate
optimized form-filling instructions using Google's Gemini AI model.

Functions:
1. extract_interactive_elements() - Extracts all interactive elements from HTML
2. generate_form_filling_strategy() - Creates optimized form filling strategy with coupon analysis
3. convert_to_structured_json() - Converts strategy to clean JSON format

Author: AI Assistant
Date: June 3, 2025
"""

import google.generativeai as genai
import json
import re
import os
from typing import Dict, List, Any, Tuple, Optional


def initialize_gemini_model(api_key: str = 'AIzaSyBS2npulOMMZ9WRj7b-UpoYHXVSa0Jju4o') -> genai.GenerativeModel:
    """
    Initialize the Gemini AI model with the provided API key.
    
    Args:
        api_key (str): Google Generative AI API key
        
    Returns:
        genai.GenerativeModel: Initialized Gemini model
    """
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash-preview-05-20')


def extract_interactive_elements(html_content: str, model: genai.GenerativeModel) -> Tuple[List[Dict], str]:
    """
    Extract all interactive elements from HTML content using Gemini AI.
    
    Args:
        html_content (str): The HTML content to analyze
        model (genai.GenerativeModel): Initialized Gemini model
        
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
    response = model.generate_content(prompt)
    
    try:
        # Look for JSON in the response (it might be wrapped in markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response.text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If no code blocks, try to find JSON directly
            json_str = response.text.strip()
        
        # Parse the JSON
        interactive_elements = json.loads(json_str)
        
        return interactive_elements, response.text
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in extract_interactive_elements: {e}")
        return [], response.text
    except Exception as e:
        print(f"Unexpected error in extract_interactive_elements: {e}")
        return [], response.text


def generate_form_filling_strategy(
    html_content: str, 
    user_data: str, 
    interactive_elements_response: str,
    model: genai.GenerativeModel
) -> Tuple[str, str]:
    """
    Generate optimized form filling strategy with coupon analysis.
    
    Args:
        html_content (str): The HTML content to analyze
        user_data (str): User data for form filling
        interactive_elements_response (str): Response from interactive elements extraction
        model (genai.GenerativeModel): Initialized Gemini model
        
    Returns:
        Tuple[str, str]: Order response and form filling strategy response
    """
    # First, extract order summary and coupon information from the HTML
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
    
    order_response = model.generate_content(order_summary_prompt)
      # Now generate form filling instructions
    form_filling_prompt = f"""
    You are an intelligent form filling assistant. Based on the interactive elements from the checkout form, user data, and order summary with available coupons, provide step-by-step instructions for filling the form optimally.

    User Data:
    {user_data}

    Order Summary and Coupons:
    {order_response.text}

    Interactive Elements (from previous analysis):
    {interactive_elements_response}

    CRITICAL VALIDATION REQUIREMENT:
    Before proceeding with any checkout/submit/place order action, you MUST validate that the user data contains ALL required information for this specific checkout form. 

    Analysis Steps:
    1. Examine the HTML form structure to identify which fields are marked as "required" (have required attribute, asterisks, or other indicators)
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

    Before providing the list, think through:
    1. What fields are required for this specific checkout form
    2. What user data is available vs what is needed
    3. What coupons are available and their benefits
    4. Which coupon provides the best discount
    5. The optimal order of actions
    6. Any dependencies between form fields
    7. Whether checkout should proceed or be blocked due to missing data

    Provide your strategic thinking first, then the ordered action list.
    """
    
    filling_response = model.generate_content(form_filling_prompt)
    print('done with this')
    return order_response.text, filling_response.text


def convert_to_structured_json(
    filling_strategy_response: str,
    model: genai.GenerativeModel
) -> Dict[str, Any]:
    """
    Convert form filling strategy to structured JSON format.
    
    Args:
        filling_strategy_response (str): Response from form filling strategy generation
        model (genai.GenerativeModel): Initialized Gemini model
        
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
    
    structured_response = model.generate_content(structured_output_prompt)
    
    try:
        # Extract JSON from response (remove any markdown formatting)
        json_text = structured_response.text.strip()
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
        print(structured_response.text)
        return {"error": "Failed to parse JSON", "raw_response": structured_response.text}
    except Exception as e:
        print(f"Unexpected error in convert_to_structured_json: {e}")
        print("Raw response:")
        print(structured_response.text)
        return {"error": str(e), "raw_response": structured_response.text}


def automate_checkout_form(
    html_content: str,
    user_data: str,
    api_key: str = 'AIzaSyBS2npulOMMZ9WRj7b-UpoYHXVSa0Jju4o',
    save_to_file: bool = True,
    output_file: str = 'form_filling_actions.json',
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Main function to automate checkout form analysis and generate structured actions.
    
    Args:
        html_content (str): The HTML content of the checkout form
        user_data (str): User data for form filling
        api_key (str): Google Generative AI API key
        save_to_file (bool): Whether to save results to JSON file
        output_file (str): Output file name for saving results
        verbose (bool): Whether to print detailed progress information
        
    Returns:
        Dict[str, Any]: Complete structured data with all analysis results
    """
    if verbose:
        print("🚀 Starting checkout form automation...")
        print("=" * 60)
    
    # Initialize model
    model = initialize_gemini_model(api_key)
    
    # Step 1: Extract interactive elements
    if verbose:
        print("Step 1: Extracting interactive elements...")
    
    interactive_elements, elements_response = extract_interactive_elements(html_content, model)
    
    if verbose:
        print(f"✅ Found {len(interactive_elements)} interactive elements")
    
    # Step 2: Generate form filling strategy
    if verbose:
        print("Step 2: Generating form filling strategy with coupon optimization...")
    
    order_response, strategy_response = generate_form_filling_strategy(
        html_content, user_data, elements_response, model
    )
    
    if verbose:
        print("✅ Strategy generated successfully")
      # Step 3: Convert to structured JSON
    if verbose:
        print("Step 3: Converting to structured JSON format...")
    
    structured_data = convert_to_structured_json(strategy_response, model)
    
    if "error" not in structured_data:
        # Check validation status
        validation_status = structured_data.get('validation_status', {})
        is_valid = validation_status.get('is_valid', True)
        
        if verbose:
            if is_valid:
                print("✅ Successfully converted to structured JSON")
                print(f"📊 Total actions: {structured_data.get('total_actions', 0)}")
            else:
                print("❌ Validation failed - insufficient user data")
                error_message = validation_status.get('error_message', 'Unknown validation error')
                print(f"Error: {error_message}")
            
            # Display clean action list
            print("\n📋 Generated Action Sequence:")
            print("-" * 40)
            for action in structured_data.get('actions', []):
                element_id = action.get('element_id', 'unknown')
                action_type = action.get('action_type', 'unknown')
                value = action.get('value', '')
                
                if action_type == 'input' or action_type == 'select':
                    print(f'<{element_id}> "{value}"')
                elif action_type == 'error':
                    print(f'<{element_id}> "{value}"')
                else:
                    print(f'<{element_id}> |{value}|')
    
    # Add additional metadata
    structured_data['metadata'] = {
        'interactive_elements_count': len(interactive_elements),
        'interactive_elements': interactive_elements,
        'order_summary_raw': order_response,
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
    
    # Run automation
    result = automate_checkout_form(
        html_content=sample_html,
        user_data=sample_user_data,
        verbose=True
    )
    
    # Print results
    print_action_sequence(result)