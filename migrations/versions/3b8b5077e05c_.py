"""empty message

Revision ID: 3b8b5077e05c
Revises: 97aefc90071f
Create Date: 2022-11-17 17:56:13.772734

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b8b5077e05c'
down_revision = '97aefc90071f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('drivers_address_id_fkey', 'drivers', type_='foreignkey')
    op.drop_column('drivers', 'address_id')
    op.drop_constraint('passengers_address_id_fkey', 'passengers', type_='foreignkey')
    op.drop_column('passengers', 'address_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('passengers', sa.Column('address_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('passengers_address_id_fkey', 'passengers', 'addresses', ['address_id'], ['id'])
    op.add_column('drivers', sa.Column('address_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('drivers_address_id_fkey', 'drivers', 'addresses', ['address_id'], ['id'])
    # ### end Alembic commands ###
