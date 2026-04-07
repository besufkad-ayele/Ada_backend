# 🔄 Keep-Alive Setup Guide for Your Render Backend

Your Render free tier backend sleeps after 15 minutes of inactivity. Here's how to keep it alive:

---

## ⭐ RECOMMENDED: GitHub Actions (100% Free & Automatic)

This is the BEST option - runs automatically on GitHub's servers, no local machine needed!

### Setup Steps:

1. **Update the workflow file** (already created at `.github/workflows/keep-alive.yml`)
   - Replace `kuraz-ai-backend.onrender.com` with YOUR actual Render URL
   - Find your URL in Render dashboard

2. **Commit and push to GitHub:**
   ```bash
   git add .github/workflows/keep-alive.yml
   git commit -m "Add keep-alive GitHub Action"
   git push origin main
   ```

3. **Enable GitHub Actions** (if not already enabled):
   - Go to your GitHub repository
   - Click "Actions" tab
   - If prompted, click "I understand my workflows, go ahead and enable them"

4. **Verify it's working:**
   - Go to "Actions" tab in your GitHub repo
   - You'll see "Keep Render Backend Alive" workflow
   - It runs automatically every 14 minutes
   - You can also click "Run workflow" to test manually

### How it works:
- GitHub Actions pings your `/api/health` endpoint every 14 minutes
- Completely free (GitHub provides 2,000 minutes/month for free)
- Runs 24/7 automatically
- No local machine needed

---

## 🖥️ Option 2: Run on Your Windows Computer

If you want to run the keep-alive script locally:

### Quick Start:

1. **Update the URL in `run_keep_alive.bat`:**
   - Open `run_keep_alive.bat`
   - Change `https://kuraz-ai-backend.onrender.com` to YOUR Render URL

2. **Double-click `run_keep_alive.bat`**
   - A terminal window will open
   - The script will ping your backend every 14 minutes
   - Keep the window open

3. **To stop:** Press `Ctrl+C` in the terminal window

### Run in Background:

If you want it to run silently in the background:

```bash
# In your terminal
python keep_alive.py
```

Or create a scheduled task in Windows Task Scheduler to run at startup.

---

## 🌐 Option 3: External Service (Also Free)

Use a free monitoring service - no code needed!

### UptimeRobot (Recommended):

1. Sign up at https://uptimerobot.com (free)
2. Click "Add New Monitor"
3. Configure:
   - Monitor Type: HTTP(s)
   - Friendly Name: Kuraz AI Backend
   - URL: `https://your-app.onrender.com/api/health`
   - Monitoring Interval: 5 minutes
4. Click "Create Monitor"

Done! Your backend will stay alive + you get uptime monitoring.

---

## 📊 Comparison

| Method | Cost | Setup | Maintenance | Monitoring |
|--------|------|-------|-------------|------------|
| **GitHub Actions** | Free | 5 min | None | Basic |
| **Local Script** | Free | 2 min | Keep running | None |
| **UptimeRobot** | Free | 3 min | None | Full |

---

## 🎯 My Recommendation

**Use GitHub Actions** because:
- ✅ Completely free
- ✅ Runs automatically 24/7
- ✅ No local machine needed
- ✅ Easy to set up
- ✅ Works even when your computer is off

**Bonus:** Add UptimeRobot too for monitoring and alerts!

---

## 🔧 Configuration

### Update Your Render URL

In all files, replace `kuraz-ai-backend.onrender.com` with your actual URL:

1. `.github/workflows/keep-alive.yml` (line 15)
2. `run_keep_alive.bat` (line 8)
3. `keep_alive.py` (use environment variable)

Find your URL in Render dashboard → Your service → URL at the top

---

## ✅ Verify It's Working

### Check GitHub Actions:
1. Go to your GitHub repo
2. Click "Actions" tab
3. See workflow runs and their status

### Check Your Backend:
```bash
curl https://your-app.onrender.com/api/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "room_types_configured": 4,
  "resort": "Tana Lakeside Resort"
}
```

---

## 🐛 Troubleshooting

### GitHub Actions not running?
- Check "Actions" tab is enabled in repo settings
- Verify the cron syntax in `.github/workflows/keep-alive.yml`
- Check workflow run logs for errors

### Local script not working?
- Verify Python is installed: `python --version`
- Install requests: `pip install requests`
- Check your BACKEND_URL is correct

### Backend still sleeping?
- Verify the keep-alive is actually running
- Check Render logs to see if requests are coming in
- Ensure interval is less than 15 minutes

---

## 💡 Pro Tip

For production, consider upgrading to Render's paid tier ($7/month):
- No sleep/cold starts
- Better performance
- More resources
- Worth it for a real application

---

**Setup complete! Your backend will stay alive 24/7.** 🎉
