import os

import psycopg2


def get_serratus_connection():
    # These credentials are public:
    # https://github.com/ababaian/serratus/wiki/SQL-Schema
    return psycopg2.connect(
        database="summary",
        host="serratus-aurora-20210406.cluster-ro-ccz9y6yshbls.us-east-1.rds.amazonaws.com",
        user="public_reader",
        password="serratus",
        port="5432")

def get_logan_connection():
    return psycopg2.connect(
        database=os.environ.get('PG_DATABASE_LOGAN'),
        host=os.environ.get('PG_HOST_LOGAN'),
        user=os.environ.get('PG_USER_LOGAN'),
        password=os.environ.get('PG_PASSWORD_LOGAN'),
        port="5432")