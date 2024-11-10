from datasources.neo4j import get_connection

conn = get_connection()


def batch_insert_data(query, df):
    results = []
    for partition in df.partitions:
        print("Processing partition")
        results.append(
            conn.query(
                query,
                parameters={"rows": partition.compute().to_dict(orient="records")},
            )
        )
    return results


def add_constraints():
    # index creation also creates unique constraints
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:SRA) ON n.runId")
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:SRA) ON n.bioSample")
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:SRA) ON n.bioProject")
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:BioProject) ON n.bioProject")
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:Palmprint) ON n.palmId")
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:Taxon) ON n.taxId")
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:Taxon) ON n.scientificName")
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:Tissue) ON n.btoId")
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:SOTU) ON n.sotu")
    conn.query("CREATE INDEX IF NOT EXISTS FOR (n:Disease) ON n.doId")


# SRA #


def add_sra_nodes(rows):
    query = """
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
            """
    return batch_insert_data(query, rows)


def add_biosample_attribute(rows):
    query = """
            UNWIND $rows as row
            MATCH (n:SRA {bioSample: row.biosample})
            SET n += {
                bioSampleTitle: row.title
            }
    """
    return batch_insert_data(query, rows)


def add_biosample_sex_attribute(rows):
    query = """
            UNWIND $rows as row
            MATCH (n:SRA {bioSample: row.biosample})
            SET n += {
                bioSampleSex: row.sex
            }
    """
    return batch_insert_data(query, rows)


def add_biosample_geo_attribute(rows):
    # Note: geo attributes are stored as arrays since there can be multiple attribute values with geo information
    #  We first clear the existing attributes and then append the new ones in a list
    query = """
        CALL apoc.periodic.iterate(
        "MATCH (n:SRA) RETURN n",
        "SET n += {
            bioSampleGeoAttributeNames: [],
            bioSampleGeoAttributeValues: [],
            bioSampleGeoId: [],
            bioSampleGeoBiomeId: [],
            bioSampleGeoBiomeName: []
        }",
        {batchSize:10000, parallel:True, retries: 0})
    """
    conn.query(query=query)

    query = """
        UNWIND $rows as row
        MATCH (n:SRA {bioSample: row.biosample})
        SET n += {
            bioSampleGeoAttributeNames: coalesce(n.bioSampleGeoAttributeNames, []) + coalesce(row.attribute_name, []),
            bioSampleGeoAttributeValues: coalesce(n.bioSampleGeoAttributeValues, []) + coalesce(row.attribute_value, []),
            bioSampleGeoId: coalesce(n.bioSampleGeoId, []) + coalesce(row.gm4326_id, []),
            bioSampleGeoBiomeId: coalesce(n.bioSampleGeoBiomeId, []) + coalesce(row.gp4326_wwf_tew_id, []),
            bioSampleGeoBiomeName: coalesce(n.bioSampleGeoBiomeName, []) + coalesce(row.biome_name, [])
        }
    """
    return batch_insert_data(query, rows)


def add_bioproject_nodes(rows):
    query = """
            UNWIND $rows as row
            MATCH (n:SRA {bioProject: row.bioproject})
            USING INDEX n:SRA(bioProject)
            MERGE (m:BioProject {bioProject: row.bioproject})
            MERGE (n)-[:HAS_BIOPROJECT]->(m)
            SET m += {
                name: row.name,
                title: row.title,
                description: row.description
            }
            """
    return batch_insert_data(query, rows)


# Palmprint #


def add_palmprint_nodes(rows):
    query = """
            UNWIND $rows as row
            MERGE (n:Palmprint {palmId: row.palm_id})
                SET n += {
                sotu: row.sotu,
                centroid: toBoolean(row.centroid = 't'),
                nickname: row.nickname,
                palmprint: row.palmprint
            }
            """
    return batch_insert_data(query, rows)


def add_sotu_labels():
    query = """
            MATCH (n:Palmprint)
            WHERE n.centroid = true
            SET n:SOTU
            """
    conn.query(query=query)


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
    query = """
            UNWIND $rows as row
            MATCH (s:Palmprint), (t:Palmprint)
            WHERE toFloat(row.distance) > 0
                AND s.palmId = row.source
                AND t.palmId = row.target
            MERGE (s)-[r:SEQUENCE_ALIGNMENT]->(t)
            SET r.percentIdentity = (1 - toFloat(row.distance))
            """
    return batch_insert_data(query, rows)


def add_palmprint_sotu_edges(rows):
    query = """
            UNWIND $rows as row
            MATCH (s:Palmprint), (t:Palmprint)
            WHERE s.palmId = row.palm_id
                AND t.palmId = row.sotu
            MERGE (s)-[r:HAS_SOTU]->(t)
            SET r.percentIdentity = toFloat(row.percent_identity)/100
            """
    return batch_insert_data(query, rows)


# Taxon #


def add_taxon_nodes(rows):
    query = """
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
            """
    return batch_insert_data(query, rows)


def add_taxon_edges(rows):
    query = """
            UNWIND $rows as row
            MATCH (s:Taxon), (t:Taxon)
            WHERE s.taxId = row.tax_id AND t.taxId = row.parent_tax_id
            MERGE (s)-[r:HAS_PARENT]->(t)
            """
    return batch_insert_data(query, rows)


# Tissues #


def add_tissue_nodes(rows):
    query = """
            UNWIND $rows as row
            MERGE (n:Tissue {
                btoId: toString(row.bto_id)
            })
            SET n += {
                scientificName: row.name
            }
            """
    return batch_insert_data(query, rows)


def add_tissue_edges(rows):
    query = """
            UNWIND $rows as row
            MATCH (s:Tissue), (t:Tissue)
            WHERE s.btoId = row.bto_id AND t.btoId = row.parent_bto_id
            MERGE (s)-[r:HAS_PARENT]->(t)
            """
    return batch_insert_data(query, rows)


def add_sra_tissue_edges(rows):
    ## Alt query: runs faster on low-memory instance (using file path /var/lib/neo4j/import)
    # alt_query = '''
    #     CALL apoc.periodic.iterate(
    #     "
    #         LOAD CSV WITH HEADERS FROM 'file:///biosample_tissue_edges.csv' AS row
    #         RETURN row
    #     ","
    #         MATCH (s:SRA), (t:Tissue)
    #         WHERE s.bioSample = row.biosample_id AND t.btoId = row.bto_id
    #         MERGE (s)-[r:HAS_TISSUE_METADATA]->(t)
    #         SET r += {
    #             sourceKey: row.source,
    #             sourceValue: row.text
    #         }
    #     ",
    #     {batchSize:10000, parallel:False, retries: 0})
    #     YIELD batches, total, errorMessages
    #     RETURN batches, total, errorMessages
    # '''
    # conn.query(query=alt_query)

    query = """
        UNWIND $rows as row
        MATCH (s:SRA), (t:Tissue)
        WHERE s.bioSample = row.biosample_id AND t.btoId = row.bto_id
        MERGE (s)-[r:HAS_TISSUE_METADATA]->(t)
        SET r += {
            sourceKey: row.source,
            sourceValue: row.text
        }
    """
    return batch_insert_data(query, rows)


# Diseases #

def add_disease_nodes(rows):
    query = '''
            UNWIND $rows as row
            MERGE (n:Disease {
                doId: row.do_id
            })
            SET n += {
                name: row.name
            }
            '''
    return batch_insert_data(query, rows)


def add_disease_edges(rows):
    query = '''
            UNWIND $rows as row
            MATCH (s:Disease), (t:Disease)
            WHERE s.doId = row.do_id AND t.doId = row.parent_do_id
            MERGE (s)-[r:HAS_PARENT]->(t)
            '''
    return batch_insert_data(query, rows)


def add_sra_disease_edges(rows):
    # Note: disease attributes are stored as arrays since there can be multiple attribute values with disease information
    query = '''
            UNWIND $rows as row
            MATCH (s:SRA), (t:Disease)
            WHERE s.bioSample = row.biosample AND t.doId = row.do_id
            MERGE (s)-[r:HAS_DISEASE]->(t)
            SET r += {
                source: coalesce(r.source, []) + coalesce(row.source, []),
                text: coalesce(r.text, []) + coalesce(row.text, [])
            }
            '''
    return batch_insert_data(query, rows)


# Heterogenous edges #


def add_sra_palmprint_edges(rows):
    query = """
            UNWIND $rows as row
            MATCH (s:SRA), (t:Palmprint)
            WHERE s.runId = row.run_id AND t.palmId = row.palm_id
            MERGE (s)-[r:HAS_PALMPRINT]->(t)
            SET r.percentIdentity = toFloat(row.percent_identity)/100
    """
    return batch_insert_data(query, rows)


def add_sra_has_sotu_edges():
    query = """
            MATCH (s:SRA)-[:HAS_PALMPRINT]->(p:Palmprint)-[:HAS_SOTU]->(t:SOTU)
            MERGE (s)-[r:HAS_SOTU]->(t)
    """
    conn.query(query=query)


def add_sra_has_host_metadata_edges(rows):
    query = """
            UNWIND $rows as row
            MATCH (s:SRA), (t:Taxon)
            WHERE s.runId = row.run_id AND t.taxId = row.tax_id
            MERGE (s)-[r:HAS_HOST_METADATA]->(t)
            """
    return batch_insert_data(query, rows)


def add_sra_has_host_stat_edges(rows):
    query = """
            UNWIND $rows as row
            MATCH (s:SRA), (t:Taxon)
            WHERE s.runId = toString(row.run_id)
            AND t.taxId = toString(row.tax_id)
            AND round(toFloat(row.kmer_perc) / 100, 4) > 0
            MERGE (s)-[r:HAS_HOST_STAT]->(t)
            SET r += {
                percentIdentity: round(toFloat(row.kmer_perc) / 100, 4),
                percentIdentityFull: CASE WHEN s.spots > 0
                    THEN round(toFloat(row.kmer) / toFloat(s.spots), 4)
                    ELSE 0.0 END,
                kmer: row.kmer,
                totalKmers: row.total_kmers,
                totalSpots: s.spots
            }
            """
    return batch_insert_data(query, rows)


def add_palmprint_taxon_edges(rows):
    query = """
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
            """
    return batch_insert_data(query, rows)
