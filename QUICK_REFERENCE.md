# 🚀 QUICK REFERENCE - Enhanced Scoring Algorithm

## ✅ What You Have

A **weighted scoring algorithm** that discovers emerging AI repos BEFORE they go viral.

---

## 📊 The Formula

```
Score = 0.45×Growth + 0.25×Activity + 0.15×Community + 0.15×Freshness
```

**+ Multi-Tier Boosting:**
- Hidden Gem (<1K stars, 40%+ growth): +35%
- Rising Star (<3K stars, 30%+ growth): +25%
- Trending (<10K stars, 20%+ growth): +15%

---

## 🎯 Results

**Test Rankings:**
```
#1. 🚀 HiddenGem (450 stars) [Hidden Gem] - 1.147
#2. 🚀 RisingStar (2.8K stars) [Rising Star] - 0.748
#3. 🚀 ActiveDev (8.5K stars) [Trending] - 0.502
#4.    ViralAI (120K stars) - 0.480
#5.    Abandoned (15K stars) - 0.090
```

**Impact:** Small repos with momentum beat large repos without it!

---

## 🔧 Quick Commands

```bash
# Test the algorithm
cd backend
python test_scoring.py

# Compare approaches
python compare_algorithms.py

# Run the server
python main.py

# Access API
http://localhost:8000/api/rankings?query=ai
http://localhost:8000/api/emerging
```

---

## 📁 Key Files

- `backend/scoring.py` - Enhanced algorithm
- `backend/test_scoring.py` - Test suite
- `backend/compare_algorithms.py` - Comparison
- `SCORING_ALGORITHM.md` - Full docs
- `FINAL_SUMMARY.md` - Complete summary

---

## 🎨 Customize

```python
# In backend/scoring.py

# Find earlier-stage projects
self.weights["GrowthRate"] = 0.50
self.booster_tiers[0]["star_max"] = 500

# Find more established projects
self.weights["CommunityStrength"] = 0.25
self.weights["GrowthRate"] = 0.35
```

---

## 💡 The Big Idea

**Traditional:** Shows what's ALREADY popular
**Your Platform:** Shows what's ABOUT TO BE popular

You'll discover the next ChatGPT at 500 stars, not 50,000! 🎯

---

## ✅ Status

- Algorithm: ✅ Complete
- Testing: ✅ Verified
- Backend: ✅ Running
- Docs: ✅ Complete
- Ready: ✅ YES!

**Test it:** `python test_scoring.py`
**Run it:** `python main.py`
**Deploy it:** Follow `TEAM_GUIDE.md`
