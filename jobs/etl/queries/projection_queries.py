import os

import pandas as pd
from datasources.neo4j import get_connection


conn = get_connection()


FEATURE_STORE_DIR = '/mnt/graphdata/features/'


def write_to_disk(query_results, file_name=''):
    df = pd.DataFrame([dict(record) for record in query_results])
    if not os.path.exists(FEATURE_STORE_DIR):
        os.makedirs(FEATURE_STORE_DIR)
    file_path = FEATURE_STORE_DIR + file_name
    df.to_csv(file_path, index=False)


def get_palmprint_nodes():
    query = '''
            MATCH (n:Palmprint)
            RETURN
                id(n) as nodeId,
                n.palmId as appId,
                n.palmId as palmId,
                labels(n) as labels,
                n.centroid as centroid
            '''
    return conn.query(query=query)


def get_has_sotu_edges():
    query = '''
            MATCH (s:Palmprint)-[r:HAS_SOTU]->(t:Palmprint)
            RETURN
                id(s) as sourceNodeId,
                s.palmId as sourceAppId,
                id(t) as targetNodeId,
                t.palmId as targetAppId,
                type(r) as relationshipType,
                1 as weight
            '''
    return conn.query(query=query)


def get_taxon_nodes():
    query = '''
            MATCH (n:Taxon)
            RETURN
                id(n) as nodeId,
                n.taxId as appId,
                n.taxId as taxId,
                labels(n) as labels,
                n.rank as rank
            '''
    return conn.query(query=query)


def get_has_parent_edges():
    query = '''
            MATCH (s:Taxon)-[r:HAS_PARENT]->(t:Taxon)
            RETURN
                id(s) as sourceNodeId,
                t.taxId as sourceAppId,
                id(t) as targetNodeId,
                t.taxId as targetAppId,
                type(r) as relationshipType,
                1 as weight
            '''
    return conn.query(query=query)


def get_has_host_edges():
    # Get inferred Palmprint -> Taxon edges
    # exclude all hosts that are descendants of unclassified Taxon 12908
    query = '''
            MATCH (s:Palmprint)<-[:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(t:Taxon)
            WHERE not (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            RETURN
                id(s) as sourceNodeId,
                s.palmId as sourceAppId,
                id(t) as targetNodeId,
                t.taxId as targetAppId,
                'HAS_HOST' as relationshipType,
                count(*) AS count
            '''
    return conn.query(query=query)
