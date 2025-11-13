"""seed_default_customer

Revision ID: e95cde616cef
Revises: 9151eeb6401d
Create Date: 2025-11-13 12:21:17.107307

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'e95cde616cef'
down_revision = '9151eeb6401d'
branch_labels = None
depends_on = None


def upgrade():
    """Create default customer if none exist"""
    # Define a minimal table representation for the query
    customers_table = table('customers',
        column('id', sa.Integer),
        column('name', sa.String),
        column('company_name', sa.String),
        column('default_sequence_start', sa.Integer),
        column('api_provider', sa.String),
        column('created_at', sa.DateTime),
        column('updated_at', sa.DateTime)
    )

    # Check if any customers exist
    conn = op.get_bind()
    result = conn.execute(sa.select(sa.func.count()).select_from(customers_table))
    customer_count = result.scalar()

    # Only insert if no customers exist
    if customer_count == 0:
        op.execute(
            customers_table.insert().values(
                name='Default Customer',
                company_name='Quick Processing',
                default_sequence_start=1,
                api_provider='usps',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        print("✅ Created default customer for quick processing")
    else:
        print(f"ℹ️  Skipping default customer creation - {customer_count} customer(s) already exist")


def downgrade():
    """Remove default customer if it's the only one and has no jobs"""
    # Define table representations
    customers_table = table('customers',
        column('id', sa.Integer),
        column('name', sa.String)
    )

    jobs_table = table('jobs',
        column('id', sa.Integer),
        column('customer_id', sa.Integer)
    )

    conn = op.get_bind()

    # Find the default customer
    result = conn.execute(
        sa.select(customers_table.c.id)
        .where(customers_table.c.name == 'Default Customer')
    )
    default_customer = result.fetchone()

    if default_customer:
        customer_id = default_customer[0]

        # Check if this customer has any jobs
        result = conn.execute(
            sa.select(sa.func.count())
            .select_from(jobs_table)
            .where(jobs_table.c.customer_id == customer_id)
        )
        job_count = result.scalar()

        if job_count == 0:
            # Safe to delete - no jobs associated
            op.execute(
                customers_table.delete()
                .where(customers_table.c.id == customer_id)
            )
            print("✅ Removed default customer")
        else:
            print(f"⚠️  Cannot remove default customer - {job_count} job(s) associated")
