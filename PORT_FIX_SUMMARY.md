# HTTP 403 Error - FIXED ✅

## What Was Wrong

You were getting an **HTTP 403 Forbidden** error when trying to access `localhost:5000` because:

1. **macOS AirPlay Receiver** was using port 5000 (on macOS 12+ it's enabled by default)
2. The **Flask app wasn't running** at all
3. **No .env file existed** (needed for configuration)
4. **Python packages weren't installed**

When you visited `localhost:5000`, you were actually connecting to **macOS Control Center's AirPlay service**, which denied access with a 403 error.

---

## What Was Fixed

### ✅ 1. Port Changed (5000 → 5001)
- Updated `app.py` to use port 5001
- Avoids conflict with macOS AirPlay Receiver
- Added explanatory comment in code

### ✅ 2. Created .env File
- Generated from `.env.example` template  
- Auto-generated secure Flask secret key
- Ready for API credentials (you'll need to add these later)

### ✅ 3. Installed Dependencies
- Flask 3.0.0
- pandas 2.1.4
- openpyxl 3.1.2
- requests 2.31.0
- python-dotenv 1.0.0
- Werkzeug 3.0.1

### ✅ 4. Started Flask Application
- Running on port 5001
- Health check verified: ✅ Working
- Process ID: 26505

### ✅ 5. Updated Documentation
- README.md - All port references changed to 5001
- QUICKSTART.md - Updated quick start guide
- INSTALL.md - Updated installation guide
- Added troubleshooting section for macOS port conflict

---

## ✨ Access Your Application

### **Open your browser to:**
```
http://localhost:5001
```

**NOT port 5000** - that's still occupied by macOS AirPlay

---

## Next Steps

### 1. Test the Application
Visit `http://localhost:5001` - you should see the IMB Generator interface

### 2. Add API Credentials
Before processing files, edit `.env` and add credentials for one of these providers:

**Option A: USPS Official (FREE)**
```bash
# Register at: https://registration.shippingapis.com/
USPS_USER_ID=your_actual_user_id
```

**Option B: SmartyStreets**
```bash
SMARTYSTREETS_AUTH_ID=your_auth_id
SMARTYSTREETS_AUTH_TOKEN=your_auth_token
```

**Option C: Google**
```bash
GOOGLE_MAPS_API_KEY=your_google_api_key
```

### 3. Try the Sample
- Download the sample CSV from the app
- Test the upload and preview features
- Configure your Mailer ID and process the sample

---

## Verification

✅ **Flask is running:** `curl http://localhost:5001/health`
```json
{
  "status": "healthy",
  "timestamp": "2025-10-20T17:58:24.024313"
}
```

✅ **Port 5001 is listening:**
```
Python  26505  nicholasdeblasio    TCP *:commplex-link (LISTEN)
```

---

## Files Modified

1. ✅ `.env` - Created with auto-generated secret key
2. ✅ `app.py` - Changed port 5000 → 5001
3. ✅ `README.md` - Updated all port references
4. ✅ `QUICKSTART.md` - Updated quick start
5. ✅ `INSTALL.md` - Updated installation guide

---

## Troubleshooting

### If you still see errors:

**"Connection refused"**
- The Flask app stopped. Restart with: `python3 app.py`

**"Port already in use"**
- Kill the process: `lsof -ti:5001 | xargs kill -9`
- Then restart: `python3 app.py`

**"Module not found"**
- Reinstall dependencies: `pip3 install -r requirements.txt`

---

## Why Port 5001?

Apple uses port 5000 for AirPlay Receiver on:
- macOS 12 (Monterey)
- macOS 13 (Ventura)  
- macOS 14 (Sonoma)
- macOS 15 (Sequoia) ← **You're on this version**

Port 5001 avoids this conflict while staying close to the standard development port.

---

## Success! 🎉

Your IMB Generator is now running at:
**http://localhost:5001**

All documentation has been updated to reflect the new port.
