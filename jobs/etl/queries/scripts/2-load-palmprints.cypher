// Create index on Palmprint:palmId. This also creates a constraint on uniqueness
CREATE INDEX IF NOT EXISTS FOR (n:Palmprint) ON n.palmId

// Create Palmprint nodes
:auto LOAD CSV WITH HEADERS FROM "https://serratus-public.s3.amazonaws.com/graph/palmdb_nodes.csv" AS row
CALL {
  WITH row
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
} IN TRANSACTIONS OF 10000 ROWS


// Create SOTU label for Palmprints that are centroids
MATCH (n:Palmprint)
WHERE n.centroid = true
SET n:SOTU

// Create Palmprint->Palmprint SEQUENCE_ALIGNMENT relationships
CALL apoc.periodic.iterate(
"
  LOAD CSV WITH HEADERS FROM 'https://serratus-public.s3.amazonaws.com/graph/palmdb_edges.csv' AS row
  WITH row WHERE toFloat(row.distance) > 0
  MATCH
    (s:Palmprint),
    (t:Palmprint)
  WHERE s.palmId = row.source AND t.palmId = row.target
  RETURN row, s, t
","
  MERGE (s)-[r:SEQUENCE_ALIGNMENT]->(t)
  SET r.distance = toFloat(row.distance)
",
{batchSize:10000, parallel:True, retries: 3})
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages

// Create Palmprint->Palmprint HAS_SOTU relationships
CALL apoc.periodic.iterate(
"
  MATCH
    (s:Palmprint),
    (t:Palmprint)
  WHERE s.centroid = false AND t.palmId = s.sotu
  RETURN s, t
","
  MERGE (s)-[r:HAS_SOTU]->(t)
",
{batchSize:10000, parallel:True, retries: 3})
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages

// Create SRA -> Palmprint HAS_PALMPRINT relationships
CALL apoc.periodic.iterate(
"
  LOAD CSV WITH HEADERS FROM 'https://serratus-public.s3.amazonaws.com/graph/palmprint_sra_edges.csv' AS row
  MATCH
    (s:SRA),
    (t:Palmprint)
  WHERE s.runId = row.run_id AND t.palmId = row.palm_id
  RETURN row, s, t
","
  MERGE (s)-[r:HAS_PALMPRINT]->(t)
",
{batchSize:10000, parallel:True, retries: 3})
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages
