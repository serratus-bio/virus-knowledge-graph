import os

from datasources.psql import get_connection
import dask.dataframe as dd


EXTRACT_DIR = '/mnt/graphdata/query_cache/'


def write_query_to_disk(query='', cache_file_path=''):
    conn = get_connection()
    cursor = conn.cursor()
    outputquery = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)
    with open(cache_file_path, 'w') as f:
        cursor.copy_expert(outputquery, f)
    conn.close()


def read_ddf_from_disk(cache_file_path=''):
    try:
        # Neo4j works best with batches of 10k - 100k, this blocksize
        # approximates that range
        df = dd.read_csv(cache_file_path, dtype='string', blocksize="1MB")
        print('Reading local cached file', cache_file_path)
        return df
    except BaseException:
        print('No local cache file found', cache_file_path)
        return None


def get_query_results(query='', cache_filename=''):
    # reading directly from PSQL to a pandas dataframe with read_sql_query
    # is memory intensive. instead, write to EBS disk then read csv into a
    # partitioned dataframe with dask
    # TODO: improve redundant loading of dataframe on creation

    if not os.path.exists(EXTRACT_DIR):
        os.makedirs(EXTRACT_DIR)

    cache_file_path = EXTRACT_DIR + cache_filename
    if not os.path.exists(cache_file_path):
        write_query_to_disk(query, cache_file_path)

    return read_ddf_from_disk(cache_file_path)


def get_sra_df():
    query = "SELECT * FROM public.srarun"
    return get_query_results(
        query=query,
        cache_filename='sql_sra_nodes.csv'
    )


def get_palmprint_df():
    query = "SELECT * FROM public.palmdb2"
    return get_query_results(
        query=query,
        cache_filename='sql_palmprint_nodes.csv'
    )


def get_palmprint_msa_df():
    query = ("SELECT * FROM public.palm_graph "
             "WHERE pident >= 40 AND palm_id1 != palm_id2")
    return get_query_results(
        query=query,
        cache_filename='sql_palmprint_edges.csv'
    )


def get_sra_palmprint_df():
    query = ("SELECT srarun.run as run_id, palm_id, percent_identity "
             "FROM palm_sra2 "
             "INNER JOIN srarun ON palm_sra2.run_id = srarun.run")
    return get_query_results(
        query=query,
        cache_filename='sql_sra_palmprint_edges.csv'
    )


def get_palmprint_sotu_df():
    query = ("SELECT palm_id, sotu, percent_identity "
             "FROM public.palmdb2")
    return get_query_results(
        query=query,
        cache_filename='sql_palmprint_sotu_edges.csv'
    )


def get_taxon_df():
    query = ("SELECT t1.tax_id, parent_tax_id, rank, genetic_code_id, "
             "mitochondrial_genetic_code_id, tax_kingdom, tax_phylum, "
             "tax_order, tax_family, tax_genus, tax_species "
             "FROM public.tax_nodes as t1 "
             "FULL JOIN public.tax_lineage as t2 "
             "ON t1.tax_id = t2.tax_id"
             )
    return get_query_results(
        query=query,
        cache_filename='sql_taxon_nodes.csv'
    )


def get_sra_has_host_metadata_df():
    query = "SELECT srarun.run as run_id, tax_id FROM srarun"
    return get_query_results(
        query=query,
        cache_filename='sql_sra_host_metadata_edges.csv'
    )


def get_sra_has_host_stat_df():
    query = ("SELECT sra_stat.run as run_id, sra_stat.taxid as tax_id, "
             "kmer, total_kmers, kmer_perc "
             "FROM sra_stat "
             )
    return get_query_results(
        query=query,
        cache_filename='sql_sra_host_stat_edges.csv'
    )


def get_palmprint_taxon_edges_df():
    query = "SELECT * FROM public.palm_tax"
    return get_query_results(
        query=query,
        cache_filename='sql_palmprint_taxon_edges.csv'
    )


def get_sra_tissue_df():
    query = ("SELECT bt.biosample_id, bt.bto_id, bt.source, bt.text "
             "FROM public.biosample_tissue as bt "
             "INNER JOIN public.srarun as sr "
             "ON bt.biosample_id = sr.bio_sample "
             )
    return get_query_results(
        query=query,
        cache_filename='sql_biosample_tissue_edges.csv'
    )
