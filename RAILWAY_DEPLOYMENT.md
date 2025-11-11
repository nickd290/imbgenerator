# Railway Deployment Guide - IMB Generator

## Prerequisites

- Railway account (https://railway.app)
- Git repository connected to Railway
- Environment variables ready

---

## Step 1: Push Code to Git

```bash
cd /Users/nicholasdeblasio/imb-generator
git add .
git commit -m "Add company management and job history features

- Extended Customer model with default IMB settings
- Added Job record creation during processing
- Built job history view with download functionality
- Implemented auto-load settings when customer selected
- Updated Procfile for automatic migrations on deploy
- Configured for Railway Volume persistent storage

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git push
```

---

## Step 2: Set Up Railway PostgreSQL Database

1. **Go to your Railway project dashboard**
2. **Click "New" → "Database" → "Add PostgreSQL"**
3. **Wait for database to provision** (1-2 minutes)
4. **Verify DATABASE_URL is automatically set** in your project variables

The `DATABASE_URL` will automatically be available to your app.

---

## Step 3: Configure Railway Volume (for file persistence)

### Option A: Using Railway Volumes (Recommended)

1. **In Railway dashboard, go to your service**
2. **Click "Variables" tab**
3. **Add volume:**
   - Name: `data`
   - Mount Path: `/data`
   - Size: Start with **1GB** ($0.25/month)

4. **Update environment variable:**
   - `UPLOAD_FOLDER=/app/data`

### Option B: Skip Volume (temporary, session-based downloads only)

If you don't need file persistence between deployments:
- Leave `UPLOAD_FOLDER` unset (defaults to `uploads/`)
- Files will be lost on container restart
- Downloads only work during active session

---

## Step 4: Set Environment Variables

Go to Railway project → **Variables** tab and add:

### Required Variables

```bash
# Database (automatically set by Railway PostgreSQL addon)
DATABASE_URL=postgresql://...  # Auto-populated

# Flask Configuration
FLASK_SECRET_KEY=<generate-with-command-below>
FLASK_ENV=production

# File Storage (if using Railway Volume)
UPLOAD_FOLDER=/app/data

# API Provider Credentials (at least one required)
API_PROVIDER=usps
USPS_USER_ID=your_usps_user_id_here

# Optional: Additional API providers
# SMARTYSTREETS_AUTH_ID=your_auth_id
# SMARTYSTREETS_AUTH_TOKEN=your_token
# GOOGLE_MAPS_API_KEY=your_api_key
```

### Generate Flask Secret Key

Run locally:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste as `FLASK_SECRET_KEY` in Railway.

---

## Step 5: Deploy

1. **Railway will automatically deploy** when you push to your connected branch
2. **Watch deployment logs** in Railway dashboard
3. **Look for successful migration:**
   ```
   INFO  [alembic.runtime.migration] Running upgrade e9e6903c6b7e -> a53d3d7ebb5e, Add company settings to customers
   ```
4. **Verify app is running:** Check deployment URL

---

## Step 6: Verify Deployment

### Test Database Connection

1. Go to your Railway app URL
2. Click "Manage Customers"
3. Try creating a test customer with default settings:
   - Name: "Test Company"
   - Mailer ID: "123456"
   - Service Type: "040"

### Test Job Creation

1. Select the test customer
2. Upload a small CSV file
3. Process it
4. Check "History" button - you should see the completed job

### Check Railway Logs

```bash
railway logs
```

Look for:
- ✅ Migration completed successfully
- ✅ Database tables created
- ✅ No error messages

---

## Troubleshooting

### Issue: "Failed to fetch customers"

**Cause:** Database not initialized or migrations didn't run

**Fix:**
1. Check Railway logs for migration errors
2. Manually run migrations:
   ```bash
   railway run flask db upgrade
   ```

### Issue: "Customer ID required" when processing

**Cause:** Frontend not sending customer_id

**Fix:**
1. Check browser console for errors
2. Verify you selected a customer before uploading
3. Clear browser cache and reload

### Issue: Files not persisting after restart

**Cause:** No Railway Volume configured

**Fix:**
1. Add Railway Volume (see Step 3)
2. Set `UPLOAD_FOLDER=/app/data`
3. Redeploy

### Issue: "API error: 401 Unauthorized"

**Cause:** Missing or invalid API credentials

**Fix:**
1. Verify `USPS_USER_ID` (or other API keys) is set in Railway variables
2. Test API credentials locally first
3. Check API provider dashboard for account status

---

## Database Migrations (Manual)

If you need to run migrations manually:

```bash
# Connect to Railway project
railway link

# Run migrations
railway run flask db upgrade

# Check migration status
railway run flask db current

# Rollback if needed
railway run flask db downgrade
```

---

## Cost Estimates

**Monthly costs for typical usage:**

- **Hobby Plan (Free):**
  - PostgreSQL: Included
  - App hosting: $5/month (500 hours)
  - Volume (1GB): $0.25/month
  - **Total: ~$5.25/month**

- **Pro Plan:**
  - PostgreSQL: $5/month
  - App hosting: Included
  - Volume (1GB): $0.25/month
  - **Total: ~$5.25/month**

---

## Monitoring

### Check Application Health

```bash
# View logs
railway logs

# Check resource usage
railway status

# View environment variables
railway variables
```

### Database Queries

Connect to database:
```bash
railway connect postgres
```

Check data:
```sql
-- Count customers
SELECT COUNT(*) FROM customers;

-- Count jobs
SELECT COUNT(*) FROM jobs;

-- Recent jobs
SELECT filename, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;
```

---

## Backup Strategy

### Database Backups

Railway automatically backs up PostgreSQL databases.

**Manual backup:**
```bash
railway run pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Volume Backups

**Manual volume backup:**
```bash
railway run tar -czf /tmp/data_backup.tar.gz /app/data
railway run cat /tmp/data_backup.tar.gz > data_backup_$(date +%Y%m%d).tar.gz
```

---

## Scaling

### Increase Volume Size

1. Go to Railway Volume settings
2. Adjust size (billed at $0.25/GB/month)
3. Restart service

### Increase Database Size

Railway PostgreSQL automatically scales. Monitor usage in dashboard.

---

## Support

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **IMB Generator Issues:** Check application logs first

---

## Post-Deployment Checklist

- [ ] Database migrations ran successfully
- [ ] Environment variables all set correctly
- [ ] Can create/edit customers
- [ ] Can save customer default settings
- [ ] Settings auto-load when customer selected
- [ ] Can process mailing lists
- [ ] Jobs are saved to database
- [ ] Job history displays correctly
- [ ] Can download files from job history
- [ ] Files persist after container restart (if using Volume)

---

**Last Updated:** November 2025

**Version:** 2.0.0 (Company Management + Job History)
