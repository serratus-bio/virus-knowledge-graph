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


# SRA #

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


# Palmprint #


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
    # query = '''
    #         UNWIND $rows as row
    #         MATCH (s:Palmprint), (t:Palmprint)
    #         WHERE toFloat(row.pident) > 0
    #           AND s.palmId = row.palm_id1
    #               AND t.palmId = row.palm_id2
    #         MERGE (s)-[r:SEQUENCE_ALIGNMENT]->(t)
    #         SET r.percentIdentity = toFloat(row.pident)
    #         '''
    query = '''
            UNWIND $rows as row
            MATCH (s:Palmprint), (t:Palmprint)
            WHERE toFloat(row.distance) > 0
                AND s.palmId = row.source
                AND t.palmId = row.target
            MERGE (s)-[r:SEQUENCE_ALIGNMENT]->(t)
            SET r.percentIdentity = (1 - toFloat(row.distance))
            '''
    return batch_insert_data(query, rows)


def add_palmprint_sotu_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (s:Palmprint), (t:Palmprint)
            WHERE s.palmId = row.palm_id
                AND t.palmId = row.sotu
            MERGE (s)-[r:HAS_SOTU]->(t)
            SET r.percentIdentity = toFloat(row.percent_identity)/100
            '''
    return batch_insert_data(query, rows)


# Taxon #


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


# Tissues #


def add_tissue_nodes(rows):
    query = '''
            UNWIND $rows as row
            MERGE (n:Tissue {
                btoId: toString(row.bto_id)
            })
            SET n += {
                scientificName: row.name
            }
            '''
    return batch_insert_data(query, rows)


def add_tissue_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (s:Tissue), (t:Tissue)
            WHERE s.btoId = row.bto_id AND t.btoId = row.parent_bto_id
            MERGE (s)-[r:HAS_PARENT]->(t)
            '''
    return batch_insert_data(query, rows)


def add_sra_tissue_edges(rows):
    # alt_query = '''
    #     CALL apoc.periodic.iterate(
    #     "
    #         LOAD CSV WITH HEADERS FROM 'file:///sql_biosample_tissue_edges.csv' AS row
    #         MATCH (s:SRA), (t:Tissue)
    #         RETURN s, t, row
    #     ","
    #         WITH s, t, row
    #         MERGE (s)-[r:HAS_TISSUE_METADATA]->(t)
    #         SET r += {
    #             sourceKey: row.source,
    #             sourceValue: row.text
    #         }
    #     ",
    #     {batchSize:100000, parallel:True, retries: 3})
    #     YIELD batches, total, errorMessages
    #     RETURN batches, total, errorMessages
    # '''
    # conn.query( query=alt_query)

    query = '''
        UNWIND $rows as row
        MATCH (s:SRA), (t:Tissue)
        WHERE s.bioSample = row.biosample_id AND t.btoId = row.bto_id
        CREATE (s)-[r:HAS_TISSUE_METADATA]->(t)
        SET r += {
            sourceKey: row.source,
            sourceValue: row.text
        }
    '''
    return batch_insert_data(query, rows)


# Heterogenous edges #


def add_sra_palmprint_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (s:SRA), (t:Palmprint)
            WHERE s.runId = row.run_id AND t.palmId = row.palm_id
            MERGE (s)-[r:HAS_PALMPRINT]->(t)
            SET r.percentIdentity = toFloat(row.percent_identity)/100
            '''
    return batch_insert_data(query, rows)


def add_sra_has_host_metadata_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (s:SRA), (t:Taxon)
            WHERE s.runId = row.run_id AND t.taxId = row.tax_id
            MERGE (s)-[r:HAS_HOST_METADATA]->(t)
            '''
    return batch_insert_data(query, rows)


def add_sra_has_host_stat_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (s:SRA), (t:Taxon)
            WHERE s.runId = toString(row.run_id)
            AND t.taxId = toString(row.tax_id)
            AND round(toFloat(row.kmer_perc / 100), 4) > 0
            MERGE (s)-[r:HAS_HOST_STAT]->(t)
            SET r += {
                percentIdentity: round(toFloat(row.kmer_perc / 100), 4),
                percentIdentityFull: CASE WHEN s.spots > 0
                    THEN round(toFloat(row.kmer) / toFloat(s.spots), 4)
                    ELSE 0.0 END,
                kmer: row.kmer,
                totalKmers: row.total_kmers,
                totalSpots: s.spots
            }
            '''
    return batch_insert_data(query, rows)


def add_palmprint_taxon_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (p:Palmprint), (t:Taxon)
            WHERE p.palmId = row.palm_id AND t.taxId = row.tax_id
            MERGE (p)-[r:HAS_INFERRED_TAXON]->(t)
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
