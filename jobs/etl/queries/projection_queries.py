import os

import pandas as pd
from datasources.neo4j import get_connection


conn = get_connection()

QUERY_CACHE_DIR = '/mnt/graphdata/query_cache/neo4j/'


def write_to_disk(
    query_results,
    file_name='',
    mode='w',
):
    df = pd.DataFrame([dict(record) for record in query_results])
    dir_name = QUERY_CACHE_DIR 
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
            MATCH (:Palmprint)-[r:HAS_SOTU*0..1]->(n:SOTU)
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


def get_taxon_has_parent_edges():
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


def get_palmprint_has_host_metadata_edges():
    # Get inferred Palmprint -> Taxon edges from Palmprint -> SRA -> Taxon
    # exclude all hosts that are descendants of unclassified Taxon 12908
    query = '''
            MATCH (s:Palmprint)<-[r:HAS_PALMPRINT]-(:SRA)
                -[:HAS_HOST_METADATA]->(t:Taxon)
            WHERE not (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            RETURN
                id(s) as sourceNodeId,
                s.palmId as sourceAppId,
                id(t) as targetNodeId,
                t.taxId as targetAppId,
                'HAS_HOST_METADATA' as relationshipType,
                count(*) AS count,
                avg(r.percentIdentity) as avgPercentIdentity,
                avg(r.percentIdentity) as weight
            '''
    return conn.query(query=query)


def get_sotu_has_host_metadata_edges():
    # Get inferred SOTU -> Taxon edges from Palmprint -> SOTU -> SRA -> Taxon
    # exclude all hosts that are descendants of unclassified Taxon 12908
    query = '''
            MATCH (s:SOTU)<-[:HAS_SOTU]-(:Palmprint)
                    <-[r:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST_METADATA]->(t:Taxon)
            WHERE not (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            OPTIONAL MATCH (s:SOTU)<-[r:HAS_PALMPRINT]-(:SRA)
                    -[:HAS_HOST_METADATA]->(t:Taxon)
            WHERE not (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            RETURN
                id(s) as sourceNodeId,
                s.palmId as sourceAppId,
                id(t) as targetNodeId,
                t.taxId as targetAppId,
                'HAS_HOST_METADATA' as relationshipType,
                count(*) AS count,
                avg(r.percentIdentity) as avgPercentIdentity,
                avg(r.percentIdentity) as weight
            '''
    return conn.query(query=query)


def get_sotu_has_host_stat_edges():
    # Get inferred SOTU -> Taxon edges from Palmprint -> SOTU -> SRA -> Taxon
    # Hardcode stat_threshold to 0.5
    query = '''
        CALL {
            MATCH (p:SOTU)<-[:HAS_SOTU]-(:Palmprint)
                <-[r:HAS_PALMPRINT]-(s:SRA)-[q:HAS_HOST_STAT]->()-[:HAS_PARENT*0..]->(t:Taxon {rank: 'order'})
            WHERE q.percentIdentity >= 0.5
            RETURN p, t, r, q
            UNION
            MATCH (p:SOTU)<-[r:HAS_PALMPRINT]-(s:SRA)
                -[q:HAS_HOST_STAT]->()-[:HAS_PARENT*0..]->(t:Taxon {rank: 'order'})
            WHERE q.percentIdentity >= 0.5
            RETURN p, t, r, q
        }
        WITH p, t, r, q
        RETURN
            id(p) as sourceNodeId,
            p.palmId as sourceAppId,
            id(t) as targetNodeId,
            t.taxId as targetAppId,
            'HAS_HOST_STAT' as relationshipType,
            count(*) AS count,
            avg(r.percentIdentity) as avgPercentIdentityPalmprint,
            avg(q.percentIdentity) as avgPercentIdentityStatKmers,
            avg(q.percentIdentityFull) as avgPercentIdentityStatSpots,
            avg(q.percentIdentity) * avg(r.percentIdentity) as weight
    '''
    return conn.query(query=query)


def get_sotu_sequnce_aligment_edges(
        page_size=10000,
        cursor=0,
):
    query = '''
        MATCH (s:SOTU)-[r:SEQUENCE_ALIGNMENT]->(t:SOTU)
        WHERE r.percentIdentity > 0.5
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


def get_sotu_has_inferred_taxon():
    # Get inferred SOTU -> Taxon has potential taxon edges
    # from Palmprint -> SOTU -> Taxon
    # exclude all hosts that are descendants of unclassified Taxon 12908
    query = '''
            MATCH (s:SOTU)<-[:HAS_SOTU]-(:Palmprint)
                    -[r:HAS_INFERRED_TAXON]->(t:Taxon)
            WHERE NOT (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            OPTIONAL MATCH (s:SOTU)-[r:HAS_INFERRED_TAXON]->(t:Taxon)
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


def get_tissue_nodes():
    query = '''
            MATCH (n:Tissue)
            RETURN
                id(n) as nodeId,
                n.btoId as btoId,
                n.scientificName as scientificName,
                labels(n) as labels
            '''
    return conn.query(query=query)


def get_tissue_has_parent_edges():
    query = '''
            MATCH (s:Tissue)-[r:HAS_PARENT]->(t:Tissue)
            RETURN
                id(s) as sourceNodeId,
                s.btoId as sourceBtoId,
                id(t) as targetNodeId,
                t.btoId as targetBtoId,
                type(r) as relationshipType,
                1 as weight
            '''
    return conn.query(query=query)



def get_sotu_has_tissue_metadata_edges():
    # Get inferred SOTU -> Tissue edges from Palmprint -> SOTU -> SRA -> Tissue
    query = '''
        CALL {
            MATCH (p:SOTU)<-[:HAS_SOTU]-(:Palmprint)
                <-[r:HAS_PALMPRINT]-(s:SRA)-[q:HAS_TISSUE_METADATA]->(t:Tissue)
            RETURN p, t, r, q
            UNION
            MATCH (p:SOTU)<-[r:HAS_PALMPRINT]-(s:SRA)
                -[q:HAS_TISSUE_METADATA]->(t:Tissue)
            RETURN p, t, r, q
        }
        WITH p, t, r, q
        RETURN
            id(p) as sourceNodeId,
            p.palmId as sourceAppId,
            id(t) as targetNodeId,
            t.btoId as targetAppId,
            type(q) as relationshipType,
            count(*) AS count,
            avg(r.percentIdentity) as avgPercentIdentityPalmprint,
            avg(r.percentIdentity) as weight
    '''
    return conn.query(query=query)