# Deployment Guide - Recipe Manager

This guide explains how to persist your data (recipes, settings, secrets) both locally and in production.

## 🔍 Current Setup Overview

**Everything is already persisting to a database!** Here's what's stored:

### Stored in Database (✅ Persists)
- **Recipes** - All recipe data including ingredients, instructions, nutrition
- **Translations** - Spanish and French translations for all recipes
- **Users** - User accounts and authentication
- **Settings** - API keys (Groq, Mistral), AI provider settings, NYT cookie
- **Weekly Plans** - Your meal planning data

### Database Location
- **Development**: `data/recipes.db` (SQLite file in your project)
- **Production**: Managed PostgreSQL database (recommended)

### Why Database Files Don't Commit to Git
Your `.gitignore` correctly excludes `*.db` files because:
1. ✅ Database files are binary and don't work well with git
2. ✅ Each developer should have their own local database
3. ✅ Production uses a different database (PostgreSQL)
4. ✅ Prevents accidentally committing sensitive user data

---

## 🏠 Local Development Setup

### 1. Create Your .env File

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values
nano .env  # or use your preferred editor
```

### 2. Set Your Environment Variables

**Minimum required:**
```env
SECRET_KEY=your-secure-random-key-here
```

**Optional (can also use Admin panel):**
```env
GROQ_API_KEY=your-groq-api-key
MISTRAL_API_KEY=your-mistral-api-key
```

### 3. Generate a Secure Secret Key

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as your `SECRET_KEY` in `.env`

### 4. Your Data Persists Locally

Your database file at `data/recipes.db` persists all your data. As long as you don't delete this file, your data is safe.

**Backing up locally:**
```bash
# Create a backup
cp data/recipes.db data/recipes.db.backup-$(date +%Y%m%d)

# Or backup with timestamp
tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz data/
```

---

## 🚀 Production Deployment

### Why Use PostgreSQL in Production?

SQLite is great for development, but production needs PostgreSQL because:
- ✅ Better concurrency (multiple users at once)
- ✅ Managed backups and disaster recovery
- ✅ Better performance at scale
- ✅ Hosted platforms provide it for free

### Option 1: Railway (Recommended - Easiest)

1. **Sign up** at [railway.app](https://railway.app)

2. **Create a new project** from GitHub repo

3. **Add PostgreSQL database:**
   - Click "+ New" → "Database" → "PostgreSQL"
   - Railway automatically sets `DATABASE_URL` environment variable

4. **Set environment variables:**
   ```
   SECRET_KEY=<generate-secure-key>
   GROQ_API_KEY=<your-key> (optional, can use admin panel)
   MISTRAL_API_KEY=<your-key> (optional, can use admin panel)
   ```

5. **Deploy!**
   - Railway automatically deploys on every git push
   - Your app will migrate the database schema automatically

### Option 2: Render

1. **Sign up** at [render.com](https://render.com)

2. **Create new Web Service** from GitHub

3. **Create PostgreSQL database:**
   - Click "New +" → "PostgreSQL"
   - Copy the "Internal Database URL"

4. **Set environment variables in your Web Service:**
   ```
   DATABASE_URL=<your-postgres-url>
   SECRET_KEY=<generate-secure-key>
   ```

5. **Deploy** - Render auto-deploys on git push

### Option 3: Heroku

1. **Install Heroku CLI** and login

2. **Create app:**
   ```bash
   heroku create your-app-name
   ```

3. **Add PostgreSQL:**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

4. **Set environment variables:**
   ```bash
   heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   heroku config:set GROQ_API_KEY=your-key
   ```

5. **Deploy:**
   ```bash
   git push heroku main
   ```

---

## 🔐 Managing Secrets in Production

You have **two options** for API keys:

### Option A: Environment Variables (Recommended for Production)

Set on your hosting platform:
```bash
# Railway/Render - Set in dashboard
GROQ_API_KEY=gsk_xxxxx
MISTRAL_API_KEY=xxxxx

# Heroku - Set via CLI
heroku config:set GROQ_API_KEY=gsk_xxxxx
```

**Pros:**
- ✅ More secure (not in database)
- ✅ Easier to rotate keys
- ✅ Better for CI/CD pipelines

### Option B: Admin Panel (Easier for Non-Technical Users)

After deployment:
1. Go to `/admin` in your app
2. Click "API Settings" tab
3. Enter your API keys
4. Click "Save"

**Pros:**
- ✅ No need to access hosting dashboard
- ✅ Can change without redeploying
- ✅ Stored encrypted in database

**Note:** Environment variables take precedence over database values.

---

## 📊 Database Migration Between Environments

### Export Data from SQLite (Development)

```bash
# Dump recipes to JSON
python -c "
from app import app, db, Recipe
with app.app_context():
    recipes = Recipe.query.all()
    import json
    with open('recipes_export.json', 'w') as f:
        json.dump([r.to_dict() for r in recipes], f)
"
```

### Import Data to PostgreSQL (Production)

After deploying with PostgreSQL:

```bash
# Run on production (Railway/Render console or Heroku run)
python -c "
from app import app, db, Recipe
import json
with app.app_context():
    with open('recipes_export.json', 'r') as f:
        data = json.load(f)
    for recipe_data in data:
        # Import logic here
        pass
"
```

**Or use the admin panel:**
1. Export recipes from local as JSON
2. Import via admin panel in production

---

## 🔄 Automatic Backups (Production)

### Railway
- Automatic daily backups (paid plans)
- Manual backups via dashboard

### Render
- Continuous data protection (paid plans)
- Point-in-time recovery

### Heroku
```bash
# Create manual backup
heroku pg:backups:capture

# Schedule automatic daily backups
heroku pg:backups:schedule DATABASE_URL --at '02:00 America/Los_Angeles'

# Download backup
heroku pg:backups:download
```

---

## ✅ Checklist for Production Deployment

- [ ] Created `.env` file locally (from `.env.example`)
- [ ] Generated secure `SECRET_KEY`
- [ ] Set up PostgreSQL database on hosting platform
- [ ] Set `DATABASE_URL` environment variable
- [ ] Set `SECRET_KEY` environment variable
- [ ] Set API keys (via env vars OR admin panel)
- [ ] Pushed code to git repository
- [ ] Connected hosting platform to GitHub repo
- [ ] Verified database tables created automatically
- [ ] Created admin user (happens automatically on first run)
- [ ] Tested login with default credentials (admin/admin123)
- [ ] Changed admin password immediately
- [ ] Set up automatic backups (if available)

---

## 🆘 Troubleshooting

### "No module named 'psycopg2'"

Add to `requirements.txt`:
```
psycopg2-binary==2.9.9
```

### Database tables not created

The app auto-creates tables on first run. Check logs:
```bash
# Railway - View in dashboard
# Render - View in dashboard
# Heroku
heroku logs --tail
```

### "Database is locked" error

This happens with SQLite in production (multiple users). Solution: **Use PostgreSQL instead.**

### Lost database connection

Check your `DATABASE_URL`:
```bash
# Heroku
heroku config:get DATABASE_URL

# Railway/Render - Check dashboard
```

### API keys not working

Priority order:
1. Environment variables (highest)
2. Database (Settings table)
3. Fallback to None

Check both locations in Admin panel.

---

## 📝 Summary

**Development:**
- ✅ Data persists in `data/recipes.db`
- ✅ API keys in `.env` OR admin panel
- ✅ Backup by copying `data/` folder

**Production:**
- ✅ Use managed PostgreSQL database
- ✅ Set `DATABASE_URL` environment variable
- ✅ Set secrets as environment variables
- ✅ Enable automatic backups
- ✅ Never use SQLite in production

**Your data is safe as long as:**
- 🔒 You have database backups
- 🔒 Your hosting platform is reliable
- 🔒 You use PostgreSQL in production
