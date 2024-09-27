import os

from datasources.psql import get_logan_connection
from .serratus_queries import (
    get_query_results,
)

def get_biosample_df():
    query = '''
        SELECT accession as biosample, title
        FROM public.biosample
    '''
    return get_query_results(
        query=query,
        cache_filename='sql_biosample_nodes.csv',
        conn=get_logan_connection(),
    )

def get_bioproject_df():
    query = '''
        SELECT accession as bioProject, name, title, description
        FROM public.bioproject
    '''
    return get_query_results(
        query=query,
        cache_filename='sql_bioproject_nodes.csv',
        conn=get_logan_connection(),
    )


def get_biosample_sex_df():
    query = '''
        SELECT biosample, sex
        FROM public.biosample_sex
    '''
    return get_query_results(
        query=query,
        cache_filename='sql_biosample_sex.csv',
        conn=get_logan_connection(),
    )
