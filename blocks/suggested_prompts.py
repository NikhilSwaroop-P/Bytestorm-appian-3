import os
import google.generativeai as genai
import json
import time

# Initialize client
genai.configure(api_key='AIzaSyBS2npulOMMZ9WRj7b-UpoYHXVSa0Jju4o')
model = genai.GenerativeModel('gemini-2.0-flash')

# Simple in-memory cache to avoid redundant API calls
suggestion_cache = {}
CACHE_EXPIRY = 3600  # Cache entries expire after 1 hour (in seconds)

# Prompt template for generating suggested search queries
prompt_template = '''
You are an AI shopping assistant for an e-commerce website. Based on the user's previous search query, past queries, preference data, and product context, 
suggest 3 alternative search queries that the user might be interested in.

### User's Current Query:
"""
{user_query}
"""

### Current Product Context:
"""
Base Product (Back Bone): {back_bone}
Detailed Product Description: {current_text}
"""

### User's Past Queries (most recent first):
"""
{past_queries}
"""

### User's Preference Data:
"""
{user_preferences}
"""

Guidelines for the suggested search queries:
1. One query should suggest different variations (colors, sizes, styles, materials) of the current product
2. One query should suggest different brands or alternatives to the current product
3. One query should suggest complementary products or accessories that would go well with the current product

Focus heavily on the current product context when generating suggestions. The base product (back bone) describes the fundamental product type, while the detailed description contains specific attributes.

Consider the user's past queries when generating suggestions. The current query and product context should be given the highest priority, followed by recent past queries, and then the user's general preferences.

The suggestions should be concise, search-oriented phrases rather than questions.

### Output Format:
Return exactly 3 suggested search queries in JSON format:
```json
{
  "suggestions": [
    "First suggested search",
    "Second suggested search",
    "Third suggested search"
  ]
}
```

### Examples:

User query: "Wireless headphones with noise cancellation"
Current Product Context: "Headphones - Bluetooth audio device for listening - Electronics" / "Sony WH-1000XM4 Wireless Noise Cancelling Headphones - Premium Sony headphones with industry-leading noise cancellation, 30-hour battery life, and touch controls - Sony Black Electronics"

```json
{
  "suggestions": [
    "White Sony WH-1000XM4 headphones",
    "Bose QuietComfort 45 noise cancelling headphones",
    "Replacement ear pads for Sony WH-1000XM4"
  ]
}
```

Now, generate 3 suggested search queries based on the user input and context provided:
'''

def get_suggested_prompts(user_query, current_text=None, back_bone=None):
    """
    Generate suggested search queries based on the user's query
    
    Args:
        user_query (str): The user's previous query
        current_text (str, optional): Current text from the main pipeline
        back_bone (str, optional): Back bone text from the main pipeline
        
    Returns:
        list: A list of 3 suggested search queries
    """
    # Check cache first
    cache_key = f"{user_query.strip().lower()}_{current_text or ''}_{back_bone or ''}"
    current_time = time.time()
    
    # Return cached suggestions if available and not expired
    if cache_key in suggestion_cache:
        cache_entry = suggestion_cache[cache_key]
        if current_time - cache_entry['timestamp'] < CACHE_EXPIRY:
            return cache_entry['suggestions']
    
    # Get past queries from logs.txt
    past_queries = []
    try:
        with open('./logs.txt', 'r') as f:
            # Get the last 5 queries (or less if there aren't that many)
            for line in f.readlines()[:5]:
                parts = line.strip().split(',')
                if len(parts) >= 3 and parts[1] == 'search':
                    past_queries.append(parts[2])
    except Exception as e:
        print(f"Error reading logs file: {e}")
    
    # Get user preferences using history_pref module
    user_preferences = ""
    try:
        from blocks import history_pref
        # Extract the base product name from the query (simplistic approach)
        base_product = user_query.split()[0] if user_query else "product"
        user_preferences = history_pref.generate_user_pref_query(base_product, './logs.txt')
    except Exception as e:
        print(f"Error getting user preferences: {e}")
      # Generate new suggestions using the API
    try:
        # Format the prompt with the user's query, current context, past queries, and preferences
        content = prompt_template.format(
            user_query=user_query,
            back_bone=back_bone or "No product type information available",
            current_text=current_text or "No detailed product description available",
            past_queries="\n".join(past_queries) if past_queries else "No past queries available",
            user_preferences=user_preferences if user_preferences else "No preference data available"
        )
        
        # Call the Gemini API
        response = model.generate_content(content)
        output = response.text
        
        # Extract the JSON part from the response
        start = output.find('{')
        end = output.rfind('}') + 1
        if start >= 0 and end > start:
            json_part = output[start:end]
            
            try:
                # Parse the JSON response
                json_data = json.loads(json_part)
                suggestions = json_data.get('suggestions', [])
                
                # Ensure we have exactly 3 suggestions
                if len(suggestions) != 3:
                    # If we don't have exactly 3, generate some defaults based on the query
                    suggestions = [
                        f"{user_query} in different colors",
                        f"Best brands for {user_query}",
                        f"Accessories for {user_query}"
                    ]
                  # Cache the result
                suggestion_cache[cache_key] = {
                    'suggestions': suggestions,
                    'timestamp': current_time,
                    'context': {
                        'current_text': current_text,
                        'back_bone': back_bone
                    }
                }
                
                return suggestions
                
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from API response: {e}")
                # Return default suggestions on error
                return generate_default_suggestions(user_query)
        else:
            print("Could not find JSON in API response")
            return generate_default_suggestions(user_query)
            
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        return generate_default_suggestions(user_query)

def generate_default_suggestions(query):
    """Generate default suggestions when the API call fails"""
    default_suggestions = [
        f"{query} in different colors",
        f"Best brands for {query}",
        f"Accessories for {query}"
    ]
    return default_suggestions

def clear_cache():
    """Clear the suggestion cache"""
    suggestion_cache.clear()
    
def prune_expired_cache():
    """Remove expired entries from the cache"""
    current_time = time.time()
    keys_to_remove = []
    
    for key, entry in suggestion_cache.items():
        if current_time - entry['timestamp'] >= CACHE_EXPIRY:
            keys_to_remove.append(key)
            
    for key in keys_to_remove:
        suggestion_cache.pop(key, None) 