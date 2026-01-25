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

### Step 4: Set Environment Variables (IMPORTANT!)

Environment variables are secret values your app needs to run. Think of them like passwords for your app.

#### Understanding What You'll See:

After deploying, your Railway project has **TWO services**:
1. **Web Service** (your Flask app) - This is where you set variables
2. **PostgreSQL** (your database) - Don't touch this one

#### How to Set Variables:

**A. Navigate to the Right Place:**

1. Look at your Railway dashboard - you'll see **two boxes/cards**:
   ```
   ┌─────────────────────┐    ┌─────────────────────┐
   │  Your-Repo-Name     │    │  PostgreSQL         │
   │  (Web Service)      │    │  (Database)         │
   │  ← Click this one!  │    │  ← NOT this one     │
   └─────────────────────┘    └─────────────────────┘
   ```

2. Click on your **web service** (the one with your repository name, NOT "PostgreSQL")

3. You'll see several tabs at the top:
   - Deployments
   - **Variables** ← Click this tab
   - Settings
   - Metrics
   - Logs

**B. Generate Your SECRET_KEY:**

Before adding variables, you need to generate a secure secret key. Choose **any ONE** of these methods:

#### Method 1: Online Generator (Easiest - No Installation Needed!)

1. Go to: **https://randomkeygen.com/**
2. Scroll to **"Fort Knox Passwords"** section
3. Copy one of the long random strings (looks like: `kJ8v#mP2$wR9@xL4...`)
4. That's your SECRET_KEY!

**Alternative online generators:**
- https://www.grc.com/passwords.htm (scroll to "63 random alpha-numeric characters")
- https://1password.com/password-generator/ (set length to 64, include symbols)

#### Method 2: Browser Console (Quick & Easy)

1. **Open your browser** (Chrome, Firefox, Safari, etc.)
2. Press `F12` or right-click → "Inspect" → Go to **"Console"** tab
3. Paste this code and press Enter:
   ```javascript
   Array.from(crypto.getRandomValues(new Uint8Array(32)), b => b.toString(16).padStart(2, '0')).join('')
   ```
4. Copy the long string that appears (like: `a1b2c3d4e5f6...`)
5. That's your SECRET_KEY!

#### Method 3: Python Command (If You Have Python Installed)

1. Open your **local terminal**
2. Run:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. Copy the output string

#### Method 4: OpenSSL (Mac/Linux Terminal)

1. Open terminal
2. Run:
   ```bash
   openssl rand -hex 32
   ```
3. Copy the output string

#### Method 5: Railway's Built-in Generator (If Available)

Some Railway users report seeing a "Generate" button next to variable values. If you see this:
1. Click **"New Variable"**
2. Enter `SECRET_KEY` as the name
3. Look for a **"Generate"** or "🎲" button
4. Click it to auto-generate a secure value

---

**What You'll Get:**

All methods produce a long random string like this:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

**Copy the entire string** - you'll need it in the next step!

**⚠️ Important:**
- Don't share this key with anyone
- Don't commit it to git
- Use a different key for each project

**C. Add the SECRET_KEY Variable:**

1. In Railway's "Variables" tab, click the **"New Variable"** button (or "+ Variable")

2. You'll see two input fields:

   ```
   ┌─────────────────────────────────────┐
   │ Variable Name                       │
   │ [Type here]                         │
   └─────────────────────────────────────┘

   ┌─────────────────────────────────────┐
   │ Variable Value                      │
   │ [Type here]                         │
   └─────────────────────────────────────┘
   ```

3. Fill them in:
   - **Variable Name**: Type `SECRET_KEY` (exactly like this, all caps)
   - **Variable Value**: Paste the long random string you generated in step B

4. Click **"Add"** button

**D. Add API Keys (Optional - Can Skip for Now):**

You can set these now OR set them later via the Admin panel in your app.

**Option 1: Set them now in Railway**

Repeat the process above for each API key:

1. Click **"New Variable"**
2. Add **GROQ_API_KEY**:
   - Variable Name: `GROQ_API_KEY`
   - Variable Value: `gsk_your_actual_groq_key_here`
   - Click "Add"

3. Click **"New Variable"** again
4. Add **MISTRAL_API_KEY**:
   - Variable Name: `MISTRAL_API_KEY`
   - Variable Value: `your_actual_mistral_key_here`
   - Click "Add"

**Option 2: Set them later via Admin panel**
1. Skip this for now
2. After your app is deployed, login and go to Admin → API Settings
3. Enter your API keys there

**E. Verify Your Variables:**

After adding variables, you should see them listed in the Variables tab:

```
DATABASE_URL          postgresql://postgres:***@***.railway.app... (Auto-set ✓)
SECRET_KEY            ******************************************* (Your value)
GROQ_API_KEY          ******************************************* (Optional)
MISTRAL_API_KEY       ******************************************* (Optional)
```

**Important Notes:**
- ⚠️ `DATABASE_URL` appears automatically - don't add it manually!
- ⚠️ Values are hidden with *** for security
- ✅ Adding/changing variables triggers automatic redeployment
- ✅ You can edit variables anytime by clicking the "•••" menu next to each one

#### Common Questions:

**Q: I don't see DATABASE_URL!**

This is the most common issue. Here's how to fix it:

**Solution 1: Check Both Services Are in Same Project**

1. Look at your Railway dashboard
2. You should see **both** services in the same project view:
   ```
   Project: your-project-name
   ├── your-repo-name (web service)
   └── PostgreSQL (database)
   ```
3. If PostgreSQL is in a different project, delete it and recreate it in the correct project

**Solution 2: Manually Connect the Services**

Railway should auto-connect them, but if it doesn't:

1. Click on your **web service** (your repo name)
2. Go to **"Settings"** tab
3. Scroll down to **"Service Variables"** or **"Connected Services"** section
4. Look for PostgreSQL in the list
5. Click **"Connect"** or **"Add Reference"** next to PostgreSQL
6. Go back to **"Variables"** tab
7. `DATABASE_URL` should now appear!

**Solution 3: Add DATABASE_URL Manually (Last Resort)**

If the above doesn't work, you can manually copy the database URL:

1. Click on your **PostgreSQL service**
2. Go to **"Connect"** tab
3. Copy the **"Postgres Connection URL"** (starts with `postgresql://`)
   - It looks like: `postgresql://postgres:password@containers-us-west-123.railway.app:5432/railway`
4. Go back to your **web service**
5. Go to **"Variables"** tab
6. Click **"New Variable"**
7. Add:
   - Variable Name: `DATABASE_URL`
   - Variable Value: Paste the URL you copied
8. Click **"Add"**

**Solution 4: Recreate Everything (If Still Not Working)**

1. Delete your PostgreSQL service (your data will be lost, but it's empty anyway)
2. Delete your web service deployment
3. Start fresh:
   - First, create PostgreSQL database
   - Then, deploy from GitHub
   - Railway should auto-connect them this time

**How to Verify DATABASE_URL is Working:**

After adding DATABASE_URL (automatically or manually):

1. Go to your **web service** → **"Variables"** tab
2. You should see:
   ```
   DATABASE_URL    postgresql://postgres:***@***.railway.app:5432/railway
   ```
3. The value should start with `postgresql://` (NOT `sqlite://`)
4. Click on it to expand and verify it has all parts:
   - Username: `postgres`
   - Password: (hidden)
   - Host: `containers-us-west-xxx.railway.app`
   - Port: `5432`
   - Database: `railway`

**Still Not Working?**

If you've tried everything above and still don't see DATABASE_URL:

1. **Contact Railway Support:**
   - Click the "?" icon in Railway dashboard
   - Or visit: https://railway.app/help

2. **Check Railway Status:**
   - Visit: https://status.railway.app/
   - Make sure there are no ongoing issues

3. **Try a Different Browser:**
   - Sometimes clearing cache helps
   - Try incognito/private mode

4. **Double-check Project Structure:**
   - Make sure both services show in the **same** project
   - They should be side-by-side in the dashboard, not in separate tabs

**Q: What if I make a typo in the variable name?**
A: Click the "•••" menu next to the variable → Delete → Add it again with correct spelling

**Q: Can I change these later?**
A: Yes! Just click the variable, edit it, and save. Your app will redeploy automatically.

**Q: Where do I get GROQ_API_KEY?**
A: Sign up at https://console.groq.com/ → Create an API key. Or skip it and set it later in your app's Admin panel.

**Q: Do I need both GROQ and MISTRAL keys?**
A: No, you only need ONE of them. Pick whichever AI service you prefer. You can change this later in Admin panel.

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
