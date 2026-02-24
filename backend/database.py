import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def save_tools_to_db(tools_data):
    """
    Save AI tools data to Supabase database
    Returns: number of tools saved
    """
    saved_count = 0
    
    for tool in tools_data:
        try:
            # Prepare data for ai_tools table
            tool_record = {
                "name": tool.get("name"),
                "full_name": tool.get("full_name"),
                "description": tool.get("description"),
                "url": tool.get("url"),
                "stars": tool.get("stars"),
                "forks": tool.get("forks"),
                "watchers": tool.get("watchers", 0),
                "open_issues": tool.get("open_issues", 0),
                "language": tool.get("language"),
                "contributors_count": tool.get("contributors_count"),
                "commits_last_month": tool.get("commits_last_month"),
                "total_commits": tool.get("total_commits"),
                "star_growth_estimate": tool.get("star_growth_estimate"),
                "days_since_last_release": tool.get("days_since_last_release"),
                "topics": tool.get("topics", []),
                "created_at": tool.get("created_at"),
                "updated_at": tool.get("updated_at"),
                "fetched_at": datetime.now().isoformat()
            }
            
            # Upsert (insert or update if exists)
            result = supabase.table("ai_tools").upsert(
                tool_record,
                on_conflict="full_name"
            ).execute()
            
            saved_count += 1
            
        except Exception as e:
            print(f"❌ Error saving {tool.get('name')}: {e}")
            continue
    
    print(f"✅ Saved {saved_count} tools to database")
    return saved_count


def save_rankings_to_db(ranked_df, category="general"):
    """
    Save ranking scores to database
    Returns: number of rankings saved
    """
    saved_count = 0
    
    for idx, row in ranked_df.iterrows():
        try:
            # First, get the tool_id from ai_tools table
            tool_result = supabase.table("ai_tools").select("id").eq(
                "full_name", row["full_name"]
            ).execute()
            
            if not tool_result.data:
                print(f"⚠️ Tool not found in database: {row['full_name']}")
                continue
            
            tool_id = tool_result.data[0]["id"]
            
            # Prepare ranking data
            ranking_record = {
                "tool_id": tool_id,
                "growth_rate": float(row.get("GrowthRate_N", 0)),
                "activity": float(row.get("Activity_N", 0)),
                "community_strength": float(row.get("CommunityStrength_N", 0)),
                "freshness": float(row.get("Freshness_N", 0)),
                "final_score": float(row.get("FinalScore", 0)),
                "boosted_score": float(row.get("BoostedScore", 0)),
                "is_boosted": bool(row.get("IsBoosted", False)),
                "rank_position": int(idx + 1),
                "category": category,
                "ranked_at": datetime.now().isoformat()
            }
            
            # Insert ranking
            result = supabase.table("rankings").insert(ranking_record).execute()
            saved_count += 1
            
        except Exception as e:
            print(f"❌ Error saving ranking for {row.get('name')}: {e}")
            continue
    
    print(f"✅ Saved {saved_count} rankings to database")
    return saved_count


def get_latest_rankings(category=None, limit=50):
    """
    Get latest rankings from database
    """
    try:
        query = supabase.table("rankings").select(
            """
            *,
            ai_tools (
                name,
                full_name,
                description,
                url,
                stars,
                forks,
                language,
                topics
            )
            """
        ).order("boosted_score", desc=True).limit(limit)
        
        if category and category != "general":
            query = query.eq("category", category)
        
        result = query.execute()
        
        return result.data
        
    except Exception as e:
        print(f"❌ Error fetching rankings: {e}")
        return []


def get_emerging_tools(limit=20):
    """
    Get tools that received the early-stage boost
    """
    try:
        result = supabase.table("rankings").select(
            """
            *,
            ai_tools (
                name,
                full_name,
                description,
                url,
                stars,
                forks,
                language
            )
            """
        ).eq("is_boosted", True).order(
            "boosted_score", desc=True
        ).limit(limit).execute()
        
        return result.data
        
    except Exception as e:
        print(f"❌ Error fetching emerging tools: {e}")
        return []


def get_tool_by_name(full_name):
    """
    Get specific tool details by full_name (owner/repo)
    """
    try:
        result = supabase.table("ai_tools").select("*").eq(
            "full_name", full_name
        ).execute()
        
        if result.data:
            return result.data[0]
        return None
        
    except Exception as e:
        print(f"❌ Error fetching tool: {e}")
        return None


def search_tools(query, limit=20):
    """
    Search tools by name or description
    """
    try:
        result = supabase.table("ai_tools").select("*").ilike(
            "name", f"%{query}%"
        ).order("stars", desc=True).limit(limit).execute()
        
        return result.data
        
    except Exception as e:
        print(f"❌ Error searching tools: {e}")
        return []


# Test the connection
if __name__ == "__main__":
    print("🔌 Testing Supabase connection...")
    
    try:
        # Try to query the ai_tools table
        result = supabase.table("ai_tools").select("count", count="exact").execute()
        print(f"✅ Connected to Supabase!")
        print(f"📊 Current tools in database: {result.count if hasattr(result, 'count') else 0}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n⚠️ Check your .env file:")
        print(f"   SUPABASE_URL: {SUPABASE_URL}")
        print(f"   SUPABASE_KEY: {'Set' if SUPABASE_KEY else 'Not set'}")