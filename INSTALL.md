# IMB Generator - Installation Guide

This guide will walk you through setting up the IMB Generator on your system.

## System Requirements

- **Operating System:** macOS, Linux, or Windows 10/11
- **Python:** Version 3.10 or higher
- **RAM:** Minimum 2GB (4GB recommended for large files)
- **Disk Space:** 500MB for application + space for uploaded files
- **Internet:** Required for address validation API calls

## Step-by-Step Installation

### 1. Install Python

#### macOS

```bash
# Using Homebrew (recommended)
brew install python@3.10

# Verify installation
python3 --version
```

#### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.10
sudo apt install python3.10 python3.10-venv python3-pip

# Verify installation
python3 --version
```

#### Windows

1. Download Python 3.10 from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important:** Check "Add Python to PATH" during installation
4. Verify in Command Prompt:
   ```cmd
   python --version
   ```

### 2. Download the Application

```bash
# If you have the code in a zip file, extract it
unzip imb-generator.zip
cd imb-generator

# Or if using git
git clone <repository-url>
cd imb-generator
```

### 3. Create Virtual Environment

A virtual environment keeps the application's dependencies isolated.

#### macOS/Linux

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your prompt
```

#### Windows

```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your prompt
```

### 4. Install Dependencies

With the virtual environment activated:

```bash
# Install all required packages
pip install -r requirements.txt

# This will install:
# - Flask (web framework)
# - pandas (data processing)
# - openpyxl (Excel file support)
# - requests (API calls)
# - python-dotenv (environment variables)
```

### 5. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit the file with your preferred text editor
# macOS/Linux:
nano .env

# Windows:
notepad .env
```

**Required Configuration:**

```env
# Generate a secret key (run this command first):
# python -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET_KEY=paste_your_generated_key_here

# Choose your API provider
API_PROVIDER=smartystreets

# Add your API credentials (see "Getting API Keys" section)
SMARTYSTREETS_AUTH_ID=your_auth_id
SMARTYSTREETS_AUTH_TOKEN=your_auth_token
```

### 6. Get API Credentials

Choose one of three address validation providers:

#### Option A: USPS Official API ⭐ **RECOMMENDED (FREE)**

1. Go to [USPS Web Tools Registration](https://registration.shippingapis.com/)
2. Click "Register" and fill out the form
3. Accept the Terms of Use
4. Check your email for your **User ID**
5. Update `.env`:
   ```env
   API_PROVIDER=usps
   USPS_USER_ID=your_user_id_here
   ```

**Pricing:** 100% FREE (unlimited)
**Best for:** Mailing companies (must be used for shipping/mailing purposes)

#### Option B: SmartyStreets

1. Go to [smartystreets.com](https://www.smartystreets.com/)
2. Click "Sign Up" (free account available)
3. After signup, go to "API Keys" section
4. Click "Create New Key"
5. Select "US Street Address" API
6. Copy the **Auth ID** and **Auth Token**
7. Update `.env`:
   ```env
   API_PROVIDER=smartystreets
   SMARTYSTREETS_AUTH_ID=your_auth_id
   SMARTYSTREETS_AUTH_TOKEN=your_auth_token
   ```

**Pricing:** 250 free/month, then $20-$1,000/month
**Best for:** Maximum accuracy, 55+ data points

#### Option C: Google Address Validation API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Address Validation API"
4. Create an API key in "Credentials"
5. Update `.env`:
   ```env
   API_PROVIDER=google
   GOOGLE_MAPS_API_KEY=your_api_key_here
   ```

**Pricing:** $200 free/month (~12,000 addresses), then $17/1,000
**Best for:** Budget-conscious users with good free tier

### 7. Generate Flask Secret Key

```bash
# Generate a secure random key
python -c "import secrets; print(secrets.token_hex(32))"

# Copy the output and paste it in .env as FLASK_SECRET_KEY
```

### 8. Test Installation

```bash
# Make sure virtual environment is activated
# You should see (venv) in your prompt

# Run the application
python app.py

# You should see:
# * Running on http://0.0.0.0:5001
```

Open your browser to: **http://localhost:5001**

**Note:** Port 5001 is used to avoid conflict with macOS AirPlay Receiver (port 5000)

You should see the IMB Generator interface!

## Quick Start Script (macOS/Linux)

For easier startup, you can use the provided script:

```bash
# Make it executable
chmod +x run.sh

# Run the application
./run.sh
```

## Verification Checklist

Before processing your first file, verify:

- [ ] Python 3.10+ is installed (`python3 --version`)
- [ ] Virtual environment is created and activated (see `(venv)` in prompt)
- [ ] All dependencies are installed (`pip list` shows flask, pandas, etc.)
- [ ] `.env` file exists with valid API credentials
- [ ] `uploads/` directory exists
- [ ] Application starts without errors
- [ ] Browser shows the interface at http://localhost:5001
- [ ] Sample CSV downloads successfully

## Common Installation Issues

### "pip: command not found"

**Solution:** Install pip
```bash
# macOS/Linux
python3 -m ensurepip --upgrade

# Or use your package manager
sudo apt install python3-pip  # Ubuntu/Debian
brew install python3           # macOS
```

### "Permission denied" errors

**Solution:** Use `--user` flag
```bash
pip install --user -r requirements.txt
```

### "No module named 'flask'"

**Cause:** Dependencies not installed or wrong Python version

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Port 5001 already in use

**Solution:** Kill the process or use a different port
```bash
# Kill existing process on port 5001
lsof -ti:5001 | xargs kill -9  # macOS/Linux

# Or run on a different port
# Edit app.py and change port=5001 to port=8080
```

**Note:** On macOS 12+, port 5000 is used by AirPlay Receiver. This app uses port 5001 by default to avoid this conflict.

### "Address already in use" error

**Cause:** Application is already running

**Solution:**
```bash
# Find and kill the process
ps aux | grep python
kill <process_id>
```

## Updating the Application

If you receive an updated version:

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart the application
python app.py
```

## Uninstallation

To completely remove the application:

```bash
# Deactivate virtual environment (if active)
deactivate

# Remove the application directory
cd ..
rm -rf imb-generator

# That's it! All files are self-contained in the project directory
```

## Getting Help

If you encounter issues not covered here:

1. Check the main [README.md](README.md) file
2. Review error messages carefully
3. Verify your Python version: `python3 --version`
4. Verify your API credentials in `.env`
5. Check API provider documentation:
   - [USPS Web Tools Docs](https://www.usps.com/business/web-tools-apis/)
   - [SmartyStreets Docs](https://www.smartystreets.com/docs)
   - [Google Address Validation Docs](https://developers.google.com/maps/documentation/address-validation)

## Next Steps

Once installed successfully:

1. Read the [README.md](README.md) for usage instructions
2. Download the sample CSV to test the application
3. Get your USPS Mailer ID (see README for instructions)
4. Process your first mailing list!

---

**Questions?** Refer to the main README.md file for detailed usage instructions and troubleshooting.
