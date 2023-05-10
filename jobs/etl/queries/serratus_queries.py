import os

from datasources.psql import get_connection
import dask.dataframe as dd

# TODO: configure with CLI arg or env vars
USE_LOCAL_CACHE = True
EXTRACT_DIR = './data/'


def write_query_to_disk(query='', cache_file_path=''):
    conn = get_connection()
    cursor = conn.cursor()
    outputquery = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)
    with open(cache_file_path, 'w') as f:
        cursor.copy_expert(outputquery, f)
    conn.close()


def read_df_from_disk(cache_file_path=''):
    try:
        # Neo4j works best with batches of 10k - 100k, this blocksize approximates that range
        df = dd.read_csv(cache_file_path, dtype='string', blocksize="1MB")
        print('Using local cached file')
        return df
    except:
        print('No local cache file found')
        return None

def get_query_results(query='', cache_filename=''):
    # reading directly from PSQL to a pandas dataframe with read_sql_query is memory intensive
    # instead, write to EBS disk then read csv into a partitioned dataframe with dask:
    # https://dask.pydata.org/en/latest/dataframe.html
    
    if not os.path.exists(EXTRACT_DIR):
        os.mkdir(EXTRACT_DIR)
    
    cache_file_path = EXTRACT_DIR + cache_filename
    if not os.path.exists(cache_file_path):
        write_query_to_disk(query, cache_file_path)

    df = read_df_from_disk(cache_file_path)
    if not USE_LOCAL_CACHE: 
        os.remove(cache_file_path) 
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
    query = ("SELECT * FROM public.palm_graph "
            "WHERE pident >= 40 AND palm_id1 != palm_id2")
    return get_query_results(
        query=query,
        cache_filename='palmprint_edges.csv'
    )


def get_sra_palmprint_df():
    query = ("SELECT srarun.run as run_id, palm_id "
        "FROM palm_sra INNER JOIN srarun ON palm_sra.run_id = srarun.run")
    return get_query_results(
        query=query,
        cache_filename='sra_palmprint_edges.csv'
    )


def get_taxon_df():
    query = ("SELECT *"
        "FROM public.tax_nodes as t1 "
        "FULL JOIN public.tax_lineage as t2 "
        "ON t1.tax_id = t2.tax_id"
    )
    return get_query_results(
        query=query,
        cache_filename='taxon_nodes.csv'
    )


def get_sra_taxon_df():
    query = "SELECT srarun.run as run_id, tax_id FROM srarun"
    return get_query_results(
        query=query,
        cache_filename='sra_taxon_edges_original.csv'
    )


def get_palmprint_taxon_edges_df():
    query = "SELECT * FROM public.palm_tax"
    return get_query_results(
        query=query,
        cache_filename='palmprint_taxon_edges.csv'
    )

