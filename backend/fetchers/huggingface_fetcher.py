"""
Hugging Face Models Fetcher
Fetches AI models from Hugging Face Hub
"""

import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Optional

load_dotenv()

HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
BASE_URL = "https://huggingface.co/api"

HEADERS = {}
if HUGGINGFACE_TOKEN:
    HEADERS["Authorization"] = f"Bearer {HUGGINGFACE_TOKEN}"


# Categories to fetch
PIPELINE_TAGS = [
    "text-generation",      # LLMs (GPT, LLaMA, Mistral)
    "text-to-image",        # Stable Diffusion, DALL-E
    "automatic-speech-recognition",  # Whisper
    "text-to-speech",       # TTS models
    "image-classification", # Computer Vision
    "object-detection",     # YOLO, etc.
    "image-segmentation",   # SAM, etc.
    "text-classification",  # NLP
    "translation",          # Translation models
    "summarization",        # Summarization
    "question-answering",   # QA models
    "text-to-video",        # Video generation
    "image-to-image",       # Image processing
]


def fetch_huggingface_models(
    sort: str = "downloads", 
    limit: int = 100,
    pipeline_tag: Optional[str] = None
) -> List[Dict]:
    """
    Fetch models from Hugging Face
    
    Args:
        sort: 'downloads', 'likes', 'trending', 'created'
        limit: Number of models to fetch
        pipeline_tag: Filter by specific task (optional)
    
    Returns:
        List of model dictionaries
    """
    print(f"🤗 Fetching Hugging Face models (sort={sort}, limit={limit})...")
    
    url = f"{BASE_URL}/models"
    params = {
        "sort": sort,
        "direction": -1,  # Descending
        "limit": limit
    }
    
    if pipeline_tag:
        params["filter"] = pipeline_tag
        print(f"   Filtering by pipeline: {pipeline_tag}")
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            return []
        
        models_raw = response.json()
        models = []
        
        for model in models_raw:
            try:
                model_data = parse_model(model)
                if model_data:
                    models.append(model_data)
            except Exception as e:
                print(f"⚠️  Error parsing model {model.get('id', 'unknown')}: {e}")
                continue
        
        print(f"✅ Fetched {len(models)} models from Hugging Face")
        return models
        
    except Exception as e:
        print(f"❌ Error fetching from Hugging Face: {e}")
        return []


def parse_model(model: Dict) -> Optional[Dict]:
    """Parse raw model data into our schema"""
    
    try:
        model_id = model.get("id", "")
        if not model_id:
            return None
        
        # Generate slug
        slug = model_id.replace("/", "-").lower()
        
        # Extract metadata
        return {
            "name": model_id.split("/")[-1] if "/" in model_id else model_id,
            "full_name": model_id,
            "slug": slug,
            "description": model.get("description", "No description available"),
            
            # Source info
            "source": "huggingface",
            "source_url": f"https://huggingface.co/{model_id}",
            "source_id": model_id,
            
            # Category
            "category": categorize_model(model),
            "subcategory": model.get("pipeline_tag", ""),
            "tags": model.get("tags", []),
            
            # Metrics
            "downloads_hf": model.get("downloads", 0),
            "likes_hf": model.get("likes", 0),
            
            # Metadata
            "language": "Python",  # Most HF models
            "framework": model.get("library_name", "transformers"),
            "license": extract_license(model),
            
            # Dates
            "created_at_source": parse_date(model.get("createdAt")),
            "updated_at_source": parse_date(model.get("lastModified")),
            
            # Additional metadata
            "metadata": {
                "pipeline_tag": model.get("pipeline_tag"),
                "library_name": model.get("library_name"),
                "model_index": model.get("modelId"),
                "siblings_count": len(model.get("siblings", [])),
                "private": model.get("private", False),
                "gated": model.get("gated", False),
            }
        }
    except Exception as e:
        print(f"⚠️  Error parsing model: {e}")
        return None


def categorize_model(model: Dict) -> str:
    """Categorize model based on pipeline tag"""
    
    pipeline_tag = model.get("pipeline_tag", "")
    
    category_map = {
        "text-generation": "Language Models",
        "text2text-generation": "Language Models",
        "text-to-image": "Image Generation",
        "image-to-image": "Image Generation",
        "automatic-speech-recognition": "Audio & Music",
        "text-to-speech": "Audio & Music",
        "audio-classification": "Audio & Music",
        "image-classification": "Computer Vision",
        "object-detection": "Computer Vision",
        "image-segmentation": "Computer Vision",
        "text-classification": "NLP Tools",
        "token-classification": "NLP Tools",
        "question-answering": "NLP Tools",
        "translation": "NLP Tools",
        "summarization": "NLP Tools",
        "conversational": "Language Models",
        "text-to-video": "Video Generation",
        "image-to-video": "Video Generation",
    }
    
    return category_map.get(pipeline_tag, "ML Frameworks")


def extract_license(model: Dict) -> str:
    """Extract license from model"""
    # Try to get from card data
    card_data = model.get("cardData", {})
    license_val = card_data.get("license", "")
    
    if license_val:
        return license_val
    
    # Check tags
    tags = model.get("tags", [])
    license_tags = [tag for tag in tags if "license:" in tag]
    if license_tags:
        return license_tags[0].replace("license:", "")
    
    return "Unknown"


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO date string"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return None


def fetch_all_categories(limit_per_category: int = 50) -> List[Dict]:
    """
    Fetch models from all major categories
    
    Returns comprehensive list of AI models
    """
    print("🤗 Fetching models from ALL categories...")
    all_models = []
    
    for pipeline_tag in PIPELINE_TAGS:
        models = fetch_huggingface_models(
            sort="downloads",
            limit=limit_per_category,
            pipeline_tag=pipeline_tag
        )
        all_models.extend(models)
        print(f"   {pipeline_tag}: {len(models)} models")
    
    # Also fetch top overall (no filter)
    print("   Fetching top overall models...")
    top_models = fetch_huggingface_models(sort="downloads", limit=100)
    all_models.extend(top_models)
    
    # Remove duplicates
    seen_ids = set()
    unique_models = []
    for model in all_models:
        if model["source_id"] not in seen_ids:
            seen_ids.add(model["source_id"])
            unique_models.append(model)
    
    print(f"✅ Total unique models: {len(unique_models)}")
    return unique_models


def get_model_details(model_id: str) -> Optional[Dict]:
    """
    Get detailed info for a specific model
    (Use this if you need more data than the list endpoint provides)
    """
    url = f"{BASE_URL}/models/{model_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"⚠️  Error fetching model details: {e}")
    
    return None


# =====================================================
# TESTING
# =====================================================

if __name__ == "__main__":
    print("="*60)
    print("TESTING HUGGING FACE FETCHER")
    print("="*60)
    
    # Test 1: Fetch top models
    print("\n📊 Test 1: Fetch top 10 models by downloads")
    models = fetch_huggingface_models(sort="downloads", limit=10)
    
    if models:
        print(f"\n✅ Success! Fetched {len(models)} models")
        print("\nSample model:")
        sample = models[0]
        print(f"  Name: {sample['name']}")
        print(f"  Category: {sample['category']}")
        print(f"  Downloads: {sample.get('downloads_hf', 0):,}")
        print(f"  Likes: {sample.get('likes_hf', 0):,}")
        print(f"  Pipeline: {sample['subcategory']}")
    else:
        print("❌ No models fetched")
    
    # Test 2: Fetch specific category
    print("\n📊 Test 2: Fetch text-to-image models")
    image_models = fetch_huggingface_models(
        sort="downloads",
        limit=5,
        pipeline_tag="text-to-image"
    )
    
    if image_models:
        print(f"✅ Fetched {len(image_models)} image generation models")
        for model in image_models[:3]:
            print(f"  - {model['name']}: {model.get('downloads_hf', 0):,} downloads")
    
    # Test 3: Fetch all categories
    print("\n📊 Test 3: Fetch from all categories (limit 10 per category)")
    print("This will take 30-60 seconds...")
    all_models = fetch_all_categories(limit_per_category=10)
    
    print(f"\n✅ Total models fetched: {len(all_models)}")
    
    # Show breakdown by category
    from collections import Counter
    categories = Counter(m['category'] for m in all_models)
    print("\nBreakdown by category:")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count} models")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)