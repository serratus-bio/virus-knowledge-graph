import pandas as pd
import pandas.io.sql as sqlio
from datasources.psql import get_connection

USE_LOCAL_CACHE = False
USE_S3_CACHE = False

def get_query_results(query='', cache_filename=''):
    if USE_LOCAL_CACHE:
        try :
            return pd.read_csv(cache_filename)
        except:
            print('No Cache file found')

    if USE_S3_CACHE:
        # TODO: use s3 cache to prevent load on DB if no changes
        url = "https://serratus-public.s3.amazonaws.com/graph/" + cache_filename
        pass

    conn = get_connection()
    df = sqlio.read_sql_query(query, conn)
    df.to_csv(cache_filename)
    conn = None
    return df


def get_sra_df():
    query = "SELECT * FROM public.srarun"
    return get_query_results(
        query=query,
        cache_filename='sra_nodes.csv'
    )


def get_palmprint_df():
    query = "SELECT * FROM public.palmdb"
    return get_query_results(
        query=query,
        cache_filename='palmprint_nodes.csv'
    )


def get_palmprint_msa_df():
    query = "SELECT * FROM public.palm_graph"
    return get_query_results(
        query=query,
        cache_filename='palmprint_edges.csv'
    )


def get_sra_palmprint_df():
    query = "SELECT srarun.run as run_id, palm_id \
        FROM palm_sra INNER JOIN srarun ON palm_sra.run_id = srarun.run"
    return get_query_results(
        query=query,
        cache_filename='sra_palmprint_edges.csv'
    )


def get_sra_taxon_df():
    query = "SELECT srarun.run as run_id, tax_id FROM srarun"
    return get_query_results(
        query=query,
        cache_filename='sra_taxon_edges_original.csv'
    )