"""
Fix for Fast Mode Profile Issue

This script addresses the issue where custom user profiles are not being used
when fast_mode=True in the checkout automation system. The issue appears to be 
in the Python backend where the user profile data is not correctly passed through
to the form filling process when using fast mode.

Issue: When fast_mode=True, the checkout automation system ignores the custom user
profile and uses default test data instead.

Fix Approach:
1. Ensure user_data is properly passed to all chunking and processing functions
2. Never override user_data with default values in fast mode
3. Ensure all form filling functions use the same user_data parameter

Implementation Steps:
"""

import os
import json
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

# ---------- Fix Implementation ----------

def fix_automate_checkout_form():
    """
    Modify the automate_checkout_form function to ensure user_data is properly passed
    through all processing paths, including fast mode.
    """
    print("Fixing automate_checkout_form function...")
    # Key changes to make:
    # 1. In chunking logic, pass user_data to all process_chunk calls
    # 2. Never default to using a different user profile in fast mode
    code_fix = """
def automate_checkout_form(
    html_content: str,
    user_data: str,
    api_key: str = 'AIzaSyBXZLvzTn2Jf52PZ_PgwDlNRtWUu37aPx4',
    save_to_file: bool = True,
    output_file: str = 'form_filling_actions.json',
    verbose: bool = False,
    fast: bool = False,
    depth: int = 1,
    max_chunks: int = 4,
    min_size_for_chunking: int = 1000,
    max_workers: int = None
) -> Dict[str, Any]:
    # ... existing code ...
    
    # When processing in chunks (fast mode), ensure user_data is passed properly
    if fast and should_chunk:
        # Process in parallel chunks for faster processing with smaller models
        if verbose:
            print("Using parallel processing with chunking...")
        
        chunks = create_html_chunks(html_content, max_chunks, verbose)
        
        # Process each chunk in parallel
        num_workers = max_workers or min(4, len(chunks))
        if verbose:
            print(f"Processing {len(chunks)} chunks with {num_workers} workers")
        
        # Create a thread pool for parallel execution
        results = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # CRITICAL FIX: Use user_data consistently for ALL chunks
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
        
        # Combine results
        strategy_response = combine_chunk_results(results, verbose)
    else:
        # Single-pass processing
        if verbose:
            print("Using single-pass processing...")
        
        strategy_response = get_form_filling_strategy(
            html_content=html_content,
            interactive_elements=interactive_elements,
            user_data=user_data,  # Always use the provided user_data
            model=model,
            verbose=verbose
        )
    
    # ... rest of existing code ...
"""
    print("✅ Fix code generated for automate_checkout_form")
    return code_fix


def fix_process_chunk():
    """
    Modify the process_chunk function to ensure it uses the provided user_data.
    """
    print("Fixing process_chunk function...")
    code_fix = """
def process_chunk(
    html_chunk: str, 
    interactive_elements: List[Dict],
    user_data: str,  # Ensure this parameter is properly used
    model: Any,
    chunk_index: int,
    total_chunks: int,
    verbose: bool = False
) -> str:
    if verbose:
        print(f"Processing chunk {chunk_index + 1}/{total_chunks} (size: {len(html_chunk)} chars)")
    
    # Create prompt for this chunk - CRITICAL FIX: Pass user_data
    prompt = create_form_filling_prompt(
        html_chunk, 
        interactive_elements,
        user_data  # Pass the actual user_data, not default
    )
    
    # Send to model
    try:
        response = generate_model_response(model, prompt)
        return response
    except Exception as e:
        if verbose:
            print(f"Error processing chunk {chunk_index + 1}: {str(e)}")
        return f"ERROR: Failed to process chunk {chunk_index + 1}: {str(e)}"
"""
    print("✅ Fix code generated for process_chunk")
    return code_fix


def fix_create_form_filling_prompt():
    """
    Modify the create_form_filling_prompt function to properly use user_data.
    """
    print("Fixing create_form_filling_prompt function...")
    code_fix = """
def create_form_filling_prompt(html_content: str, interactive_elements: List[Dict], user_data: str) -> str:
    # CRITICAL FIX: Always use the passed user_data, never override with default
    prompt = f\"\"\"
You are an AI assistant that helps fill out checkout forms. 

# USER PROFILE DATA
```
{user_data}  # This is the custom user profile data
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
\"\"\"
    return prompt
"""
    print("✅ Fix code generated for create_form_filling_prompt")
    return code_fix


def fix_process_checkout_server_route():
    """
    Ensure the server route properly passes user profile data.
    """
    print("Fixing server process_checkout route...")
    code_fix = """
@app.route('/process-checkout', methods=['POST'])
def process_checkout():
    # ... existing code ...
    
    # Get optional parameters
    user_profile = data.get('user_profile', {})
    if user_profile:
        # Convert user profile to format expected by processor
        user_data = "\\n".join([f"{key}: {value}" for key, value in user_profile.items()])
    else:
        user_data = DEFAULT_USER_DATA
        
    checkout_url = form_data.get('url')
    api_key = data.get('api_key', os.environ.get('GOOGLE_API_KEY'))
    
    # Get advanced parameters
    advanced_settings = data.get('advanced_settings', {})
    fast_mode = advanced_settings.get('fast_mode', False)
    
    # ... more parameters ...
    
    # Process the checkout page - CRITICAL: Always pass user_data
    result = process_checkout_page(
        html_content=html_content,
        checkout_url=checkout_url,
        user_data=user_data,  # Always pass user_data, regardless of fast_mode
        api_key=api_key,
        save_to_file=False,
        verbose=False,
        fast=fast_mode,
        # ... other parameters ...
    )
    
    # ... rest of function ...
"""
    print("✅ Fix code generated for server process_checkout route")
    return code_fix


def apply_fixes():
    """
    Main function to apply all fixes.
    """
    print("\n==== Fix for Fast Mode Profile Issue ====\n")
    print("This script provides fixes for the issue where custom user profiles")
    print("are not being used when fast_mode=True in checkout automation.")
    
    fixes = [
        fix_automate_checkout_form(),
        fix_process_chunk(),
        fix_create_form_filling_prompt(),
        fix_process_checkout_server_route()
    ]
    
    print("\n==== Summary of Fixes ====\n")
    print("1. Modified automate_checkout_form to pass user_data in fast mode chunking")
    print("2. Fixed process_chunk to properly use provided user_data")
    print("3. Fixed create_form_filling_prompt to never override user_data")
    print("4. Updated server route to pass user_data regardless of mode")
    
    print("\n==== Implementation Instructions ====\n")
    print("1. Update checkout_automation.py with the fixed functions")
    print("2. Update server.py for the fixed route implementation")
    print("3. Test with both fast_mode=True and fast_mode=False")
    
    print("\nRun this script to view the fixes.")
    return fixes


if __name__ == "__main__":
    apply_fixes() 