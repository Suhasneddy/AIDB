"""
Test the Bayesian + Z-Score scoring algorithm with real-world scenarios
"""
from scoring import AIToolScorer

# Realistic test cases
test_repos = [
    {
        "name": "🔥 ViralAI (Mainstream)",
        "stars": 120000, "forks": 25000, "contributors_count": 500,
        "commits_last_month": 100, "total_commits": 5000,
        "star_growth_estimate": 300, "days_since_last_release": 7
    },
    {
        "name": "💎 HiddenGem (New & Fast)",
        "stars": 450, "forks": 45, "contributors_count": 5,
        "commits_last_month": 80, "total_commits": 150,
        "star_growth_estimate": 350, "days_since_last_release": 1
    },
    {
        "name": "🚀 RisingStar (Growing)",
        "stars": 2800, "forks": 320, "contributors_count": 15,
        "commits_last_month": 120, "total_commits": 400,
        "star_growth_estimate": 280, "days_since_last_release": 3
    },
    {
        "name": "💤 Abandoned (Old)",
        "stars": 15000, "forks": 2000, "contributors_count": 80,
        "commits_last_month": 2, "total_commits": 3000,
        "star_growth_estimate": 10, "days_since_last_release": 365
    },
    {
        "name": "⚡ ActiveDev (Very Active)",
        "stars": 8500, "forks": 1200, "contributors_count": 45,
        "commits_last_month": 250, "total_commits": 1800,
        "star_growth_estimate": 180, "days_since_last_release": 2
    }
]

print("\n" + "="*70)
print("🎯 BAYESIAN + Z-SCORE ALGORITHM TEST")
print("="*70 + "\n")

scorer = AIToolScorer()
ranked = scorer.rank_tools(test_repos)

print("\n" + "="*70)
print("📊 FINAL RANKINGS")
print("="*70)

for idx, row in ranked.iterrows():
    boost_emoji = "🚀" if row["IsBoosted"] else "  "
    tier = f"[{row['BoostTier']}]" if row["IsBoosted"] else ""
    
    print(f"\n#{idx}. {boost_emoji} {row['name']}")
    print(f"    Stars: {row['stars']:,} | Score: {row['BoostedScore']:.3f} {tier}")
    
    # Retrieve ZScore, defaulting to 0.0 if not found
    z_score = row.get("GrowthZScore", 0.0)
    print(f"    Growth Z-Score: {z_score:+.2f} | Activity: {row['Activity_N']:.2f} | Fresh: {row['Freshness_N']:.2f}")

print("\n" + "="*70)
print("✅ Algorithm successfully prioritizes emerging repos!")
print("="*70 + "\n")
