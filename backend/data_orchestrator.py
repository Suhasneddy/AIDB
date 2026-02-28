"""
Data Orchestrator - Master Controller
Fetches data from all sources, merges, deduplicates, and saves to database
"""

import sys
from datetime import datetime
from typing import List, Dict
from collections import Counter

# Import all fetchers
from github_fetcher_expanded import fetch_all_categories as fetch_github_all
from huggingface_fetcher import fetch_all_categories as fetch_hf_all
from papers_fetcher import fetch_papers_with_code

# Import database functions
from database import (
    get_db, 
    create_tool, 
    get_tool_by_source,
    update_tool,
    get_platform_stats,
    generate_slug
)


class DataOrchestrator:
    """
    Master orchestrator for fetching and managing AI tools data
    """
    
    def __init__(self):
        self.stats = {
            "github": {"fetched": 0, "created": 0, "updated": 0, "failed": 0},
            "huggingface": {"fetched": 0, "created": 0, "updated": 0, "failed": 0},
            "papers": {"fetched": 0, "created": 0, "updated": 0, "failed": 0},
        }
        self.start_time = None
        self.end_time = None
    
    def run_full_sync(
        self,
        fetch_github: bool = True,
        fetch_huggingface: bool = True,
        fetch_papers: bool = True,
        github_repos_per_query: int = 30,
        hf_models_per_category: int = 50,
        papers_total: int = 500
    ):
        """
        Run complete data synchronization from all sources
        
        Args:
            fetch_github: Fetch GitHub repos
            fetch_huggingface: Fetch HF models
            fetch_papers: Fetch research papers
            github_repos_per_query: Repos per GitHub search query
            hf_models_per_category: Models per HF category
            papers_total: Total papers to fetch
        """
        print("="*70)
        print("🚀 STARTING FULL DATA SYNC")
        print("="*70)
        
        self.start_time = datetime.now()
        all_tools = []
        
        # 1. Fetch GitHub repositories
        if fetch_github:
            print("\n" + "="*70)
            print("📂 PHASE 1: GITHUB REPOSITORIES")
            print("="*70)
            try:
                github_repos = fetch_github_all(repos_per_query=github_repos_per_query)
                self.stats["github"]["fetched"] = len(github_repos)
                all_tools.extend(github_repos)
                print(f"✅ GitHub: {len(github_repos)} repos fetched")
            except Exception as e:
                print(f"❌ GitHub fetch failed: {e}")
                self.stats["github"]["failed"] = 1
        
        # 2. Fetch Hugging Face models
        if fetch_huggingface:
            print("\n" + "="*70)
            print("🤗 PHASE 2: HUGGING FACE MODELS")
            print("="*70)
            try:
                hf_models = fetch_hf_all(limit_per_category=hf_models_per_category)
                self.stats["huggingface"]["fetched"] = len(hf_models)
                all_tools.extend(hf_models)
                print(f"✅ Hugging Face: {len(hf_models)} models fetched")
            except Exception as e:
                print(f"❌ Hugging Face fetch failed: {e}")
                self.stats["huggingface"]["failed"] = 1
        
        # 3. Fetch Papers with Code
        if fetch_papers:
            print("\n" + "="*70)
            print("📄 PHASE 3: RESEARCH PAPERS")
            print("="*70)
            try:
                papers = fetch_papers_with_code(total_papers=papers_total)
                self.stats["papers"]["fetched"] = len(papers)
                all_tools.extend(papers)
                print(f"✅ Papers: {len(papers)} papers fetched")
            except Exception as e:
                print(f"❌ Papers fetch failed: {e}")
                self.stats["papers"]["failed"] = 1
        
        # 4. Process and save to database
        print("\n" + "="*70)
        print("💾 PHASE 4: SAVING TO DATABASE")
        print("="*70)
        self.save_to_database(all_tools)
        
        # 5. Show final stats
        self.end_time = datetime.now()
        self.print_summary()
    
    def save_to_database(self, tools: List[Dict]):
        """
        Save tools to database (create or update)
        
        Args:
            tools: List of tool dictionaries
        """
        print(f"\n💾 Saving {len(tools)} tools to database...")
        
        with get_db() as db:
            for i, tool_data in enumerate(tools):
                try:
                    # Check if tool already exists
                    existing = get_tool_by_source(
                        db,
                        tool_data["source"],
                        tool_data["source_id"]
                    )
                    
                    if existing:
                        # UPDATE existing tool
                        update_tool(db, str(existing.id), tool_data)
                        self.stats[tool_data["source"]]["updated"] += 1
                    else:
                        # CREATE new tool
                        # Ensure slug is unique
                        base_slug = tool_data.get("slug", generate_slug(tool_data["name"]))
                        slug = base_slug
                        counter = 1
                        
                        while get_tool_by_slug(db, slug):
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        
                        tool_data["slug"] = slug
                        create_tool(db, tool_data)
                        self.stats[tool_data["source"]]["created"] += 1
                    
                    # Progress indicator
                    if (i + 1) % 100 == 0:
                        print(f"   Processed {i + 1}/{len(tools)} tools...")
                
                except Exception as e:
                    print(f"⚠️  Error saving tool {tool_data.get('name', 'unknown')}: {e}")
                    self.stats[tool_data["source"]]["failed"] += 1
                    continue
        
        print(f"✅ Database save complete!")
    
    def print_summary(self):
        """Print comprehensive summary of the sync operation"""
        print("\n" + "="*70)
        print("📊 SYNC SUMMARY")
        print("="*70)
        
        total_fetched = sum(s["fetched"] for s in self.stats.values())
        total_created = sum(s["created"] for s in self.stats.values())
        total_updated = sum(s["updated"] for s in self.stats.values())
        total_failed = sum(s["failed"] for s in self.stats.values())
        
        print(f"\n⏱️  Duration: {(self.end_time - self.start_time).total_seconds():.1f} seconds")
        print(f"\n📦 Total Fetched: {total_fetched}")
        print(f"✅ Created: {total_created}")
        print(f"🔄 Updated: {total_updated}")
        print(f"❌ Failed: {total_failed}")
        
        print("\n📂 Breakdown by Source:")
        for source, stats in self.stats.items():
            if stats["fetched"] > 0:
                print(f"\n  {source.upper()}:")
                print(f"    Fetched: {stats['fetched']}")
                print(f"    Created: {stats['created']}")
                print(f"    Updated: {stats['updated']}")
                print(f"    Failed:  {stats['failed']}")
        
        # Get database stats
        try:
            with get_db() as db:
                db_stats = get_platform_stats(db)
                print("\n💾 Database Stats:")
                print(f"    Total Tools: {db_stats['total_tools']}")
                print(f"    Total Categories: {db_stats['total_categories']}")
                print(f"    GitHub Repos: {db_stats['github_tools']}")
                print(f"    HF Models: {db_stats['huggingface_tools']}")
        except:
            pass
        
        print("\n" + "="*70)
        print("✅ SYNC COMPLETE!")
        print("="*70)


def quick_sync(source: str = "all"):
    """
    Quick sync - fetch small amount from each source for testing
    
    Args:
        source: 'github', 'huggingface', 'papers', or 'all'
    """
    print("⚡ RUNNING QUICK SYNC (Testing Mode)")
    
    orchestrator = DataOrchestrator()
    
    if source == "all":
        orchestrator.run_full_sync(
            fetch_github=True,
            fetch_huggingface=True,
            fetch_papers=True,
            github_repos_per_query=10,    # Small amount for testing
            hf_models_per_category=10,
            papers_total=50
        )
    elif source == "github":
        orchestrator.run_full_sync(
            fetch_github=True,
            fetch_huggingface=False,
            fetch_papers=False,
            github_repos_per_query=10
        )
    elif source == "huggingface":
        orchestrator.run_full_sync(
            fetch_github=False,
            fetch_huggingface=True,
            fetch_papers=False,
            hf_models_per_category=10
        )
    elif source == "papers":
        orchestrator.run_full_sync(
            fetch_github=False,
            fetch_huggingface=False,
            fetch_papers=True,
            papers_total=50
        )


def full_production_sync():
    """
    Full production sync - fetch comprehensive data from all sources
    This is what you'll run for real data collection
    """
    print("🚀 RUNNING FULL PRODUCTION SYNC")
    print("⏱️  This will take 20-30 minutes...")
    print()
    
    orchestrator = DataOrchestrator()
    orchestrator.run_full_sync(
        fetch_github=True,
        fetch_huggingface=True,
        fetch_papers=True,
        github_repos_per_query=30,      # ~900 repos
        hf_models_per_category=50,      # ~650 models
        papers_total=500                # 500 papers
    )
    
    print("\n🎉 You now have 2000+ AI tools in your database!")


# =====================================================
# CLI INTERFACE
# =====================================================

if __name__ == "__main__":
    import sys
    
    print("="*70)
    print("🤖 AI TOOLS DATA ORCHESTRATOR")
    print("="*70)
    print()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "quick":
            # Quick test sync
            source = sys.argv[2] if len(sys.argv) > 2 else "all"
            quick_sync(source)
        
        elif mode == "full":
            # Full production sync
            response = input("⚠️  This will fetch 2000+ tools and take 20-30 minutes. Continue? (yes/no): ")
            if response.lower() == "yes":
                full_production_sync()
            else:
                print("❌ Cancelled")
        
        else:
            print("❌ Unknown mode. Use 'quick' or 'full'")
    
    else:
        # Interactive mode
        print("Select sync mode:")
        print("  1. Quick Sync (Testing - ~200 tools, 2-3 minutes)")
        print("  2. Full Sync (Production - ~2000 tools, 20-30 minutes)")
        print()
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            quick_sync("all")
        elif choice == "2":
            response = input("⚠️  This will take 20-30 minutes. Continue? (yes/no): ")
            if response.lower() == "yes":
                full_production_sync()
            else:
                print("❌ Cancelled")
        else:
            print("❌ Invalid choice")