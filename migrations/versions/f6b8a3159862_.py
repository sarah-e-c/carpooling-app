"""Revision to add some constraints to the database

Revision ID: f6b8a3159862
Revises: 16d4ac742010
Create Date: 2022-11-18 19:13:34.677906

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6b8a3159862'
down_revision = '16d4ac742010'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('carpools_driver_index_key', 'carpools', type_='unique')
    op.alter_column('event_carpool_signups', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_constraint('event_carpool_signups_user_id_key', 'event_carpool_signups', type_='unique')
    op.alter_column('generated_carpool_part_passenger_links', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_constraint('generated_carpool_part_passenger_links_user_id_key', 'generated_carpool_part_passenger_links', type_='unique')
    op.alter_column('generated_carpool_parts', 'driver_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_constraint('generated_carpool_parts_driver_id_key', 'generated_carpool_parts', type_='unique')
    op.alter_column('generated_carpool_passenger_links', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_constraint('generated_carpool_passenger_links_user_id_key', 'generated_carpool_passenger_links', type_='unique')
    op.drop_constraint('generated_carpool_response_passenger_id_fkey', 'generated_carpool_response', type_='foreignkey')
    op.drop_column('generated_carpool_response', 'passenger_id')
    op.alter_column('generated_carpools', 'driver_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_constraint('generated_carpools_driver_id_key', 'generated_carpools', type_='unique')
    op.drop_constraint('passenger_carpool_links_user_id_key', 'passenger_carpool_links', type_='unique')
    op.drop_constraint('passenger_event_links_user_id_key', 'passenger_event_links', type_='unique')


    op.execute("""
    UPDATE users
    SET emergency_contact_number = 'not provided'
    WHERE emergency_contact_number IS NULL;
    UPDATE users
    SET emergency_contact_relation= 'not provided'
    WHERE emergency_contact_relation IS NULL;
    """)
    op.alter_column('users', 'emergency_contact_number',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('users', 'emergency_contact_relation',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.create_unique_constraint(None, 'users', ['email_address'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'emergency_contact_relation',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('users', 'emergency_contact_number',
               existing_type=sa.VARCHAR(),
               nullable=True)

    op.execute("""
    UPDATE users
    SET emergency_contact_number = NULL
    WHERE emergency_contact_number = 'not provided';
    UPDATE users
    SET emergency_contact_relation= NULL
    WHERE emergency_contact_relation = 'not provided';
    """)
    op.create_unique_constraint('passenger_event_links_user_id_key', 'passenger_event_links', ['user_id'])
    op.create_unique_constraint('passenger_carpool_links_user_id_key', 'passenger_carpool_links', ['user_id'])
    op.create_unique_constraint('generated_carpools_driver_id_key', 'generated_carpools', ['driver_id'])
    op.alter_column('generated_carpools', 'driver_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.add_column('generated_carpool_response', sa.Column('passenger_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('generated_carpool_response_passenger_id_fkey', 'generated_carpool_response', 'users', ['passenger_id'], ['id'])
    op.create_unique_constraint('generated_carpool_passenger_links_user_id_key', 'generated_carpool_passenger_links', ['user_id'])
    op.alter_column('generated_carpool_passenger_links', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_unique_constraint('generated_carpool_parts_driver_id_key', 'generated_carpool_parts', ['driver_id'])
    op.alter_column('generated_carpool_parts', 'driver_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_unique_constraint('generated_carpool_part_passenger_links_user_id_key', 'generated_carpool_part_passenger_links', ['user_id'])
    op.alter_column('generated_carpool_part_passenger_links', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_unique_constraint('event_carpool_signups_user_id_key', 'event_carpool_signups', ['user_id'])
    op.alter_column('event_carpool_signups', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_unique_constraint('carpools_driver_index_key', 'carpools', ['driver_index'])
    # ### end Alembic commands ###
