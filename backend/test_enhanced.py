from scoring import AIToolScorer

# Test data
repos = [
    {"name": "HiddenGem", "stars": 450, "forks": 45, "contributors_count": 5,
     "commits_last_month": 80, "total_commits": 150, "star_growth_estimate": 350, "days_since_last_release": 1},
    
    {"name": "ViralAI", "stars": 120000, "forks": 25000, "contributors_count": 500,
     "commits_last_month": 100, "total_commits": 5000, "star_growth_estimate": 300, "days_since_last_release": 7},
]

print("\n" + "="*60)
print("ENHANCED ALGORITHM TEST")
print("="*60 + "\n")

scorer = AIToolScorer()
ranked = scorer.rank_tools(repos)

print("\nRESULTS:")
print("-"*60)
for idx, row in ranked.iterrows():
    boost = "[BOOSTED]" if row["IsBoosted"] else ""
    print(f"#{idx}. {row['name']:15} - {row['stars']:>7,} stars")
    print(f"    Score: {row['BoostedScore']:.3f} {boost}")
    print(f"    Tier: {row['BoostTier']}")
    print()

print("="*60)
print("WEIGHTS:")
print(f"  Growth: {scorer.weights['GrowthRate']*100:.0f}%")
print(f"  Activity: {scorer.weights['Activity']*100:.0f}%")
print(f"  Community: {scorer.weights['CommunityStrength']*100:.0f}%")
print(f"  Freshness: {scorer.weights['Freshness']*100:.0f}%")
print("\nBOOST TIERS:")
for tier in scorer.booster_tiers:
    print(f"  {tier['name']}: <{tier['star_max']} stars, {tier['growth_min']*100:.0f}%+ growth = +{(tier['boost']-1)*100:.0f}% boost")
print("="*60)
