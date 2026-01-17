# 🚂 Deploy to Railway - Step by Step

Railway is the **best free option** because it includes persistent storage on the free tier.

## ✅ Why Railway?

- ✅ **$5 free credits/month** (enough for your app)
- ✅ **Persistent storage** (data doesn't get deleted)
- ✅ **No sleep mode** (instant response)
- ✅ **Automatic HTTPS**
- ✅ **Super easy setup** (5 minutes)

---

## 🚀 Deployment Steps

### 1. Push Your Code to GitHub

```bash
# Make sure everything is committed and pushed
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

### 2. Sign Up on Railway

1. Go to **[https://railway.app](https://railway.app)**
2. Click **"Login"**
3. Choose **"Login with GitHub"**
4. Authorize Railway to access your repositories

### 3. Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Find and select your **"Test"** repository
4. Click on it to deploy

### 4. Configure Environment Variables

Railway will start deploying automatically. While it deploys:

1. Click on your service (the deployment card)
2. Go to **"Variables"** tab
3. Click **"+ New Variable"**
4. Add these variables:

| Variable Name | Value |
|---------------|-------|
| `MISTRAL_API_KEY` | Your Mistral API key from console.mistral.ai |
| `SECRET_KEY` | Any random string (e.g., `my-super-secret-key-12345`) |
| `PORT` | `8080` |
| `FLASK_DEBUG` | `False` |

5. Click **"Deploy"** if needed

### 5. Generate Public URL

1. Go to **"Settings"** tab
2. Scroll to **"Networking"** section
3. Click **"Generate Domain"**
4. Your app will be live at: `https://your-app-name.up.railway.app`

### 6. Wait for Deployment

- Watch the **"Deployments"** tab
- It should take 2-5 minutes
- Look for **"SUCCESS"** status

### 7. Access Your App

1. Click on the generated domain URL
2. You'll see your Recipe Translator app! 🎉
3. Login with:
   - Username: `admin`
   - Password: `admin123`
4. **IMPORTANT:** Change the admin password immediately!

---

## 🎯 Post-Deployment

### First Steps:
1. ✅ Change admin password (Admin Panel → Users)
2. ✅ Add your Mistral API key if you haven't
3. ✅ Set NYT cookie (Admin Panel → API Settings) if needed
4. ✅ Test translating a recipe

### Your Data:
- ✅ **Users are persistent** (won't be deleted)
- ✅ **Settings are persistent** (saved across restarts)
- ✅ **No data loss on deploy**

---

## 💰 About Free Credits

### How Credits Work:
- You get **$5 free credits every month**
- Your app uses approximately **$0.50 - $2/month**
- **Credits reset monthly** (not cumulative)
- You'll get an email if running low

### If Credits Run Out:
1. Add a credit card (no charge until you approve)
2. Or wait until next month (app pauses until credits reset)
3. Or deploy to another platform

---

## 🔧 Troubleshooting

### App Won't Start?
**Check logs:**
1. Go to your project
2. Click on the service
3. Click **"Deployments"** → View logs
4. Look for error messages

**Common fixes:**
- Verify `MISTRAL_API_KEY` is set correctly
- Check that `gunicorn` is in `requirements.txt` ✅
- Ensure `PORT=8080` is set

### Database/Storage Issues?
Railway automatically provides persistent storage - no configuration needed!

### API Errors?
- Check your Mistral API key is valid
- Go to [console.mistral.ai](https://console.mistral.ai) to verify

---

## 🆚 Railway vs Render

| Feature | Railway | Render |
|---------|---------|--------|
| **Free Storage** | ✅ Yes | ❌ No |
| **Sleep Mode** | ❌ No | ✅ Yes (15min) |
| **Free Tier** | $5 credits | Forever free |
| **Setup** | 5 min | 5 min |
| **Best For** | This app! | Static sites |

---

## 📞 Need Help?

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **Status Page:** https://status.railway.app

---

## 🎉 You're Done!

Your app is now live with:
- ✅ Persistent data storage
- ✅ Fast response times
- ✅ Automatic HTTPS
- ✅ Free hosting (with credits)

Share your URL and enjoy your recipe translator! 🍳
