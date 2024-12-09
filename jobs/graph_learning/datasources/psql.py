import os

import psycopg2


def get_logan_read_connection():
    return psycopg2.connect(
        database=os.environ.get('PG_DATABASE_LOGAN'),
        host=os.environ.get('PG_HOST'),
        user=os.environ.get('PG_USER_LOGAN'),
        password=os.environ.get('PG_PASSWORD_LOGAN'),
        port="5432")


def get_logan_write_connection():
    return psycopg2.connect(
        database=os.environ.get('PG_DATABASE_LOGAN'),
        host=os.environ.get('PG_HOST'),
        user=os.environ.get('PG_WRITE_USER'),
        password=os.environ.get('PG_WRITE_PASSWORD'),
        port="5432")

