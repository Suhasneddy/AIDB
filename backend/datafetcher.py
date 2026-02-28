import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

# GitHub API configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
} if GITHUB_TOKEN else {}


# All AI-related search queries to cover different categories
AI_QUERIES = [
    "topic:machine-learning",
    "topic:deep-learning",
    "topic:artificial-intelligence",
    "topic:llm",
    "topic:gpt",
    "topic:stable-diffusion",
    "topic:computer-vision",
    "topic:nlp",
    "topic:generative-ai",
    "topic:transformers",
    "ai-coding OR code-generation OR copilot",
    "text-to-speech OR voice-ai OR music-generation",
    "video-generation OR text-to-video",
    "automation OR ai-agent OR ai-workflow",
]


def _fetch_one_query(query, per_page=30):
    """
    Fetch repos for a single query. Used by ThreadPoolExecutor for parallel fetching.
    Returns list of processed repo dicts.
    """
    search_url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page
    }

    try:
        response = requests.get(search_url, headers=HEADERS, params=params, timeout=15)

        if response.status_code == 403:
            print(f"⚠️ Rate limited on query: {query[:40]}...")
            return []

        if response.status_code != 200:
            print(f"❌ GitHub API error {response.status_code} for: {query[:40]}...")
            return []

        repos_data = response.json().get("items", [])
        return [_process_repo(repo) for repo in repos_data]

    except Exception as e:
        print(f"❌ Error fetching '{query[:40]}...': {e}")
        return []


def _process_repo(repo):
    """Process a single repo dict from GitHub API into our standard format."""
    created_date = datetime.fromisoformat(repo["created_at"].replace("Z", "+00:00"))
    updated_date = datetime.fromisoformat(repo["updated_at"].replace("Z", "+00:00"))
    days_since_created = max((datetime.now(created_date.tzinfo) - created_date).days, 1)
    days_since_update = (datetime.now(updated_date.tzinfo) - updated_date).days

    star_growth = repo["stargazers_count"] / days_since_created

    return {
        "name": repo["name"],
        "full_name": repo["full_name"],
        "description": repo["description"] or "No description available",
        "url": repo["html_url"],
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "language": repo["language"] or "Unknown",
        "topics": repo.get("topics", []),
        "created_at": repo["created_at"],
        "updated_at": repo["updated_at"],
        "open_issues": repo.get("open_issues_count", 0),
        "watchers": repo.get("watchers_count", 0),
        "owner_avatar": repo.get("owner", {}).get("avatar_url", ""),
        "license": repo.get("license", {}).get("name", "Unknown") if repo.get("license") else "Unknown",

        # Estimated metrics (no extra API calls)
        "contributors_count": max(repo.get("watchers_count", 0) // 10, 1),
        "commits_last_month": 50 if days_since_update < 30 else 10,
        "total_commits": max(repo["stargazers_count"] // 10, 1),
        "star_growth_estimate": int(star_growth),
        "days_since_last_release": days_since_update,
    }


def fetch_all_ai_repos(target_count=100):
    """
    FAST VERSION: Fetch ~100 unique AI repos using parallel API calls.
    Uses ThreadPoolExecutor to call all queries simultaneously.
    Typically completes in 3-8 seconds instead of 5 minutes.
    """
    print(f"🚀 Fetching {target_count} AI repos using parallel calls...")
    start_time = datetime.now()

    all_repos = {}  # Use dict keyed by full_name for deduplication

    # Fetch all queries in parallel (max 3 threads to respect rate limits)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(_fetch_one_query, query, 30): query
            for query in AI_QUERIES
        }

        for future in as_completed(futures):
            query = futures[future]
            try:
                repos = future.result()
                for repo in repos:
                    if repo["full_name"] not in all_repos:
                        all_repos[repo["full_name"]] = repo
            except Exception as e:
                print(f"❌ Thread error for '{query[:40]}': {e}")

    # Sort by stars and trim to target count
    sorted_repos = sorted(all_repos.values(), key=lambda r: r["stars"], reverse=True)
    result = sorted_repos[:target_count]

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"✅ Fetched {len(result)} unique AI repos in {elapsed:.1f}s (from {len(all_repos)} total)")

    return result


def fetch_github_repos(query="machine-learning", max_results=30):
    """
    Original single-query fetcher (used for search and specific category queries).
    """
    return _fetch_one_query(query, per_page=min(max_results, 30))


if __name__ == "__main__":
    print("Testing FAST parallel GitHub fetcher...\n")
    repos = fetch_all_ai_repos(target_count=100)

    if repos:
        print(f"\n✅ Successfully fetched {len(repos)} unique repos!")
        print(f"\nTop 5 by stars:")
        for i, r in enumerate(repos[:5], 1):
            print(f"  {i}. {r['name']} ⭐ {r['stars']:,} ({r['language']})")
    else:
        print("❌ No repos fetched. Check your GITHUB_TOKEN in .env")