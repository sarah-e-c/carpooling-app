"""empty message

Revision ID: 97aefc90071f
Revises: 3b1cb9d6b7b1
Create Date: 2022-11-16 14:03:28.291880

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97aefc90071f'
down_revision = '3b1cb9d6b7b1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("""
    CREATE SEQUENCE IF NOT EXISTS addresses_id_seq OWNED BY addresses.id;
SELECT setval('addresses_id_seq', coalesce(max(id), 0) + 1, false) FROM addresses;
ALTER TABLE addresses ALTER COLUMN id SET DEFAULT nextval('addresses_id_seq');
""")
    op.drop_constraint('addresses_id_key1', 'addresses', type_='unique')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("""
    DROP SEQUENCE IF EXISTS addresses_id_seq;
    """)
    op.create_unique_constraint('addresses_id_key1', 'addresses', ['id'])
    # ### end Alembic commands ###