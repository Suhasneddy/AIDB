import asyncio
import threading
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from datafetcher import fetch_all_ai_repos, fetch_github_repos
from scoring import AIToolScorer
from cache_manager import cache

app = FastAPI(
    title="AI Tool Discovery API",
    description="Real-time AI tool ranking with growth-based intelligence",
    version="2.0.0"
)

# Enable CORS - Allow ALL origins so Vercel frontend can talk to Render backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scorer = AIToolScorer()

# ─── Global state ───
_data_ready = False


def _preload_data():
    """
    Background function: Fetch 100 AI repos, score them, and cache everything.
    Runs on server startup and every 30 minutes after.
    """
    global _data_ready
    print("\n" + "=" * 60)
    print("🚀 PRELOADING AI TOOL DATA...")
    print("=" * 60)

    try:
        # Step 1: Fetch 100 repos in parallel (~5 seconds)
        repos = fetch_all_ai_repos(target_count=100)

        if not repos:
            print("❌ No repos fetched. Check GITHUB_TOKEN.")
            return

        # Step 2: Score and rank them
        ranked_df = scorer.rank_tools(repos)
        all_results = ranked_df.to_dict("records")

        # Step 3: Cache the full dataset
        cache.set("all_tools", all_results)

        # Step 4: Pre-build category caches
        categories_map = {
            "ai": "ai OR artificial-intelligence",
            "machine-learning": "machine-learning OR deep-learning",
            "llm": "gpt OR llm OR language-model",
            "image-generation": "stable-diffusion OR image-generation",
            "code-ai": "code-generation OR copilot OR ai-coding",
            "nlp": "nlp OR sentiment-analysis OR text",
            "computer-vision": "computer-vision OR object-detection",
            "audio-ai": "text-to-speech OR music-generation OR voice",
            "video-ai": "video-generation OR text-to-video",
            "research": "machine-learning OR deep-learning OR research",
        }

        for cat_key, _ in categories_map.items():
            # Filter from the already-fetched data by matching topics
            cat_results = [t for t in all_results if _matches_category(t, cat_key)]
            if cat_results:
                cache.set(f"rankings_{cat_key}", cat_results)

        # Step 5: Cache trending (top by BoostedScore)
        cache.set("rankings_ai_8", all_results[:8])
        cache.set("rankings_machine-learning_10", all_results[:10])
        cache.set("rankings_github_6", all_results[:6])

        # Step 6: Cache emerging tools
        emerging_df = scorer.get_emerging_tools(ranked_df)
        cache.set("emerging_tools", emerging_df.to_dict("records"))

        _data_ready = True
        print(f"\n✅ PRELOAD COMPLETE! {len(all_results)} tools cached and ready.")
        print("⚡ All API endpoints will now respond INSTANTLY!\n")

    except Exception as e:
        print(f"❌ Preload error: {e}")
        import traceback
        traceback.print_exc()


def _matches_category(tool, category):
    """Check if a tool matches a category based on its topics, name, or language."""
    topics = [t.lower() for t in tool.get("topics", [])]
    name = tool.get("name", "").lower()
    desc = (tool.get("description") or "").lower()

    keyword_map = {
        "ai": ["ai", "artificial-intelligence", "machine-learning", "deep-learning"],
        "machine-learning": ["machine-learning", "deep-learning", "ml", "neural-network"],
        "llm": ["llm", "gpt", "language-model", "chatgpt", "transformer", "nlp"],
        "image-generation": ["stable-diffusion", "image-generation", "dall-e", "diffusion", "text-to-image"],
        "code-ai": ["code-generation", "copilot", "coding", "code-assistant"],
        "nlp": ["nlp", "text", "sentiment", "language"],
        "computer-vision": ["computer-vision", "object-detection", "image-classification", "yolo"],
        "audio-ai": ["text-to-speech", "tts", "music", "voice", "audio"],
        "video-ai": ["video-generation", "text-to-video", "video"],
        "research": ["research", "paper", "benchmark", "dataset"],
    }

    keywords = keyword_map.get(category, [category])
    search_text = " ".join(topics) + " " + name + " " + desc
    return any(kw in search_text for kw in keywords)


def _schedule_refresh():
    """Refresh data every 30 minutes in a background thread."""
    while True:
        time.sleep(1800)  # 30 minutes
        print("🔄 Scheduled data refresh starting...")
        _preload_data()


@app.on_event("startup")
async def startup_event():
    """On server start: preload data in background thread."""
    print("🚀 Starting AI Tool Discovery API v2.0...")

    # Start preloading in a background thread (non-blocking)
    thread = threading.Thread(target=_preload_data, daemon=True)
    thread.start()

    # Start the periodic refresh scheduler
    refresh_thread = threading.Thread(target=_schedule_refresh, daemon=True)
    refresh_thread.start()


@app.get("/")
def root():
    """Health check"""
    return {
        "status": "online",
        "data_ready": _data_ready,
        "message": "AI Tool Discovery API v2.0 - IMDB for AI Tools",
        "cached_keys": cache.get_all_keys(),
        "endpoints": [
            "/api/rankings",
            "/api/rankings?query=llm&limit=20",
            "/api/emerging",
            "/api/categories",
            "/api/tool/{owner/repo}",
            "/api/search?q=keyword",
            "/api/refresh",
        ]
    }


@app.get("/api/rankings")
def get_rankings(query: str = "ai", limit: int = 20):
    """Get ranked AI tools — cached and instant after startup."""
    try:
        # Try specific cache key first
        cache_key = f"rankings_{query}_{limit}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return {
                "success": True,
                "total": len(cached_data),
                "query": query,
                "from_cache": True,
                "data": cached_data[:limit]
            }

        # Try the master "all_tools" cache and filter
        all_tools = cache.get("all_tools")
        if all_tools:
            filtered = [t for t in all_tools if _matches_category(t, query)]
            if not filtered:
                filtered = all_tools  # Fallback to all tools
            results = filtered[:limit]
            cache.set(cache_key, results)
            return {
                "success": True,
                "total": len(results),
                "query": query,
                "from_cache": True,
                "data": results
            }

        # If no cache at all (first request before preload finishes), fetch live
        print(f"📡 Cache miss - fetching live for: {query}")
        repos = fetch_github_repos(query=query, max_results=min(limit, 30))

        if not repos:
            return {"success": False, "message": "No repositories found. Data is still loading, try again in 30 seconds.", "data": []}

        ranked_df = scorer.rank_tools(repos)
        results = ranked_df.to_dict("records")
        cache.set(cache_key, results)

        return {
            "success": True,
            "total": len(results),
            "query": query,
            "from_cache": False,
            "data": results[:limit]
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "message": str(e), "data": []}


@app.get("/api/emerging")
def get_emerging():
    """Get fast-growing emerging tools — cached!"""
    try:
        cached_data = cache.get("emerging_tools")
        if cached_data:
            return {
                "success": True,
                "total": len(cached_data),
                "from_cache": True,
                "data": cached_data
            }

        # Fallback: compute from all_tools
        all_tools = cache.get("all_tools")
        if all_tools:
            emerging = [t for t in all_tools if t.get("IsBoosted", False)]
            cache.set("emerging_tools", emerging)
            return {
                "success": True,
                "total": len(emerging),
                "from_cache": True,
                "data": emerging
            }

        return {"success": False, "message": "Data still loading, try again in 30 seconds.", "data": []}

    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "message": str(e), "data": []}


@app.get("/api/categories")
def get_categories():
    """Get available categories"""
    categories = [
        {"name": "🤖 LLMs", "query": "llm", "icon": "🤖"},
        {"name": "🎨 Image Gen", "query": "image-generation", "icon": "🎨"},
        {"name": "🎬 Video AI", "query": "video-ai", "icon": "🎬"},
        {"name": "🎵 Audio AI", "query": "audio-ai", "icon": "🎵"},
        {"name": "💻 Code AI", "query": "code-ai", "icon": "💻"},
        {"name": "👁️ Vision", "query": "computer-vision", "icon": "👁️"},
        {"name": "💬 NLP", "query": "nlp", "icon": "💬"},
        {"name": "🔬 Research", "query": "research", "icon": "🔬"},
        {"name": "⚡ All AI", "query": "ai", "icon": "⚡"},
        {"name": "🧠 ML", "query": "machine-learning", "icon": "🧠"},
    ]

    return {"success": True, "categories": categories}


@app.get("/api/tool/{owner}/{repo}")
def get_tool_detail(owner: str, repo: str):
    """Get details for a specific tool by owner/repo"""
    full_name = f"{owner}/{repo}"
    try:
        all_tools = cache.get("all_tools")
        if all_tools:
            tool = next((t for t in all_tools if t.get("full_name") == full_name), None)
            if tool:
                return {"success": True, "data": tool}

        return {"success": False, "message": f"Tool '{full_name}' not found"}

    except Exception as e:
        return {"success": False, "message": str(e)}


@app.get("/api/search")
def search_tools(q: str = "", limit: int = 20):
    """Search tools by name, description, or topics"""
    if not q:
        return {"success": False, "message": "Query parameter 'q' is required", "data": []}

    try:
        all_tools = cache.get("all_tools")
        if all_tools:
            q_lower = q.lower()
            results = [
                t for t in all_tools
                if q_lower in t.get("name", "").lower()
                or q_lower in (t.get("description") or "").lower()
                or q_lower in " ".join(t.get("topics", [])).lower()
            ]
            return {
                "success": True,
                "total": len(results[:limit]),
                "query": q,
                "data": results[:limit]
            }

        # Fallback to live search
        repos = fetch_github_repos(query=q, max_results=limit)
        if repos:
            ranked_df = scorer.rank_tools(repos)
            results = ranked_df.to_dict("records")
            return {"success": True, "total": len(results), "query": q, "data": results}

        return {"success": True, "total": 0, "query": q, "data": []}

    except Exception as e:
        return {"success": False, "message": str(e), "data": []}


@app.get("/api/refresh")
def refresh_data():
    """Manually trigger a data refresh (runs in background)"""
    thread = threading.Thread(target=_preload_data, daemon=True)
    thread.start()
    return {"success": True, "message": "Data refresh started in background. Check back in ~10 seconds."}


@app.get("/api/clear-cache")
def clear_cache():
    """Clear all cache"""
    cache.clear()
    return {"success": True, "message": "Cache cleared"}


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AI Tool Discovery API v2.0 - IMDB for AI Tools")
    print("=" * 60)
    print("\n📍 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("⚡ Data preloads on startup — first request takes ~10s, then INSTANT!")
    print("\n✨ Ready for demo!")
    print("Press CTRL+C to stop\n")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)