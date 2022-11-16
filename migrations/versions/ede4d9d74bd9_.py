"""empty message

Revision ID: ede4d9d74bd9
Revises: cfd50aee529f
Create Date: 2022-11-09 11:37:23.605187

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ede4d9d74bd9'
down_revision = 'cfd50aee529f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.create_table('addresses',
    # sa.Column('id', sa.Integer(), nullable=False),
    # sa.Column('address_line_1', sa.String(), nullable=False),
    # sa.Column('address_line_2', sa.String(), nullable=True),
    # sa.Column('city', sa.String(), nullable=False),
    # sa.Column('state', sa.String(), nullable=False),
    # sa.Column('zip_code', sa.String(), nullable=False),
    # sa.Column('latitude', sa.Float(), nullable=False),
    # sa.Column('longitude', sa.Float(), nullable=False),
    # sa.Column('code', sa.String(), nullable=False),
    # sa.Column('passenger_id', sa.Integer(), nullable=True),
    # sa.Column('driver_id', sa.Integer(), nullable=True),
    # sa.ForeignKeyConstraint(['driver_id'], ['drivers.index'], ),
    # sa.ForeignKeyConstraint(['passenger_id'], ['passengers.index'], ),
    # sa.PrimaryKeyConstraint('id'),
    # sa.UniqueConstraint('id')
    # )
    # op.create_table('auth_keys',
    # sa.Column('index', sa.Integer(), nullable=False),
    # sa.Column('key', sa.String(), nullable=False),
    # sa.Column('date_created', sa.DateTime(), nullable=True),
    # sa.PrimaryKeyConstraint('index')
    # )
    # op.create_table('drivers',
    # sa.Column('index', sa.Integer(), nullable=False),
    # sa.Column('last_name', sa.String(), nullable=False),
    # sa.Column('first_name', sa.String(), nullable=False),
    # sa.Column('num_seats', sa.Integer(), nullable=False),
    # sa.Column('phone_number', sa.String(), nullable=False),
    # sa.Column('email_address', sa.String(), nullable=False),
    # sa.Column('student_or_parent', sa.String(), nullable=False),
    # sa.Column('num_years_with_license', sa.String(), nullable=True),
    # sa.Column('car_type_1', sa.String(), nullable=False),
    # sa.Column('car_color_1', sa.String(), nullable=False),
    # sa.Column('car_type_2', sa.String(), nullable=True),
    # sa.Column('car_color_2', sa.String(), nullable=True),
    # sa.Column('emergency_contact_number', sa.String(), nullable=False),
    # sa.Column('emergency_contact_relation', sa.String(), nullable=False),
    # sa.Column('extra_information', sa.String(), nullable=True),
    # sa.Column('region_name', sa.String(), nullable=True),
    # sa.Column('address_line_1', sa.String(), nullable=True),
    # sa.Column('address_line_2', sa.String(), nullable=True),
    # sa.Column('city', sa.String(), nullable=True),
    # sa.Column('zip_code', sa.String(), nullable=True),
    # sa.Column('address_id', sa.Integer(), nullable=True),
    # sa.ForeignKeyConstraint(['address_id'], ['addresses.id'], ),
    # sa.ForeignKeyConstraint(['region_name'], ['regions.name'], ),
    # sa.PrimaryKeyConstraint('index')
    # )
    # op.create_table('passengers',
    # sa.Column('index', sa.Integer(), nullable=False),
    # sa.Column('last_name', sa.String(), nullable=False),
    # sa.Column('first_name', sa.String(), nullable=False),
    # sa.Column('phone_number', sa.String(), nullable=False),
    # sa.Column('email_address', sa.String(), nullable=False),
    # sa.Column('emergency_contact_number', sa.String(), nullable=True),
    # sa.Column('emergency_contact_relation', sa.String(), nullable=True),
    # sa.Column('extra_information', sa.String(), nullable=True),
    # sa.Column('region_name', sa.String(), nullable=True),
    # sa.Column('address_line_1', sa.String(), nullable=True),
    # sa.Column('address_line_2', sa.String(), nullable=True),
    # sa.Column('city', sa.String(), nullable=True),
    # sa.Column('zip_code', sa.String(), nullable=True),
    # sa.Column('address_id', sa.Integer(), nullable=True),
    # sa.ForeignKeyConstraint(['address_id'], ['addresses.id'], ),
    # sa.ForeignKeyConstraint(['region_name'], ['regions.name'], ),
    # sa.PrimaryKeyConstraint('index')
    # )
    # op.create_table('regions',
    # sa.Column('name', sa.String(), nullable=False),
    # sa.Column('dropoff_location', sa.String(), nullable=False),
    # sa.Column('color', sa.String(), nullable=False),
    # sa.PrimaryKeyConstraint('name')
    # )
    # op.create_table('distance_matrix',
    # sa.Column('index', sa.Integer(), nullable=False),
    # sa.Column('origin_id', sa.Integer(), nullable=False),
    # sa.Column('destination_id', sa.Integer(), nullable=False),
    # sa.ForeignKeyConstraint(['destination_id'], ['addresses.id'], ),
    # sa.ForeignKeyConstraint(['origin_id'], ['addresses.id'], ),
    # sa.PrimaryKeyConstraint('index')
    # )
    # op.create_table('student_and_region',
    # sa.Column('index', sa.Integer(), nullable=False),
    # sa.Column('student_first_name', sa.String(), nullable=False),
    # sa.Column('student_last_name', sa.String(), nullable=False),
    # sa.Column('region_name', sa.String(), nullable=True),
    # sa.ForeignKeyConstraint(['region_name'], ['regions.name'], ),
    # sa.PrimaryKeyConstraint('index')
    # )
    # op.create_table('users',
    # sa.Column('id', sa.Integer(), nullable=False),
    # sa.Column('password', sa.String(), nullable=True),
    # sa.Column('first_name', sa.String(), nullable=False),
    # sa.Column('last_name', sa.String(), nullable=False),
    # sa.Column('driver_id', sa.Integer(), nullable=True),
    # sa.Column('passenger_id', sa.Integer(), nullable=True),
    # sa.Column('team_auth_key', sa.String(), nullable=False),
    # sa.Column('is_admin', sa.Integer(), nullable=False),
    # sa.ForeignKeyConstraint(['driver_id'], ['drivers.index'], ),
    # sa.ForeignKeyConstraint(['passenger_id'], ['passengers.index'], ),
    # sa.PrimaryKeyConstraint('id')
    # )
    # op.create_table('events',
    # sa.Column('index', sa.Integer(), nullable=False),
    # sa.Column('event_name', sa.String(), nullable=False),
    # sa.Column('event_date', sa.DateTime(), nullable=False),
    # sa.Column('event_start_time', sa.DateTime(), nullable=False),
    # sa.Column('event_end_time', sa.DateTime(), nullable=False),
    # sa.Column('event_location', sa.String(), nullable=False),
    # sa.Column('event_description', sa.String(), nullable=True),
    # sa.Column('user_id', sa.Integer(), nullable=True),
    # sa.Column('address_id', sa.Integer(), nullable=True),
    # sa.ForeignKeyConstraint(['address_id'], ['addresses.id'], ),
    # sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    # sa.PrimaryKeyConstraint('index')
    # )
    # op.create_table('carpools',
    # sa.Column('index', sa.Integer(), nullable=False),
    # sa.Column('driver_index', sa.Integer(), nullable=True),
    # sa.Column('num_passengers', sa.Integer(), nullable=False),
    # sa.Column('event_index', sa.Integer(), nullable=False),
    # sa.Column('destination', sa.String(), nullable=False),
    # sa.Column('extra_information', sa.String(), nullable=True),
    # sa.Column('region_name', sa.String(), nullable=False),
    # sa.ForeignKeyConstraint(['driver_index'], ['drivers.index'], ),
    # sa.ForeignKeyConstraint(['event_index'], ['events.index'], ),
    # sa.ForeignKeyConstraint(['region_name'], ['regions.name'], ),
    # sa.PrimaryKeyConstraint('index')
    # )
    # op.create_table('event_sign_ups',
    # sa.Column('id', sa.Integer(), nullable=False),
    # sa.Column('event_id', sa.Integer(), nullable=True),
    # sa.Column('user_id', sa.Integer(), nullable=True),
    # sa.Column('check_in_time', sa.DateTime(), nullable=False),
    # sa.Column('check_out_time', sa.DateTime(), nullable=True),
    # sa.Column('re_check_in_time', sa.DateTime(), nullable=True),
    # sa.ForeignKeyConstraint(['event_id'], ['events.index'], ),
    # sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    # sa.PrimaryKeyConstraint('id')
    # )
    # op.create_table('passenger_event_links',
    # sa.Column('index', sa.Integer(), nullable=False),
    # sa.Column('passenger_id', sa.Integer(), nullable=True),
    # sa.Column('event_id', sa.Integer(), nullable=True),
    # sa.ForeignKeyConstraint(['event_id'], ['events.index'], ),
    # sa.ForeignKeyConstraint(['passenger_id'], ['passengers.index'], ),
    # sa.PrimaryKeyConstraint('index')
    # )
    # op.create_table('passenger_carpool_links',
    # sa.Column('index', sa.Integer(), nullable=False),
    # sa.Column('passenger_id', sa.Integer(), nullable=True),
    # sa.Column('carpool_id', sa.Integer(), nullable=True),
    # sa.ForeignKeyConstraint(['carpool_id'], ['carpools.index'], ),
    # sa.ForeignKeyConstraint(['passenger_id'], ['passengers.index'], ),
    # sa.PrimaryKeyConstraint('index')
    # )
    # ### end Alembic commands ###
    pass


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('passenger_carpool_links')
    op.drop_table('passenger_event_links')
    op.drop_table('event_sign_ups')
    op.drop_table('carpools')
    op.drop_table('events')
    op.drop_table('users')
    op.drop_table('student_and_region')
    op.drop_table('distance_matrix')
    op.drop_table('regions')
    op.drop_table('passengers')
    op.drop_table('drivers')
    op.drop_table('auth_keys')
    op.drop_table('addresses')
    # ### end Alembic commands ###
