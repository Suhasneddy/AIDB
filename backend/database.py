import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

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

# ─── Analytics / Page View Tracking ───

def record_page_view(page, referrer="", user_agent=""):
    """Record a single page view in the page_views table."""
    try:
        record = {
            "page": page,
            "referrer": referrer or "",
            "user_agent": user_agent or "",
            "created_at": datetime.now().isoformat(),
        }
        result = supabase.table("page_views").insert(record).execute()
        return True
    except Exception as e:
        print(f"❌ Error recording page view: {e}")
        return False


def get_page_view_analytics(period="daily", days=30):
    """
    Get page view analytics aggregated by time period.
    period: 'daily', 'weekly', or 'monthly'
    Returns: list of {date, count} dicts
    """
    try:
        # Calculate date range
        if period == "weekly":
            since = datetime.now() - timedelta(days=90)
        elif period == "monthly":
            since = datetime.now() - timedelta(days=365)
        else:  # daily
            since = datetime.now() - timedelta(days=days)

        since_str = since.isoformat()

        # Fetch raw page views within range
        result = supabase.table("page_views").select(
            "created_at, page"
        ).gte("created_at", since_str).order(
            "created_at", desc=False
        ).execute()

        rows = result.data or []

        # Aggregate by date
        date_counts = {}
        page_counts = {}

        for row in rows:
            ts = row.get("created_at", "")
            page = row.get("page", "unknown")

            if not ts:
                continue

            # Parse date
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                continue

            if period == "monthly":
                key = dt.strftime("%Y-%m")
            elif period == "weekly":
                # ISO week: Monday start
                week_start = dt - timedelta(days=dt.weekday())
                key = week_start.strftime("%Y-%m-%d")
            else:
                key = dt.strftime("%Y-%m-%d")

            date_counts[key] = date_counts.get(key, 0) + 1
            page_counts[page] = page_counts.get(page, 0) + 1

        # Sort and format
        timeline = [{"date": k, "views": v} for k, v in sorted(date_counts.items())]
        top_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "timeline": timeline,
            "top_pages": [{"page": p, "views": v} for p, v in top_pages],
            "total": sum(date_counts.values()),
            "period": period,
        }

    except Exception as e:
        print(f"❌ Error fetching analytics: {e}")
        return {"timeline": [], "top_pages": [], "total": 0, "period": period}


def get_page_view_summary():
    """Get quick summary: total views, today's views, this week's views."""
    try:
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        # Total views
        total_res = supabase.table("page_views").select(
            "id", count="exact"
        ).execute()
        total = total_res.count if hasattr(total_res, 'count') and total_res.count else len(total_res.data or [])

        # Today's views
        today_res = supabase.table("page_views").select(
            "id", count="exact"
        ).gte("created_at", today_start).execute()
        today = today_res.count if hasattr(today_res, 'count') and today_res.count else len(today_res.data or [])

        # This week's views
        week_res = supabase.table("page_views").select(
            "id", count="exact"
        ).gte("created_at", week_start).execute()
        week = week_res.count if hasattr(week_res, 'count') and week_res.count else len(week_res.data or [])

        return {"total": total, "today": today, "this_week": week}

    except Exception as e:
        print(f"❌ Error fetching page view summary: {e}")
        return {"total": 0, "today": 0, "this_week": 0}


def get_feedback_analytics():
    """Get feedback breakdown: by type, by rating, by date."""
    try:
        all_feedback = get_all_feedback()

        type_counts = {}
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        daily_counts = {}

        for fb in all_feedback:
            # Type distribution
            fb_type = fb.get("feedback_type", "general")
            type_counts[fb_type] = type_counts.get(fb_type, 0) + 1

            # Rating distribution
            rating = fb.get("rating", 0)
            if rating in rating_counts:
                rating_counts[rating] += 1

            # Daily trend
            ts = fb.get("created_at", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    day_key = dt.strftime("%Y-%m-%d")
                    daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
                except Exception:
                    pass

        total = len(all_feedback)
        avg_rating = round(
            sum(fb.get("rating", 0) for fb in all_feedback) / max(total, 1), 1
        )

        return {
            "total": total,
            "average_rating": avg_rating,
            "by_type": [{"type": k, "count": v} for k, v in type_counts.items()],
            "by_rating": [{"rating": k, "count": v} for k, v in sorted(rating_counts.items())],
            "daily_trend": [{"date": k, "count": v} for k, v in sorted(daily_counts.items())],
        }

    except Exception as e:
        print(f"❌ Error fetching feedback analytics: {e}")
        return {"total": 0, "average_rating": 0, "by_type": [], "by_rating": [], "daily_trend": []}


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


# ─── Feedback CRUD ───

def save_feedback(data):
    """Save user feedback to the feedback table."""
    try:
        record = {
            "name": data.get("name", "Anonymous"),
            "email": data.get("email", ""),
            "rating": data.get("rating", 5),
            "message": data.get("message", ""),
            "feedback_type": data.get("feedback_type", "general"),
            "created_at": datetime.now().isoformat(),
        }
        result = supabase.table("feedback").insert(record).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"❌ Error saving feedback: {e}")
        return None


def get_all_feedback():
    """Get all feedback entries (admin)."""
    try:
        result = supabase.table("feedback").select("*").order(
            "created_at", desc=True
        ).execute()
        return result.data or []
    except Exception as e:
        print(f"❌ Error fetching feedback: {e}")
        return []


def delete_feedback(feedback_id):
    """Delete a feedback entry by ID."""
    try:
        result = supabase.table("feedback").delete().eq("id", feedback_id).execute()
        return True
    except Exception as e:
        print(f"❌ Error deleting feedback: {e}")
        return False


# ─── Tool Suggestion CRUD ───

def save_tool_suggestion(data):
    """Save a user's AI tool suggestion."""
    try:
        record = {
            "tool_name": data.get("tool_name", ""),
            "tool_url": data.get("tool_url", ""),
            "category": data.get("category", ""),
            "description": data.get("description", ""),
            "submitter_name": data.get("submitter_name", "Anonymous"),
            "submitter_email": data.get("submitter_email", ""),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        result = supabase.table("tool_suggestions").insert(record).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"❌ Error saving tool suggestion: {e}")
        return None


def get_all_suggestions():
    """Get all tool suggestions (admin)."""
    try:
        result = supabase.table("tool_suggestions").select("*").order(
            "created_at", desc=True
        ).execute()
        return result.data or []
    except Exception as e:
        print(f"❌ Error fetching suggestions: {e}")
        return []


def delete_suggestion(suggestion_id):
    """Delete a tool suggestion by ID."""
    try:
        result = supabase.table("tool_suggestions").delete().eq("id", suggestion_id).execute()
        return True
    except Exception as e:
        print(f"❌ Error deleting suggestion: {e}")
        return False