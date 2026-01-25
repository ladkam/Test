# Database Setup and Persistence

## Issue: Recipes Disappearing After Login/Restart

**Problem:** The database was stored in the `instance/` folder, which is gitignored. Every time you pull updates or redeploy, the instance folder (including your recipes) gets wiped.

**Solution:** The database is now stored in the `data/` folder with an absolute path.

## Database Location

- **Database file:** `data/recipes.db`
- **Folder structure:** The `data/` folder is tracked in git (with `.gitkeep`)
- **Database files:** `data/*.db` are gitignored for security/size reasons

## How Data Persists Now

1. The `data/` folder structure IS tracked in git
2. The `data/.gitkeep` file ensures the folder exists
3. Database files (`*.db`) in the data folder are gitignored
4. The app creates `data/recipes.db` using an absolute path
5. This database persists across deployments and restarts

## Configuration

The database path can be customized using the `DATABASE_URL` environment variable:

```bash
# In .env file (copy from .env.example)
DATABASE_URL=sqlite:///data/recipes.db

# Or for PostgreSQL in production:
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## Backup Your Data

To backup your recipes:

```bash
# Create a backup
cp data/recipes.db data/recipes.backup-$(date +%Y%m%d).db

# Or export to a different location
cp data/recipes.db ~/my-backups/recipes-$(date +%Y%m%d).db
```

## Migration from Old Location

If you had recipes in the old `instance/recipes.db` location, they were automatically copied to `data/recipes.db` during the first run after this update.

## Production Deployment

For production, consider using a managed database service (PostgreSQL, MySQL) instead of SQLite for better reliability and concurrent access.
