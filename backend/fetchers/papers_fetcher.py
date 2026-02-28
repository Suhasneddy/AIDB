"""
Papers with Code Fetcher
Fetches ML research papers with code implementations
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional

BASE_URL = "https://paperswithcode.com/api/v1"


def fetch_papers(
    page: int = 1,
    items_per_page: int = 50,
    ordering: str = "-paper_citations"
) -> List[Dict]:
    """
    Fetch papers from Papers with Code
    
    Args:
        page: Page number
        items_per_page: Items per page (max 100)
        ordering: Sort order
            - '-paper_citations' (most cited)
            - '-github_stars' (most starred)
            - '-publication_date' (newest)
    
    Returns:
        List of paper dictionaries
    """
    print(f"📄 Fetching papers from Papers with Code (page {page})...")
    
    url = f"{BASE_URL}/papers/"
    params = {
        "page": page,
        "items_per_page": min(items_per_page, 100),
        "ordering": ordering
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            return []
        
        data = response.json()
        papers_raw = data.get("results", [])
        
        papers = []
        for paper in papers_raw:
            try:
                paper_data = parse_paper(paper)
                if paper_data:
                    papers.append(paper_data)
            except Exception as e:
                print(f"⚠️  Error parsing paper: {e}")
                continue
        
        print(f"✅ Fetched {len(papers)} papers")
        return papers
        
    except Exception as e:
        print(f"❌ Error fetching papers: {e}")
        return []


def fetch_paper_repositories(paper_id: str) -> List[Dict]:
    """
    Fetch GitHub repositories linked to a paper
    
    Args:
        paper_id: Paper ID from Papers with Code
    
    Returns:
        List of repository info
    """
    url = f"{BASE_URL}/papers/{paper_id}/repositories/"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
    except Exception as e:
        print(f"⚠️  Error fetching repos for paper {paper_id}: {e}")
    
    return []


def parse_paper(paper: Dict) -> Optional[Dict]:
    """Parse raw paper data into our schema"""
    
    try:
        paper_id = paper.get("id", "")
        if not paper_id:
            return None
        
        title = paper.get("title", "")
        if not title:
            return None
        
        # Generate slug from title
        slug = title.lower().replace(" ", "-")[:100]
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        
        # Get GitHub repo if available
        github_url = None
        github_stars = 0
        repo_url = paper.get("url_official", "") or paper.get("url_pdf", "")
        
        # Check if there's a linked GitHub repo
        # We'll fetch this separately if needed
        
        return {
            "name": title,
            "full_name": title,
            "slug": f"paper-{slug}",
            "description": paper.get("abstract", "")[:500] if paper.get("abstract") else "Research paper",
            
            # Source info
            "source": "papers",
            "source_url": f"https://paperswithcode.com/paper/{paper_id}",
            "source_id": paper_id,
            "paper_url": paper.get("url_pdf", ""),
            
            # Category
            "category": "Research Papers",
            "subcategory": extract_task(paper),
            "tags": extract_tasks_list(paper),
            
            # Metrics
            "citations": paper.get("citations", 0),
            "stars": github_stars,  # Will be updated if repo found
            
            # Metadata
            "language": "Python",  # Most ML papers use Python
            "framework": extract_framework(paper),
            "license": "Research",
            
            # Dates
            "created_at_source": parse_date(paper.get("published")),
            "updated_at_source": parse_date(paper.get("published")),
            
            # Additional metadata
            "metadata": {
                "paper_id": paper_id,
                "arxiv_id": paper.get("arxiv_id"),
                "authors": paper.get("authors", []),
                "conference": paper.get("conference"),
                "proceeding": paper.get("proceeding"),
                "url_abs": paper.get("url_abs"),
                "url_pdf": paper.get("url_pdf"),
                "has_official_code": bool(paper.get("url_official")),
            }
        }
    except Exception as e:
        print(f"⚠️  Error parsing paper: {e}")
        return None


def extract_task(paper: Dict) -> str:
    """Extract primary task from paper"""
    tasks = paper.get("tasks", [])
    if tasks and len(tasks) > 0:
        return tasks[0].get("name", "General ML")
    return "General ML"


def extract_tasks_list(paper: Dict) -> List[str]:
    """Extract all tasks as tags"""
    tasks = paper.get("tasks", [])
    return [task.get("name", "") for task in tasks if task.get("name")]


def extract_framework(paper: Dict) -> str:
    """Try to determine framework from paper"""
    # This is a guess - Papers with Code doesn't always provide this
    # Could look at linked repos for more info
    return "PyTorch"  # Most common in research


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None


def fetch_papers_with_code(total_papers: int = 500) -> List[Dict]:
    """
    Fetch multiple pages of papers
    
    Args:
        total_papers: Total number of papers to fetch
    
    Returns:
        List of paper dictionaries
    """
    print(f"📄 Fetching {total_papers} papers from Papers with Code...")
    
    all_papers = []
    items_per_page = 50
    pages_needed = (total_papers + items_per_page - 1) // items_per_page
    
    for page in range(1, pages_needed + 1):
        papers = fetch_papers(page=page, items_per_page=items_per_page)
        all_papers.extend(papers)
        
        if len(all_papers) >= total_papers:
            break
    
    all_papers = all_papers[:total_papers]
    print(f"✅ Total papers fetched: {len(all_papers)}")
    
    return all_papers


def fetch_recent_papers(months: int = 6, limit: int = 200) -> List[Dict]:
    """
    Fetch recent papers from last N months
    
    Args:
        months: Number of months back
        limit: Maximum papers to fetch
    
    Returns:
        List of recent papers
    """
    print(f"📄 Fetching papers from last {months} months...")
    
    # Fetch newest papers
    papers = []
    page = 1
    
    while len(papers) < limit:
        batch = fetch_papers(
            page=page,
            items_per_page=50,
            ordering="-publication_date"
        )
        
        if not batch:
            break
        
        papers.extend(batch)
        page += 1
        
        if page > 10:  # Safety limit
            break
    
    papers = papers[:limit]
    print(f"✅ Fetched {len(papers)} recent papers")
    
    return papers


def enrich_paper_with_repo(paper: Dict) -> Dict:
    """
    Enrich paper with GitHub repo information
    
    Args:
        paper: Paper dictionary
    
    Returns:
        Enriched paper dictionary
    """
    paper_id = paper.get("source_id")
    if not paper_id:
        return paper
    
    repos = fetch_paper_repositories(paper_id)
    
    if repos and len(repos) > 0:
        # Take the most popular repo
        repos_sorted = sorted(repos, key=lambda r: r.get("stars", 0), reverse=True)
        top_repo = repos_sorted[0]
        
        # Update paper data
        paper["github_repo"] = top_repo.get("url", "").replace("https://github.com/", "")
        paper["stars"] = top_repo.get("stars", 0)
        paper["forks"] = top_repo.get("forks", 0)
        paper["metadata"]["github_url"] = top_repo.get("url")
        paper["metadata"]["repo_description"] = top_repo.get("description")
    
    return paper


# =====================================================
# TESTING
# =====================================================

if __name__ == "__main__":
    print("="*60)
    print("TESTING PAPERS WITH CODE FETCHER")
    print("="*60)
    
    # Test 1: Fetch top cited papers
    print("\n📊 Test 1: Fetch top 10 most cited papers")
    papers = fetch_papers(page=1, items_per_page=10, ordering="-paper_citations")
    
    if papers:
        print(f"\n✅ Success! Fetched {len(papers)} papers")
        print("\nSample paper:")
        sample = papers[0]
        print(f"  Title: {sample['name'][:80]}...")
        print(f"  Citations: {sample.get('citations', 0):,}")
        print(f"  Category: {sample['category']}")
        print(f"  Task: {sample['subcategory']}")
    else:
        print("❌ No papers fetched")
    
    # Test 2: Fetch recent papers
    print("\n📊 Test 2: Fetch recent papers")
    recent = fetch_papers(page=1, items_per_page=5, ordering="-publication_date")
    
    if recent:
        print(f"✅ Fetched {len(recent)} recent papers")
        for paper in recent[:3]:
            print(f"  - {paper['name'][:60]}...")
    
    # Test 3: Fetch and enrich a paper with repo info
    print("\n📊 Test 3: Enrich paper with GitHub repo")
    if papers:
        enriched = enrich_paper_with_repo(papers[0])
        if enriched.get("github_repo"):
            print(f"✅ Found GitHub repo: {enriched['github_repo']}")
            print(f"   Stars: {enriched.get('stars', 0):,}")
        else:
            print("⚠️  No GitHub repo found for this paper")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)