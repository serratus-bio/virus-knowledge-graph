import os

import pandas as pd
from datasources.neo4j import get_connection


conn = get_connection()

# TODO: use query_cache dir instead of features dir
FEATURE_STORE_DIR = '/mnt/graphdata/features/'


def write_to_disk(
    query_results,
    file_name='',
    projection_version='',
    mode='w',
):
    df = pd.DataFrame([dict(record) for record in query_results])
    version_dir = f"data-v{projection_version}"
    dir_name = FEATURE_STORE_DIR + version_dir + '/'
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    file_path = dir_name + file_name
    header = True if mode == 'w' else False
    df.to_csv(file_path, index=False, mode=mode, header=header)


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


def get_sotu_nodes():
    query = '''
            MATCH (n:SOTU)
            OPTIONAL MATCH (n)<-[r:HAS_SOTU]-(:Palmprint)
            RETURN
                id(n) as nodeId,
                n.palmId as appId,
                n.palmId as palmId,
                labels(n) as labels,
                n.centroid as centroid,
                count(r) as numPalmprints
            '''
    return conn.query(query=query)


def get_has_sotu_edges():
    query = '''
            MATCH (s:Palmprint)-[r:HAS_SOTU]->(t:SOTU)
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
                s.taxId as sourceAppId,
                id(t) as targetNodeId,
                t.taxId as targetAppId,
                type(r) as relationshipType,
                1 as weight
            '''
    return conn.query(query=query)


def get_palmprint_has_host_edges():
    # Get inferred Palmprint -> Taxon edges from Palmprint -> SRA -> Taxon
    # exclude all hosts that are descendants of unclassified Taxon 12908
    query = '''
            MATCH (s:Palmprint)<-[r:HAS_PALMPRINT]-(:SRA)
                -[:HAS_HOST]->(t:Taxon)
            WHERE not (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            RETURN
                id(s) as sourceNodeId,
                s.palmId as sourceAppId,
                id(t) as targetNodeId,
                t.taxId as targetAppId,
                'HAS_HOST' as relationshipType,
                count(*) AS count,
                avg(r.percentIdentity) as avgPercentIdentity,
                avg(r.percentIdentity) as weight
            '''
    return conn.query(query=query)


def get_sotu_has_host_edges():
    # Get inferred SOTU -> Taxon edges from Palmprint -> SOTU -> SRA -> Taxon
    # exclude all hosts that are descendants of unclassified Taxon 12908
    query = '''
            MATCH (s:SOTU)<-[:HAS_SOTU]-(:Palmprint)
                    <-[r:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(t:Taxon)
            WHERE NOT (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            OPTIONAL MATCH (s:SOTU)<-[r:HAS_PALMPRINT]-(:SRA)
                    -[:HAS_HOST]->(t:Taxon)
            WHERE NOT (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            RETURN
                id(s) as sourceNodeId,
                s.palmId as sourceAppId,
                id(t) as targetNodeId,
                t.taxId as targetAppId,
                'HAS_HOST' as relationshipType,
                count(*) AS count,
                avg(r.percentIdentity) as avgPercentIdentity,
                avg(r.percentIdentity) as weight
            '''
    return conn.query(query=query)


def get_sotu_sequnce_aligment_edges(
        page_size=10000,
        cursor=0,
):
    query = '''
        MATCH (s:SOTU)-[r:SEQUENCE_ALIGNMENT]->(t:SOTU)
        WHERE r.percentIdentity > 0.7
        RETURN
            id(s) as sourceNodeId,
            s.palmId as sourceAppId,
            id(t) as targetNodeId,
            t.palmId as targetAppId,
            type(r) as relationshipType,
            r.percentIdentity as weight,
            r.percentIdentity as percentIdentity
        ORDER BY r.percentIdentity DESC
        SKIP $cursor
        LIMIT $page_size
        '''
    return conn.query(
        query,
        parameters={
            'page_size': page_size,
            'cursor': cursor,
        }
    )


def get_sotu_has_potential_taxon():
    # Get inferred SOTU -> Taxon has potential taxon edges
    # from Palmprint -> SOTU -> Taxon
    # exclude all hosts that are descendants of unclassified Taxon 12908
    query = '''
            MATCH (s:SOTU)<-[:HAS_SOTU]-(:Palmprint)
                    -[r:HAS_POTENTIAL_TAXON]->(t:Taxon)
            WHERE NOT (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            OPTIONAL MATCH (s:SOTU)-[r:HAS_POTENTIAL_TAXON]->(t:Taxon)
            WHERE NOT (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            RETURN
                id(s) as sourceNodeId,
                s.palmId as sourceAppId,
                id(t) as targetNodeId,
                t.taxId as targetAppId,
                type(r) as relationshipType,
                count(*) AS count,
                avg(r.percentIdentity) as avgPercentIdentity,
                avg(r.percentIdentity) as weight
            '''
    return conn.query(query=query)
