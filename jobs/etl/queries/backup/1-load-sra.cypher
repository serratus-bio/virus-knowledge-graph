
// Create index on SRA:runId. This also creates a constraint on uniqueness
CREATE INDEX IF NOT EXISTS FOR (n:SRA) ON n.runId

// Create SRA nodes
CALL apoc.periodic.iterate(
"
  LOAD CSV WITH HEADERS FROM 'https://serratus-public.s3.amazonaws.com/graph/sra_nodes.csv' AS row
  RETURN row
","
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
",
{batchSize:10000, parallel:True, retries: 3})
YIELD batches, total, errorMessages
RETURN batches, total, errorMessages

