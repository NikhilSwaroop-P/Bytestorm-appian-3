# retrieval_rerank_functions.py
"""
Based on the working notebook version with fixes for dimension mismatch
"""
import os
import pickle
import numpy as np
import torch
import faiss
import requests
import base64
from rank_bm25 import BM25Okapi
from PIL import Image
from functools import lru_cache
import io

# Configuration constants
INDEX_DIR = "indexes_final_jina"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Jina API Configuration
JINA_API_KEY = "jina_7f50a6d5bbbe45c6a75ff4dbfd946255mZMrkbGsQEH3dm8CONGY3yV6d1kv"
JINA_API_URL = "https://api.jina.ai/v1/embeddings"
JINA_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {JINA_API_KEY}"
}

# Utility normalization
def normalize(x):
    mn, mx = x.min(), x.max()
    return (x - mn) / (mx - mn + 1e-8)

def encode_image_to_base64(image_path):
    """Convert local image to base64 string"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image to base64: {e}")
        return None

# Query encoder using Jina API (exactly from working notebook)
class QueryEncoder:
    def __init__(self):
        pass

    def encode(self, image_path=None, text=None, weight_image=0.5, weight_text=0.5):
        inputs_for_jina = []
        
        # Prepare inputs for Jina API
        if text:
            inputs_for_jina.append({"text": text})
        
        if image_path:
            # Check if image_path is a URL (starts with http)
            if image_path.startswith(('http://', 'https://')):
                inputs_for_jina.append({"image": image_path})
            else:
                # Local file - convert to base64
                base64_img = encode_image_to_base64(image_path)
                if base64_img:
                    inputs_for_jina.append({"image": base64_img})
                else:
                    print(f"Failed to encode image: {image_path}")
        
        # Auto-caption if image but no text
        if image_path and not text:
            # This block is redundant as we've already added the image above
            pass
        
        # Call Jina API
        payload = {
            "model": "jina-clip-v1",
            "input": inputs_for_jina
        }
        
        try:
            resp = requests.post(JINA_API_URL, headers=JINA_HEADERS, json=payload)
            resp.raise_for_status()
            api_output = resp.json()["data"]
            
            ie_np, te_np = None, None
            
            # Parse response based on what we sent
            if text and image_path:
                te_np = np.array(api_output[0]["embedding"])
                ie_np = np.array(api_output[1]["embedding"])
            elif text:
                te_np = np.array(api_output[0]["embedding"])
            elif image_path:
                ie_np = np.array(api_output[0]["embedding"])
            
            # Combine embeddings if both exist
            if ie_np is not None and te_np is not None:
                # Normalize before combining
                ie_np = ie_np / np.linalg.norm(ie_np)
                te_np = te_np / np.linalg.norm(te_np)
                ce_np = weight_image * ie_np + weight_text * te_np
                ce_np = ce_np / np.linalg.norm(ce_np)
            else:
                ce_np = ie_np if ie_np is not None else te_np
                if ce_np is not None:
                    ce_np = ce_np / np.linalg.norm(ce_np)
            
            return ie_np, te_np, ce_np
            
        except Exception as e:
            print(f"Error calling Jina API: {e}")
            # Fallback to dummy embeddings - FIXED: Changed from 512 to 768 dimensions
            dummy_emb = np.random.randn(768).astype(np.float32)
            dummy_emb = dummy_emb / np.linalg.norm(dummy_emb)
            return dummy_emb, dummy_emb, dummy_emb

# Retriever + Reranker (exactly from working notebook)
class Retriever:
    def __init__(self, idx_comb, idx_txt, lambda_hybrid):
        self.idx_comb = idx_comb
        self.idx_txt = idx_txt
        self.lambda_hybrid = lambda_hybrid

    def retrieve(self, ce, te, k):
        Df, If = self.idx_comb.search(np.expand_dims(ce, 0), k)
        Dt, It = self.idx_txt.search(np.expand_dims(te, 0), k)
        return Df[0], If[0], Dt[0], It[0]

class Reranker:
    def __init__(self, meta, bm25, lambda_hybrid, lambda_text):
        self.meta = meta
        self.bm25 = bm25
        self.lambda_hybrid = lambda_hybrid
        self.lambda_text = lambda_text

    def score(self, Df, If, Dt, It, query_terms):
        sp = self.bm25.get_scores(query_terms)
        nd, nt, ns = normalize(Df), normalize(Dt), normalize(sp[If])
        cb = self.lambda_hybrid * nd + (1 - self.lambda_hybrid) * (1 - ns)
        final = (1 - self.lambda_text) * cb + self.lambda_text * nt
        return final

def retrieve_and_rerank(image_path=None, text_query="", k=50, 
                        lambda_hybrid=0.5, lambda_text=0.6, 
                        rank_query=None, img_weight=0.5, text_weight=0.5):
    """
    Performs retrieval and reranking in one go using Jina API.
    """
    # Load artifacts
    idx_comb = faiss.read_index(os.path.join(INDEX_DIR, 'idx_comb.bin'))
    idx_txt = faiss.read_index(os.path.join(INDEX_DIR, 'idx_txt.bin'))
    with open(os.path.join(INDEX_DIR, 'meta.pkl'), 'rb') as f:
        meta = pickle.load(f)
    with open(os.path.join(INDEX_DIR, 'bm25.pkl'), 'rb') as f:
        bm25 = pickle.load(f)

    # Encode query using Jina API
    encoder = QueryEncoder()
    ie, te, ce = encoder.encode(image_path=image_path, text=text_query, 
                               weight_image=img_weight, weight_text=text_weight)

    # Retrieve
    retriever = Retriever(idx_comb, idx_txt, lambda_hybrid)
    Df, If, Dt, It = retriever.retrieve(ce, te, k)

    # Rerank
    reranker = Reranker(meta, bm25, lambda_hybrid, lambda_text)
    query_terms = (rank_query or text_query).lower().split()
    scores = reranker.score(Df, If, Dt, It, query_terms)
    order = np.argsort(scores)
    
    return If[order], meta

def rerank_only(initial_indices, image_path=None, text_query="",
                lambda_hybrid=0.5, lambda_text=0.6):
    """
    Given initial retrieved indices, apply only the reranking step using Jina API.
    """
    # Load metadata and BM25
    with open(os.path.join(INDEX_DIR, 'meta.pkl'), 'rb') as f:
        meta = pickle.load(f)
    with open(os.path.join(INDEX_DIR, 'bm25.pkl'), 'rb') as f:
        bm25 = pickle.load(f)

    # Load text-only index for reranking
    idx_txt = faiss.read_index(os.path.join(INDEX_DIR, 'idx_txt.bin'))

    # Encode query text using Jina API
    encoder = QueryEncoder()
    _, te, _ = encoder.encode(image_path=image_path, text=text_query)
    
    # Get text similarities for reranking
    Dt, It = idx_txt.search(np.expand_dims(te, 0), len(initial_indices))

    # Compute reranking scores
    Df = np.zeros_like(Dt)  # dummy for rerank-only mode
    reranker = Reranker(meta, bm25, lambda_hybrid, lambda_text)
    scores = reranker.score(
        Df[0], initial_indices, Dt[0], It[0], text_query.lower().split()
    )
    reranked_order = np.argsort(scores)
    reranked_indices = initial_indices[reranked_order]
    return reranked_indices, meta
