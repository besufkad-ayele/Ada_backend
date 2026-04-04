# ✅ Render Deployment Checklist

Quick reference checklist for deploying Kuraz AI to Render.

---

## Before Deployment

- [ ] All code is committed to Git
- [ ] `.gitignore` excludes `.env`, `*.db`, `__pycache__/`
- [ ] `requirements.txt` includes `psycopg2-binary`
- [ ] `runtime.txt` specifies Python version
- [ ] Code pushed to GitHub repository

---

## Render Setup

- [ ] Render account created
- [ ] GitHub account connected to Render
- [ ] PostgreSQL database created on Render
- [ ] Database connection string copied

---

## Web Service Configuration

- [ ] New Web Service created
- [ ] Repository selected
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Instance type selected (Free or Starter)

---

## Environment Variables Set

- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `GEMINI_API_KEY` - Your Gemini API key
- [ ] `RESORT_NAME` - Your resort name
- [ ] `RESORT_TOTAL_ROOMS` - Total room count
- [ ] `PYTHON_VERSION` - 3.11.0

---

## Post-Deployment

- [ ] Deployment completed successfully
- [ ] Database seeded: `POST /api/seed`
- [ ] Health check passes: `GET /api/health`
- [ ] API docs accessible: `/docs`
- [ ] Test key endpoints working

---

## Testing Endpoints

```bash
# Replace YOUR_APP_NAME with your actual Render service name

# Health check
curl https://YOUR_APP_NAME.onrender.com/api/health

# Seed database
curl -X POST https://YOUR_APP_NAME.onrender.com/api/seed

# Get room types
curl https://YOUR_APP_NAME.onrender.com/api/room-types

# API documentation
# Visit: https://YOUR_APP_NAME.onrender.com/docs
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Build fails | Check Logs tab, verify requirements.txt |
| Database error | Verify DATABASE_URL is Internal URL |
| App crashes | Check all environment variables are set |
| Slow first request | Free tier sleeps - upgrade or use ping service |

---

## Quick Commands

```bash
# Push updates
git add .
git commit -m "Your message"
git push origin main

# Local testing
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

**Your Service URL**: `https://YOUR_APP_NAME.onrender.com`
