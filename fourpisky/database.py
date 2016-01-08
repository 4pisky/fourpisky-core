from sqlalchemy.engine.url import URL

import getpass

default_username = getpass.getuser()
default_password = default_username
drivername = 'postgres'
default_host = 'localhost'
dbname = 'voeventdb'

voevent_broker_db_params = dict(drivername=drivername,
                                username=default_username,
                                password=default_password,
                                host=default_host,
                                database=dbname)
voevent_broker_db_url = URL(**voevent_broker_db_params)

