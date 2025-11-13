"""force_update_customers_to_smartystreets

Revision ID: 7335b88fa9d8
Revises: b9136eacecdd
Create Date: 2025-11-13 15:48:23.295928

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7335b88fa9d8'
down_revision = 'b9136eacecdd'
branch_labels = None
depends_on = None


def upgrade():
    """Force update ALL customers to use smartystreets provider"""
    # Execute raw SQL to update all customer records
    op.execute("""
        UPDATE customers
        SET api_provider = 'smartystreets',
            updated_at = CURRENT_TIMESTAMP
        WHERE api_provider != 'smartystreets'
    """)
    print("🔧 FORCED UPDATE: All customers now use SmartyStreets provider")


def downgrade():
    """Revert customers back to usps"""
    op.execute("""
        UPDATE customers
        SET api_provider = 'usps',
            updated_at = CURRENT_TIMESTAMP
        WHERE api_provider = 'smartystreets'
    """)
    print("⏪ Reverted customers back to USPS provider")
