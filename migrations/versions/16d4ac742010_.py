"""BIG REVISON: renaming events, migrating data

Revision ID: 16d4ac742010
Revises: 3b8b5077e05c
Create Date: 2022-11-18 12:39:05.237995

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '16d4ac742010'
down_revision = '3b8b5077e05c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    # renaming events
    op.alter_column('events', 'event_date', new_column_name='date')
    op.alter_column('events',
                    'event_description',
                    new_column_name='description')
    op.alter_column('events', 'event_location', new_column_name='location')
    op.alter_column('events', 'event_start_time', new_column_name='start_time')
    op.alter_column('events', 'event_end_time', new_column_name='end_time')
    op.alter_column('events', 'event_name', new_column_name='name')
    op.alter_column('events', 'user_id', new_column_name='creator_id')

    op.rename_table('users', 'old_users')  # renaming it so the new users table can fit right in

    # defining a new users table and copying the data over
    new_users_table = op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('email_address', sa.String(length=120), nullable=False),
        sa.Column('password', sa.String(length=120), nullable=False),
        sa.Column('first_name', sa.String(length=120), nullable=False),
        sa.Column('last_name', sa.String(length=120), nullable=False),
        sa.Column(
            'team_auth_key', sa.String(length=10), nullable=False, default='0'
        ),  # a special key sent out by the team to allow access to the site
        sa.Column('is_admin', sa.SmallInteger(), nullable=False, default=0),
        sa.Column('pool_points', sa.Float, default=0.0, nullable=False),
        sa.Column('email_address', sa.String(), nullable=False),
        sa.Column('student_or_parent', sa.String(), nullable=True),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('emergency_contact_number', sa.String(), nullable=True),
        sa.Column('emergency_contact_relation', sa.String(),
                  nullable=True),  # will be set later
        sa.Column('extra_information', sa.String(length=200), nullable=True),
        sa.Column('region_name',
                  sa.String(length=40),
                  sa.ForeignKey('regions.name'),
                  nullable=True),
        sa.Column('num_seats', sa.Integer(), nullable=True),
        sa.Column('num_years_with_license', sa.String(), nullable=True),
        sa.Column('car_type_1', sa.String(), nullable=True),
        sa.Column('car_color_1', sa.String(), nullable=True),
        sa.Column('car_type_2', sa.String(), nullable=True),
        sa.Column('car_color_2', sa.String(), nullable=True),
    )

    # moving the data from the old users table to the new users table
    conn = op.get_bind()
    old_users = conn.execute(
        """SELECT old_users.id,
         passengers.email_address, 
         old_users.password, 
         old_users.first_name,
          old_users.last_name,
           old_users.team_auth_key,
            old_users.is_admin,
             old_users.pool_points,
              drivers.student_or_parent,
               passengers.phone_number,
                passengers.emergency_contact_number,
                 passengers.emergency_contact_relation, 
                 passengers.extra_information, 
                 passengers.region_name,
                  drivers.num_seats, 
                  drivers.num_years_with_license, 
                  drivers.car_type_1, 
                  drivers.car_color_1, 
                  drivers.car_type_2, 
                  drivers.car_color_2
    FROM ((old_users 
    LEFT JOIN drivers ON old_users.driver_id = drivers.index) 
    INNER JOIN passengers ON old_users.passenger_id = passengers.index)
    """)
    old_users = old_users.fetchall()
    new_users = []
    for user in old_users:
        new_users.append({
            'id': user[0],
            'email_address': user[1],
            'password': user[2],
            'first_name': user[3],
            'last_name': user[4],
            'team_auth_key': user[5],
            'is_admin': user[6],
            'pool_points': user[7],
            'student_or_parent': user[8],
            'phone_number': user[9],
            'emergency_contact_number': user[10],
            'emergency_contact_relation': user[11],
            'extra_information': user[12],
            'region_name': user[13],
            'num_seats': user[14],
            'num_years_with_license': user[15],
            'car_type_1': user[16],
            'car_color_1': user[17],
            'car_type_2': user[18],
            'car_color_2': user[19],
        })

    op.bulk_insert(new_users_table, new_users)

    print(new_users_table)

    # creating the legacy drivers table
    legacy_drivers_table = op.create_table(
        'legacy_drivers',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('first_name', sa.String(length=120), nullable=False),
        sa.Column('last_name', sa.String(length=120), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('email_address', sa.String(), nullable=False),
        sa.Column('num_seats', sa.Integer(), nullable=True),
        sa.Column('num_years_with_license', sa.String(), nullable=True),
        sa.Column('student_or_parent', sa.String(), nullable=True),
        sa.Column('car_type_1', sa.String(), nullable=True),
        sa.Column('car_color_1', sa.String(), nullable=True),
        sa.Column('car_type_2', sa.String(), nullable=True),
        sa.Column('car_color_2', sa.String(), nullable=True),
        sa.Column('emergency_contact_number', sa.String(), nullable=True),
        sa.Column('emergency_contact_relation', sa.String(), nullable=True),
        sa.Column('extra_information', sa.String(length=200), nullable=True),
    )

    # moving the data from the old drivers table to the legacy drivers table
    op.execute(
        """INSERT INTO legacy_drivers (id, first_name, last_name, email_address, phone_number, num_seats, num_years_with_license, car_type_1, car_color_1, car_type_2, car_color_2, emergency_contact_number, emergency_contact_relation, extra_information, student_or_parent)
    SELECT drivers.index, drivers.first_name, drivers.last_name, drivers.email_address, drivers.phone_number, drivers.num_seats, drivers.num_years_with_license, drivers.car_type_1, drivers.car_color_1, drivers.car_type_2, drivers.car_color_2, drivers.emergency_contact_number, drivers.emergency_contact_relation, drivers.extra_information, drivers.student_or_parent
    FROM drivers
    FULL OUTER JOIN old_users ON drivers.index = old_users.driver_id
    WHERE old_users.first_name IS NULL
    """
        # the logic here is that if the first_name is null, then the user does not exist in the old_users table, and therefore is a legacy driver
    )

    # moving data from the keys

    # will fix this later

    # getting the new foreign keys

    # dict -- tablename: [oldname, newname]
    tables_to_change_foreign_keys_passengers = {'event_carpool_signups': ['passenger_id', 'user_id'],
                                                'passenger_carpool_links': ['passenger_id', 'user_id'],
                                                'passenger_event_links': ['passenger_id', 'user_id'],
                                                'generated_carpool_part_passenger_links': ['passenger_id', 'user_id'],
                                                'generated_carpool_passenger_links': ['passenger_id', 'user_id'],
                                                }

    tables_to_change_foreign_keys_drivers = {'generated_carpool_parts': ['driver_id', 'driver_id'],
                                             'generated_carpools': ['driver_id', 'driver_id'],
                                             'carpools': ['driver_index', 'driver_index'],
                                             }

    # address is not included because it is turning into many to many: more on that later

    # changing the foreign keys
    for table, names in tables_to_change_foreign_keys_passengers.items():
        print('starting table', table)
        op.drop_constraint(f'{table}_{names[0]}_fkey',
                           table,
                           type_='foreignkey')
        op.add_column(table, sa.Column(f'{names[1]}', sa.Integer(), nullable=True, unique=True))
        op.execute(f"""
        UPDATE {table}
        SET {names[1]} = old_users.id
        FROM old_users
        WHERE {table}.{names[0]} = old_users.passenger_id
        """)

        op.create_foreign_key(None, table, 'users', [f'{names[1]}'], ['id'])
        op.drop_column(table, 'passenger_id')

    for table, names in tables_to_change_foreign_keys_drivers.items():
        op.drop_constraint(f'{table}_{names[0]}_fkey',
                           table,
                           type_='foreignkey')
        op.alter_column(table, names[1], new_column_name='old_column')
        op.add_column(table, sa.Column(f'{names[1]}', sa.Integer(), nullable=True, unique=False))
        op.execute(f"""
        UPDATE {table}
        SET {names[1]} = old_users.id
        FROM old_users
        WHERE {table}.old_column = old_users.driver_id;
        """)
        op.create_foreign_key(None, table, 'users', [names[1]], ['id'])
        op.drop_column(table, 'old_column')

    # need to create table here so it connects to the new table
    op.create_table(
        'address_user_links',
        sa.Column('address_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['address_id'],
            ['addresses.id'],
        ), sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
        ), sa.PrimaryKeyConstraint('address_id', 'user_id'))

    # moving data into the links

    # moving the address data that are not linked to a passenger into the address table
    op.alter_column('addresses', 'code', nullable=True)
    op.alter_column('addresses', 'latitude', nullable=True)
    op.alter_column('addresses', 'longitude', nullable=True)
    op.execute("""
    INSERT INTO addresses (address_line_1, address_line_2, city, state, zip_code)
    SELECT passengers.address_line_1, passengers.address_line_2, passengers.city, 'VA', passengers.zip_code
    FROM passengers
    FULL OUTER JOIN addresses
    ON addresses.passenger_id = passengers.index
    WHERE passengers.address_line_1 IS NOT NULL
    AND addresses.address_line_1 IS NULL;

    UPDATE addresses
    SET passenger_id = passengers.index
    FROM passengers
    WHERE passengers.address_line_1 = addresses.address_line_1 AND passengers.address_line_2 = addresses.address_line_2 AND passengers.city = addresses.city AND passengers.zip_code = addresses.zip_code;

    INSERT INTO address_user_links (address_id, user_id)
    SELECT addresses.id, old_users.id
    FROM passengers 
    INNER JOIN addresses
        ON addresses.passenger_id = passengers.index
    INNER JOIN old_users 
        ON passengers.index = old_users.passenger_id;
    """)
    op.drop_constraint('addresses_driver_id_fkey',
                       'addresses',
                       type_='foreignkey')
    op.drop_constraint('addresses_passenger_id_fkey',
                       'addresses',
                       type_='foreignkey')

    op.drop_column('addresses', 'driver_id')
    op.drop_column('addresses', 'passenger_id')
    # handling addresses

    # moving the keys that depended on the old users table
    op.drop_constraint('generated_carpool_response_user_id_fkey', 'generated_carpool_response', type_='foreignkey')
    op.create_foreign_key('generated_carpool_response_user_id_fkey', 'generated_carpool_response', 'users', ['user_id'],
                          ['id'])
    op.drop_constraint('event_sign_ups_user_id_fkey', 'event_sign_ups', type_='foreignkey')
    op.create_foreign_key('event_sign_ups_user_id_fkey', 'event_sign_ups', 'users', ['user_id'], ['id'])
    op.drop_constraint('events_user_id_fkey', 'events', type_='foreignkey')
    op.create_foreign_key('events_user_id_fkey', 'events', 'users', ['creator_id'], ['id'])
    op.drop_constraint('generated_carpool_response_passenger_id_fkey', 'generated_carpool_response', type_='foreignkey')
    op.create_foreign_key('generated_carpool_response_passenger_id_fkey', 'generated_carpool_response', 'users',
                          ['passenger_id'], ['id'])

    # dropping the tables
    op.drop_table('old_users')
    op.drop_table('drivers')
    op.drop_table('passengers')
    # ### end Alembic commands ###


def downgrade():
    # renaming users table
    op.alter_column('events', 'date', new_column_name='event_date')
    op.alter_column('events',
                    'description',
                    new_column_name='event_description')
    op.alter_column('events', 'location', new_column_name='event_location')
    op.alter_column('events', 'start_time', new_column_name='event_start_time')
    op.alter_column('events', 'end_time', new_column_name='event_end_time')
    op.alter_column('events', 'name', new_column_name='event_name')
    op.alter_column('events', 'creator_id', new_column_name='user_id')

    op.rename_table('users', 'old_users')

    new_users_table = op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('password', sa.String(length=120), nullable=False),
        sa.Column('first_name', sa.String(length=120), nullable=False),
        sa.Column('last_name', sa.String(length=120), nullable=False),
        sa.Column(
            'team_auth_key', sa.String(length=10), nullable=False, default='0'
        ),  # a special key sent out by the team to allow access to the site
        sa.Column('is_admin', sa.SmallInteger(), nullable=False, default=0),
        sa.Column('pool_points', sa.Float, default=0.0, nullable=False),
        sa.Column('passenger_id', sa.Integer(), nullable=True, unique=True),
        sa.Column('driver_id', sa.Integer(), nullable=True, unique=True),
    )

    conn = op.get_bind()
    conn.execute("""
    INSERT INTO users (id, password, first_name, last_name, team_auth_key, is_admin, pool_points)
    SELECT id, password, first_name, last_name, team_auth_key, is_admin, pool_points
    FROM old_users
    """)
    passengers_table = op.create_table(
        'passengers',
        sa.Column('index', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('last_name',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('first_name',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('phone_number',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('email_address',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('emergency_contact_number',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('emergency_contact_relation',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('extra_information',
                  sa.VARCHAR(length=200),
                  autoincrement=False,
                  nullable=True),
        sa.Column('region_name',
                  sa.VARCHAR(length=40),
                  autoincrement=False,
                  nullable=True),
        sa.Column('address_line_1',
                  sa.VARCHAR(length=50),
                  autoincrement=False,
                  nullable=True),
        sa.Column('address_line_2',
                  sa.VARCHAR(length=50),
                  autoincrement=False,
                  nullable=True),
        sa.Column('city',
                  sa.VARCHAR(length=20),
                  autoincrement=False,
                  nullable=True),
        sa.Column('zip_code',
                  sa.VARCHAR(length=12),
                  autoincrement=False,
                  nullable=True),
        sa.ForeignKeyConstraint(['region_name'], ['regions.name'],
                                name='passengers_region_name_fkey'),
        sa.PrimaryKeyConstraint('index', name='passengers_pkey'))
    # filling with data

    op.execute("""
    INSERT INTO passengers (index, last_name, first_name, phone_number, email_address, emergency_contact_number, emergency_contact_relation, extra_information, region_name, address_line_1, address_line_2, city, zip_code)
    SELECT DISTINCT old_users.id, old_users.last_name, old_users.first_name, old_users.phone_number, old_users.email_address, old_users.emergency_contact_number, old_users.emergency_contact_relation, old_users.extra_information, old_users.region_name, addresses.address_line_1, addresses.address_line_2, addresses.city, addresses.zip_code
    FROM old_users
    INNER JOIN address_user_links ON old_users.id = address_user_links.user_id
    INNER JOIN addresses ON address_user_links.address_id = addresses.id
    """)

    # filling the users table with the passenger_id
    op.execute("""
    UPDATE users
    SET passenger_id = passengers.index
    FROM passengers
    WHERE passengers.last_name = users.last_name AND passengers.first_name = users.first_name
    """)

    drivers_table = op.create_table(
        'drivers',
        sa.Column('index', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('last_name',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('first_name',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('num_seats',
                  sa.INTEGER(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('phone_number',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('email_address',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('student_or_parent',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('num_years_with_license',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('car_type_1',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('car_color_1',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=False),
        sa.Column('car_type_2',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('car_color_2',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('emergency_contact_number',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('emergency_contact_relation',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('extra_information',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('region_name',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('address_line_1',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('address_line_2',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True),
        sa.Column('city', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('zip_code', sa.VARCHAR(), autoincrement=False,
                  nullable=True),
        sa.ForeignKeyConstraint(['region_name'], ['regions.name'],
                                name='drivers_region_name_fkey'),
        sa.PrimaryKeyConstraint('index', name='drivers_pkey'))
    # putting the users into drivers
    op.execute("""
    INSERT INTO drivers (index, last_name, first_name, num_seats, phone_number, email_address, student_or_parent, num_years_with_license, car_type_1, car_color_1, car_type_2, car_color_2, emergency_contact_number, emergency_contact_relation, extra_information, region_name, address_line_1, address_line_2, city, zip_code)
    SELECT old_users.id, old_users.last_name, old_users.first_name, old_users.num_seats, old_users.phone_number, old_users.email_address, old_users.student_or_parent, old_users.num_years_with_license, old_users.car_type_1, old_users.car_color_1, old_users.car_type_2, old_users.car_color_2, old_users.emergency_contact_number, old_users.emergency_contact_relation, old_users.extra_information, old_users.region_name, addresses.address_line_1, addresses.address_line_2, addresses.city, addresses.zip_code
    FROM old_users
    INNER JOIN address_user_links ON old_users.id = address_user_links.user_id
    INNER JOIN addresses ON address_user_links.address_id = addresses.id
    WHERE old_users.num_seats IS NOT NULL
    """)

    # filling the drivers table with the legacy drivers
    op.execute("""
    INSERT INTO drivers (index, last_name, first_name, num_seats, phone_number, email_address, student_or_parent, num_years_with_license, car_type_1, car_color_1, car_type_2, car_color_2, emergency_contact_number, emergency_contact_relation, extra_information)
    SELECT 10000 + legacy_drivers.id, legacy_drivers.last_name, legacy_drivers.first_name, legacy_drivers.num_seats, legacy_drivers.phone_number, legacy_drivers.email_address, legacy_drivers.student_or_parent, legacy_drivers.num_years_with_license, legacy_drivers.car_type_1, legacy_drivers.car_color_1, legacy_drivers.car_type_2, legacy_drivers.car_color_2, legacy_drivers.emergency_contact_number, legacy_drivers.emergency_contact_relation, legacy_drivers.extra_information
    FROM legacy_drivers
    """)

    # filling the users table with the driver_id
    op.execute("""
    UPDATE users
    SET driver_id = drivers.index
    FROM drivers
    WHERE drivers.last_name = users.last_name AND drivers.first_name = users.first_name
    """)

    tables_to_change_foreign_keys_passengers = {'event_carpool_signups': ['user_id', 'passenger_id'],
                                                'passenger_carpool_links': ['user_id', 'passenger_id'],
                                                'passenger_event_links': ['user_id', 'passenger_id'],
                                                'generated_carpool_part_passenger_links': ['user_id', 'passenger_id'],
                                                'generated_carpool_passenger_links': ['user_id', 'passenger_id'],
                                                }

    tables_to_change_foreign_keys_drivers = {'generated_carpool_parts': ['driver_id', 'driver_id'],
                                             'generated_carpools': ['driver_id', 'driver_id'],
                                             'carpools': ['driver_index', 'driver_index'],
                                             }
    # address is not included because it is turning into many to many: more on that later

    # changing the foreign keys
    for table, names in tables_to_change_foreign_keys_passengers.items():
        print('starting table', table)
        op.drop_constraint(f'{table}_{names[0]}_fkey',
                           table,
                           type_='foreignkey')
        op.add_column(table, sa.Column(f'{names[1]}', sa.Integer(), nullable=True, unique=True))

        op.execute(f"""
        UPDATE {table}
        SET {names[1]} = passengers.index
        FROM passengers
        INNER JOIN users
        ON users.passenger_id = passengers.index
        WHERE {table}.{names[0]} = users.id
        """)

        op.create_foreign_key(None, table, 'passengers', [f'{names[1]}'], ['index'])
        op.drop_column(table, names[0])

    for table, names in tables_to_change_foreign_keys_drivers.items():
        print('starting table', table)
        op.drop_constraint(f'{table}_{names[0]}_fkey',
                           table,
                           type_='foreignkey')
        op.alter_column(table, names[1], new_column_name='old_column')
        op.add_column(table, sa.Column(f'{names[1]}', sa.Integer(), nullable=True, unique=True))
        op.execute(f"""
        UPDATE {table}
        SET {names[1]} = drivers.index
        FROM drivers
        INNER JOIN users
        ON users.driver_id = drivers.index
        WHERE {table}.old_column = users.id;
        """)
        op.create_foreign_key(None, table, 'drivers', [names[1]], ['index'])
        op.drop_column(table, 'old_column')

    # redoing the primary key constraints
    op.drop_constraint('generated_carpool_response_user_id_fkey', 'generated_carpool_response', type_='foreignkey')
    op.create_foreign_key('generated_carpool_response_user_id_fkey', 'generated_carpool_response', 'users', ['user_id'],
                          ['id'])
    op.drop_constraint('event_sign_ups_user_id_fkey', 'event_sign_ups', type_='foreignkey')
    op.create_foreign_key('event_sign_ups_user_id_fkey', 'event_sign_ups', 'users', ['user_id'], ['id'])
    op.drop_constraint('events_user_id_fkey', 'events', type_='foreignkey')
    op.create_foreign_key('events_user_id_fkey', 'events', 'users', ['user_id'], ['id'])
    op.drop_constraint('generated_carpool_response_passenger_id_fkey', 'generated_carpool_response', type_='foreignkey')
    op.create_foreign_key('generated_carpool_response_passenger_id_fkey', 'generated_carpool_response', 'passengers',
                          ['passenger_id'], ['index'])

    # handling addresses
    op.add_column('addresses', sa.Column('passenger_id', sa.Integer(), nullable=True, unique=True))
    op.add_column('addresses', sa.Column('driver_id', sa.Integer(), nullable=True, unique=True))

    op.drop_constraint('addresses_passenger_id_key', 'addresses', type_='unique')
    op.execute("""
    UPDATE addresses
    SET passenger_id = passengers.index
    FROM passengers, users, address_user_links
    WHERE users.passenger_id = passengers.index
    AND users.id = address_user_links.user_id
    AND address_user_links.address_id = addresses.id
    """)
    op.execute("""
    UPDATE addresses
    SET driver_id = drivers.index
    FROM drivers, users, address_user_links
    WHERE users.driver_id = drivers.index
    AND users.id = address_user_links.user_id
    AND address_user_links.address_id = addresses.id
    """)

    op.execute("""
    DELETE FROM address_user_links
    USING addresses
    WHERE address_user_links.address_id = addresses.id
    AND addresses.latitude IS NULL;
    DELETE FROM addresses
    WHERE latitude IS NULL;
    """)

    op.alter_column('addresses', 'latitude', nullable=False)
    op.alter_column('addresses', 'longitude', nullable=False)
    op.alter_column('addresses', 'code', nullable=False)

    op.drop_constraint('address_user_links_user_id_fkey', 'address_user_links', type_='foreignkey')
    op.drop_constraint('address_user_links_address_id_fkey', 'address_user_links', type_='foreignkey')
    op.drop_table('address_user_links')
    op.drop_table('old_users')
    op.drop_table('legacy_drivers')

    op.create_foreign_key('addresses_passenger_id_fkey', 'addresses', 'passengers', ['passenger_id'], ['index'])
    op.create_foreign_key('addresses_driver_id_fkey', 'addresses', 'drivers', ['driver_id'], ['index'])

    # ### end Alembic commands ###
