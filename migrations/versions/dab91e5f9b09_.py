"""Migration to add time to generated carpool parts and carpool.

Revision ID: dab91e5f9b09
Revises: 8e887f87d166
Create Date: 2022-11-25 18:53:33.387682

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dab91e5f9b09'
down_revision = '8e887f87d166'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('generated_carpool_parts', sa.Column('from_time', sa.DateTime(), nullable=True))
    op.execute("""
    UPDATE generated_carpool_parts
    SET from_time = now()
    WHERE from_time IS NULL;
    """)
    op.alter_column('generated_carpool_parts', 'from_time', nullable=False)

    op.add_column('generated_carpool_parts', sa.Column('to_time', sa.DateTime(), nullable=True))
    op.execute("""
    UPDATE generated_carpool_parts
    SET to_time = now()
    WHERE to_time IS NULL;
    """)
    op.alter_column('generated_carpool_parts', 'to_time', nullable=False)

    op.add_column('generated_carpools', sa.Column('from_time', sa.DateTime(), nullable=True))
    op.execute("""
    UPDATE generated_carpools
    SET from_time=now()
    WHERE from_time IS NULL;
    """)
    op.alter_column('generated_carpools', 'from_time', nullable=False)

    op.add_column('generated_carpools', sa.Column('to_time', sa.DateTime(), nullable=True))
    op.execute("""
    UPDATE generated_carpools
    SET to_time=now()
    WHERE to_time IS NULL;
    """)
    op.alter_column('generated_carpools', 'to_time', nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('generated_carpools', 'to_time')
    op.drop_column('generated_carpools', 'from_time')
    op.drop_column('generated_carpool_parts', 'to_time')
    op.drop_column('generated_carpool_parts', 'from_time')
    # ### end Alembic commands ###
