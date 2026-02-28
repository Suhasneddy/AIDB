# 🚀 How to Open the Discovery Page

## Method 1: Double-Click (Easiest)

1. Navigate to: `AI-Discovery\frontend\`
2. Double-click: `discover.html`
3. It will open in your default browser

## Method 2: Use Launcher Script

1. Double-click: `open-discovery.bat` (in root folder)
2. It will check backend and open the page

## Method 3: From Browser

1. Open your browser (Chrome/Edge/Firefox)
2. Press `Ctrl + O` (Open File)
3. Navigate to: `AI-Discovery\frontend\discover.html`
4. Click Open

## Method 4: Drag & Drop

1. Open your browser
2. Drag `discover.html` file into browser window
3. Drop it

---

## ⚠️ IMPORTANT: Backend Must Be Running!

Before opening the page, start the backend:

```bash
cd backend
python main.py
```

You should see:
```
🚀 Starting AI Tool Discovery API v2.0...
📍 Server: http://localhost:8000
```

---

## 🔧 If Page Shows Error

### Check Backend Status:
1. Open browser
2. Go to: `http://localhost:8000`
3. Should show: `{"status":"online",...}`

### If Backend Not Running:
```bash
cd AI-Discovery\backend
python main.py
```

### If Still Not Working:
Check browser console (F12) for errors

---

## 📁 File Locations

```
AI-Discovery/
├── backend/
│   └── main.py          ← Start this first
├── frontend/
│   ├── index.html       ← Homepage
│   └── discover.html    ← Discovery page (NEW!)
└── open-discovery.bat   ← Quick launcher
```

---

## ✅ Success Checklist

- [ ] Backend running at localhost:8000
- [ ] Opened discover.html in browser
- [ ] Can see "Discover AI Tools" title
- [ ] Can see category filters
- [ ] Can see tool cards loading
- [ ] Can click filters and see results update

---

## 🎯 Quick Test

1. Open `discover.html`
2. Click "🤖 LLMs" category
3. Click "Top 30" limit
4. Click "📈 Growth" sort
5. Should see 30 LLM tools sorted by growth!

---

## 💡 Pro Tip

Bookmark this in your browser:
`file:///C:/Users/Acer/OneDrive/Documents/6th SEM/AI-Discovery/frontend/discover.html`

(Adjust path to your actual location)
