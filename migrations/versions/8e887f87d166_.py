"""Slight little revision to the database because the id wasn't serial for some reason.

Revision ID: 8e887f87d166
Revises: 44d833d2c46e
Create Date: 2022-11-23 17:26:40.416046

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8e887f87d166'
down_revision = '44d833d2c46e'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE SEQUENCE generated_carpool_part_passenger_links_id_seq;
    ALTER TABLE generated_carpool_part_passenger_links ALTER COLUMN id SET DEFAULT nextval('generated_carpool_part_passenger_links_id_seq');
    """
               )


def downgrade():
    op.execute("""
    ALTER TABLE generated_carpool_part_passenger_links ALTER COLUMN id DROP DEFAULT;
    DROP SEQUENCE generated_carpool_part_passenger_links_id_seq;
    """
               )
