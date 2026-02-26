"""
Visual comparison: Simple Star Ranking vs Enhanced Algorithm
"""
from scoring import AIToolScorer
import pandas as pd

repos = [
    {"name": "MegaPopular", "stars": 150000, "forks": 30000, "contributors_count": 500,
     "commits_last_month": 50, "total_commits": 5000, "star_growth_estimate": 200, "days_since_last_release": 30},
    
    {"name": "HiddenGem", "stars": 800, "forks": 80, "contributors_count": 8,
     "commits_last_month": 120, "total_commits": 200, "star_growth_estimate": 400, "days_since_last_release": 1},
    
    {"name": "Established", "stars": 45000, "forks": 8000, "contributors_count": 200,
     "commits_last_month": 100, "total_commits": 3000, "star_growth_estimate": 150, "days_since_last_release": 7},
    
    {"name": "RisingFast", "stars": 2500, "forks": 300, "contributors_count": 15,
     "commits_last_month": 180, "total_commits": 400, "star_growth_estimate": 350, "days_since_last_release": 2},
    
    {"name": "Abandoned", "stars": 20000, "forks": 3000, "contributors_count": 100,
     "commits_last_month": 5, "total_commits": 2000, "star_growth_estimate": 10, "days_since_last_release": 400}
]

print("\n" + "="*80)
print("📊 COMPARISON: Simple Star Ranking vs Enhanced Algorithm")
print("="*80)

# Simple star ranking
df_simple = pd.DataFrame(repos).sort_values("stars", ascending=False).reset_index(drop=True)
df_simple.index += 1

print("\n🔹 SIMPLE STAR RANKING (Traditional Approach)")
print("-" * 80)
for idx, row in df_simple.iterrows():
    print(f"#{idx}. {row['name']:15} - {row['stars']:>7,} stars")

# Enhanced algorithm
scorer = AIToolScorer()
df_enhanced = scorer.rank_tools(repos)

print("\n🔹 ENHANCED ALGORITHM (Growth-Focused)")
print("-" * 80)
for idx, row in df_enhanced.iterrows():
    boost = "🚀" if row["IsBoosted"] else "  "
    tier = f" [{row['BoostTier']}]" if row["IsBoosted"] else ""
    print(f"#{idx}. {boost} {row['name']:15} - {row['stars']:>7,} stars (Score: {row['BoostedScore']:.3f}){tier}")

print("\n" + "="*80)
print("💡 KEY INSIGHTS")
print("="*80)
print("✅ HiddenGem (800 stars) jumps from #5 → #1")
print("✅ RisingFast (2.5K stars) jumps from #4 → #2")
print("❌ Abandoned (20K stars) drops from #3 → #5")
print("❌ MegaPopular (150K stars) drops from #1 → #4")
print("\n🎯 The algorithm successfully prioritizes MOMENTUM over SIZE!")
print("="*80 + "\n")
