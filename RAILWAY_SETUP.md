# Railway Deployment Guide - Recipe Manager

Complete step-by-step guide to deploy your Recipe Manager app on Railway with PostgreSQL database.

## 🚂 Why Railway?

- ✅ **Free tier includes PostgreSQL** (500MB storage, 500 hours compute)
- ✅ **Automatic deployments** on every git push
- ✅ **Environment variables** managed in dashboard
- ✅ **DATABASE_URL** automatically set and connected
- ✅ **Zero configuration** - just works!

---

## 📋 Prerequisites

1. GitHub account with your code pushed
2. Railway account (free) - sign up at [railway.app](https://railway.app)

---

## 🚀 Step-by-Step Setup

### Step 1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Click "Login" and sign in with your GitHub account
3. Authorize Railway to access your repositories

### Step 2: Create a New Project

1. Click **"New Project"** button on Railway dashboard
2. Select **"Deploy from GitHub repo"**
3. Choose your repository from the list
   - If you don't see it, click "Configure GitHub App" to grant access
4. Railway will detect it's a Flask app automatically

### Step 3: Add PostgreSQL Database

**This is the key step for database persistence!**

1. In your project dashboard, click **"+ New"** button
2. Select **"Database"**
3. Choose **"Add PostgreSQL"**
4. Railway will provision a PostgreSQL database instantly

**That's it!** Railway automatically:
- Creates the database
- Sets the `DATABASE_URL` environment variable
- Connects your app to the database

### Step 4: Set Environment Variables

Your app needs these environment variables:

1. Click on your **web service** (not the database)
2. Go to the **"Variables"** tab
3. Click **"+ New Variable"** and add:

```
SECRET_KEY
```
Value: Generate with this command locally:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Optional but recommended** (or set via Admin panel later):
```
GROQ_API_KEY = your-groq-key-here
MISTRAL_API_KEY = your-mistral-key-here
```

4. Click **"Add"** for each variable

### Step 5: Deploy!

Railway automatically deploys when you:
- Push to your GitHub repository
- Add/change environment variables
- Click "Deploy" in the dashboard

**First deployment:**
1. Railway builds your app (installs requirements.txt)
2. Runs your Flask app with gunicorn
3. Your app automatically creates all database tables on first run
4. Creates default admin user (username: `admin`, password: `admin123`)

### Step 6: Access Your App

1. In Railway dashboard, click on your web service
2. Go to **"Settings"** tab
3. Under **"Domains"**, click **"Generate Domain"**
4. Railway gives you a URL like: `your-app-name.up.railway.app`
5. Click the URL to open your app!

### Step 7: Login and Change Admin Password

1. Go to your app URL
2. Login with:
   - Username: `admin`
   - Password: `admin123`
3. **IMMEDIATELY** change the password!
   - Go to Admin → Users → Change Password

---

## 🔧 Verify Database Connection

### Check if DATABASE_URL is Set

1. Click on your web service in Railway
2. Go to **"Variables"** tab
3. You should see `DATABASE_URL` automatically set
   - It looks like: `postgresql://postgres:password@host.railway.app:5432/railway`
   - This was automatically added when you created the PostgreSQL service

### Check Database Tables Were Created

1. Click on your **PostgreSQL service** (not the web service)
2. Go to **"Data"** tab
3. You should see tables:
   - `users`
   - `recipes`
   - `recipe_translation`
   - `settings`
   - `weekly_plan`
   - `plan_recipe`

If you see these tables, your database is working! ✅

---

## 📊 View Database Data

### Option 1: Railway Dashboard

1. Click on **PostgreSQL service**
2. Go to **"Data"** tab
3. Select a table from dropdown
4. Browse your data directly in Railway

### Option 2: External Database Client

1. Click on **PostgreSQL service**
2. Go to **"Connect"** tab
3. Copy connection details:
   - **Public URL**: `postgresql://postgres:password@...`
   - Or individual fields (host, port, user, password, database)
4. Use in your favorite client:
   - pgAdmin
   - DBeaver
   - TablePlus
   - psql command line

---

## 🔄 Automatic Deployments

Every time you push to GitHub:
1. Railway detects the push
2. Rebuilds your app
3. Deploys the new version
4. **Database persists** - no data loss!

Watch deployments:
- Click on your web service
- Go to **"Deployments"** tab
- See real-time logs

---

## 💾 Database Backups

### Manual Backup

1. Click on **PostgreSQL service**
2. Go to **"Settings"** tab
3. Scroll to **"Danger Zone"**
4. Click **"Backup Database"**
5. Download backup file

### Restore from Backup

1. Click on PostgreSQL service
2. Go to **"Settings"** tab
3. Under **"Restore"**, upload your backup file

**Note:** Automatic backups require Pro plan ($5/month)

---

## 🐛 Troubleshooting

### App Won't Start

**Check logs:**
1. Click on web service
2. Go to **"Deployments"** tab
3. Click on latest deployment
4. View build and runtime logs

**Common issues:**
- Missing `requirements.txt` - Make sure it's committed to git
- Missing `Procfile` - Not needed, Railway auto-detects Flask
- Port issues - Railway sets `PORT` automatically, your app should use it

### Database Connection Failed

**Check DATABASE_URL:**
1. Web service → Variables tab
2. Verify `DATABASE_URL` exists and starts with `postgresql://`
3. If missing, make sure PostgreSQL service is in same project

**Reconnect services:**
1. Click web service → Settings
2. Under "Service Variables"
3. Click "Connect" next to PostgreSQL service

### Can't Access App URL

**Generate domain:**
1. Web service → Settings
2. Scroll to "Domains"
3. Click "Generate Domain"
4. Wait 30 seconds for DNS propagation

### Tables Not Created

**Check logs for errors:**
```bash
# Look for migration errors in deployment logs
```

**Manually create tables:**
1. Railway console: Web service → Settings → "Open Terminal"
2. Run:
```python
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

---

## 🔐 Environment Variables Reference

| Variable | Required | Where to Set | Description |
|----------|----------|--------------|-------------|
| `DATABASE_URL` | ✅ Auto | Railway sets automatically | PostgreSQL connection string |
| `SECRET_KEY` | ✅ Manual | Variables tab | Flask session encryption key |
| `GROQ_API_KEY` | ❌ Optional | Variables or Admin panel | Groq AI translation API |
| `MISTRAL_API_KEY` | ❌ Optional | Variables or Admin panel | Mistral AI translation API |
| `PORT` | ✅ Auto | Railway sets automatically | Port for web service |

---

## 💰 Railway Free Tier Limits

- **Compute**: 500 hours/month (~21 days if running 24/7)
- **PostgreSQL**: 500MB storage, 500 hours
- **Bandwidth**: 100GB/month
- **Deployments**: Unlimited
- **Custom domains**: 1 free

**Pro tips for free tier:**
- App sleeps after inactivity (saves hours)
- First request wakes it up (~30 seconds)
- Database never sleeps
- Upgrade to Hobby plan ($5/mo) for:
  - 500 hours → Unlimited
  - Custom domains
  - Automatic backups

---

## ✅ Deployment Checklist

- [ ] Pushed code to GitHub
- [ ] Created Railway account
- [ ] Created new project from GitHub repo
- [ ] Added PostgreSQL database
- [ ] Set `SECRET_KEY` environment variable
- [ ] Generated domain
- [ ] Verified app is running
- [ ] Logged in with admin/admin123
- [ ] Changed admin password
- [ ] Set API keys (via Variables or Admin panel)
- [ ] Verified database tables exist
- [ ] Tested creating a recipe
- [ ] Confirmed data persists after redeployment

---

## 🎉 You're Done!

Your app is now running with:
- ✅ Persistent PostgreSQL database
- ✅ Automatic deployments on git push
- ✅ Free HTTPS domain
- ✅ Environment variable management
- ✅ Database backups available

**Next steps:**
1. Import your recipes (if migrating from local)
2. Share your app URL with others
3. Consider upgrading to Hobby plan for unlimited hours

**Your Railway URL**: `https://your-app-name.up.railway.app`

Happy cooking! 🍳
