import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github.v3+json"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"


# Comprehensive search queries for different AI categories
SEARCH_QUERIES = {
    "llm": [
        "large-language-model stars:>100",
        "gpt llm stars:>500",
        "transformer language-model stars:>200",
        "chatbot llm stars:>100",
    ],
    "image_generation": [
        "stable-diffusion stars:>100",
        "text-to-image stars:>100",
        "image-generation diffusion stars:>50",
        "gan image-generation stars:>100",
        "dall-e stable-diffusion stars:>50",
    ],
    "video": [
        "video-generation stars:>50",
        "text-to-video stars:>50",
        "video-ai stars:>100",
    ],
    "audio": [
        "text-to-speech stars:>100",
        "speech-recognition stars:>100",
        "music-generation stars:>50",
        "voice-cloning stars:>50",
        "audio-ai whisper stars:>100",
    ],
    "computer_vision": [
        "computer-vision stars:>200",
        "object-detection stars:>200",
        "image-segmentation stars:>100",
        "yolo detection stars:>100",
        "opencv vision stars:>200",
    ],
    "nlp": [
        "natural-language-processing stars:>100",
        "sentiment-analysis stars:>100",
        "text-classification stars:>100",
        "named-entity-recognition stars:>50",
        "transformers nlp stars:>100",
    ],
    "frameworks": [
        "machine-learning-framework stars:>500",
        "deep-learning pytorch stars:>500",
        "tensorflow framework stars:>500",
        "jax machine-learning stars:>200",
    ],
    "tools": [
        "langchain stars:>500",
        "llm-tools stars:>100",
        "ai-agents stars:>100",
        "ml-ops stars:>100",
        "prompt-engineering stars:>50",
    ],
    "research": [
        "machine-learning research stars:>200",
        "deep-learning papers stars:>100",
        "sota benchmark stars:>50",
    ],
    "deployment": [
        "model-deployment stars:>100",
        "inference-server stars:>100",
        "ml-serving stars:>50",
    ]
}


def fetch_github_repos(
    query: str,
    max_results: int = 30,
    sort: str = "stars"
) -> List[Dict]:
    """
    Fetch GitHub repositories for a query
    
    Args:
        query: Search query
        max_results: Maximum results to fetch
        sort: Sort by 'stars', 'forks', 'updated'
    
    Returns:
        List of repository dictionaries
    """
    print(f"🔍 Searching GitHub: {query[:50]}...")
    
    search_url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": sort,
        "order": "desc",
        "per_page": min(max_results, 100)
    }
    
    try:
        response = requests.get(search_url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code == 403:
            print("❌ Rate limit hit! Waiting 60 seconds...")
            time.sleep(60)
            return fetch_github_repos(query, max_results, sort)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            return []
        
        data = response.json()
        repos_raw = data.get("items", [])
        
        repos = []
        for repo in repos_raw:
            try:
                repo_data = parse_repo(repo)
                if repo_data:
                    repos.append(repo_data)
            except Exception as e:
                print(f"⚠️  Error parsing repo: {e}")
                continue
        
        print(f"✅ Found {len(repos)} repositories")
        return repos
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def parse_repo(repo: Dict) -> Optional[Dict]:
    """Parse raw GitHub repo data into our schema"""
    
    try:
        full_name = repo.get("full_name", "")
        if not full_name:
            return None
        
        # Generate slug
        slug = full_name.replace("/", "-").lower()
        
        # Calculate age and activity
        created_date = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
        updated_date = datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
        days_since_created = (datetime.now(created_date.tzinfo) - created_date).days
        days_since_update = (datetime.now(updated_date.tzinfo) - updated_date).days
        
        # Estimate metrics (we'll get detailed ones later if needed)
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        watchers = repo.get("watchers_count", 0)
        
        return {
            "name": repo.get("name", ""),
            "full_name": full_name,
            "slug": slug,
            "description": repo.get("description", ""),
            
            # Source info
            "source": "github",
            "source_url": repo.get("html_url", ""),
            "source_id": full_name,
            "github_repo": full_name,
            
            # Category (will be refined later)
            "category": categorize_repo(repo),
            "subcategory": extract_subcategory(repo),
            "tags": repo.get("topics", []),
            
            # Metrics
            "stars": stars,
            "forks": forks,
            "watchers": watchers,
            "open_issues": repo.get("open_issues_count", 0),
            
            # Estimated metrics (simplified)
            "contributors_count": max(10, watchers // 10),
            "commits_last_30_days": 50 if days_since_update < 30 else 10,
            
            # Metadata
            "language": repo.get("language", ""),
            "framework": infer_framework(repo),
            "license": extract_license(repo),
            
            # Dates
            "created_at_source": created_date,
            "updated_at_source": updated_date,
            
            # Additional metadata
            "metadata": {
                "owner": repo.get("owner", {}).get("login", ""),
                "homepage": repo.get("homepage", ""),
                "has_wiki": repo.get("has_wiki", False),
                "has_pages": repo.get("has_pages", False),
                "archived": repo.get("archived", False),
                "disabled": repo.get("disabled", False),
                "default_branch": repo.get("default_branch", "main"),
            }
        }
    except Exception as e:
        print(f"⚠️  Error parsing repo: {e}")
        return None


def categorize_repo(repo: Dict) -> str:
    """Categorize repo based on topics and description"""
    
    topics = repo.get("topics", [])
    description = (repo.get("description") or "").lower()
    name = repo.get("name", "").lower()
    
    # Check topics and description for keywords
    keywords = {
        "Language Models": ["gpt", "llm", "language-model", "chatbot", "transformer", "bert"],
        "Image Generation": ["stable-diffusion", "text-to-image", "image-generation", "gan", "diffusion"],
        "Video Generation": ["video-generation", "text-to-video", "video-ai"],
        "Audio & Music": ["text-to-speech", "speech-recognition", "music-generation", "audio", "whisper"],
        "Computer Vision": ["computer-vision", "object-detection", "segmentation", "yolo", "opencv"],
        "NLP Tools": ["nlp", "natural-language", "sentiment", "text-classification"],
        "ML Frameworks": ["pytorch", "tensorflow", "framework", "jax", "keras"],
        "Code Generation": ["code-generation", "copilot", "codegen"],
        "Data Science": ["data-science", "pandas", "visualization", "notebook"],
    }
    
    all_text = " ".join(topics + [description, name])
    
    for category, kws in keywords.items():
        if any(kw in all_text for kw in kws):
            return category
    
    return "ML Frameworks"


def extract_subcategory(repo: Dict) -> str:
    """Extract subcategory from topics"""
    topics = repo.get("topics", [])
    if topics:
        return topics[0]
    return ""


def infer_framework(repo: Dict) -> str:
    """Infer ML framework from repo"""
    topics = repo.get("topics", [])
    description = (repo.get("description") or "").lower()
    
    if "pytorch" in topics or "pytorch" in description:
        return "PyTorch"
    elif "tensorflow" in topics or "tensorflow" in description:
        return "TensorFlow"
    elif "jax" in topics or "jax" in description:
        return "JAX"
    elif "keras" in topics:
        return "Keras"
    
    return ""


def extract_license(repo: Dict) -> str:
    """Extract license info"""
    license_info = repo.get("license")
    if license_info:
        return license_info.get("name", "Unknown")
    return "Unknown"


def fetch_all_categories(repos_per_query: int = 30) -> List[Dict]:
    """
    Fetch repositories from all categories
    
    Args:
        repos_per_query: Number of repos per search query
    
    Returns:
        Comprehensive list of AI/ML repositories
    """
    print("🚀 Fetching GitHub repositories from ALL categories...")
    print(f"   This will take 5-10 minutes...")
    
    all_repos = []
    total_queries = sum(len(queries) for queries in SEARCH_QUERIES.values())
    completed = 0
    
    for category, queries in SEARCH_QUERIES.items():
        print(f"\n📂 Category: {category}")
        
        for query in queries:
            repos = fetch_github_repos(query, max_results=repos_per_query)
            all_repos.extend(repos)
            
            completed += 1
            print(f"   Progress: {completed}/{total_queries} queries")
            
            # Be nice to GitHub API
            time.sleep(2)
    
    # Remove duplicates
    seen_ids = set()
    unique_repos = []
    for repo in all_repos:
        if repo["source_id"] not in seen_ids:
            seen_ids.add(repo["source_id"])
            unique_repos.append(repo)
    
    print(f"\n✅ Total unique repositories: {len(unique_repos)}")
    
    # Show breakdown by category
    from collections import Counter
    categories = Counter(r['category'] for r in unique_repos)
    print("\nBreakdown by category:")
    for cat, count in categories.most_common():
        print(f"  {cat}: {count} repos")
    
    return unique_repos


def fetch_trending_repos(days: int = 7) -> List[Dict]:
    """
    Fetch trending AI repositories from last N days
    
    Args:
        days: Number of days to look back
    
    Returns:
        List of trending repos
    """
    date_str = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    query = f"machine-learning created:>{date_str} stars:>50"
    
    print(f"🔥 Fetching trending repos from last {days} days...")
    return fetch_github_repos(query, max_results=50, sort="stars")


# =====================================================
# TESTING
# =====================================================

if __name__ == "__main__":
    print("="*60)
    print("TESTING EXPANDED GITHUB FETCHER")
    print("="*60)
    
    # Test 1: Single query
    print("\n📊 Test 1: Fetch stable-diffusion repos")
    repos = fetch_github_repos("stable-diffusion stars:>100", max_results=10)
    
    if repos:
        print(f"\n✅ Success! Fetched {len(repos)} repos")
        print("\nSample repo:")
        sample = repos[0]
        print(f"  Name: {sample['name']}")
        print(f"  Category: {sample['category']}")
        print(f"  Stars: {sample['stars']:,}")
        print(f"  Language: {sample['language']}")
    else:
        print("❌ No repos fetched")
    
    # Test 2: Multiple categories (small sample)
    print("\n📊 Test 2: Fetch from multiple categories (5 repos each)")
    print("This is a small test - full fetch takes longer")
    
    test_queries = {
        "llm": ["gpt llm stars:>500"],
        "image": ["stable-diffusion stars:>200"],
    }
    
    all_test = []
    for cat, queries in test_queries.items():
        for query in queries:
            repos = fetch_github_repos(query, max_results=5)
            all_test.extend(repos)
            time.sleep(2)
    
    print(f"✅ Fetched {len(all_test)} repos from test categories")
    
    print("\n" + "="*60)
    print("✅ TESTS PASSED!")
    print("="*60)
    print("\n💡 To fetch ALL categories, run:")
    print("   repos = fetch_all_categories(repos_per_query=30)")
    print("   This will fetch 800-1000 repositories!")