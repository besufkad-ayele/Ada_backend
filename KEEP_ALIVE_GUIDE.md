# Keep-Alive Solutions for Render Free Tier

Render's free tier spins down services after 15 minutes of inactivity. Here are the best solutions:

## ⭐ Recommended: External Monitoring Services (FREE)

### Option 1: UptimeRobot (Best)
1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Create a new monitor:
   - Monitor Type: HTTP(s)
   - URL: `https://your-app.onrender.com/api/health`
   - Monitoring Interval: 5 minutes (free tier)
3. Done! Your backend will stay alive automatically.

### Option 2: Cron-job.org
1. Sign up at [cron-job.org](https://cron-job.org)
2. Create a new cron job:
   - URL: `https://your-app.onrender.com/api/health`
   - Schedule: Every 14 minutes
3. Enable the job.

### Option 3: BetterUptime
1. Sign up at [betteruptime.com](https://betteruptime.com)
2. Create a heartbeat monitor
3. Set interval to 10 minutes

## 🐍 Option: Python Keep-Alive Script

If you want to run your own keep-alive service:

### Local Machine
```bash
# Set your backend URL
export BACKEND_URL=https://your-app.onrender.com

# Run the script
python keep_alive.py
```

### Deploy on Another Free Service

Deploy `keep_alive.py` on:
- **PythonAnywhere** (free tier)
- **Heroku** (if you have credits)
- **Railway** (free tier)

### GitHub Actions (Free)
Create `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Backend Alive

on:
  schedule:
    - cron: '*/14 * * * *'  # Every 14 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Backend
        run: |
          curl -f https://your-app.onrender.com/api/health || exit 1
```

## 💰 Best Solution: Upgrade Render Plan

If this is a production app, consider:
- **Render Starter Plan** ($7/month): No sleep, better performance
- **Render Standard Plan** ($25/month): Even better resources

## ⚙️ Configuration

Your backend already has a health endpoint at `/api/health` that returns:
```json
{
  "status": "healthy",
  "database": "connected",
  "room_types_configured": 4,
  "resort": "Kuraz Resort & Spa"
}
```

## 📊 Monitoring

All external services provide:
- Uptime statistics
- Response time tracking
- Email/SMS alerts if your backend goes down
- Status pages

## 🎯 Recommendation

**Use UptimeRobot** - it's free, reliable, and provides monitoring + keep-alive in one solution.
