import time
from datasources.neo4j import Neo4jConnection

conn = Neo4jConnection(uri="bolt://35.174.107.132:7687",
                       user="neo4j",
                       pwd="")

def add_constraints():
    conn.query('CREATE INDEX IF NOT EXISTS FOR (n:SRA) ON n.runId')
    conn.query('CREATE INDEX IF NOT EXISTS FOR (n:Palmprint) ON n.palmId')
    conn.query('CREATE INDEX IF NOT EXISTS FOR (n:Taxon) ON n.taxId')
    conn.query('CREATE INDEX IF NOT EXISTS FOR (n:Taxon) ON n.scientificName')


def batch_insert_data(query, rows, batch_size=10000):
    total = 0
    batch = 0
    start = time.time()
    result = None
    while batch * batch_size < len(rows):
        res = conn.query(query,
                         parameters = {'rows': rows[batch*batch_size:(batch+1)*batch_size].to_dict('records')})
        total += res[0]['total']
        batch += 1
        result = {
            "total": total,
            "batches": batch,
            "time": time.time() - start
        }
    return result


###### SRA ######


def add_sra_nodes(rows, batch_size=10000):
    query = '''
            MERGE (n:SRA {runId: row.run_id})
            SET n += {
                avgLength: toInteger(row.avg_length),
                bases: toInteger(row.bases),
                spots: toInteger(row.spots),
                spotsWithMates: toInteger(row.spots_with_mates),
                releaseDate: datetime(replace(row.release_date, ' ', 'T'))
                experiment: row.experiment,
                sraStudy: row.sra_study,
                bioProject: row.bio_project,
                bioSample: row.bio_sample,
                sampleName: row.sample_name,
                submission: row.submission,
                projectId: row.project_id
            }
            '''
    return batch_insert_data(query, rows, batch_size)


###### Palmprint ######


def add_palmprint_nodes(rows, batch_size=10000):
    query = '''
            MERGE (n:Palmprint)
                SET n += {
                palmId: row.palm_id,
                sotu: row.sotu,
                centroid: toBoolean(row.centroid),
                taxPhylum: row.tax_phylum,
                taxClass: row.tax_class,
                taxOrder: row.tax_order,
                taxFamily: row.tax_family,
                taxGenus: row.tax_genus,
                taxSpecies: row.tax_species,
                nickname: row.nickname,
                palmprint: row.palmprint
            }
            '''
    return batch_insert_data(query, rows, batch_size)


def add_sotu_labels(rows, batch_size=10000):
    query = '''
            MATCH (n:Palmprint)
            WHERE n.centroid = true
            SET n:SOTU
            '''
    return batch_insert_data(query, rows, batch_size)


def add_palmprint_msa_edges(rows, batch_size=10000):
    query = '''
            MATCH
                (s:Palmprint),
                (t:Palmprint)
            WHERE s.palmId = row.source AND t.palmId = row.target AND toFloat(row.distance) > 0
            MERGE (s)-[r:SEQUENCE_ALIGNMENT]->(t)
            SET r.distance = toFloat(row.distance)
            '''
    return batch_insert_data(query, rows, batch_size)


def add_palmprint_sotu_edges(batch_size=10000):
    query = '''
            MATCH
                (s:Palmprint),
                (t:Palmprint)
            WHERE s.centroid = false AND t.palmId = s.sotu
            MERGE (s)-[r:HAS_SOTU]->(t)
            '''
    return batch_insert_data(query, None, batch_size)


def add_sra_palmprint_edges(rows, batch_size=10000):
    query = '''
            MATCH
                (s:SRA),
                (t:Palmprint)
            WHERE s.runId = row.run_id AND t.palmId = row.palm_id
            MERGE (s)-[r:HAS_PALMPRINT]->(t)
            '''
    return batch_insert_data(query, rows, batch_size)


###### Taxon ######


def add_taxon_nodes(rows, batch_size=10000):
    query = '''
            MERGE (n:Taxon {
                taxId: toString(toInteger(row.tax_id))
            })
            SET n.scientificName = row.scientific_name
            SET n.rank = row.rank
            SET n.potentialHosts = row.potential_hosts
            '''
    return batch_insert_data(query, rows, batch_size)


def add_taxon_edges(rows, batch_size=10000):
    query = '''
            MATCH
                (s:Taxon),
                (t:Taxon)
            WHERE s.taxId = row.tax_id AND t.taxId = row.parent_tax_id
            MERGE (s)-[r:PARENT]->(t)
            '''
    return batch_insert_data(query, rows, batch_size)

def add_sra_taxon_edges(rows, batch_size=10000):
    query = '''
            MATCH
                (s:SRA),
                (t:Taxon)
            WHERE s.runId = row.run_id AND t.taxId = row.tax_id
            MERGE (s)-[r:HAS_HOST]->(t)
            SET t:Host
            '''
    return batch_insert_data(query, rows, batch_size)
