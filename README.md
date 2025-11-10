# IMB Generator - Intelligent Mail Barcode Generator

A production-ready Flask web application for generating USPS Intelligent Mail Barcodes (IMB) from mailing lists. This tool validates addresses via API, generates compliant IMB barcodes, and exports enhanced mailing lists with all original data plus IMB tracking codes.

## Features

✅ **File Upload**
- Drag-and-drop interface for CSV and Excel files
- Support for .csv, .xlsx, and .xls formats
- File size up to 50MB
- Preview first 10 rows before processing

✅ **Smart Column Mapping**
- Auto-detects address fields (street, city, state, ZIP)
- Manual column mapping with dropdown selection
- Visual indicators for auto-detected columns

✅ **Address Validation**
- USPS Official API integration (FREE, recommended for mailing companies)
- SmartyStreets API integration (premium, 55+ data points)
- Google Address Validation API integration (budget-friendly, CASS certified)
- Returns ZIP+4, delivery point, carrier route, and DPV status
- All providers are CASS certified
- Batch processing with error handling

✅ **IMB Generation**
- Full USPS 4-state barcode implementation
- Configurable service types (First-Class, Marketing Mail, etc.)
- Auto-incrementing sequence numbers
- CRC error detection
- Generates 31-digit tracking codes and 65-character barcodes

✅ **Export & Reporting**
- Preserves ALL original columns
- Adds 14 new IMB-related columns
- Exports to timestamped CSV files
- Separate error report for failed addresses
- Processing summary with success/failure stats

## Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- API credentials from USPS, SmartyStreets, or Google (choose one)

### 2. Installation

```bash
# Clone or download the repository
cd imb-generator

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy the example environment file and configure your API credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your API credentials:

```env
# Choose your API provider: usps, smartystreets, or google
API_PROVIDER=usps

# USPS Official API (if using USPS - FREE)
USPS_USER_ID=your_usps_user_id_here

# OR SmartyStreets credentials (if using SmartyStreets)
SMARTYSTREETS_AUTH_ID=your_auth_id_here
SMARTYSTREETS_AUTH_TOKEN=your_auth_token_here

# OR Google API key (if using Google)
GOOGLE_MAPS_API_KEY=your_google_api_key_here

# Flask configuration
FLASK_SECRET_KEY=your_secret_key_here
```

**Generate a secure Flask secret key:**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4. Run the Application

```bash
python app.py
```

Open your browser to: **http://localhost:5001**

**Note:** Port 5001 is used to avoid conflict with macOS AirPlay Receiver (which uses port 5000 on macOS 12+)

## Getting API Keys

Choose one of the three address validation providers below. All are CASS certified and support IMB generation.

### Option 1: USPS Official API ⭐ **RECOMMENDED FOR MAILING COMPANIES**

**Best for:** Actual mailing operations (FREE, most authoritative)

1. Visit [USPS Web Tools Registration](https://registration.shippingapis.com/)
2. Click "Register" and fill out the form with your information
3. Accept the Terms of Use (Note: **Must be used for shipping/mailing purposes only**)
4. Check your email for your **User ID**
5. Copy the User ID to your `.env` file as `USPS_USER_ID`

**Pricing:** **100% FREE** (unlimited usage)

**Provides:** ZIP+4, Delivery Point (2-digit), Carrier Route, DPV Confirmation

**Important:** The USPS API license requires it be used exclusively for shipping and mailing purposes. This is perfect for mailing companies generating IMB codes.

---

### Option 2: SmartyStreets

**Best for:** Premium accuracy, no usage restrictions, 55+ data points

1. Visit [SmartyStreets.com](https://www.smartystreets.com/)
2. Sign up for a free account
3. Navigate to "API Keys" in your dashboard
4. Create a new "US Street Address API" key
5. Copy the **Auth ID** and **Auth Token** to your `.env` file

**Pricing:** 250 free lookups/month, then $20-$1,000/month for unlimited

**Provides:** ZIP+4, Delivery Point, Carrier Route, DPV, plus lat/long, time zone, congressional district, and 50+ other data points

**Pros:** Industry-leading accuracy, no usage restrictions, extensive metadata

---

### Option 3: Google Address Validation API

**Best for:** Budget-conscious users with moderate volume

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Address Validation API" for your project
   - Navigate to "APIs & Services" → "Library"
   - Search for "Address Validation API"
   - Click "Enable"
4. Create an API key:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the API key to your `.env` file as `GOOGLE_MAPS_API_KEY`
5. (Optional) Restrict your API key to only Address Validation API for security

**Pricing:** $200 free credit per month (~12,000 addresses), then $17 per 1,000 lookups

**Provides:** CASS certified addresses, ZIP+4, Delivery Point (via USPS data), DPV Confirmation

**Pros:** Generous free tier, CASS certified, backed by Google infrastructure

---

### API Comparison Table

| Feature | USPS Official | SmartyStreets | Google |
|---------|---------------|---------------|---------|
| **Free Tier** | Unlimited FREE | 250/month | 12,000/month |
| **Paid Price** | Always FREE | $20-$1000/mo | $17/1,000 |
| **CASS Certified** | ✅ Yes | ✅ Yes | ✅ Yes |
| **ZIP+4** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Delivery Point** | ✅ Yes (2-digit) | ✅ Yes (2-digit) | ✅ Yes |
| **Carrier Route** | ✅ Yes | ✅ Yes | ✅ Yes |
| **DPV Status** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Extra Data** | Basic | 55+ fields | Standard |
| **Usage Restrictions** | Mailing only | None | None |
| **Best For** | Mailing companies | Maximum accuracy | Budget + volume |

**Recommendation:** Use **USPS Official API** if you're a mailing company (free and most authoritative). Use **SmartyStreets** for maximum accuracy and extra data. Use **Google** for non-mailing applications with good volume needs.

## Getting a USPS Mailer ID

To generate IMB barcodes, you need a **USPS Mailer ID** (6 or 9 digits).

1. Register at the [USPS Business Customer Gateway](https://gateway.usps.com/)
2. Complete the Intelligent Mail verification process
3. Request a Mailer ID (MID) through your account
4. You'll receive a 6-digit or 9-digit Mailer ID

**Note:** The Mailer ID registration process can take several business days. For testing, you can use a sample Mailer ID like `123456` (6-digit), but this won't be valid for actual USPS mailings.

## Input File Format

### Required Columns

Your CSV or Excel file must contain address information. Column names can vary, but should include:

- **Street Address** (e.g., "Address", "Street", "Address1")
- **City** (e.g., "City", "Town")
- **State** (e.g., "State", "ST")
- **ZIP Code** (e.g., "ZIP", "Zipcode", "Postal Code")

### Example CSV Format

```csv
Name,Address,City,State,ZIP,Company,Phone
John Doe,123 Main St,New York,NY,10001,ABC Corp,555-1234
Jane Smith,456 Oak Ave,Los Angeles,CA,90001,XYZ Inc,555-5678
Bob Johnson,789 Pine Rd,Chicago,IL,60601,Demo LLC,555-9012
```

### Important Notes

- All original columns are preserved in the output
- Street addresses should be in standard format (e.g., "123 Main St")
- State should be 2-letter abbreviation (NY, CA, TX, etc.)
- ZIP codes can be 5-digit or 9-digit (ZIP+4)

## Output Columns

The application adds the following columns to your original data:

| Column Name | Description |
|-------------|-------------|
| `validated_address` | USPS-standardized street address |
| `validated_city` | Standardized city name |
| `validated_state` | State abbreviation (2 letters) |
| `validated_zip5` | 5-digit ZIP code |
| `zip_plus4` | 4-digit ZIP extension |
| `delivery_point` | 2-digit delivery point code |
| `routing_code` | 11-digit routing code (ZIP5+ZIP4+DP) |
| `carrier_route` | USPS carrier route (e.g., "C001") |
| `dpv_status` | Delivery Point Validation status |
| `imb_tracking_code` | 31-digit IMB tracking number |
| `imb_barcode` | 65-character 4-state barcode string |
| `sequence_number` | Sequential number for this piece |
| `validation_status` | SUCCESS or ERROR |
| `validation_message` | Success/error message |

## IMB Barcode Structure

The Intelligent Mail Barcode consists of:

```
BarcoDE ID (2) + Service Type (3) + Mailer ID (6/9) + Sequence (9/6) + Routing (11)
= 31 total digits
```

### Example Breakdown

```
Tracking Code: 00040123456000000001902105432001
├─ Barcode ID: 00
├─ Service Type: 040 (First-Class Mail)
├─ Mailer ID: 123456 (6 digits)
├─ Sequence: 000000001 (9 digits, balances to 15 with Mailer ID)
└─ Routing Code: 90210543201 (ZIP 90210, +4 5432, DP 01)
```

### Service Type Identifiers

| Code | Service Type |
|------|--------------|
| 040 | First-Class Mail |
| 240 | USPS Marketing Mail |
| 340 | Periodicals |
| 440 | Bound Printed Matter |
| 540 | Package Services |

## Usage Guide

### Step 1: Upload File

1. Drag and drop your CSV or Excel file into the upload zone
2. Or click "Select File" to browse for your file
3. Wait for the file to upload and preview to appear

### Step 2: Map Columns

1. Review the auto-detected column mappings
2. Adjust mappings if needed using the dropdown menus
3. Ensure all required fields are mapped:
   - Street Address
   - City
   - State
   - ZIP Code

### Step 3: Configure IMB Settings

1. Enter your **USPS Mailer ID** (6 or 9 digits)
2. Select **Service Type** (e.g., First-Class Mail)
3. Set **Starting Sequence Number** (default: 1)
4. Set **Barcode Identifier** (default: 00)
5. Choose **API Provider** (USPS, SmartyStreets, or Google)

### Step 4: Process

1. Click "Process Mailing List"
2. Wait for processing to complete (API validates each address)
3. Review the summary statistics

### Step 5: Download Results

1. Click "Download Results" for the complete file with IMB codes
2. Click "Download Errors" if there are failed addresses
3. Click "Process Another File" to start over

## Troubleshooting

### "HTTP 403 Forbidden" or "Access Denied" on localhost

**Cause:** On macOS 12 (Monterey) and later, Apple uses port 5000 for AirPlay Receiver

**Solution:** This app now uses port 5001 by default to avoid this conflict

If you see this error:
1. Make sure you're accessing **`http://localhost:5001`** (not 5000)
2. Verify the Flask app is running (`python app.py`)
3. Check that port 5001 is free: `lsof -i :5001`

**Alternative:** Disable AirPlay Receiver in macOS (not recommended):
- System Settings → General → AirDrop & Handoff → Toggle off "AirPlay Receiver"

---

### "Address not found or invalid"

**Cause:** The address couldn't be validated by the API

**Solution:**
- Verify the address is a valid US address
- Check for typos in street name, city, or state
- Ensure ZIP code matches the city/state
- Try standardizing abbreviations (St vs Street, Ave vs Avenue)

### "API error: 401 Unauthorized"

**Cause:** Invalid API credentials

**Solution:**
- Verify your API key/credentials in `.env`
- Check that you've selected the correct API provider
- Ensure your API account is active and has available credits

### "File too large"

**Cause:** File exceeds 50MB limit

**Solution:**
- Split your file into smaller chunks
- Remove unnecessary columns before upload
- Or increase `MAX_UPLOAD_SIZE` in `.env` (in bytes)

### "Mailer ID must be 6 or 9 digits"

**Cause:** Invalid Mailer ID format

**Solution:**
- Verify your Mailer ID from USPS
- Ensure it contains only numbers
- Pad with leading zeros if needed (e.g., `000123` for a 6-digit ID)

### Python Dependencies Installation Errors

**On macOS/Linux:**
```bash
# If you get SSL errors
pip install --upgrade certifi

# If you get permission errors
pip install --user -r requirements.txt
```

**On Windows:**
```bash
# If you get encoding errors
pip install -r requirements.txt --no-cache-dir
```

## Project Structure

```
imb-generator/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .env                     # Your configuration (not in git)
├── README.md                # This file
├── utils/
│   ├── address_validator.py # API integration (USPS/SmartyStreets/Google)
│   ├── imb_generator.py     # IMB encoding and generation
│   └── file_processor.py    # CSV/Excel file handling
├── templates/
│   └── index.html           # Single-page application UI
├── static/
│   ├── css/
│   │   └── style.css        # Custom styles
│   └── js/
│       └── app.js           # Client-side logic
└── uploads/                 # Temporary file storage
```

## API Reference

### POST `/api/upload`

Upload a mailing list file.

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "success": true,
  "filename": "mailing_list.csv",
  "preview": {
    "columns": ["Name", "Address", "City", "State", "ZIP"],
    "num_rows": 1000,
    "preview": [...],
    "detected_columns": {
      "street": "Address",
      "city": "City",
      "state": "State",
      "zip": "ZIP"
    }
  }
}
```

### POST `/api/process`

Process uploaded file with IMB generation.

**Request:**
```json
{
  "mapping": {
    "street": "Address",
    "city": "City",
    "state": "State",
    "zip": "ZIP"
  },
  "config": {
    "mailer_id": "123456",
    "service_type": "040",
    "starting_sequence": 1,
    "barcode_id": "00",
    "api_provider": "smartystreets"
  }
}
```

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_records": 1000,
    "successful": 985,
    "failed": 15,
    "success_rate": 98.5,
    "api_calls": 1000
  },
  "results": [...],
  "output_filename": "mailing_list_IMB_20250120_143022.csv"
}
```

### GET `/api/download/output`

Download processed file with IMB codes.

### GET `/api/download/errors`

Download error report (failed addresses only).

### GET `/api/sample`

Download sample CSV file.

## Development

### Running in Development Mode

```bash
export FLASK_ENV=development
python app.py
```

### Running Tests

```bash
# Test IMB generator
python utils/imb_generator.py

# Test address validator (requires API credentials)
python utils/address_validator.py

# Test file processor
python utils/file_processor.py
```

## Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### Using Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app:app"]
```

### Environment Variables for Production

```env
FLASK_ENV=production
FLASK_SECRET_KEY=<strong-random-key>
MAX_UPLOAD_SIZE=52428800
```

## Performance Considerations

- **Processing Speed:** ~50-100 addresses per minute (limited by API rate limits)
- **Large Files:** Files with 10,000+ rows will take 2-3 hours to process
- **Batch Processing:** Consider splitting very large files into smaller chunks
- **API Costs:** Monitor your API usage to avoid unexpected charges

## Security Notes

- Never commit `.env` file to version control
- Use strong, random values for `FLASK_SECRET_KEY`
- Uploaded files are stored temporarily and should be cleaned periodically
- API keys should be kept confidential
- Consider rate limiting in production environments

## License

This project is provided as-is for use by mailing companies and USPS business customers.

## Support

For issues or questions:
1. Check this README and the troubleshooting section
2. Review the code comments in `utils/` directory
3. Verify your API credentials and USPS Mailer ID
4. Check API provider documentation:
   - [USPS Web Tools Docs](https://www.usps.com/business/web-tools-apis/)
   - [SmartyStreets Docs](https://www.smartystreets.com/docs)
   - [Google Address Validation Docs](https://developers.google.com/maps/documentation/address-validation)

## Credits

Built with:
- Flask (Python web framework)
- Bootstrap 5 (UI framework)
- Pandas (Data processing)
- USPS/SmartyStreets/Google APIs (Address validation)

---

**Last Updated:** January 2025

**Version:** 1.0.0
