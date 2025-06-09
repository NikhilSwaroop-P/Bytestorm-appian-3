# main_pipeline.py
"""
Pipeline entrypoint with debug logging and parallel processing
"""

import os
# Fix OpenMP library conflict
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import logging
from pydoc import text
import time
import concurrent.futures
from functools import partial
from blocks import query_manipulations, special_case_handler, image_extractions, retrival, extract_tags
from blocks import voyage_rerank
from blocks import fast_special_filter
from blocks import history_pref

# Configure logging
def setup_logger():
    logger = logging.getLogger("main_pipeline")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger

logger = setup_logger()

current_text = ''
back_bone = ''
retrieved_idx = None
meta = None
img_weight = 0.3
text_weight = 0.7

# Parallel processing helpers
def process_tags_and_update_metadata(final_out, meta, current_text):
    """Process tags in parallel and update metadata"""
    tags = extract_tags.get_tags(current_text)
    
    def update_item_tags(idx):
        if idx < len(meta):
            meta[idx]['tags'] = tags
            return idx
        return None
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(update_item_tags, final_out))
    
    return tags

def main_pipeline(modification_text: str, reset: bool, image_path: str = None) -> int:
    """
    Main pipeline to process the modification text and current text.
    Uses parallel processing where appropriate to optimize performance.
    """
    global current_text
    global back_bone
    global retrieved_idx
    global meta, img_weight, text_weight
    
    logger.debug(f"Starting main_pipeline with: modification_text='{modification_text}', reset={reset}, image_path={image_path}")
    logger.debug(f"Initial state: current_text='{current_text}', back_bone='{back_bone}'")
    
    query_dict = {}
    special_case_dict = None
    conflict = False
    final_out = None
    
    # Start parsing the query in a separate thread while other operations run
    with concurrent.futures.ThreadPoolExecutor() as executor:
        filter_list_future = executor.submit(fast_special_filter.parse_split_query, modification_text)
        
        if reset:
            logger.debug("Reset is True: extracting base description")
            intent = image_extractions.intention(image_path, modification_text)
            logger.debug(f"Intent result: {intent}")
            
            if intent['intent'] == 1:
                logger.debug("Special intent detected")
                image_path = None
                current_text = intent['recommendations_query']
                logger.debug(f"Intent is special, current_text is now: {current_text}")
                img_weight = 0
                text_weight = 1
            else:
                logger.debug("No special intent, proceeding with image extraction")
                img_weight = 0.3
                text_weight = 0.7
                
            if image_path:
                logger.debug(f"Extracting description from image: {image_path}")
                back_bone, current_text = image_extractions.discription(image_path)
                logger.debug(f"Image description extracted: back_bone='{back_bone}', current_text='{current_text}'")
            else:
                logger.debug("No image path, extracting from text")
                back_bone, current_text = image_extractions.text_split(current_text)
                logger.debug(f"Text split: back_bone='{back_bone}', current_text='{current_text}'")
                
            # Generate user preference query in parallel
            pref_future = executor.submit(history_pref.generate_user_pref_query, back_bone, './logs.txt')
        
        # Process image in parallel if available
        if image_path:
            logger.debug(f"Modifying query based on image: {image_path}")
            modify_future = executor.submit(image_extractions.modify_query, image_path, modification_text)
        
        # Wait for parallel operations to complete
        if reset and 'pref_future' in locals():
            modification_text = pref_future.result()
        
        if image_path and 'modify_future' in locals():
            modification_text = modify_future.result()
            logger.debug(f"Modified query: '{modification_text}'")
        
        # Get the filter list result
        filter_list = filter_list_future.result()
    
    
    if modification_text:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit both tasks in parallel
            query_dict_future = executor.submit(query_manipulations.split_query, modification_text)
            conflict_future = executor.submit(query_manipulations.conflict_check, current_text, modification_text)
            
            # Get results
            query_dict = query_dict_future.result()
            conflict = conflict_future.result()
            
            logger.debug(f"Query dict after splitting: {query_dict}")
            logger.debug(f"Conflict detected: {conflict}")
    else:
        logger.debug("No modification text provided, query_dict will be empty")
        query_dict = {}
    
    # Process general and special query parts    
    if query_dict.get('general'):
        logger.debug(f"Updating current_text with general query: '{query_dict['general']}'")
        prev_text = current_text
        current_text = image_extractions.alternate_current_text(current_text, query_dict['general'])
        logger.debug(f"Text updated: '{prev_text}' -> '{current_text}'")
        
    if query_dict.get('special'):
        logger.debug(f"Processing special case from query: {query_dict['special']}")
        special_case_dict = special_case_handler.special_case_split(query_dict)
        logger.debug(f"Special case dictionary: {special_case_dict}")
        logger.debug(f"Special case dictionary: {special_case_dict}")
    
    # Main retrieval and reranking logic
    if conflict or reset:
        logger.debug(f"Retrieving and reranking due to conflict={conflict} or reset={reset}")
        retrieved_idx, meta = retrival.retrieve_and_rerank(
            image_path=image_path, 
            text_query=back_bone, 
            rank_query=current_text, 
            img_weight=img_weight, 
            text_weight=text_weight, 
            k=200
        )
        
        logger.debug("Reranking with voyage_rerank")
        reranked_idx, meta = voyage_rerank.rerank_products(retrieved_idx, meta, current_text, k=50)
        logger.debug(f"Reranked to {len(reranked_idx) if reranked_idx else 0} items")
        
        # Ensure reranked_idx isn't None before proceeding
        if reranked_idx is None or len(reranked_idx) == 0:
            logger.warning("No results from rerank_products, returning empty results")
            return [], meta
        
        if query_dict.get('special'):
            logger.debug(f"Applying special case filtering")
            final_out, le = special_case_handler.special_case_filter(special_case_dict, reranked_idx, meta)
        else:
            logger.debug("No special filtering applied")
            final_out = reranked_idx
    else:
        logger.debug("No conflict/reset - using rerank_only path")
        reranked_idx, meta = voyage_rerank.rerank_products(retrieved_idx, meta, current_text, k=50)
        logger.debug(f"Reranked to {len(reranked_idx) if reranked_idx else 0} items")
        
        # Ensure reranked_idx isn't None before proceeding
        if reranked_idx is None or len(reranked_idx) == 0:
            logger.warning("No results from rerank_products, returning empty results")
            return [], meta
            
        if query_dict.get('special'):
            logger.debug(f"Applying special case filtering")
            final_out, le = special_case_handler.special_case_filter(special_case_dict, reranked_idx, meta)
        else:
            logger.debug("No special filtering needed")
            final_out = reranked_idx
    
    # Extract tags and update metadata in parallel
    logger.debug(f"Extracting tags from current text: '{current_text}'")
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            tags_future = executor.submit(process_tags_and_update_metadata, final_out, meta, current_text)
            
            # Apply special filters in parallel if needed
            if len(filter_list) > 0:
                logger.debug(f"Applying fast special filter with {len(filter_list)} filters")
                filter_future = executor.submit(
                    fast_special_filter.rerank_with_spec_filter, 
                    filter_list, meta, final_out, batch_size=20
                )
                final_out = filter_future.result()
            
            # Wait for tag processing to complete
            tags = tags_future.result()
            logger.debug(f"Extracted tags: {tags}")
    except Exception as e:
        logger.error(f"Error extracting tags: {e}")
            
    logger.debug(f"Pipeline completed. Returning {len(final_out) if final_out else 0} items")
    return final_out, meta

# Display helper
def show_results(result, metadata):
    """
    Display the top results inline in a Jupyter notebook.
    """
    logger.debug(f"Displaying top {min(10, len(result))} results")
    from IPython.display import display, HTML
    html = ['<div style="display: flex; flex-wrap: wrap; gap: 16px;">']
    
    # Process results in parallel for faster rendering
    def process_result(item_tuple):
        i, idx = item_tuple
        item = metadata[idx]
        text = item.get('text_input', '') or repr(item)
        image_path = item.get('image_path')
        img_tag = f'<img src="{image_path}" style="max-width:150px; max-height:150px; display:block; margin:auto;"/>' if image_path else ''
        return (
            '<div style="width:200px; border:1px solid #ddd; border-radius:8px; padding:8px;">'
            f'<strong>Result {i}</strong><br/>'
            f'{img_tag}'
            f'<div style="margin-top:8px; font-size:0.9em; line-height:1.2;">{text}</div>'
            '</div>'
        )
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(process_result, enumerate(result[:30], start=1)))
    
    html.extend(results)
    html.append('</div>')
    display(HTML(''.join(html)))

# Test run
if __name__ == '__main__':
    logger.debug("Starting test run")
    result, metadata = main_pipeline(None, True, 'img2.jpg')
    logger.debug(f"Test run completed with {len(result)} results")
    show_results(result, metadata)

