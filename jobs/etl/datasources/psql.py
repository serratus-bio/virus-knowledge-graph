import psycopg2


def get_connection():
    # These credentials are public:
    # https://github.com/ababaian/serratus/wiki/SQL-Schema
    return psycopg2.connect(
        database="summary",
        host="serratus-aurora-20210406.cluster-ro-ccz9y6yshbls.us-east-1.rds.amazonaws.com",
        user="public_reader",
        password="serratus",
        port="5432")
