// Create index on Palmprint:palmId. This also creates a uniqueness constraint
CREATE INDEX IF NOT EXISTS FOR (n:Palmprint) ON n.palmId

// Create Palmprint nodes in batched transactions
:auto LOAD CSV WITH HEADERS FROM "https://serratus-public.s3.amazonaws.com/graph/palmdb_nodes.csv" AS row
CALL {
  WITH row
  MERGE (n:Palmprint {
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
  })
} IN TRANSACTIONS OF 10000 ROWS

// Create Palmprint relationships in parallel batches
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
  MERGE (s)-[r:GLOBAL_ALIGNMENT]->(t)
  SET r.distance = toFloat(row.distance)
",
{batchSize:10000, parallel:True, retries: 3})
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages

// Create index on Host:scientificName. This also creates a uniqueness constraint
CREATE INDEX IF NOT EXISTS FOR (n:Host) ON n.scientificName

// Create Host nodes
:auto LOAD CSV WITH HEADERS FROM "https://serratus-public.s3.amazonaws.com/graph/host_nodes.csv" AS row
CALL {
  WITH row
  MERGE (n:Host {
    scientificName: row.scientific_name
  })
  SET n.taxId = row.taxonomy_id
} IN TRANSACTIONS OF 10000 ROWS


// Create Palmprint - Host edges
:auto LOAD CSV WITH HEADERS FROM "https://serratus-public.s3.amazonaws.com/graph/host_palmprint_edges.csv" AS row
CALL {
  WITH row
  MATCH
    (s:Palmprint),
    (t:Host)
  WHERE s.palmId = row.palm_id AND t.scientificName = row.scientific_name
  MERGE (s)-[r:SOURCE_ORGANISM]->(t)
} IN TRANSACTIONS OF 10000 ROWS


// Create Host - Host edges
// TODO