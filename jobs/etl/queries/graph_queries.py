from datasources.neo4j import get_connection

conn = get_connection()


def batch_insert_data(query, df):
    results = []
    for partition in df.partitions:
        results.append(conn.query(
            query,
            parameters={
                'rows': partition.compute().to_dict(orient="records")
            }
        ))
    return results


def add_constraints():
    conn.query('CREATE INDEX IF NOT EXISTS FOR (n:SRA) ON n.runId')
    conn.query('CREATE INDEX IF NOT EXISTS FOR (n:Palmprint) ON n.palmId')
    conn.query('CREATE INDEX IF NOT EXISTS FOR (n:Taxon) ON n.taxId')
    conn.query('CREATE INDEX IF NOT EXISTS FOR (n:Taxon) ON n.scientificName')


###### SRA ######

def add_sra_nodes(rows):
    query = '''
            UNWIND $rows as row
            MERGE (n:SRA {runId: row.run})
            SET n += {
                avgLength: toInteger(row.avg_length),
                bases: toInteger(row.bases),
                spots: toInteger(row.spots),
                spotsWithMates: toInteger(row.spots_with_mates),
                releaseDate: datetime(replace(row.release_date, ' ', 'T')),
                experiment: row.experiment,
                sraStudy: row.sra_study,
                bioProject: row.bio_project,
                bioSample: row.bio_sample,
                sampleName: row.sample_name,
                submission: row.submission,
                projectId: row.project_id
            }
            '''
    return batch_insert_data(query, rows)

###### Palmprint ######


def add_palmprint_nodes(rows):
    query = '''
            UNWIND $rows as row
            MERGE (n:Palmprint {palmId: row.palm_id})
                SET n += {
                sotu: row.sotu,
                centroid: toBoolean(row.centroid = 't'),
                nickname: row.nickname,
                palmprint: row.palmprint
            }
            '''
    return batch_insert_data(query, rows)


def add_sotu_labels():
    query = '''
            MATCH (n:Palmprint)
            WHERE n.centroid = true
            SET n:SOTU
            '''
    conn.query(
        query=query
    )


def add_palmprint_msa_edges(rows):
    query_alt = '''
            UNWIND $rows as row
            MATCH (s:Palmprint), (t:Palmprint)
            WHERE toFloat(row.pident) > 0 AND s.palmId = row.palm_id1 AND t.palmId = row.palm_id2
            MERGE (s)-[r:SEQUENCE_ALIGNMENT]->(t)
            SET r.percentIdentity = toFloat(row.pident)
            '''
    query = '''
            UNWIND $rows as row
            MATCH (s:Palmprint), (t:Palmprint)
            WHERE toFloat(row.distance) > 0 AND s.palmId = row.source AND t.palmId = row.target
            MERGE (s)-[r:SEQUENCE_ALIGNMENT]->(t)
            SET r.percentIdentity = (1 - toFloat(row.distance))
            '''
    return batch_insert_data(query, rows)


def add_palmprint_sotu_edges():
    query = '''
            MATCH (s:Palmprint), (t:Palmprint)
            WHERE s.centroid = false AND t.palmId = s.sotu
            MERGE (s)-[r:HAS_SOTU]->(t)
            '''
    conn.query(
        query=query
    )


def get_palmprint_nodes():
    query = '''
            MATCH (n:Palmprint)
            RETURN id(n) as id, labels(n) as labels, n.centroid as centroid
            '''
    return conn.query(query=query)


def get_has_sotu_edges():
    query = '''
            MATCH (s:Palmprint)-[r:HAS_SOTU]->(t:Palmprint)
            RETURN id(s) as sourceNodeId, id(t) as targetNodeId, type(r) as relationshipType, 1 as weight
            '''
    return conn.query(query=query)


###### Taxon ######


def add_taxon_nodes(rows):
    query = '''
            UNWIND $rows as row
            MERGE (n:Taxon {
                taxId: toString(toInteger(row.tax_id))
            })
            SET n += {
                scientificName: row.scientific_name,
                rank: row.rank,
                taxKingdom: row.tax_kingdom,
                taxPhylum: row.tax_phylum,
                taxOrder: row.tax_order,
                taxFamily: row.tax_family,
                taxGenus: row.tax_genus,
                taxSpecies: row.tax_species
            }
            '''
    return batch_insert_data(query, rows)


def add_taxon_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (s:Taxon), (t:Taxon)
            WHERE s.taxId = row.tax_id AND t.taxId = row.parent_tax_id
            MERGE (s)-[r:HAS_PARENT]->(t)
            '''
    return batch_insert_data(query, rows)


def get_taxon_nodes():
    query = '''
            MATCH (n:Taxon)
            RETURN id(n) as id, labels(n) as labels, n.rank as rank
            '''
    return conn.query(query=query)


def get_has_parent_edges():
    query = '''
            MATCH (s:Taxon)-[r:HAS_PARENT]->(t:Taxon)
            RETURN id(s) as sourceNodeId, id(t) as targetNodeId, type(r) as relationshipType, 1 as weight
            '''
    return conn.query(query=query)


###### Heterogenous edges ######


def add_sra_palmprint_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (s:SRA), (t:Palmprint)
            WHERE s.runId = row.run_id AND t.palmId = row.palm_id
            MERGE (s)-[r:HAS_PALMPRINT]->(t)
            '''
    return batch_insert_data(query, rows)


def add_sra_taxon_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (s:SRA), (t:Taxon)
            WHERE s.runId = row.run_id AND t.taxId = row.tax_id
            MERGE (s)-[r:HAS_HOST]->(t)
            SET t:Host
            '''
    return batch_insert_data(query, rows)


def add_palmprint_taxon_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (p:Palmprint), (t:Taxon)
            WHERE p.palmId = row.palm_id AND t.taxId = row.tax_id
            MERGE (p)-[r:HAS_POTENTIAL_TAXON]->(t)
            SET r += {
                percentIdentity: toFloat(row.percent_identity),
                palmprintCoverage: toFloat(row.pp_cov)
            }
            SET p += {
                taxKingdom: row.tax_kingdom,
                taxPhylum: row.tax_phylum,
                taxOrder: row.tax_order,
                taxFamily: row.tax_family,
                taxGenus: row.tax_genus,
                taxSpecies: row.tax_species
            }
            '''
    return batch_insert_data(query, rows)


def get_has_host_edges():
    # Get inferred Palmprint -> Taxon edges
    # exclude all hosts that are descendants of unclassified Taxon 12908
    query = '''
            MATCH (s:Palmprint)<-[:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(t:Taxon)
            WHERE not (t)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
            RETURN id(s) as sourceNodeId, id(t) as targetNodeId, 'HAS_HOST' as relationshipType, count(*) AS weight
            '''
    return conn.query(query=query)
