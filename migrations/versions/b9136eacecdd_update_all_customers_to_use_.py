"""Update all customers to use smartystreets provider

Revision ID: b9136eacecdd
Revises: e95cde616cef
Create Date: 2025-11-13 13:49:13.649106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9136eacecdd'
down_revision = 'e95cde616cef'
branch_labels = None
depends_on = None


def upgrade():
    """Update all customers with api_provider='usps' to 'smartystreets'"""
    # Update all customers to use smartystreets instead of usps
    op.execute("""
        UPDATE customers
        SET api_provider = 'smartystreets'
        WHERE api_provider = 'usps' OR api_provider IS NULL
    """)
    print("✅ Updated all customers to use SmartyStreets provider")


def downgrade():
    """Revert customers back to usps provider"""
    op.execute("""
        UPDATE customers
        SET api_provider = 'usps'
        WHERE api_provider = 'smartystreets'
    """)
    print("⏪ Reverted customers back to USPS provider")
