"""
Cart product suggestion module with MMR search implementation
"""
import os
import numpy as np
import pickle
import logging
from blocks import retrival
from blocks import history_pref
from blocks import cart_index_helper

# Configure logging
logger = logging.getLogger("cart_suggestions")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Load metadata and index
INDEX_DIR = "indexes_final_jina"
META_PATH = os.path.join(INDEX_DIR, "meta.pkl")

def load_metadata():
    """Load metadata from pickle file"""
    try:
        with open(META_PATH, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata: {e}")
        return []

def mmr_search(query_embedding, index, metadata, query_results, lambda_param=0.5, k=10):
    """
    Apply Maximum Marginal Relevance to get diverse results
    
    Args:
        query_embedding: Embedding vector of the query
        index: FAISS index for similarity search
        metadata: List of product metadata
        query_results: Initial query results (indices)
        lambda_param: Trade-off between relevance and diversity (0 to 1)
        k: Number of results to return
        
    Returns:
        List of diverse product indices
    """
    # Import numpy for array operations
    import numpy as np
    
    # Handle tuple from QueryEncoder
    if isinstance(query_embedding, tuple) and len(query_embedding) == 3:
        # Use the combined embedding (last element)
        query_embedding = query_embedding[2]
    
    # Check if query_results is empty
    if query_results is None or isinstance(query_results, (list, np.ndarray)) and len(query_results) == 0:
        logger.warning("Empty query results provided to mmr_search")
        return []
    
    # Initialize results with the first item
    selected = [query_results[0]]
    
    # Make sure the first item index is valid for metadata
    if selected[0] >= len(metadata):
        logger.error(f"Index {selected[0]} out of range for metadata with length {len(metadata)}")
        return []
        
    selected_embeddings = [cart_index_helper.get_item_embedding(metadata[query_results[0]])]
    
    # Initialize the candidate set with the rest of the results
    candidates = query_results[1:]
      # Helper function to compute cosine similarity
    def cosine_similarity(a, b):
        # Handle tuple input (in case query_embedding is a tuple from QueryEncoder)
        if isinstance(a, tuple) and len(a) == 3:
            a = a[2]  # Use combined embedding (last element)
            
        # Ensure inputs are properly formatted arrays
        a_array = np.asarray(a, dtype=np.float32)
        b_array = np.asarray(b, dtype=np.float32)
        
        # Calculate norms
        a_norm = np.linalg.norm(a_array)
        b_norm = np.linalg.norm(b_array)
        
        # Handle zero division
        if a_norm == 0 or b_norm == 0:
            return 0.0
            
        return float(np.dot(a_array, b_array) / (a_norm * b_norm))
    
    # Iterate until we have k items or no more candidates
    while len(selected) < k and candidates:
        best_score = -np.inf
        best_idx = -1
        best_candidate_idx = -1
          # For each candidate, compute the MMR score
        for i, candidate_idx in enumerate(candidates):
            candidate_embedding = cart_index_helper.get_item_embedding(metadata[candidate_idx])
            
            # Compute relevance to query (first term in MMR)
            relevance = cosine_similarity(query_embedding, candidate_embedding)
            
            # Compute diversity (second term in MMR)
            max_similarity = max(
                [cosine_similarity(candidate_embedding, sel_emb) for sel_emb in selected_embeddings]
            ) if selected_embeddings else 0
            
            # Compute MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
            
            # Update best candidate if this one is better
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = i
                best_candidate_idx = candidate_idx
        
    # Add the best candidate to selected items
        if best_idx != -1:
            selected.append(best_candidate_idx)
            selected_embeddings.append(cart_index_helper.get_item_embedding(metadata[best_candidate_idx]))
            candidates.pop(best_idx)
        else:
            break
    
    return selected

def get_cart_suggestions(cart_items, user_history=None, num_suggestions=8):
    """
    Get product suggestions based on items in the cart and user history
    
    Args:
        cart_items: List of products in the cart
        user_history: Optional user history data
        num_suggestions: Number of suggestions to return
        
    Returns:
        List of suggested products
    """
    try:
        logger.debug(f"Getting suggestions for {len(cart_items)} cart items")
        
        # Load metadata
        metadata = load_metadata()
        if not metadata:
            logger.error("Failed to load metadata")
            return []
        
        # Initialize the query encoder
        query_encoder = retrival.QueryEncoder()
        
        # Build a combined query from cart items titles and categories
        cart_query = " ".join([
            f"{item.get('title', '')} {item.get('category', '')}" 
            for item in cart_items
        ])
        
        logger.debug(f"Combined cart query: {cart_query}")
        
        # Get user preferences if available
        user_pref_query = ""
        if user_history:
            try:
                # Extract a base product name from the cart items
                base_product = cart_items[0].get('title', '').split()[0] if cart_items else "product"
                user_pref_query = history_pref.generate_user_pref_query(base_product, './logs.txt')
                logger.debug(f"User preference query: {user_pref_query}")
            except Exception as e:
                logger.error(f"Error getting user preferences: {e}")
        
        # Combine cart query with user preferences
        combined_query = f"{cart_query} {user_pref_query}".strip()
          # Get query embedding
        query_embedding = query_encoder.encode(text=combined_query)
        
        # Load the combined index
        idx_comb, meta = cart_index_helper.load_indexes()
        if idx_comb is None:
            logger.error("Failed to load index")
            return []
        
        # Get initial search results
        distances, query_results = cart_index_helper.search(idx_comb, query_embedding, k=50)
          # Check if we got any results
        if query_results is None or isinstance(query_results, (list, np.ndarray)) and len(query_results) == 0:
            logger.error("Search returned no results")
            return []
        
        # Apply MMR to get diverse results
        diverse_results = mmr_search(
            query_embedding, 
            idx_comb, 
            metadata, 
            query_results, 
            lambda_param=0.6,  # Favor relevance over diversity
            k=num_suggestions
        )
          # If MMR returned no results, return empty list
        if diverse_results is None or isinstance(diverse_results, (list, np.ndarray)) and len(diverse_results) == 0:
            logger.warning("MMR returned no diverse results")
            return []
        
        # Filter out items that are already in the cart
        cart_item_ids = [int(item.get('id')) if item.get('id') is not None else -1 for item in cart_items]
        filtered_results = [idx for idx in diverse_results if idx not in cart_item_ids]
        
        # If no results after filtering, return empty list
        if not filtered_results:
            logger.warning("No suggestions left after filtering out cart items")
            return []
        
        # Prepare the result products
        suggestions = []
        for idx in filtered_results[:num_suggestions]:
            if idx >= len(metadata):
                logger.warning(f"Index {idx} out of range for metadata with length {len(metadata)}")
                continue
                
            item = metadata[idx]
            
            # Format price
            price = item.get('price', '')
            if isinstance(price, str) and not price.startswith('₹'):
                price = f"₹{price}"
            
            suggestion = {
                'id': idx,
                'title': item.get('name', ''),
                'description': item.get('discription', ''),
                'price': price,
                'image_url': item.get('image_url', ''),
                'rating': item.get('rating', 0),
                'rating_count': item.get('rating_count', 0),
            }
            suggestions.append(suggestion)
        
        logger.debug(f"Returning {len(suggestions)} suggestions")
        return suggestions
        
    except Exception as e:
        logger.error(f"Error getting cart suggestions: {e}")
        return []
