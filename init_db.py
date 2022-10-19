import os
import psycopg2

conn = psycopg2.connect(
        host="localhost",
        database="flask_db",
        user="mert",
        password="123456")

cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS log')
cur.execute('DROP TABLE IF EXISTS online_users;')
cur.execute('DROP TABLE IF EXISTS users;')

cur.execute('CREATE TABLE users (username varchar (20) PRIMARY KEY,'
                                 'firstname varchar (50) NOT NULL,'
                                 'middlename varchar (50),'
                                 'lastname varchar (50) NOT NULL,'
                                 'birthdate date NOT NULL,'
                                 'email varchar (50) NOT NULL,'
                                 'password varchar (64) NOT NULL,'
                                 'salt varchar (8));'
                                 )
cur.execute('CREATE TABLE online_users (username varchar (20) references users(username),'
                                 'ip_address varchar (15) PRIMARY KEY,'
                                 'logindatetime timestamp NOT NULL);'
                                 )
cur.execute('CREATE TABLE log (ip_address varchar (15) NOT NULL,'
                                 'activity_timestamp timestamp NOT NULL,'
                                 'activity_url varchar (50) NOT NULL,'
                                 'activity_method varchar(10) NOT NULL);'
                                 )

conn.commit()

cur.close()
conn.close()