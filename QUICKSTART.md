# Quick Start Guide - IMB Generator

Get up and running with the IMB Generator in 5 minutes!

## Prerequisites

- Python 3.10+ installed
- API credentials from USPS, SmartyStreets, or Google (choose one)
- 5 minutes of your time

## Installation (3 steps)

### 1. Install Dependencies

```bash
cd imb-generator

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt
```

### 2. Configure API Credentials

```bash
# Copy environment template
cp .env.example .env

# Generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output

# Edit .env file
nano .env  # or use your favorite editor
```

Add your credentials to `.env`:

```env
FLASK_SECRET_KEY=paste_your_generated_key_here
API_PROVIDER=usps

# USPS (FREE - Recommended)
USPS_USER_ID=your_usps_user_id

# OR SmartyStreets
# SMARTYSTREETS_AUTH_ID=your_auth_id
# SMARTYSTREETS_AUTH_TOKEN=your_auth_token

# OR Google
# GOOGLE_MAPS_API_KEY=your_api_key
```

**Don't have API credentials yet? Choose one:**
- **USPS Official**: [registration.shippingapis.com](https://registration.shippingapis.com/) - **FREE** unlimited (recommended for mailing companies)
- **SmartyStreets**: [smartystreets.com](https://www.smartystreets.com) - 250 free/month, premium accuracy
- **Google**: [console.cloud.google.com](https://console.cloud.google.com/) - $200 free/month (~12,000 addresses)

### 3. Run the Application

```bash
python app.py
```

Open your browser to: **http://localhost:5001**

**Note:** Using port 5001 to avoid conflict with macOS AirPlay Receiver

## First Run (Test with Sample Data)

1. **Download Sample CSV**
   - Click "Download Sample CSV" button on the homepage
   - This gives you a properly formatted test file

2. **Upload File**
   - Drag and drop the sample CSV into the upload zone
   - Wait for preview to appear

3. **Verify Column Mapping**
   - Auto-detected columns should be highlighted
   - Verify mappings are correct:
     - Street Address → Address
     - City → City
     - State → State
     - ZIP Code → ZIP

4. **Configure IMB Settings**
   - Mailer ID: Enter `123456` (for testing only)
   - Service Type: Leave as "040 - First-Class Mail"
   - Starting Sequence: Leave as "1"
   - Barcode ID: Leave as "00"
   - API Provider: Select your provider

5. **Process**
   - Click "Process Mailing List"
   - Wait for processing (about 1-2 minutes for 10 addresses)
   - Review results

6. **Download Results**
   - Click "Download Results" to get CSV with IMB codes
   - Open in Excel or any spreadsheet program
   - Look for new columns: `imb_tracking_code`, `imb_barcode`, etc.

## Understanding Your Results

Your output CSV will have these new columns:

| Column | What It Means |
|--------|---------------|
| `validated_address` | USPS-corrected street address |
| `validated_zip5` | 5-digit ZIP code |
| `zip_plus4` | ZIP+4 extension |
| `delivery_point` | 2-digit delivery point code |
| `imb_tracking_code` | 31-digit IMB tracking number |
| `imb_barcode` | 65-character barcode (A/T/D/F format) |
| `validation_status` | SUCCESS or ERROR |

## Production Use

Before using with real mailing data:

1. **Get a Real USPS Mailer ID**
   - Register at [USPS Business Customer Gateway](https://gateway.usps.com/)
   - Apply for Intelligent Mail verification
   - Receive your 6 or 9-digit Mailer ID

2. **Verify API Limits**
   - Check your API provider's monthly/daily limits
   - Estimate costs for your mailing volume
   - Consider upgrading if needed

3. **Test with Small Batch**
   - Start with 10-50 addresses
   - Verify results are accurate
   - Check that barcodes are properly formatted

4. **Process Full List**
   - Upload your complete mailing list
   - Monitor progress
   - Review error report for any failed addresses

## Troubleshooting

### "API error: 401 Unauthorized"
- Check that your API credentials in `.env` are correct
- Verify you selected the right provider (USPS, SmartyStreets, or Google)
- Make sure your API account is active

### "Address not found"
- Verify the address is a valid US address
- Check for typos in street name or ZIP code
- Some rural addresses may not validate

### "File too large"
- Maximum file size is 50MB
- Split large files into smaller chunks
- Remove unnecessary columns before upload

### Application won't start
- Make sure virtual environment is activated: `source venv/bin/activate`
- Verify Python version: `python3 --version` (should be 3.10+)
- Reinstall dependencies: `pip install -r requirements.txt`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review [INSTALL.md](INSTALL.md) for advanced setup options
- Check the API reference section for integration options

## Need Help?

1. Check the troubleshooting sections in README.md
2. Verify your .env configuration
3. Test with the sample CSV first
4. Review error messages carefully

## Tips for Best Results

✅ **DO:**
- Use standardized address formats
- Include ZIP codes when possible
- Test with small batches first
- Keep your API credentials secure

❌ **DON'T:**
- Upload files with sensitive data without reviewing security
- Commit the `.env` file to version control
- Use test Mailer IDs for actual USPS mailings
- Exceed your API rate limits

---

**You're all set!** Start processing mailing lists with USPS-compliant IMB barcodes. 🎉
