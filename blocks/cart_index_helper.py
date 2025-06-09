"""
Helper module for cart suggestions with index loading functions
"""
import os
import pickle
import faiss
import numpy as np

# Index directory configuration
INDEX_DIR = "indexes_final_jina"

def load_indexes():
    """
    Load the necessary indexes and metadata for cart suggestions
    
    Returns:
        tuple: (idx_comb, meta) - The combined index and metadata
    """
    try:
        # Load the combined index
        idx_comb = faiss.read_index(os.path.join(INDEX_DIR, 'idx_comb.bin'))
        
        # Load metadata
        with open(os.path.join(INDEX_DIR, 'meta.pkl'), 'rb') as f:
            meta = pickle.load(f)
            
        return idx_comb, meta
    except Exception as e:
        print(f"Error loading indexes: {e}")
        # Return empty index and metadata as fallback
        return None, []

def get_item_embedding(item):
    """
    Extract the embedding from an item in the metadata
    
    Args:
        item: The metadata item
        
    Returns:
        numpy.ndarray: The embedding vector
    """
    try:
        # Extract embedding from metadata item
        if isinstance(item, dict):
            if 'item_embedding' in item:
                emb = item['item_embedding']
            elif 'embedding' in item:
                emb = item['embedding']
            else:
                # Fallback - return dummy embedding
                dummy_emb = np.random.randn(768).astype(np.float32)
                dummy_emb = dummy_emb / np.linalg.norm(dummy_emb)
                return dummy_emb
                
            # Convert to proper numpy array if needed
            if not isinstance(emb, np.ndarray):
                emb = np.array(emb, dtype=np.float32)
                
            # Normalize if needed
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
                
            return emb
        else:
            # Item is not a dictionary, possibly already an embedding
            if isinstance(item, np.ndarray):
                return item
            else:
                # Try to convert to numpy array
                try:
                    emb = np.array(item, dtype=np.float32)
                    # Normalize if needed
                    norm = np.linalg.norm(emb)
                    if norm > 0:
                        emb = emb / norm
                    return emb
                except:
                    # Cannot convert, return dummy embedding
                    dummy_emb = np.random.randn(768).astype(np.float32)
                    dummy_emb = dummy_emb / np.linalg.norm(dummy_emb)
                    return dummy_emb
    except Exception as e:
        print(f"Error in get_item_embedding: {e}")
        # Return a normalized dummy embedding as fallback
        dummy_emb = np.random.randn(768).astype(np.float32)
        dummy_emb = dummy_emb / np.linalg.norm(dummy_emb)
        return dummy_emb

def search(index, query_embedding, k=10):
    """
    Search the index with a query embedding
    
    Args:
        index: FAISS index
        query_embedding: The query embedding vector
        k: Number of results to return
        
    Returns:
        tuple: (distances, indices) - Search results
    """
    try:
        if index is None:
            # Fallback for when index loading failed
            print("Index is None, returning empty results")
            return [], []
            
        # Handle different query_embedding formats
        if isinstance(query_embedding, tuple) and len(query_embedding) == 3:
            # This is likely from retrival.QueryEncoder().encode() which returns (ie, te, ce)
            # Use the combined embedding (ce) which is the third element
            query_embedding = query_embedding[2]
            
        # Ensure query embedding is properly shaped and normalized
        query_np = np.asarray(query_embedding).astype('float32')
        if len(query_np.shape) == 1:
            # Normalize the vector
            norm = np.linalg.norm(query_np)
            if norm > 0:
                query_np = query_np / norm
            query_np = np.expand_dims(query_np, 0)
        
        # Search the index
        distances, indices = index.search(query_np, k)
        
        # Check if we got any results
        if len(indices[0]) == 0:
            print("Search returned no results")
            return [], []
            
        return distances[0], indices[0]
    except Exception as e:
        print(f"Error searching index: {e}")
        return [], []
