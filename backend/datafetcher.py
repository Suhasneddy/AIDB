import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def fetch_github_repos(query="machine-learning", max_results=20):
    """
    Fetch AI/ML repositories from GitHub with detailed metrics
    """
    url = "https://api.github.com/search/repositories"
    
    params = {
        "q": f"{query} stars:>100",  # Only repos with 100+ stars
        "sort": "stars",
        "order": "desc",
        "per_page": max_results
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        
        repos_data = response.json()["items"]
        enriched_repos = []

        for repo in repos_data:
            # Get additional details for each repo
            repo_details = get_repo_details(repo["full_name"])
            
            enriched_repos.append({
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo["description"] or "No description",
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "watchers": repo["watchers_count"],
                "open_issues": repo["open_issues_count"],
                "language": repo["language"] or "Unknown",
                "created_at": repo["created_at"],
                "updated_at": repo["updated_at"],
                "url": repo["html_url"],
                "topics": repo.get("topics", []),
                
                # From detailed API call
                "contributors_count": repo_details["contributors_count"],
                "commits_last_month": repo_details["commits_last_month"],
                "total_commits": repo_details["total_commits"],
                "star_growth_estimate": repo_details["star_growth_estimate"],
                "days_since_last_release": repo_details["days_since_last_release"]
            })

        print(f"✅ Fetched {len(enriched_repos)} repositories from GitHub")
        return enriched_repos

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching GitHub data: {e}")
        return []


def get_repo_details(full_name):
    """
    Get detailed metrics for a specific repository
    """
    details = {
        "contributors_count": 0,
        "commits_last_month": 0,
        "total_commits": 0,
        "star_growth_estimate": 0,
        "days_since_last_release": 999
    }

    max_retries = 2
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            # Get contributors count
            contributors_url = f"https://api.github.com/repos/{full_name}/contributors"
            contrib_response = requests.get(contributors_url, headers=HEADERS, params={"per_page": 1}, timeout=5)
            if contrib_response.status_code == 200:
                # GitHub returns total count in Link header
                link_header = contrib_response.headers.get("Link", "")
                if "last" in link_header:
                    # Extract page number from last page link
                    import re
                    match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if match:
                        details["contributors_count"] = int(match.group(1))
                else:
                    details["contributors_count"] = len(contrib_response.json())

            # Get recent commits (last month)
            one_month_ago = (datetime.now() - timedelta(days=30)).isoformat()
            commits_url = f"https://api.github.com/repos/{full_name}/commits"
            commits_response = requests.get(
                commits_url, 
                headers=HEADERS, 
                params={"since": one_month_ago, "per_page": 100},
                timeout=5
            )
            if commits_response.status_code == 200:
                details["commits_last_month"] = len(commits_response.json())

            # Get total commits (approximate from latest commit)
            total_commits_response = requests.get(commits_url, headers=HEADERS, params={"per_page": 1}, timeout=5)
            if total_commits_response.status_code == 200:
                link_header = total_commits_response.headers.get("Link", "")
                if "last" in link_header:
                    import re
                    match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if match:
                        details["total_commits"] = int(match.group(1))
                else:
                    details["total_commits"] = 1

            # Get latest release date
            releases_url = f"https://api.github.com/repos/{full_name}/releases/latest"
            release_response = requests.get(releases_url, headers=HEADERS, timeout=5)
            if release_response.status_code == 200:
                release_date = release_response.json().get("published_at")
                if release_date:
                    release_dt = datetime.fromisoformat(release_date.replace("Z", "+00:00"))
                    details["days_since_last_release"] = (datetime.now(release_dt.tzinfo) - release_dt).days

            # Estimate star growth (stars per day since creation)
            details["star_growth_estimate"] = 100  # Placeholder for now
            
            # If we got here successfully, break out of retry loop
            break
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Retry {attempt + 1} for {full_name}")
                import time
                time.sleep(retry_delay)
            else:
                print(f"⚠️ Could not fetch all details for {full_name}: {e}")

    return details


def fetch_huggingface_models(limit=10):
    """
    Fetch popular models from Hugging Face
    (Simplified - can be expanded later)
    """
    url = "https://huggingface.co/api/models"
    
    params = {
        "sort": "downloads",
        "direction": -1,
        "limit": limit,
        "filter": "text-generation"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        models = response.json()
        
        results = []
        for model in models:
            results.append({
                "name": model.get("id", "Unknown"),
                "downloads": model.get("downloads", 0),
                "likes": model.get("likes", 0),
                "tags": model.get("tags", []),
                "url": f"https://huggingface.co/{model.get('id')}"
            })

        print(f"✅ Fetched {len(results)} models from Hugging Face")
        return results

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching Hugging Face data: {e}")
        return []


# Test the fetcher
if __name__ == "__main__":
    print("🔍 Testing GitHub API Fetcher...\n")
    
    repos = fetch_github_repos(query="llm", max_results=5)
    
    if repos:
        print("\n📊 Sample Repository Data:")
        for i, repo in enumerate(repos[:3], 1):
            print(f"\n{i}. {repo['name']}")
            print(f"   ⭐ Stars: {repo['stars']:,}")
            print(f"   🍴 Forks: {repo['forks']:,}")
            print(f"   👥 Contributors: {repo['contributors_count']}")
            print(f"   💻 Commits (last month): {repo['commits_last_month']}")
    
    print("\n" + "="*50)
    print("🤗 Testing Hugging Face API Fetcher...\n")
    
    models = fetch_huggingface_models(limit=3)
    
    if models:
        print("\n📊 Sample Model Data:")
        for i, model in enumerate(models, 1):
            print(f"\n{i}. {model['name']}")
            print(f"   📥 Downloads: {model['downloads']:,}")
            print(f"   ❤️ Likes: {model['likes']}")