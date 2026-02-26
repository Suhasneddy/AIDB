# 🎨 Frontend - AI Discovery Platform

## 📄 Pages

### 1. **index.html** - Homepage
- Hero section with search
- Trending tools (top 8)
- Top 10 rankings
- Open source highlights

### 2. **discover.html** - Main Discovery Page ⭐ NEW!
**Full-featured tool discovery with:**
- ✅ Category filters (9 categories)
- ✅ Result limits (Top 20/30/50)
- ✅ Multiple sort options (Score/Stars/Growth/Freshness)
- ✅ Real-time filtering
- ✅ Boost tier badges
- ✅ Stats dashboard

### 3. **rankings.html** - Full Rankings List
- Top 30 AI repositories
- Filter by trending/new/most stars
- Mobile-optimized

### 4. **tool.html** - Individual Tool Details
- Detailed tool information
- Metrics and scores
- Direct GitHub link

### 5. **compare.html** - Compare Tools
- Side-by-side comparison
- Metric breakdown

## 🚀 Quick Start

### 1. Start Backend
```bash
cd backend
python main.py
```
Backend runs at: `http://localhost:8000`

### 2. Open Frontend
Simply open any HTML file in your browser:
- `index.html` - Start here
- `discover.html` - Full discovery experience

## 🎯 Discovery Page Features

### Category Filters
- 🤖 **LLMs** - Language models, GPT, transformers
- 🎨 **Image Gen** - Stable Diffusion, DALL-E, image generation
- 🎬 **Video AI** - Video generation, text-to-video
- 🎵 **Audio AI** - Text-to-speech, music generation
- 💻 **Code AI** - Code generation, Copilot, coding assistants
- 👁️ **Vision** - Computer vision, object detection
- 💬 **NLP** - Natural language processing, sentiment analysis
- 🧠 **ML** - Machine learning, deep learning, neural networks

### Result Limits
- **Top 20** - Quick overview
- **Top 30** - Comprehensive list
- **Top 50** - Deep dive

### Sort Options
- 🏆 **Score** - By enhanced algorithm score (default)
- ⭐ **Stars** - By GitHub stars
- 📈 **Growth** - By growth rate
- 🔥 **Freshness** - By recent updates

## 🎨 Features

### Smart Filtering
- Real-time category matching
- Topic-based search
- Keyword detection in name/description

### Visual Indicators
- 🚀 **Boost badges** - Shows Hidden Gem/Rising Star/Trending
- **Rank numbers** - Clear positioning
- **Score display** - 0-10 scale
- **Growth percentage** - Shows momentum

### Interactive UI
- Hover effects on cards
- Click to open GitHub repo
- Responsive design
- Glass morphism effects

## 🔧 Configuration

### Change API URL
Edit the API_URL in each HTML file:
```javascript
const API_URL = 'http://localhost:8000';  // Local
// const API_URL = 'https://your-api.onrender.com';  // Production
```

### Customize Categories
In `discover.html`, modify the `categoryMap` object:
```javascript
const categoryMap = {
    'your-category': ['keyword1', 'keyword2', 'keyword3']
};
```

## 📊 How It Works

1. **Load Tools** - Fetches 100 tools from API
2. **Filter** - Applies category filter
3. **Sort** - Sorts by selected criteria
4. **Limit** - Shows top N results
5. **Display** - Renders cards with all info

## 🎯 Example Usage

### Find Top 20 LLM Tools by Growth
1. Open `discover.html`
2. Click "🤖 LLMs" category
3. Click "📈 Growth" sort
4. Click "Top 20" limit
5. Results update instantly!

### Find Top 30 Image Generation Tools
1. Click "🎨 Image Gen" category
2. Keep "🏆 Score" sort (default)
3. Click "Top 30" limit
4. Browse results!

## 🚀 Deployment

### Deploy to Vercel
```bash
cd frontend
vercel
```

### Deploy to Netlify
1. Drag & drop `frontend` folder to Netlify
2. Update API_URL to your backend URL
3. Done!

## 📱 Mobile Support

All pages are fully responsive:
- Touch-friendly buttons
- Optimized layouts
- Fast loading
- Smooth scrolling

## ✨ Tips

1. **Reset Filters** - Click "Reset All" to start fresh
2. **Boost Badges** - Look for 🚀 to find hidden gems
3. **Growth %** - High growth = emerging tool
4. **Score** - 8.0+ = excellent tool

## 🎓 Understanding the UI

### Card Layout
```
#Rank  Tool Name  🚀 Boost Badge
       full_name
       Description...

⭐ Stars  🔱 Forks  ● Language

[topic] [topic] [topic]     Growth: XX%
```

### Score Meaning
- **9.0-10.0** - Exceptional (top 1%)
- **8.0-8.9** - Excellent (top 5%)
- **7.0-7.9** - Very Good (top 10%)
- **6.0-6.9** - Good (top 25%)
- **< 6.0** - Average

## 🔥 Pro Tips

1. **Discover Hidden Gems** - Sort by Growth + Top 20
2. **Find Established Tools** - Sort by Stars + Top 30
3. **Latest Innovations** - Sort by Freshness + Top 20
4. **Best Overall** - Sort by Score + Top 30 (default)

---

**Status:** ✅ Fully functional
**Backend Required:** Yes (http://localhost:8000)
**Browser Support:** All modern browsers
