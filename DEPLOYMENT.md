# Deployment Guide - NYT Recipe Translator

This guide covers the **easiest and cheapest** ways to deploy your recipe translator app.

---

## 🏆 Option 1: Render (Recommended - FREE)

**Best for:** Easy deployment, free tier, persistent storage
**Cost:** Free forever
**Setup time:** 5-10 minutes

### Steps:

1. **Push your code to GitHub** (if not already done)

2. **Go to [Render.com](https://render.com)** and sign up with your GitHub account

3. **Create a New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the `recipe-translator` repository

4. **Configure the service:**
   - **Name:** `recipe-translator` (or any name you like)
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`

5. **Add Environment Variables:**
   Click "Advanced" → "Add Environment Variable":
   - `MISTRAL_API_KEY` = `your-mistral-api-key`
   - `SECRET_KEY` = Click "Generate" to auto-generate
   - `FLASK_DEBUG` = `False`

6. **Click "Create Web Service"**

7. **Wait 5-10 minutes** for deployment to complete

8. **Your app will be live at:** `https://your-app-name.onrender.com`

### Important Notes:
- ✅ Free tier includes 750 hours/month (enough for 24/7 uptime)
- ✅ Automatic HTTPS
- ✅ Persistent disk for storing settings/users (enable in settings if needed)
- ⚠️ App sleeps after 15 minutes of inactivity (wakes up in ~30 seconds on first request)

---

## 🚀 Option 2: Railway (FREE with Credits)

**Best for:** Easy deployment, good free credits
**Cost:** Free $5 credits/month (usually enough for small apps)
**Setup time:** 5 minutes

### Steps:

1. **Go to [Railway.app](https://railway.app)** and sign up with GitHub

2. **Click "New Project" → "Deploy from GitHub repo"**

3. **Select your repository**

4. **Add Environment Variables:**
   - `MISTRAL_API_KEY` = `your-mistral-api-key`
   - `SECRET_KEY` = (generate a random string)
   - `PORT` = `8080`

5. **Railway auto-detects Python and deploys**

6. **Generate a domain:**
   - Go to Settings → Generate Domain
   - Your app will be live at: `https://your-app.up.railway.app`

### Important Notes:
- ✅ Very fast deployment
- ✅ Automatic HTTPS
- ✅ Doesn't sleep (unlike Render)
- ⚠️ Free credits may run out if high traffic

---

## 💰 Option 3: PythonAnywhere (FREE - Limited)

**Best for:** Python-specific hosting, simple setup
**Cost:** Free tier available
**Setup time:** 10-15 minutes

### Steps:

1. **Go to [PythonAnywhere.com](https://www.pythonanywhere.com)** and create a free account

2. **Upload your code:**
   - Go to "Files" → Upload files or clone from GitHub
   - Or use: `git clone https://github.com/yourusername/your-repo.git`

3. **Create a Web App:**
   - Go to "Web" → "Add a new web app"
   - Choose "Flask"
   - Python version: 3.10

4. **Configure WSGI file:**
   - Edit the WSGI configuration file
   - Point it to your `app.py`

5. **Install dependencies:**
   - Open a Bash console
   - `cd` to your project directory
   - `pip install -r requirements.txt`

6. **Set environment variables:**
   - In Web tab, scroll to "Environment variables"
   - Add `MISTRAL_API_KEY`, `SECRET_KEY`, etc.

7. **Reload the web app**

### Important Notes:
- ✅ 100% free tier available
- ✅ No sleep mode
- ⚠️ Custom domain not available on free tier
- ⚠️ Limited to 512MB storage and 100 seconds CPU/day on free tier

---

## 🌐 Option 4: Fly.io (FREE Tier)

**Best for:** Global deployment, Docker-based
**Cost:** Free tier available
**Setup time:** 10-15 minutes

### Steps:

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login:**
   ```bash
   fly auth login
   ```

3. **Launch your app:**
   ```bash
   fly launch
   ```
   - Follow the prompts
   - Choose a unique app name
   - Select region closest to you
   - Don't deploy yet

4. **Set environment variables:**
   ```bash
   fly secrets set MISTRAL_API_KEY=your-key
   fly secrets set SECRET_KEY=your-secret
   ```

5. **Deploy:**
   ```bash
   fly deploy
   ```

### Important Notes:
- ✅ Global CDN
- ✅ No sleep mode
- ✅ Great for production
- ⚠️ Requires Dockerfile (Fly can auto-generate)

---

## 📝 Preparation Checklist

Before deploying to any platform:

- [ ] **Get your Mistral API key** from [console.mistral.ai](https://console.mistral.ai)
- [ ] **Push code to GitHub** (most platforms deploy from GitHub)
- [ ] **Create a strong SECRET_KEY** (or use auto-generate)
- [ ] **Test locally first:** `python app.py`
- [ ] **Check requirements.txt** is up to date

---

## 🎯 Quick Comparison

| Platform | Cost | Sleep? | Custom Domain | Setup Difficulty |
|----------|------|--------|---------------|------------------|
| **Render** | Free | After 15min | ✅ Free | ⭐ Easy |
| **Railway** | $5 credits | No | ✅ Free | ⭐ Easy |
| **PythonAnywhere** | Free | No | ❌ Paid only | ⭐⭐ Medium |
| **Fly.io** | Free | No | ✅ Free | ⭐⭐⭐ Advanced |

---

## 🔐 Security Tips

1. **Never commit .env file** - Already in `.gitignore` ✅
2. **Use strong SECRET_KEY** in production
3. **Change default admin password** after first login
4. **Enable HTTPS** (automatic on all platforms above)
5. **Keep dependencies updated:** `pip list --outdated`

---

## 🆘 Troubleshooting

### App won't start:
- Check logs in platform dashboard
- Verify all environment variables are set
- Ensure `gunicorn` is in requirements.txt

### Database errors:
- Make sure the `data/` directory is persistent
- Check file permissions
- Render: Enable persistent disk in settings

### API errors:
- Verify `MISTRAL_API_KEY` is correct
- Check API quota at console.mistral.ai

---

## 📞 Need Help?

- **Render Docs:** https://render.com/docs
- **Railway Docs:** https://docs.railway.app
- **Flask Deployment:** https://flask.palletsprojects.com/en/latest/deploying/

---

**Recommended:** Start with **Render** - it's the easiest and has the best free tier for this type of app! 🎉
