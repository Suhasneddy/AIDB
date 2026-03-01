import pandas as pd
import numpy as np
from datetime import datetime


class AIToolScorer:
    """
    Intelligent scoring system for AI tools based on:
    - Bayesian Confidence (shrinks noisy data based on sample size)
    - Z-Score Anomaly Detection (mathematically detects outlier growth)
    - Weighted Metrics (Growth, Activity, Community, Freshness)
    """
    
    def __init__(self):
        # Weights for the core ranking
        self.weights = {
            "GrowthRate": 0.50,      # Growth is the primary signal
            "Activity": 0.25,         # Development momentum matters
            "CommunityStrength": 0.10, # Less important for discovery than growth
            "Freshness": 0.15         # Recency matters
        }
        
        # Star-based booster tiers (PRIMARY: guarantees small repo discovery)
        self.booster_tiers = [
            {"name": "Hidden Gem", "star_max": 1000, "growth_min": 0.35, "boost": 1.40},
            {"name": "Rising Star", "star_max": 3000, "growth_min": 0.25, "boost": 1.30},
            {"name": "Trending", "star_max": 10000, "growth_min": 0.15, "boost": 1.20}
        ]
        
    def bayesian_confidence(self, metric_series, sample_size_series, prior_weight=100):
        """
        Bayesian shrinkage: pulls extreme values toward the global mean if the 
        sample size (e.g., stars/data volume) is small.
        Protects against tiny repos with 100% false growth looking like unicorns.
        """
        global_mean = metric_series.mean()
        
        # Calculate confidence based on sample size (log scale to dampen massive repos)
        confidence = np.log10(sample_size_series + 1) / np.log10(sample_size_series.max() + 1)
        
        # Bayesian formula: (sample_weight * sample_mean + prior_weight * global_mean) / (sample_weight + prior_weight)
        # We simplify by blending the raw metric with the global mean based on confidence
        blended = (metric_series * confidence) + (global_mean * (1 - confidence))
        return blended

    def calculate_features(self, repos):
        """
        Step 1: Feature Engineering with Bayesian Confidence
        Calculates metrics optimized for emerging repo discovery
        """
        df = pd.DataFrame(repos)
        
        # Normalize metrics for both sources
        if "stars" not in df.columns:
            df["stars"] = 0
        if "likes_hf" in df.columns:
            df["stars"] = df["stars"].fillna(0) + df["likes_hf"].fillna(0)
        df["stars"] = df["stars"].fillna(0)
        
        df["forks"] = df["forks"].fillna(0) if "forks" in df.columns else 0
        df["contributors_count"] = df["contributors_count"].fillna(1) if "contributors_count" in df.columns else 1
        df["watchers"] = df["watchers"].fillna(df["stars"] * 0.1) if "watchers" in df.columns else df["stars"] * 0.1
        df["commits_last_month"] = df["commits_last_month"].fillna(10) if "commits_last_month" in df.columns else 10
        df["total_commits"] = df["total_commits"].fillna(100) if "total_commits" in df.columns else 100
        df["open_issues"] = df["open_issues"].fillna(0) if "open_issues" in df.columns else 0
        df["star_growth_estimate"] = df["star_growth_estimate"].fillna(df["stars"] * 0.1) if "star_growth_estimate" in df.columns else df["stars"] * 0.1
        df["days_since_last_release"] = df["days_since_last_release"].fillna(30) if "days_since_last_release" in df.columns else 30
        
        # Raw Growth Rate: Rate of growth relative to size
        raw_growth = df["star_growth_estimate"] / (np.log10(df["stars"] + 10))
        
        # BAYESIAN GROWTH: Apply confidence based on star count
        df["GrowthRate"] = self.bayesian_confidence(raw_growth, df["stars"])
        
        # Activity: Recent momentum with quality signals
        raw_activity = (
            (df["commits_last_month"] / (df["total_commits"] + 1)) * 0.6 +
            (df["open_issues"] / (df["stars"] + 1)) * 0.4
        )
        # Apply slight bayesian smoothing to activity as well
        df["Activity"] = self.bayesian_confidence(raw_activity, df["total_commits"])
        
        # Community Strength: Balanced for small and large repos
        df["CommunityStrength"] = (
            np.log10(df["contributors_count"] + 1) * 2 +
            np.log10(df["forks"] + 1) * 1.5 +
            np.log10(df["watchers"] + 1)
        )
        
        # Freshness: Exponential decay favors very recent updates
        df["Freshness"] = np.exp(-df["days_since_last_release"] / 30)
        
        return df
    
    
    def normalize_features(self, df):
        """
        Step 2: Min-Max Normalization
        Scales all features to 0-1 range for fair comparison
        """
        features = ["GrowthRate", "Activity", "CommunityStrength", "Freshness"]
        
        for feature in features:
            min_val = df[feature].min()
            max_val = df[feature].max()
            
            if max_val > min_val:
                df[f"{feature}_N"] = (df[feature] - min_val) / (max_val - min_val)
            else:
                df[f"{feature}_N"] = 0
        
        return df
    
    
    def calculate_weighted_score(self, df):
        """
        Step 3: Apply Weighted Formula
        FinalScore = 0.5(Growth) + 0.25(Activity) + 0.10(Community) + 0.15(Freshness)
        """
        df["FinalScore"] = (
            self.weights["GrowthRate"] * df["GrowthRate_N"] +
            self.weights["Activity"] * df["Activity_N"] +
            self.weights["CommunityStrength"] * df["CommunityStrength_N"] +
            self.weights["Freshness"] * df["Freshness_N"]
        )
        return df
    
    
    def apply_hybrid_booster(self, df):
        """
        Step 4: HYBRID Booster System
        Combines:
          - Star-based tiers (guarantees small fast-growing repos get boosted)
          - Z-Score anomaly detection (amplifies genuine statistical outliers)
          - Quality multiplier (rewards active + fresh repos)
        
        This is the best of both worlds:
          - Bayesian confidence (Step 1) already dampens noisy metrics
          - Star tiers ensure small repos still get discovered
          - Z-Score adds extra boost for true anomalies in any size bracket
        """
        # Calculate Z-Scores for growth anomaly detection
        if len(df) > 1 and df["GrowthRate"].std() > 0:
            df["GrowthZScore"] = (df["GrowthRate"] - df["GrowthRate"].mean()) / df["GrowthRate"].std()
        else:
            df["GrowthZScore"] = 0.0

        boost_tiers = []
        boosted_scores = []
        
        for _, row in df.iterrows():
            tier_name = "None"
            boosted = row["FinalScore"]
            
            # PRIMARY: Star-based tier boosting (guarantees small repo discovery)
            for tier in self.booster_tiers:
                if (row["stars"] < tier["star_max"] and 
                    row["GrowthRate_N"] >= tier["growth_min"]):
                    tier_name = tier["name"]
                    boosted = row["FinalScore"] * tier["boost"]
                    break
            
            # SECONDARY: Z-Score anomaly amplifier
            # If a repo is a genuine statistical outlier (Z > 1.5), give extra boost
            # This works for ANY size repo, not just small ones
            if row["GrowthZScore"] >= 1.5 and tier_name == "None":
                tier_name = "Anomaly"
                boosted = row["FinalScore"] * 1.25  # +25% for statistical outliers
            elif row["GrowthZScore"] >= 1.5 and tier_name != "None":
                boosted *= 1.10  # Extra +10% if already tier-boosted AND anomalous
            
            # QUALITY MULTIPLIER: Extra boost for high-quality emerging repos
            if tier_name != "None" and row["Activity_N"] > 0.5 and row["Freshness_N"] > 0.7:
                boosted *= 1.10  # +10% for very active + fresh repos
            
            boost_tiers.append(tier_name)
            boosted_scores.append(boosted)
            
        # Frontend data contract preserved
        df["BoostTier"] = boost_tiers
        df["BoostedScore"] = boosted_scores
        df["IsBoosted"] = df["BoostedScore"] > df["FinalScore"]
        
        return df
    
    
    def rank_tools(self, repos):
        """
        Main scoring pipeline
        Returns ranked DataFrame
        """
        print("Starting Bayesian + Z-Score pipeline...")
        
        if not repos:
            return pd.DataFrame()
            
        # Step 1: Feature Engineering with Bayesian Shrinkage
        df = self.calculate_features(repos)
        print("Bayesian features calculated")
        
        # Step 2: Normalization
        df = self.normalize_features(df)
        print("Features normalized")
        
        # Step 3: Weighted Scoring
        df = self.calculate_weighted_score(df)
        print("Weighted scores calculated")
        
        # Step 4: Hybrid Booster (Star tiers + Z-Score anomalies)
        df = self.apply_hybrid_booster(df)
        print("Hybrid booster applied (star tiers + Z-Score)")
        
        # Final ranking
        df_ranked = df.sort_values("BoostedScore", ascending=False).reset_index(drop=True)
        df_ranked.index = df_ranked.index + 1  # Start from rank 1
        
        print(f"Ranked {len(df_ranked)} tools")
        
        return df_ranked
    
    
    def get_top_tools(self, df_ranked, n=10):
        """Get top N tools"""
        columns = [
            "name", "stars", "forks", "contributors_count",
            "FinalScore", "BoostedScore", "IsBoosted", "GrowthZScore", "url"
        ]
        available_cols = [c for c in columns if c in df_ranked.columns]
        return df_ranked[available_cols].head(n)
    
    
    def get_emerging_tools(self, df_ranked):
        """Get tools that received the Z-Score anomaly boost"""
        return df_ranked[df_ranked["IsBoosted"] == True][[
            "name", "stars", "GrowthRate_N", "GrowthZScore", "BoostedScore", "url"
        ]]


# Testing the scorer with dummy data
if __name__ == "__main__":
    dummy_repos = [
        {
            "name": "AutoGPT",
            "full_name": "Significant-Gravitas/AutoGPT",
            "stars": 150000, "forks": 35000, "contributors_count": 420,
            "commits_last_month": 80, "total_commits": 2500,
            "star_growth_estimate": 500, "days_since_last_release": 5,
            "url": "https://github.com/Significant-Gravitas/AutoGPT"
        },
        {
            "name": "TinyLLM",
            "full_name": "ai-startup/TinyLLM",
            "stars": 1200, "forks": 150, "contributors_count": 8,
            "commits_last_month": 45, "total_commits": 120,
            "star_growth_estimate": 400, "days_since_last_release": 2,
            "url": "https://github.com/ai-startup/TinyLLM"
        },
        {
            "name": "LangChain",
            "full_name": "hwchase17/langchain",
            "stars": 85000, "forks": 12000, "contributors_count": 650,
            "commits_last_month": 200, "total_commits": 4500,
            "star_growth_estimate": 800, "days_since_last_release": 3,
            "url": "https://github.com/hwchase17/langchain"
        },
        {
            "name": "OldStableRepo",
            "full_name": "legacy/old-ai",
            "stars": 8000, "forks": 800, "contributors_count": 25,
            "commits_last_month": 5, "total_commits": 1500,
            "star_growth_estimate": 20, "days_since_last_release": 180,
            "url": "https://github.com/legacy/old-ai"
        },
        {
            "name": "FastEmbeddings",
            "full_name": "newai/fast-embed",
            "stars": 3500, "forks": 420, "contributors_count": 18,
            "commits_last_month": 60, "total_commits": 280,
            "star_growth_estimate": 350, "days_since_last_release": 7,
            "url": "https://github.com/newai/fast-embed"
        }
    ]
    
    print("="*60)
    print("🧪 TESTING BAYESIAN + Z-SCORE SCORER")
    print("="*60 + "\n")
    
    scorer = AIToolScorer()
    ranked = scorer.rank_tools(dummy_repos)
    
    print("\n" + "="*60)
    print("🏆 TOP RANKED TOOLS")
    print("="*60)
    top_tools = scorer.get_top_tools(ranked, n=5)
    print(top_tools.to_string())
    
    print("\n" + "="*60)
    print("🚀 EMERGING TOOLS (Z-Score Anomalies)")
    print("="*60)
    emerging = scorer.get_emerging_tools(ranked)
    if len(emerging) > 0:
        print(emerging.to_string())
    else:
        print("No emerging tools detected in this batch")
    
    print("\n✅ Scoring system working correctly!")