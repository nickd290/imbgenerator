"""
Database models for IMB Generator
Defines Customer and Job models for tracking processing history
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Customer(db.Model):
    """Customer model for tracking clients"""
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    company_name = db.Column(db.String(200))
    email = db.Column(db.String(200))

    # Default IMB settings
    default_mailer_id = db.Column(db.String(20))
    default_service_type = db.Column(db.String(10), default='040')
    default_barcode_id = db.Column(db.String(10), default='00')
    default_sequence_start = db.Column(db.Integer, default=1)
    api_provider = db.Column(db.String(20), default='usps')

    # Sequence tracking (prevents duplicate IMB sequence numbers)
    last_sequence_number = db.Column(db.Integer, default=0)
    last_mailer_id_used = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to jobs
    jobs = db.relationship('Job', backref='customer', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Convert model to dictionary for JSON responses"""
        return {
            'id': self.id,
            'name': self.name,
            'company_name': self.company_name,
            'email': self.email,
            'default_mailer_id': self.default_mailer_id,
            'default_service_type': self.default_service_type,
            'default_barcode_id': self.default_barcode_id,
            'default_sequence_start': self.default_sequence_start,
            'api_provider': self.api_provider,
            'last_sequence_number': self.last_sequence_number,
            'last_mailer_id_used': self.last_mailer_id_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Customer {self.name}>'


class Job(db.Model):
    """Job model for tracking IMB generation processing jobs"""
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    filename = db.Column(db.String(500), nullable=False)
    mailer_id = db.Column(db.String(20), nullable=False)
    sequence_start = db.Column(db.Integer, nullable=False)
    sequence_end = db.Column(db.Integer)  # Last sequence number used in this job
    service_type = db.Column(db.String(10))
    barcode_id = db.Column(db.String(10))
    mail_service_mode = db.Column(db.String(20))  # 'basic' or 'full_service'

    # Processing statistics
    total_records = db.Column(db.Integer, default=0)
    successful_records = db.Column(db.Integer, default=0)
    failed_records = db.Column(db.Integer, default=0)

    # File paths
    output_file_path = db.Column(db.String(500))
    error_file_path = db.Column(db.String(500))

    # Status tracking
    status = db.Column(db.String(50), default='pending')  # pending, processing, complete, error
    error_message = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    def to_dict(self):
        """Convert model to dictionary for JSON responses"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'filename': self.filename,
            'mailer_id': self.mailer_id,
            'sequence_start': self.sequence_start,
            'sequence_end': self.sequence_end,
            'service_type': self.service_type,
            'barcode_id': self.barcode_id,
            'mail_service_mode': self.mail_service_mode,
            'total_records': self.total_records,
            'successful_records': self.successful_records,
            'failed_records': self.failed_records,
            'output_file_path': self.output_file_path,
            'error_file_path': self.error_file_path,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def __repr__(self):
        return f'<Job {self.id} - {self.filename}>'
