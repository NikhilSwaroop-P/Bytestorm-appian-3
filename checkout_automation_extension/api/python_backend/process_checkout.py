"""
Process Checkout Page Module

This module provides extended functionality for checkout page automation.
It acts as a wrapper around the basic checkout automation to provide more
comprehensive analysis and features.

Functions:
1. process_checkout_page() - Main entry point for advanced checkout processing
2. analyze_checkout_page() - Analyzes a checkout page and generates insights
3. optimize_checkout_strategy() - Optimizes checkout strategy based on page analysis

"""

import json
import os
from typing import Dict, List, Any, Optional
from checkout_automation import automate_checkout_form, initialize_model

def process_checkout_page(
    html_content: str,
    checkout_url: Optional[str] = None,
    user_data: Optional[str] = None,
    api_key: str = 'AIzaSyBXZLvzTn2Jf52PZ_PgwDlNRtWUu37aPx4',
    api_keys: Optional[List[str]] = None,
    save_to_file: bool = True,
    output_file: str = 'form_filling_actions.json',
    verbose: bool = True,
    fast: bool = False,
    depth: int = 1,
    thinking_budget: int = 1024,
    max_chunks: int = 4,
    min_size_for_chunking: int = 1000,
    max_workers: int = None
) -> Dict[str, Any]:
    """
    Enhanced checkout page processing with additional analysis and insights.
    
    This function extends the basic checkout automation with more sophisticated
    analysis, including site recognition, checkout flow optimization, and
    detailed reporting.
    
    Args:
        html_content (str): The HTML content of the checkout form
        checkout_url (str, optional): The URL of the checkout page for site recognition
        user_data (str, optional): User data for form filling. If not provided, default test data is used.
        api_key (str): Single Google Generative AI API key (for backward compatibility)
        api_keys (List[str], optional): List of Google Generative AI API keys for automatic cycling
        save_to_file (bool): Whether to save results to JSON file
        output_file (str): Output file name for saving results
        verbose (bool): Whether to print detailed progress information
        fast (bool): If True, use Gemma models instead of Gemini for faster processing
        depth (int): Model depth when using fast mode: 0=1B, 1=4B, 2=12B
        thinking_budget (int): Number of tokens for thinking budget when using Gemini
        max_chunks (int): Maximum number of chunks to split HTML into
        min_size_for_chunking (int): Minimum size in bytes to trigger chunking
        max_workers (int): Maximum number of worker threads for parallel processing
        
    Returns:
        Dict[str, Any]: Complete structured data with all analysis results
    """
    if verbose:
        print("🚀 Starting enhanced checkout page processing...")
    
    # Use default test data if user data is not provided
    if user_data is None:
        user_data = """
        name: John Doe
        email: john.doe@example.com
        phone: +1-555-0123
        address: 123 Main St
        city: New York
        state: NY
        zip: 10001
        country: United States
        card_number: 4111111111111111
        card_expiry: 12/25
        card_cvv: 123
        """
        if verbose:
            print("ℹ️  Using default test user data")
    
    # Site recognition (if URL is provided)
    site_info = {}
    if checkout_url:
        site_info = analyze_site_from_url(checkout_url, verbose)
    
    # Process the checkout form using the core automation
    if verbose:
        print("🔄 Processing checkout form with AI automation...")
        if fast:
            gemma_models = ["gemma-3-1b-it", "gemma-3-4b-it", "gemma-3-12b-it"]
            selected_model = gemma_models[min(depth, 2)]
            print(f"💨 Using fast mode with model: {selected_model}")
        else:
            print(f"🧠 Using Gemini model with thinking budget: {thinking_budget}")
    
    # Set thinking budget globally in checkout_automation module
    import checkout_automation
    checkout_automation.THINKING_BUDGET = thinking_budget
    
    automation_result = automate_checkout_form(
        html_content=html_content,
        user_data=user_data,
        api_key=api_key,
        api_keys=api_keys,
        save_to_file=True,  # We'll handle saving separately
        # verbose=verbose,
        verbose=True,  # Always verbose for enhanced processing
        fast=fast,
        depth=depth,
        max_chunks=max_chunks,
        min_size_for_chunking=min_size_for_chunking,
        max_workers=max_workers
    )
    
    # Add site-specific insights
    enhanced_result = {
        **automation_result,
        'site_analysis': site_info,
        'processing_metadata': {
            'checkout_url': checkout_url,
            'processing_time': '...',  # Would be calculated in real implementation
            'enhancement_features': ['site_recognition', 'advanced_validation', 'optimization_insights']
        }
    }
    
    # Generate additional insights
    if verbose:
        print("🔍 Generating advanced insights...")
    
    insights = generate_checkout_insights(enhanced_result, verbose)
    enhanced_result['insights'] = insights
    
    # Save enhanced results
    if save_to_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_result, f, indent=2, ensure_ascii=False)
            if verbose:
                print(f"💾 Enhanced results saved to: {output_file}")
        except Exception as e:
            if verbose:
                print(f"❌ Failed to save enhanced results: {e}")
    
    if verbose:
        print("✅ Enhanced checkout processing completed!")
    
    return enhanced_result


def analyze_site_from_url(checkout_url: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Analyze the site from URL to provide site-specific insights.
    
    Args:
        checkout_url (str): URL of the checkout page
        verbose (bool): Whether to print analysis information
        
    Returns:
        Dict[str, Any]: Site analysis information
    """
    # Return default values if checkout_url is None
    if checkout_url is None:
        if verbose:
            print("No checkout URL provided, using default site analysis")
        return {
            'domain': 'unknown',
            'platform': 'unknown',
            'is_https': False,
            'path': '',
            'checkout_type': 'standard_checkout'
        }
        
    if verbose:
        print(f"🌍 Analyzing site from URL: {checkout_url}")
    
    # Extract domain and basic site info
    from urllib.parse import urlparse
    parsed_url = urlparse(checkout_url)
    domain = parsed_url.netloc.lower()
    
    # Common e-commerce platform detection
    platform_indicators = {
        'shopify': ['shopify.com', 'myshopify.com'],
        'woocommerce': ['wp-content', 'woocommerce'],
        'magento': ['magento', 'pub/static'],
        'amazon': ['amazon.com', 'amazon.'],
        'ebay': ['ebay.com'],
        'etsy': ['etsy.com'],
        'bigcommerce': ['bigcommerce.com']
    }
    
    detected_platform = 'unknown'
    for platform, indicators in platform_indicators.items():
        if any(indicator in checkout_url.lower() for indicator in indicators):
            detected_platform = platform
            break
    
    site_analysis = {
        'domain': domain,
        'platform': detected_platform,
        'is_https': parsed_url.scheme == 'https',
        'path': parsed_url.path,
        'checkout_type': determine_checkout_type(checkout_url)
    }
    
    if verbose:
        print(f"   Platform: {detected_platform}")
        print(f"   Domain: {domain}")
        print(f"   HTTPS: {site_analysis['is_https']}")
    
    return site_analysis


def determine_checkout_type(checkout_url: str) -> str:
    """
    Determine the type of checkout based on URL patterns.
    
    Args:
        checkout_url (str): URL of the checkout page
        
    Returns:
        str: Type of checkout (single_page, multi_step, guest, etc.)
    """
    # Return default value if checkout_url is None
    if checkout_url is None:
        return 'standard_checkout'
        
    url_lower = checkout_url.lower()
    
    if 'guest' in url_lower:
        return 'guest_checkout'
    elif 'step' in url_lower or 'multi' in url_lower:
        return 'multi_step'
    elif 'express' in url_lower:
        return 'express_checkout'
    else:
        return 'standard_checkout'


def generate_checkout_insights(enhanced_result: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Generate advanced insights from the checkout analysis.
    
    Args:
        enhanced_result (Dict[str, Any]): Enhanced result data
        verbose (bool): Whether to print insight generation information
        
    Returns:
        Dict[str, Any]: Generated insights
    """
    if verbose:
        print("💡 Generating checkout optimization insights...")
    
    # Extract key data for analysis
    actions = enhanced_result.get('actions', [])
    validation_status = enhanced_result.get('validation_status', {})
    cost_optimization = enhanced_result.get('cost_optimization', {})
    site_analysis = enhanced_result.get('site_analysis', {})
    
    insights = {
        'form_complexity': analyze_form_complexity(actions),
        'optimization_opportunities': identify_optimization_opportunities(actions, cost_optimization),
        'risk_assessment': assess_checkout_risks(validation_status, site_analysis),
        'recommendations': generate_recommendations(enhanced_result)
    }
    
    if verbose:
        print(f"   Form complexity: {insights['form_complexity']['level']}")
        print(f"   Optimization opportunities: {len(insights['optimization_opportunities'])}")
        print(f"   Risk level: {insights['risk_assessment']['level']}")
    
    return insights


def analyze_form_complexity(actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the complexity of the checkout form.
    
    Args:
        actions (List[Dict[str, Any]]): List of form actions
        
    Returns:
        Dict[str, Any]: Form complexity analysis
    """
    total_actions = len(actions)
    input_actions = sum(1 for action in actions if action.get('action_type') == 'input')
    button_actions = sum(1 for action in actions if action.get('action_type') == 'button')
    
    if total_actions <= 5:
        complexity_level = 'simple'
    elif total_actions <= 15:
        complexity_level = 'moderate'
    else:
        complexity_level = 'complex'
    
    return {
        'level': complexity_level,
        'total_actions': total_actions,
        'input_fields': input_actions,
        'buttons': button_actions,
        'estimated_completion_time': f"{total_actions * 3}-{total_actions * 5} seconds"
    }


def identify_optimization_opportunities(actions: List[Dict[str, Any]], cost_optimization: Dict[str, Any]) -> List[str]:
    """
    Identify opportunities for checkout optimization.
    
    Args:
        actions (List[Dict[str, Any]]): List of form actions
        cost_optimization (Dict[str, Any]): Cost optimization data
        
    Returns:
        List[str]: List of optimization opportunities
    """
    opportunities = []
    
    # Check for coupon opportunities
    if cost_optimization.get('coupons_available'):
        opportunities.append("Apply available coupons for cost savings")
    
    # Check for form field optimization
    required_fields = [action for action in actions if 'required' in action.get('description', '').lower()]
    if len(required_fields) > 10:
        opportunities.append("Consider guest checkout to reduce form complexity")
    
    # Check for autofill opportunities
    common_fields = ['email', 'name', 'address', 'phone']
    fillable_fields = [action for action in actions if any(field in action.get('element_id', '').lower() for field in common_fields)]
    if len(fillable_fields) > 5:
        opportunities.append("Enable browser autofill for faster completion")
    
    return opportunities


def assess_checkout_risks(validation_status: Dict[str, Any], site_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assess potential risks in the checkout process.
    
    Args:
        validation_status (Dict[str, Any]): Validation status data
        site_analysis (Dict[str, Any]): Site analysis data
        
    Returns:
        Dict[str, Any]: Risk assessment
    """
    risk_factors = []
    risk_level = 'low'
    
    # Check validation issues
    if not validation_status.get('is_valid', True):
        risk_factors.append("Form validation issues detected")
        risk_level = 'high'
    
    # Check HTTPS
    if not site_analysis.get('is_https', True):
        risk_factors.append("Non-HTTPS connection detected")
        risk_level = 'high'
    
    # Check platform recognition
    if site_analysis.get('platform') == 'unknown':
        risk_factors.append("Unknown e-commerce platform")
        if risk_level == 'low':
            risk_level = 'medium'
    
    return {
        'level': risk_level,
        'factors': risk_factors,
        'recommendation': 'Proceed with caution' if risk_level == 'high' else 'Safe to proceed'
    }


def generate_recommendations(enhanced_result: Dict[str, Any]) -> List[str]:
    """
    Generate actionable recommendations based on the analysis.
    
    Args:
        enhanced_result (Dict[str, Any]): Complete enhanced result data
        
    Returns:
        List[str]: List of recommendations
    """
    recommendations = []
    
    # Validation-based recommendations
    validation_status = enhanced_result.get('validation_status', {})
    if not validation_status.get('is_valid', True):
        recommendations.append("Complete missing required information before proceeding")
    
    # Cost optimization recommendations
    cost_optimization = enhanced_result.get('cost_optimization', {})
    if cost_optimization.get('recommended_coupon') and cost_optimization.get('recommended_coupon') != 'None':
        savings = cost_optimization.get('estimated_savings', 'unknown')
        recommendations.append(f"Apply coupon '{cost_optimization['recommended_coupon']}' to save {savings}")
    
    # Security recommendations
    site_analysis = enhanced_result.get('site_analysis', {})
    if not site_analysis.get('is_https', True):
        recommendations.append("Verify the site security before entering payment information")
    
    # General recommendations
    recommendations.append("Review all information before submitting the order")
    
    return recommendations


# Example usage
if __name__ == "__main__":
    # Example with enhanced processing
    sample_html = """
    <form id="checkout-form">
        <input type="text" id="first-name" name="first_name" required>
        <input type="email" id="email" name="email" required>
        <input type="text" id="coupon-code" name="coupon">
        <button type="submit" id="submit-btn">Place Order</button>
    </form>
    """
    
    # Example with default settings (Gemini model)
    result_high_quality = process_checkout_page(
        html_content=sample_html,
        checkout_url="https://example-store.com/checkout",
        verbose=True,
        fast=False,
        thinking_budget=2048
    )
    
    # Example with fast mode (Gemma model)
    result_fast = process_checkout_page(
        html_content=sample_html,
        checkout_url="https://example-store.com/checkout",
        verbose=True,
        fast=True,
        depth=1,  # Use Gemma 4B model
        max_chunks=4,
        min_size_for_chunking=1000
    )
    
    print(json.dumps(result_high_quality, indent=2))
