"""
Cache Warmup Script
Run this BEFORE your demo to pre-load all data into cache
This makes the demo SUPER FAST!
"""

import requests
import time

API_URL = "http://localhost:8000"

print("🔥 WARMING UP CACHE...")
print("="*60)

# Queries to pre-load
queries = [
    ("machine-learning", 20),
    ("ai", 8),
    ("github", 6),
    ("gpt OR llm", 30),
    ("stable-diffusion OR image-generation", 20),
    ("video-generation", 15),
]

total = len(queries) + 1  # +1 for emerging
completed = 0

for query, limit in queries:
    try:
        print(f"\n📡 Fetching: {query[:50]}...")
        response = requests.get(f"{API_URL}/api/rankings", params={"query": query, "limit": limit})
        
        if response.status_code == 200:
            data = response.json()
            completed += 1
            print(f"✅ Cached {data.get('total', 0)} tools for '{query}'")
        else:
            print(f"❌ Failed: {query}")
        
        time.sleep(1)  # Be nice to the API
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Warm up emerging tools
try:
    print(f"\n📡 Fetching emerging tools...")
    response = requests.get(f"{API_URL}/api/emerging")
    if response.status_code == 200:
        data = response.json()
        completed += 1
        print(f"✅ Cached {data.get('total', 0)} emerging tools")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print(f"🎉 CACHE WARMED! ({completed}/{total} endpoints)")
print("✨ Your app is now SUPER FAST!")
print("="*60)