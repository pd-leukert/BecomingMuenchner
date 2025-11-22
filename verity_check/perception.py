import json
import requests
import os
from typing import Dict, Any, Optional, List
import re
from prompt import CATEGORIZATION_PROMPT, PROMPTS
# Default vLLM endpoint - can be overridden by env var
VLLM_API_URL = os.getenv("VLLM_API_URL", "http://localhost:8000/v1/chat/completions")
MODEL_NAME = os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2-VL-7B-Instruct")

def categorize_document(image_content_blocks: List[Dict[str, Any]], doc_name: str) -> str:
    """Categorizes the document using the VLM."""
    print("🔍 Categorizing document...")
    cat_payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CATEGORIZATION_PROMPT},
                    *image_content_blocks
                ]
            }
        ],
        "max_tokens": 256,
        "temperature": 0.1
    }
    try:
        response = requests.post(VLLM_API_URL, json=cat_payload)
        response.raise_for_status()
        cat_result = response.json()
        cat_content = cat_result["choices"][0]["message"]["content"]
        
        clean_cat = cat_content.strip()
        if clean_cat.startswith("```json"): clean_cat = clean_cat[7:]
        if clean_cat.endswith("```"): clean_cat = clean_cat[:-3]
        
        cat_data = json.loads(clean_cat.strip())
        doc_category = cat_data.get("category", "Identity")
        print(f"✅ Categorized {doc_name} as: {doc_category} (Confidence: {cat_data.get('confidence')})")
        return doc_category
        
    except Exception as e:
        print(f"⚠️ Categorization of {doc_name} failed: {e}. Defaulting to Identity.")
        return "Identity"

def extract_structured_data(image_content_blocks: List[Dict[str, Any]], doc_category: str, doc_name: str) -> Dict[str, Any]:
    """Extracts structured data from the document using the VLM."""
    if doc_category not in PROMPTS:
        print(f"⚠️ Unknown category '{doc_category}' for {doc_name}, defaulting to Identity prompt.")
        doc_category = "Identity"

    prompt = PROMPTS[doc_category]
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *image_content_blocks
                ]
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.1
    }
    
    extracted_json = {}
    try:
        response = requests.post(VLLM_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        json_blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)
        
        if not json_blocks:
            json_blocks = re.findall(r"(\{.*?\})", content, re.DOTALL)
        
        if json_blocks:
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if isinstance(data, dict):
                        extracted_json.update(data)
                except json.JSONDecodeError:
                    continue
            
            if not extracted_json:
                 extracted_json = json.loads(content)
        else:
            extracted_json = json.loads(content)
        
    except Exception as e:
        print(f"Extraction Error: {e}")
        print(f"Raw content was: {content if 'content' in locals() else 'N/A'}")
        extracted_json = {"error": str(e), "raw_content": content if 'content' in locals() else "N/A"}
        
    return extracted_json

def extract_data(images_base64: List[str], doc_name: str) -> Dict[str, Any]:
    """
    Sends images to the VLM. If category is not provided, it first categorizes the document,
    then extracts structured data based on the determined category.
    
    Args:
        images_base64: List of Base64 encoded image strings (one per page).
        doc_name: Name of the document for logging.
        
    Returns:
        Dictionary containing:
            - category: The determined or provided category
            - data: The extracted JSON data
    """
    # Limit to first 5 pages to avoid token overflow
    if len(images_base64) > 5:
        print(f"⚠️ Document has {len(images_base64)} pages. Limiting to first 5 pages.")
        images_base64 = images_base64[:5]
    
    image_content_blocks = []
    for img_b64 in images_base64:
        image_content_blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
        })

    doc_category = categorize_document(image_content_blocks, doc_name)
    extracted_json = extract_structured_data(image_content_blocks, doc_category, doc_name)

    return {
        "category": doc_category,
        "data": extracted_json
    }
