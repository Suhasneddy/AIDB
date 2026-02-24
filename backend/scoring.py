import pandas as pd
import numpy as np
from datetime import datetime


class AIToolScorer:
    """
    Intelligent scoring system for AI tools based on:
    - Growth Rate
    - Development Activity  
    - Community Strength
    - Freshness
    """
    
    def __init__(self):
        self.weights = {
            "GrowthRate": 0.40,
            "Activity": 0.25,
            "CommunityStrength": 0.20,
            "Freshness": 0.15
        }
        
        # Early-stage booster thresholds
        self.growth_threshold = 0.3
        self.star_limit = 5000
        
    
    def calculate_features(self, repos):
        """
        Step 1: Feature Engineering
        Calculate the 4 core metrics from raw data
        """
        df = pd.DataFrame(repos)
        
        # Growth Rate: proportional star growth
        # Higher value = faster growing relative to size
        df["GrowthRate"] = df["star_growth_estimate"] / (df["stars"] + 1)
        
        # Activity: recent development activity
        # Higher value = more active development
        df["Activity"] = df["commits_last_month"] / (df["total_commits"] + 1)
        
        # Community Strength: engagement metrics
        # Higher value = stronger community
        df["CommunityStrength"] = (
            df["contributors_count"] + 
            df["forks"] + 
            (df["stars"] / 100)  # Normalize stars contribution
        )
        
        # Freshness: recency of updates
        # Higher value = more recently updated
        df["Freshness"] = 1 / (df["days_since_last_release"] + 1)
        
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
        FinalScore = 0.4(Growth) + 0.25(Activity) + 0.2(Community) + 0.15(Freshness)
        """
        df["FinalScore"] = (
            self.weights["GrowthRate"] * df["GrowthRate_N"] +
            self.weights["Activity"] * df["Activity_N"] +
            self.weights["CommunityStrength"] * df["CommunityStrength_N"] +
            self.weights["Freshness"] * df["Freshness_N"]
        )
        
        return df
    
    
    def apply_early_stage_booster(self, df):
        """
        Step 4: Early-Stage Growth Booster
        Give 20% bonus to small repos with high growth
        This discovers hidden gems before they go viral
        """
        def boost_score(row):
            if (row["GrowthRate_N"] > self.growth_threshold and 
                row["stars"] < self.star_limit):
                return row["FinalScore"] * 1.2
            return row["FinalScore"]
        
        df["BoostedScore"] = df.apply(boost_score, axis=1)
        df["IsBoosted"] = df["BoostedScore"] > df["FinalScore"]
        
        return df
    
    
    def rank_tools(self, repos):
        """
        Main scoring pipeline
        Returns ranked DataFrame
        """
        print("🔄 Starting scoring pipeline...")
        
        # Step 1: Feature Engineering
        df = self.calculate_features(repos)
        print("✅ Features calculated")
        
        # Step 2: Normalization
        df = self.normalize_features(df)
        print("✅ Features normalized")
        
        # Step 3: Weighted Scoring
        df = self.calculate_weighted_score(df)
        print("✅ Weighted scores calculated")
        
        # Step 4: Early-Stage Booster
        df = self.apply_early_stage_booster(df)
        print("✅ Booster applied")
        
        # Final ranking
        df_ranked = df.sort_values("BoostedScore", ascending=False).reset_index(drop=True)
        df_ranked.index = df_ranked.index + 1  # Start from rank 1
        
        print(f"✅ Ranked {len(df_ranked)} tools")
        
        return df_ranked
    
    
    def get_top_tools(self, df_ranked, n=10):
        """
        Get top N tools with key metrics
        """
        columns = [
            "name", "stars", "forks", "contributors_count",
            "FinalScore", "BoostedScore", "IsBoosted", "url"
        ]
        
        return df_ranked[columns].head(n)
    
    
    def get_emerging_tools(self, df_ranked):
        """
        Get tools that received the early-stage boost
        """
        return df_ranked[df_ranked["IsBoosted"] == True][[
            "name", "stars", "GrowthRate_N", "BoostedScore", "url"
        ]]


# Testing the scorer with dummy data
if __name__ == "__main__":
    # Dummy data for testing
    dummy_repos = [
        {
            "name": "AutoGPT",
            "full_name": "Significant-Gravitas/AutoGPT",
            "stars": 150000,
            "forks": 35000,
            "contributors_count": 420,
            "commits_last_month": 80,
            "total_commits": 2500,
            "star_growth_estimate": 500,
            "days_since_last_release": 5,
            "url": "https://github.com/Significant-Gravitas/AutoGPT"
        },
        {
            "name": "TinyLLM",
            "full_name": "ai-startup/TinyLLM",
            "stars": 1200,
            "forks": 150,
            "contributors_count": 8,
            "commits_last_month": 45,
            "total_commits": 120,
            "star_growth_estimate": 400,  # Fast growing!
            "days_since_last_release": 2,
            "url": "https://github.com/ai-startup/TinyLLM"
        },
        {
            "name": "LangChain",
            "full_name": "hwchase17/langchain",
            "stars": 85000,
            "forks": 12000,
            "contributors_count": 650,
            "commits_last_month": 200,
            "total_commits": 4500,
            "star_growth_estimate": 800,
            "days_since_last_release": 3,
            "url": "https://github.com/hwchase17/langchain"
        },
        {
            "name": "OldStableRepo",
            "full_name": "legacy/old-ai",
            "stars": 8000,
            "forks": 800,
            "contributors_count": 25,
            "commits_last_month": 5,
            "total_commits": 1500,
            "star_growth_estimate": 20,  # Barely growing
            "days_since_last_release": 180,
            "url": "https://github.com/legacy/old-ai"
        },
        {
            "name": "FastEmbeddings",
            "full_name": "newai/fast-embed",
            "stars": 3500,
            "forks": 420,
            "contributors_count": 18,
            "commits_last_month": 60,
            "total_commits": 280,
            "star_growth_estimate": 350,
            "days_since_last_release": 7,
            "url": "https://github.com/newai/fast-embed"
        }
    ]
    
    print("="*60)
    print("🧪 TESTING AI TOOL SCORER")
    print("="*60 + "\n")
    
    scorer = AIToolScorer()
    ranked = scorer.rank_tools(dummy_repos)
    
    print("\n" + "="*60)
    print("🏆 TOP RANKED TOOLS")
    print("="*60)
    top_tools = scorer.get_top_tools(ranked, n=5)
    print(top_tools.to_string())
    
    print("\n" + "="*60)
    print("🚀 EMERGING TOOLS (Early-Stage Boost Applied)")
    print("="*60)
    emerging = scorer.get_emerging_tools(ranked)
    if len(emerging) > 0:
        print(emerging.to_string())
    else:
        print("No emerging tools detected in this batch")
    
    print("\n✅ Scoring system working correctly!")