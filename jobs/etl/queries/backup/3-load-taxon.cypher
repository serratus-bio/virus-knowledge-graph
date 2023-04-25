// Create index on Taxon:taxId and Taxon:scientificName. This also creates a constraint on uniqueness
CREATE INDEX IF NOT EXISTS FOR (n:Taxon) ON n.taxId
CREATE INDEX IF NOT EXISTS FOR (n:Taxon) ON n.scientificName

// Create Taxon nodes
CALL apoc.periodic.iterate(
"
  LOAD CSV WITH HEADERS FROM 'https://serratus-public.s3.amazonaws.com/graph/taxon_nodes.csv' AS row
  return row
","
  MERGE (n:Taxon {
    taxId: toString(toInteger(row.tax_id))
  })
  SET n.scientificName = row.scientific_name
  SET n.rank = row.rank
  SET n.potentialHosts = row.potential_hosts
",
{batchSize:10000, parallel:True, retries: 3})
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages

// Create Taxon -> Taxon PARENT relationships
:auto LOAD CSV WITH HEADERS FROM "https://serratus-public.s3.amazonaws.com/graph/taxon_nodes.csv" AS row
CALL {
  WITH row
  MATCH
    (s:Taxon),
    (t:Taxon)
  WHERE s.taxId = row.tax_id AND t.taxId = row.parent_tax_id
  MERGE (s)-[r:PARENT]->(t)
} IN TRANSACTIONS OF 10000 ROWS

// Create SRA -> Taxon HAS_HOST edges and add Host label to Taxon node
:auto LOAD CSV WITH HEADERS FROM "https://serratus-public.s3.amazonaws.com/graph/sra_taxon_edges.csv" AS row
CALL {
  WITH row
  MATCH
    (s:SRA),
    (t:Taxon)
  WHERE s.runId = row.run_id AND t.taxId = row.tax_id
  MERGE (s)-[r:HAS_HOST]->(t)
  SET t:Host
} IN TRANSACTIONS OF 10000 ROWS

// Create Palmprint -> Taxon HAS_POTENTIAL_TAXON edges
CALL apoc.periodic.iterate(
"
  LOAD CSV WITH HEADERS FROM 'https://serratus-public.s3.amazonaws.com/graph/palmprint_taxon_edges.csv' AS row
  return row
","
  MATCH (s:Palmprint), (t:Taxon)
  WHERE s.palmId = row.palm_id AND t.taxId = toString(toInteger(row.tax_id))
  MERGE (s)-[r:HAS_POTENTIAL_TAXON]->(t)
  SET r.rank = row.rank
",
{batchSize:10000, parallel:True, retries: 3})
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages
