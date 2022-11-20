"""empty message

Revision ID: 2fac2aa8b798
Revises: f6b8a3159862
Create Date: 2022-11-18 20:45:50.485368

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2fac2aa8b798'
down_revision = 'f6b8a3159862'
branch_labels = None
depends_on = None


def upgrade():
        op.execute("""
        CREATE SEQUENCE IF NOT EXISTS users_id_seq OWNED BY users.id;
    SELECT setval('users_id_seq', coalesce(max(id), 0) + 1, false) FROM users;
    ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq');
    """)
        op.execute("""
    CREATE SEQUENCE IF NOT EXISTS addresses_id_seq OWNED BY addresses.id;
    SELECT setval('addresses_id_seq', coalesce(max(id), 0) + 1, false) FROM addresses;
    ALTER TABLE addresses ALTER COLUMN id SET DEFAULT nextval('addresses_id_seq');
    """)



def downgrade():
    op.execute("""
    CREATE SEQUENCE IF NOT EXISTS users_id_seq OWNED BY users.id;
    SELECT setval('users_id_seq', coalesce(max(id), 0) + 1, false) FROM users;
    ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq');
    """)
    op.execute("""
    CREATE SEQUENCE IF NOT EXISTS addresses_id_seq OWNED BY addresses.id;
    SELECT setval('addresses_id_seq', coalesce(max(id), 0) + 1, false) FROM addresses;
    ALTER TABLE addresses ALTER COLUMN id SET DEFAULT nextval('addresses_id_seq');
    """)
