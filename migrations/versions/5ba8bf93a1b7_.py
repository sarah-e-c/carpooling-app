"""empty message

Revision ID: 5ba8bf93a1b7
Revises: 2a6528c39b04
Create Date: 2022-11-09 12:10:12.078629

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5ba8bf93a1b7'
down_revision = '2a6528c39b04'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('destinations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('address_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['address_id'], ['addresses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_constraint('addresses_id_key', 'addresses', type_='unique')
    op.add_column('distance_matrix', sa.Column('seconds', sa.Float(), nullable=False))
    op.add_column('distance_matrix', sa.Column('kilos', sa.Float(), nullable=False))
    op.add_column('events', sa.Column('destination_id', sa.Integer(), nullable=True))
    op.drop_constraint('events_address_id_fkey', 'events', type_='foreignkey')
    op.create_foreign_key(None, 'events', 'destinations', ['destination_id'], ['id'])
    op.drop_column('events', 'address_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('address_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'events', type_='foreignkey')
    op.create_foreign_key('events_address_id_fkey', 'events', 'addresses', ['address_id'], ['id'])
    op.drop_column('events', 'destination_id')
    op.drop_column('distance_matrix', 'kilos')
    op.drop_column('distance_matrix', 'seconds')
    op.create_unique_constraint('addresses_id_key', 'addresses', ['id'])
    op.drop_table('destinations')
    # ### end Alembic commands ###
