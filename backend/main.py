from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from datafetcher import fetch_github_repos
from scoring import AIToolScorer
from cache_manager import cache

app = FastAPI(
    title="AI Tool Discovery API",
    description="Real-time AI tool ranking with growth-based intelligence",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scorer = AIToolScorer()


@app.get("/")
def root():
    """Health check"""
    return {
        "status": "online",
        "message": "AI Tool Discovery API - Mini Project Demo",
        "endpoints": ["/api/rankings", "/api/emerging", "/api/categories"]
    }


@app.get("/api/rankings")
def get_rankings(query: str = "machine-learning", limit: int = 20):
    """Get ranked AI tools - WITH CACHING FOR SPEED!"""
    try:
        cache_key = f"rankings_{query}_{limit}"
        
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return {
                "success": True,
                "total": len(cached_data),
                "query": query,
                "from_cache": True,
                "data": cached_data
            }
        
        # If not in cache, fetch fresh data
        print(f"📡 Fetching fresh data for: {query}")
        repos = fetch_github_repos(query=query, max_results=min(limit, 30))
        
        if not repos:
            return {"success": False, "message": "No repositories found", "data": []}
        
        ranked_df = scorer.rank_tools(repos)
        results = ranked_df.to_dict('records')
        
        # Save to cache for next time
        cache.set(cache_key, results)
        
        return {
            "success": True,
            "total": len(results),
            "query": query,
            "from_cache": False,
            "data": results
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "message": str(e), "data": []}


@app.get("/api/emerging")
def get_emerging():
    """Get fast-growing emerging tools - WITH CACHING!"""
    try:
        cache_key = "emerging_tools"
        
        # Try cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return {
                "success": True,
                "total": len(cached_data),
                "from_cache": True,
                "data": cached_data
            }
        
        print(f"📡 Fetching emerging tools...")
        repos = fetch_github_repos(query="ai OR llm", max_results=30)
        
        if not repos:
            return {"success": False, "message": "No repositories found", "data": []}
        
        ranked_df = scorer.rank_tools(repos)
        emerging_df = scorer.get_emerging_tools(ranked_df)
        
        results = emerging_df.to_dict('records')
        
        # Cache it
        cache.set(cache_key, results)
        
        return {
            "success": True,
            "total": len(results),
            "from_cache": False,
            "data": results
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "message": str(e), "data": []}


@app.get("/api/categories")
def get_categories():
    """Get available categories"""
    categories = [
        {"name": "🤖 LLMs", "query": "gpt OR llm OR language-model", "icon": "🤖"},
        {"name": "🎨 Image Gen", "query": "stable-diffusion OR image-generation OR dall-e", "icon": "🎨"},
        {"name": "🎬 Video AI", "query": "video-generation OR text-to-video", "icon": "🎬"},
        {"name": "🎵 Audio AI", "query": "text-to-speech OR music-generation OR voice", "icon": "🎵"},
        {"name": "💻 Code AI", "query": "code-generation OR copilot OR ai-coding", "icon": "💻"},
        {"name": "👁️ Vision", "query": "computer-vision OR object-detection", "icon": "👁️"},
        {"name": "💬 NLP", "query": "nlp OR sentiment-analysis OR text", "icon": "💬"},
        {"name": "🔬 Research", "query": "machine-learning OR deep-learning OR research", "icon": "🔬"},
        {"name": "⚡ Productivity", "query": "automation OR workflow OR productivity", "icon": "⚡"},
        {"name": "✨ Creative", "query": "generative-art OR creative-ai OR design", "icon": "✨"}
    ]
    
    return {"success": True, "categories": categories}


@app.get("/api/clear-cache")
def clear_cache():
    """Clear all cache - useful for refreshing data"""
    cache.clear()
    return {"success": True, "message": "Cache cleared"}


if __name__ == "__main__":
    print("="*60)
    print("🚀 AI Tool Discovery API - FAST VERSION")
    print("="*60)
    print("\n📍 Server: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("💾 Caching enabled - first load slow, then INSTANT!")
    print("\n✨ Ready for demo!")
    print("Press CTRL+C to stop\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)