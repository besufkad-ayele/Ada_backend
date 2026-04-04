# 🚀 Render Deployment Guide for Kuraz AI

Complete step-by-step guide to deploy your FastAPI application to Render.

---

## 📋 Prerequisites

1. **GitHub Account** - Your code must be in a GitHub repository
2. **Render Account** - Sign up at https://render.com (free tier available)
3. **Gemini API Key** - Get from https://makersuite.google.com/app/apikey

---

## 🔧 Step 1: Prepare Your Repository

### 1.1 Initialize Git (if not already done)

```bash
git init
git add .
git commit -m "Initial commit - Kuraz AI backend"
```

### 1.2 Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `kuraz-ai-backend`)
3. Don't initialize with README (you already have files)

### 1.3 Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/kuraz-ai-backend.git
git branch -M main
git push -u origin main
```

---

## 🌐 Step 2: Create Render Web Service

### 2.1 Sign Up / Log In to Render

1. Go to https://render.com
2. Sign up or log in (can use GitHub account)

### 2.2 Create New Web Service

1. Click **"New +"** button in dashboard
2. Select **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your repository: `kuraz-ai-backend`

### 2.3 Configure Web Service

Fill in the following settings:

- **Name**: `kuraz-ai-backend` (or your preferred name)
- **Region**: Choose closest to your users (e.g., Frankfurt, Singapore)
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: `Free` (or paid for better performance)

---

## 🗄️ Step 3: Set Up PostgreSQL Database

### 3.1 Create PostgreSQL Database

1. In Render dashboard, click **"New +"**
2. Select **"PostgreSQL"**
3. Configure:
   - **Name**: `kuraz-ai-db`
   - **Database**: `kuraz_ai`
   - **User**: `kuraz_admin` (auto-generated)
   - **Region**: Same as your web service
   - **Instance Type**: `Free`

4. Click **"Create Database"**

### 3.2 Get Database Connection String

1. Once created, go to your database dashboard
2. Find **"Internal Database URL"** (starts with `postgresql://`)
3. Copy this URL - you'll need it in the next step

---

## 🔐 Step 4: Configure Environment Variables

### 4.1 Add Environment Variables to Web Service

1. Go to your web service dashboard
2. Click **"Environment"** tab
3. Add the following environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | `postgresql://user:pass@host/db` | Paste from Step 3.2 |
| `GEMINI_API_KEY` | `your_gemini_api_key` | Get from Google AI Studio |
| `RESORT_NAME` | `Tana Lakeside Resort` | Your resort name |
| `RESORT_TOTAL_ROOMS` | `120` | Total room count |
| `PYTHON_VERSION` | `3.11.0` | Python version |

4. Click **"Save Changes"**

---

## 🚀 Step 5: Deploy

### 5.1 Trigger Deployment

Render will automatically deploy when you:
- Push to your GitHub repository
- Or click **"Manual Deploy"** → **"Deploy latest commit"**

### 5.2 Monitor Deployment

1. Go to **"Logs"** tab to watch deployment progress
2. Wait for: `✅ Build successful` and `Application startup complete`
3. Deployment typically takes 3-5 minutes

---

## 🧪 Step 6: Initialize Database

### 6.1 Seed the Database

Once deployed, initialize your database with data:

1. Find your service URL (e.g., `https://kuraz-ai-backend.onrender.com`)
2. Call the seed endpoint:

```bash
curl -X POST https://your-app-name.onrender.com/api/seed
```

Or visit in browser:
```
https://your-app-name.onrender.com/api/seed
```

---

## ✅ Step 7: Test Your Deployment

### 7.1 Test Health Endpoint

```bash
curl https://your-app-name.onrender.com/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "room_types_configured": 4,
  "resort": "Tana Lakeside Resort"
}
```

### 7.2 Access API Documentation

Visit these URLs in your browser:
- **Swagger UI**: `https://your-app-name.onrender.com/docs`
- **ReDoc**: `https://your-app-name.onrender.com/redoc`

### 7.3 Test Key Endpoints

```bash
# Get room types
curl https://your-app-name.onrender.com/api/room-types

# Get dashboard KPIs
curl https://your-app-name.onrender.com/api/dashboard/kpis

# Get optimal pricing
curl -X POST https://your-app-name.onrender.com/api/pricing/optimal-price \
  -H "Content-Type: application/json" \
  -d '{
    "room_type": "deluxe",
    "check_in_date": "2026-05-01",
    "check_out_date": "2026-05-05"
  }'
```

---

## 🔄 Step 8: Continuous Deployment

### 8.1 Auto-Deploy on Git Push

Render automatically deploys when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Update pricing algorithm"
git push origin main
```

Render will detect the push and redeploy automatically.

### 8.2 Manual Deploy

In Render dashboard:
1. Go to your web service
2. Click **"Manual Deploy"**
3. Select **"Deploy latest commit"**

---

## 🐛 Troubleshooting

### Issue: Build Fails

**Check:**
- Logs tab for specific error messages
- `requirements.txt` has all dependencies
- Python version matches `runtime.txt`

**Solution:**
```bash
# Test locally first
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Issue: Database Connection Error

**Check:**
- `DATABASE_URL` environment variable is set correctly
- Database is in the same region as web service
- Internal Database URL is used (not External)

**Solution:**
- Copy Internal Database URL from PostgreSQL dashboard
- Update `DATABASE_URL` in Environment tab

### Issue: Application Crashes on Startup

**Check:**
- Logs for Python errors
- All environment variables are set
- Database is running

**Solution:**
```bash
# Check logs in Render dashboard
# Look for Python tracebacks
# Verify all required env vars are present
```

### Issue: Free Tier Sleeps After Inactivity

**Note:** Free tier services sleep after 15 minutes of inactivity

**Solutions:**
- Upgrade to paid tier ($7/month)
- Use a service like UptimeRobot to ping your app every 10 minutes
- Accept the cold start delay (first request takes 30-60 seconds)

---

## 💰 Cost Estimate

### Free Tier
- **Web Service**: Free (750 hours/month)
- **PostgreSQL**: Free (90 days, then $7/month)
- **Total**: $0 for first 90 days, then $7/month

### Paid Tier (Recommended for Production)
- **Web Service**: $7/month (Starter)
- **PostgreSQL**: $7/month (Starter)
- **Total**: $14/month

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use environment variables** - For all secrets
3. **Restrict CORS** - Update `allow_origins` in `app/main.py`
4. **Enable HTTPS** - Render provides free SSL certificates
5. **Use strong database passwords** - Auto-generated by Render

---

## 📊 Monitoring

### View Logs
1. Go to web service dashboard
2. Click **"Logs"** tab
3. Real-time logs appear here

### View Metrics
1. Click **"Metrics"** tab
2. See CPU, Memory, Request count

### Set Up Alerts
1. Go to **"Settings"**
2. Add notification email
3. Get alerts for crashes/errors

---

## 🎉 Success!

Your Kuraz AI backend is now live on Render!

**Your API URL**: `https://your-app-name.onrender.com`

**Next Steps:**
1. Update your frontend to use the new API URL
2. Test all endpoints thoroughly
3. Monitor logs for any issues
4. Set up custom domain (optional)

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL on Render](https://render.com/docs/databases)
- [Environment Variables](https://render.com/docs/environment-variables)

---

## 🆘 Need Help?

- **Render Support**: https://render.com/docs/support
- **FastAPI Discord**: https://discord.gg/fastapi
- **GitHub Issues**: Create an issue in your repository

---

**Deployed with ❤️ for Ethiopia Hospitality Hackathon 2026**
