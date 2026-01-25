# Troubleshooting Guide - Railway Deployment Issues

## 🔍 How to Check Error Logs in Railway

### Step 1: Access Deployment Logs

1. Go to your Railway dashboard
2. Click on your **web service** (your repository name)
3. Click on the **"Deployments"** tab
4. Click on the **latest deployment** (top of the list)
5. You'll see the **Build Logs** and **Deploy Logs**

### Step 2: Look for Errors

Scroll through the logs looking for:
- ❌ Red text or "ERROR"
- ⚠️ "WARNING" or "FAILED"
- 🔴 Lines with `Traceback` (Python errors)
- Stack traces showing which file/line failed

---

## 🚨 Common Errors and Solutions

### Error 1: "No module named 'psycopg2'"

**Error Message:**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solution:**
Your `requirements.txt` is missing the PostgreSQL driver.

1. Make sure your `requirements.txt` includes:
   ```
   psycopg2-binary==2.9.9
   ```
2. Commit and push to GitHub:
   ```bash
   git add requirements.txt
   git commit -m "Add psycopg2-binary"
   git push
   ```
3. Railway will automatically redeploy

---

### Error 2: "relation 'users' does not exist" or "ProgrammingError"

**Error Message:**
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "users" does not exist
```

**What it means:** Database tables weren't created.

**Solution A: Wait for Auto-Creation**

Your app should auto-create tables on first run. Give it 1-2 minutes and refresh.

**Solution B: Manually Create Tables**

1. In Railway, click your **web service** → **Settings** tab
2. Scroll to **"Service"** section
3. Click **"Open Terminal"** or look for a console/shell option
4. Run this command:
   ```python
   python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Tables created!')"
   ```

**Solution C: Check DATABASE_URL**

1. Web service → Variables tab
2. Verify `DATABASE_URL` exists and starts with `postgresql://`
3. If missing, follow the DATABASE_URL troubleshooting in RAILWAY_SETUP.md

---

### Error 3: "werkzeug.routing.exceptions.BuildError"

**Error Message:**
```
werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'static'
```

**Solution:**

This usually means a template issue. Check your recent changes to template files.

1. Make sure all `url_for()` calls have valid endpoints
2. Check that static files exist in the `static/` folder
3. Verify templates are in the `templates/` folder

---

### Error 4: Can't Login - Invalid Credentials

**Symptoms:**
- Login page loads fine
- Username/password are rejected
- No error in logs

**Solution:**

The admin user might not have been created. Create it manually:

1. Railway web service → Settings → Open Terminal
2. Run:
   ```python
   python << 'EOF'
   from app import app, db, User
   with app.app_context():
       # Check if admin exists
       admin = User.query.filter_by(username='admin').first()
       if not admin:
           admin = User(username='admin', role='admin')
           admin.set_password('admin123')
           db.session.add(admin)
           db.session.commit()
           print('✓ Admin user created!')
       else:
           print('Admin user already exists')
   EOF
   ```

---

### Error 5: "Port Already in Use" or "Address Already in Use"

**Error Message:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**

Railway sets the `PORT` environment variable automatically. Make sure your app uses it:

In `app.py`, add at the bottom:
```python
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
```

But for Railway, you should use gunicorn (already in requirements.txt), so this shouldn't be an issue.

---

### Error 6: "Application failed to respond"

**Symptoms:**
- Build succeeds
- Deployment shows as running
- But app doesn't respond/times out

**Check 1: Verify Gunicorn is Running**

In deployment logs, you should see:
```
Starting gunicorn...
Listening at: http://0.0.0.0:XXXX
```

**Check 2: Add Procfile (if missing)**

Create a file named `Procfile` (no extension) in your project root:
```
web: gunicorn app:app
```

Then commit and push:
```bash
git add Procfile
git commit -m "Add Procfile for Railway"
git push
```

**Check 3: Check if App is Starting**

Look in deploy logs for:
```
Creating database tables...
✓ Database initialized
✓ Created default admin user
```

If you don't see this, the app isn't starting properly.

---

### Error 7: "SECRET_KEY" Related Errors

**Error Message:**
```
RuntimeError: The session is unavailable because no secret key was set.
```

**Solution:**

1. Go to web service → Variables tab
2. Make sure `SECRET_KEY` exists
3. If missing, add it (see RAILWAY_SETUP.md Step 4)
4. Use any of these methods to generate:
   - https://randomkeygen.com/ (easiest)
   - Browser console: `crypto.randomBytes(32).toString('hex')`
   - Python: `python -c "import secrets; print(secrets.token_hex(32))"`

---

### Error 8: "Internal Server Error" (500 Error)

**Symptoms:**
- App loads but shows "Internal Server Error"
- Or blank white page

**Solution:**

1. Check the **Deploy Logs** in Railway (not Build Logs)
2. Look for Python tracebacks showing the actual error
3. Common causes:
   - Missing environment variables
   - Database connection issues
   - Template rendering errors
   - Missing static files

**Enable Debug Mode (Temporarily):**

⚠️ **Only for debugging - disable in production!**

In `app.py`, temporarily add:
```python
app.config['DEBUG'] = True  # Remove this after debugging!
```

Redeploy and check the error page for detailed stack trace.

**Remember to remove debug mode after fixing!**

---

## 🔧 Step-by-Step Debugging Process

If you're stuck, follow this process:

### 1. Check Build Logs
- Railway → Web Service → Deployments → Latest deployment
- Look for errors during `pip install`
- Verify all dependencies installed successfully

### 2. Check Deploy Logs
- Same deployment, scroll down to "Deploy Logs"
- Look for Python errors/tracebacks
- Check if app started successfully

### 3. Check Environment Variables
- Web Service → Variables tab
- Verify these exist:
  - `DATABASE_URL` (auto-set by Railway)
  - `SECRET_KEY` (you set this)
  - `PORT` (auto-set by Railway)

### 4. Check Database Connection
- Click PostgreSQL service → Data tab
- Verify tables exist: users, recipes, settings, etc.
- If no tables, manually create them (see Error 2 above)

### 5. Test Database Connection
- Web service → Settings → Open Terminal
- Run:
  ```python
  python -c "from app import app, db; app.app_context().push(); print(db.engine.url)"
  ```
- Should print: `postgresql://postgres:***@***.railway.app:5432/railway`

### 6. Check Domain is Active
- Web Service → Settings → Domains
- Verify domain is generated and active
- Try accessing it in incognito mode (clears cache)

---

## 📋 Deployment Checklist

Before asking for help, verify:

- [ ] `psycopg2-binary==2.9.9` is in requirements.txt
- [ ] Pushed latest code to GitHub
- [ ] PostgreSQL service exists in same project
- [ ] `DATABASE_URL` appears in web service variables
- [ ] `SECRET_KEY` is set in web service variables
- [ ] Build logs show successful pip install
- [ ] Deploy logs show "Database initialized"
- [ ] Database tables exist (check PostgreSQL → Data tab)
- [ ] Domain is generated and accessible

---

## 🆘 Getting Help

If you're still stuck after trying everything above:

### Share These Details:

1. **Full error message** from logs (copy/paste)
2. **Which step failed** (build or deploy?)
3. **Your environment variables** (names only, not values):
   - DATABASE_URL exists? (yes/no)
   - SECRET_KEY exists? (yes/no)
4. **Screenshot** of the error page or logs

### Where to Get Help:

1. **Railway Discord:** https://discord.gg/railway
2. **Railway Docs:** https://docs.railway.app/
3. **GitHub Issues:** Check if others had similar issues

---

## 🎯 Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Can't login | Create admin user manually (see Error 4) |
| Database tables missing | Run `db.create_all()` (see Error 2) |
| Missing psycopg2 | Add to requirements.txt and push |
| No DATABASE_URL | Follow RAILWAY_SETUP.md troubleshooting |
| App won't start | Check SECRET_KEY is set |
| 500 error | Check deploy logs for Python traceback |
| Build failed | Check build logs for missing dependencies |

---

## 🔍 What To Share With Me

If you need help, please share:

**1. Copy the error from Railway logs:**
```
# In Railway:
# Deployments → Latest → Scroll to the error
# Copy the entire error message including the traceback
```

**2. Verify your setup:**
- [ ] DATABASE_URL exists in variables? (yes/no)
- [ ] SECRET_KEY exists in variables? (yes/no)
- [ ] PostgreSQL service created? (yes/no)
- [ ] Can see database tables? (yes/no)

**3. What's happening:**
- Does the app load at all?
- Do you see a login page?
- What happens when you try to login?
- Any error message on screen?

With this information, I can quickly identify and fix the issue! 🚀
