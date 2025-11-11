"""
IMB Generator Flask Application
Main application file with routes and processing logic
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import traceback

from utils.file_processor import FileProcessor
from utils.address_validator import AddressValidator
from utils.multi_api_validator import MultiAPIValidator
from utils.imb_generator import IMBGenerator, build_routing_code
from models import db, Customer, Job
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_SIZE', 52428800))  # 50MB default

# File storage configuration
# For Railway: Set UPLOAD_FOLDER=/app/data (mount Railway Volume at /data)
# For local development: Uses ./uploads
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database configuration
# Fix PostgreSQL URL dialect for Railway (postgres:// → postgresql://)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///imb_generator.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and migrations
db.init_app(app)
migrate = Migrate(app, db)

# Initialize utilities
file_processor = FileProcessor(upload_folder=app.config['UPLOAD_FOLDER'])


def get_address_validator(provider=None, enable_multi_api=None):
    """
    Initialize address validator based on configuration.

    Returns either a single-provider AddressValidator or a multi-provider
    MultiAPIValidator with automatic fallback.

    Args:
        provider: API provider name (overrides env config)
        enable_multi_api: Enable multi-API fallback (overrides env config)

    Returns:
        AddressValidator or MultiAPIValidator instance
    """
    # Check if multi-API fallback is enabled
    if enable_multi_api is None:
        enable_multi_api = os.getenv('ENABLE_MULTI_API_FALLBACK', 'false').lower() == 'true'

    if enable_multi_api:
        # Multi-API mode with automatic fallback
        primary = os.getenv('PRIMARY_API_PROVIDER', 'smartystreets')
        fallback = os.getenv('FALLBACK_API_PROVIDER', 'google')

        app.logger.info(f"Initializing multi-API validator: {primary} (primary) + {fallback} (fallback)")

        # Prepare API credentials
        credentials = {
            'user_id': os.getenv('USPS_USER_ID'),
            'auth_id': os.getenv('SMARTYSTREETS_AUTH_ID'),
            'auth_token': os.getenv('SMARTYSTREETS_AUTH_TOKEN'),
            'api_key': os.getenv('GOOGLE_MAPS_API_KEY')
        }

        return MultiAPIValidator(
            primary_provider=primary,
            fallback_provider=fallback,
            enable_fallback=True,
            **credentials
        )
    else:
        # Single-provider mode (legacy)
        if provider is None:
            provider = os.getenv('API_PROVIDER', 'usps')

        app.logger.info(f"Initializing single-provider validator: {provider}")

        return AddressValidator(provider=provider)


@app.route('/')
def index():
    """Render main application page."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload and return preview data.

    Returns:
        JSON with file preview and detected columns
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file_processor.allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload CSV or Excel file.'}), 400

        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Store filepath in session
        session['uploaded_file'] = filepath
        session['original_filename'] = filename

        # Load and preview file
        df = file_processor.load_file(filepath)

        # NaN handling now done at load time in file_processor.load_file()
        preview_data = file_processor.preview_data(df, num_rows=10)

        # Return flattened structure that JavaScript expects
        return jsonify({
            'success': True,
            'filename': filename,
            'columns': preview_data['columns'],
            'row_count': preview_data['num_rows'],
            'column_count': preview_data['num_columns'],
            'preview': preview_data['preview'],
            'detected_mapping': preview_data['detected_columns']
        })

    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@app.route('/api/validate-mapping', methods=['POST'])
def validate_mapping():
    """
    Validate column mapping against uploaded file.

    Expected JSON:
        {
            "mapping": {
                "street": "Address",
                "city": "City",
                "state": "State",
                "zip": "ZIP"
            }
        }

    Returns:
        JSON with validation result
    """
    try:
        data = request.get_json()
        mapping = data.get('mapping', {})

        if 'uploaded_file' not in session:
            return jsonify({'error': 'No file uploaded'}), 400

        # Load file
        df = file_processor.load_file(session['uploaded_file'])

        # Validate mapping
        is_valid, errors = file_processor.validate_mapping(df, mapping)

        return jsonify({
            'valid': is_valid,
            'errors': errors
        })

    except Exception as e:
        app.logger.error(f"Mapping validation error: {str(e)}")
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500


@app.route('/api/process', methods=['POST'])
def process_file():
    """
    Process uploaded file with IMB generation.

    Expected JSON:
        {
            "mapping": {...},
            "config": {
                "mailer_id": "123456",
                "barcode_id": "00",
                "service_type": "040",
                "starting_sequence": 1,
                "api_provider": "usps"
            }
        }

    Returns:
        JSON with processing results
    """
    try:
        data = request.get_json()
        mapping = data.get('mapping', {})
        config = data.get('config', {})

        if 'uploaded_file' not in session:
            return jsonify({'error': 'No file uploaded'}), 400

        # Validate configuration
        required_config = ['mailer_id', 'service_type', 'api_provider', 'customer_id']
        for field in required_config:
            if field not in config:
                return jsonify({'error': f'Missing configuration: {field}'}), 400

        # Verify customer exists
        customer = Customer.query.get(config['customer_id'])
        if not customer:
            return jsonify({'error': 'Invalid customer ID'}), 400

        # Create Job record
        job = Job(
            customer_id=config['customer_id'],
            filename=session.get('original_filename', 'unknown.csv'),
            mailer_id=config.get('mailer_id'),
            sequence_start=int(config.get('starting_sequence', 1)),
            service_type=config.get('service_type', '040'),
            barcode_id=config.get('barcode_id', '00'),
            status='processing',
            started_at=datetime.utcnow()
        )
        db.session.add(job)
        db.session.commit()

        app.logger.info(f"Created Job {job.id} for customer {customer.name}")

        # Load file
        df = file_processor.load_file(session['uploaded_file'])

        # Prepare DataFrame
        df_prepared = file_processor.prepare_for_processing(df, mapping)

        # Initialize address validator (single-provider or multi-API with fallback)
        api_provider = config.get('api_provider', 'usps')
        validator = get_address_validator(provider=api_provider)

        # Initialize IMB generator
        imb_gen = IMBGenerator(
            barcode_id=config.get('barcode_id', '00'),
            service_type=config.get('service_type', '040'),
            mailer_id=config.get('mailer_id')
        )

        # Process each row
        results = []
        sequence_num = int(config.get('starting_sequence', 1))

        for idx, row in df_prepared.iterrows():
            try:
                # Log the address being validated
                app.logger.info(f"Processing row {idx + 1}: {row['_street']}, {row['_city']}, {row['_state']} {row['_zip']}")

                # Validate address
                validation_result = validator.validate_address(
                    street=row['_street'],
                    city=row['_city'],
                    state=row['_state'],
                    zipcode=row['_zip']
                )

                app.logger.info(f"Validation result for row {idx + 1}: {validation_result['status']}")

                # Generate IMB if validation successful
                if validation_result['status'] == 'SUCCESS':
                    routing_code = validation_result['routing_code']

                    imb_result = imb_gen.generate_barcode(
                        mailer_id=config.get('mailer_id'),
                        sequence_num=sequence_num,
                        routing_code=routing_code
                    )

                    if imb_result['valid']:
                        results.append({
                            **validation_result,
                            'imb_tracking_code': imb_result['tracking_code'],
                            'imb_barcode': imb_result['barcode'],
                            'sequence_number': sequence_num,
                            'validation_status': 'SUCCESS'
                        })
                    else:
                        results.append({
                            **validation_result,
                            'imb_tracking_code': '',
                            'imb_barcode': '',
                            'sequence_number': sequence_num,
                            'validation_status': 'ERROR',
                            'validation_message': f"IMB generation failed: {', '.join(imb_result['errors'])}"
                        })
                else:
                    results.append({
                        **validation_result,
                        'imb_tracking_code': '',
                        'imb_barcode': '',
                        'sequence_number': sequence_num,
                        'validation_status': 'ERROR'
                    })

                sequence_num += 1

            except Exception as e:
                app.logger.error(f"Error processing row {idx}: {str(e)}")
                results.append({
                    'validated_address': row['_street'],
                    'validated_city': row['_city'],
                    'validated_state': row['_state'],
                    'validated_zip5': row['_zip'][:5] if row['_zip'] else '',
                    'zip_plus4': '',
                    'delivery_point': '',
                    'routing_code': '',
                    'carrier_route': '',
                    'dpv_status': 'Error',
                    'imb_tracking_code': '',
                    'imb_barcode': '',
                    'sequence_number': sequence_num,
                    'validation_status': 'ERROR',
                    'validation_message': f'Processing error: {str(e)}'
                })
                sequence_num += 1

        # Add results to DataFrame
        df_with_imb = file_processor.add_imb_columns(df, results)

        # Export to CSV
        output_path = file_processor.export_to_csv(
            df_with_imb,
            session['original_filename']
        )

        # Export errors if any
        error_path = file_processor.export_errors(
            df_with_imb,
            session['original_filename']
        )

        # Store output path in session
        session['output_file'] = output_path
        session['error_file'] = error_path

        # Generate summary
        summary = file_processor.get_processing_summary(df_with_imb)

        # Update Job record with results
        job.total_records = summary['total_records']
        job.successful_records = summary['successful']
        job.failed_records = summary['failed']
        job.output_file_path = output_path
        job.error_file_path = error_path
        job.status = 'complete'
        job.completed_at = datetime.utcnow()
        db.session.commit()

        app.logger.info(f"Job {job.id} completed: {summary['successful']}/{summary['total_records']} successful")

        # Return results preview (first 50 rows) - comprehensive NaN cleaning for JSON serialization
        results_df = df_with_imb.head(50)
        # Fill NaN with empty string and handle inf values
        results_df = results_df.fillna('')
        results_df = results_df.replace([float('inf'), float('-inf')], '')
        results_preview = results_df.to_dict('records')

        return jsonify({
            'success': True,
            'summary': summary,
            'results': results_preview,
            'output_filename': os.path.basename(output_path),
            'error_filename': os.path.basename(error_path) if error_path else None,
            'job_id': job.id
        })

    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}\n{traceback.format_exc()}")

        # Update Job status if job was created
        if 'job' in locals():
            try:
                job.status = 'failed'
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.session.commit()
            except Exception as db_error:
                app.logger.error(f"Failed to update job status: {str(db_error)}")
                db.session.rollback()

        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@app.route('/api/download/<file_type>')
def download_file(file_type):
    """
    Download processed file.

    Args:
        file_type: 'output' or 'errors'

    Returns:
        File download
    """
    try:
        if file_type == 'output':
            if 'output_file' not in session:
                return jsonify({'error': 'No output file available'}), 404

            filepath = session['output_file']
        elif file_type == 'errors':
            if 'error_file' not in session or session['error_file'] is None:
                return jsonify({'error': 'No error file available'}), 404

            filepath = session['error_file']
        else:
            return jsonify({'error': 'Invalid file type'}), 400

        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath)
        )

    except Exception as e:
        app.logger.error(f"Download error: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@app.route('/api/sample')
def download_sample():
    """Download sample CSV file."""
    try:
        # Create sample data
        sample_data = {
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Address': ['123 Main St', '456 Oak Ave', '789 Pine Rd'],
            'City': ['New York', 'Los Angeles', 'Chicago'],
            'State': ['NY', 'CA', 'IL'],
            'ZIP': ['10001', '90001', '60601'],
            'Company': ['ABC Corp', 'XYZ Inc', 'Demo LLC'],
            'Phone': ['555-1234', '555-5678', '555-9012']
        }

        df = pd.DataFrame(sample_data)
        sample_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sample_mailing_list.csv')
        df.to_csv(sample_path, index=False)

        return send_file(
            sample_path,
            as_attachment=True,
            download_name='sample_mailing_list.csv'
        )

    except Exception as e:
        app.logger.error(f"Sample download error: {str(e)}")
        return jsonify({'error': f'Sample download failed: {str(e)}'}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# ========================================
# Customer Management API Endpoints
# ========================================

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get all customers."""
    try:
        customers = Customer.query.order_by(Customer.name).all()
        return jsonify({
            'customers': [customer.to_dict() for customer in customers]
        })
    except Exception as e:
        app.logger.error(f"Error fetching customers: {str(e)}")
        return jsonify({'error': 'Failed to fetch customers'}), 500


@app.route('/api/customers', methods=['POST'])
def create_customer():
    """Create a new customer."""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Customer name is required'}), 400

        # Create new customer
        customer = Customer(
            name=data['name'],
            company_name=data.get('company_name'),
            email=data.get('email'),
            default_mailer_id=data.get('default_mailer_id'),
            default_service_type=data.get('default_service_type', '040'),
            default_barcode_id=data.get('default_barcode_id', '00'),
            default_sequence_start=data.get('default_sequence_start', 1),
            api_provider=data.get('api_provider', 'usps')
        )

        db.session.add(customer)
        db.session.commit()

        return jsonify({
            'message': 'Customer created successfully',
            'customer': customer.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating customer: {str(e)}")
        return jsonify({'error': 'Failed to create customer'}), 500


@app.route('/api/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """Get a specific customer."""
    try:
        customer = Customer.query.get_or_404(customer_id)
        return jsonify({'customer': customer.to_dict()})
    except Exception as e:
        app.logger.error(f"Error fetching customer: {str(e)}")
        return jsonify({'error': 'Customer not found'}), 404


@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """Update a customer."""
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = request.get_json()

        # Update fields
        if 'name' in data:
            customer.name = data['name']
        if 'company_name' in data:
            customer.company_name = data['company_name']
        if 'email' in data:
            customer.email = data['email']
        if 'default_mailer_id' in data:
            customer.default_mailer_id = data['default_mailer_id']
        if 'default_service_type' in data:
            customer.default_service_type = data['default_service_type']
        if 'default_barcode_id' in data:
            customer.default_barcode_id = data['default_barcode_id']
        if 'default_sequence_start' in data:
            customer.default_sequence_start = data['default_sequence_start']
        if 'api_provider' in data:
            customer.api_provider = data['api_provider']

        customer.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Customer updated successfully',
            'customer': customer.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating customer: {str(e)}")
        return jsonify({'error': 'Failed to update customer'}), 500


@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """Delete a customer."""
    try:
        customer = Customer.query.get_or_404(customer_id)
        db.session.delete(customer)
        db.session.commit()

        return jsonify({'message': 'Customer deleted successfully'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting customer: {str(e)}")
        return jsonify({'error': 'Failed to delete customer'}), 500


# ========================================
# Job Management API Endpoints
# ========================================

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs, optionally filtered by customer."""
    try:
        customer_id = request.args.get('customer_id', type=int)

        if customer_id:
            jobs = Job.query.filter_by(customer_id=customer_id).order_by(Job.created_at.desc()).all()
        else:
            jobs = Job.query.order_by(Job.created_at.desc()).all()

        return jsonify({
            'jobs': [job.to_dict() for job in jobs]
        })
    except Exception as e:
        app.logger.error(f"Error fetching jobs: {str(e)}")
        return jsonify({'error': 'Failed to fetch jobs'}), 500


@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get a specific job."""
    try:
        job = Job.query.get_or_404(job_id)
        return jsonify({'job': job.to_dict()})
    except Exception as e:
        app.logger.error(f"Error fetching job: {str(e)}")
        return jsonify({'error': 'Job not found'}), 404


@app.route('/api/jobs/<int:job_id>/download/<file_type>')
def download_job_file(job_id, file_type):
    """
    Download processed file from a job.

    Args:
        job_id: Job ID
        file_type: 'output' or 'errors'

    Returns:
        File download
    """
    try:
        job = Job.query.get_or_404(job_id)

        # Get file path based on type
        if file_type == 'output':
            file_path = job.output_file_path
        elif file_type == 'errors':
            file_path = job.error_file_path
        else:
            return jsonify({'error': 'Invalid file type'}), 400

        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found or no longer available'}), 404

        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path),
            mimetype='text/csv'
        )

    except Exception as e:
        app.logger.error(f"Error downloading job file: {str(e)}")
        return jsonify({'error': 'Failed to download file'}), 500


# Error handlers
@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    app.logger.error(f"Internal error: {str(e)}")
    return jsonify({'error': 'Internal server error. Please try again.'}), 500


if __name__ == '__main__':
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize database tables
    with app.app_context():
        db.create_all()
        app.logger.info('Database tables created successfully')

    # Run app on Railway-assigned port or 5001 for local dev
    # (port 5000 is used by macOS AirPlay Receiver on macOS 12+)
    port = int(os.getenv('PORT', 5001))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_ENV', 'development') == 'development'
    )
