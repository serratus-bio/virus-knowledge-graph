
// Projection with Palmprint and Host nodes and UNDIRECTED_HOST edges
MATCH (source:Palmprint)
OPTIONAL MATCH (source:Palmprint)<-[:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(target:Taxon)
WITH source, target, count(*) AS countOfReads
WITH gds.alpha.graph.project(
    'palmprintHost',
    source,
    target,
    {
      sourceNodeLabels: labels(source),
      targetNodeLabels: labels(target)
    },
    {
      relationshipType: 'UNDIRECTED_HOST',
      properties: { countOfReads: countOfReads }
    },
    {
      undirectedRelationshipTypes: ['UNDIRECTED_HOST']
    }
) AS graph
RETURN graph.nodeCount AS nodeCount, graph.relationshipCount AS relationshipCount





// Inspect relationsip property
CALL gds.graph.relationshipProperty.stream('palmprintHost', 'countOfReads')
YIELD sourceNodeId, targetNodeId, propertyValue AS countOfReads
RETURN
  gds.util.asNode(sourceNodeId).palmId AS palmId,
  gds.util.asNode(targetNodeId).taxId AS taxId,
  countOfReads
ORDER BY countOfReads DESC
LIMIT 10


// Create pipeline
CALL gds.beta.pipeline.linkPrediction.create('lp-pipeline')

// Add node properties to pipeline
CALL gds.beta.pipeline.linkPrediction.addNodeProperty('lp-pipeline', 'fastRP', {
  mutateProperty: 'embedding',
  embeddingDimension: 256,
  randomSeed: 42
})

// Add the link feature
CALL gds.beta.pipeline.linkPrediction.addFeature('lp-pipeline', 'hadamard', {
  nodeProperties: ['embedding']
})

// Configure the data splits
// https://neo4j.com/docs/graph-data-science/current/machine-learning/linkprediction-pipelines/config/#linkprediction-configure-splits
CALL gds.beta.pipeline.linkPrediction.configureSplit('lp-pipeline', {
  testFraction: 0.0625, //0.0625, 0.25
  trainFraction: 0.25, //0.25, 0.6
  validationFolds: 3
})

// Add an MLP model candidate
// https://neo4j.com/docs/graph-data-science/current/machine-learning/linkprediction-pipelines/config/#linkprediction-adding-model-candidates
// gds.beta.model.list()
// CALL gds.alpha.pipeline.linkPrediction.configureAutoTuning()
CALL gds.alpha.pipeline.linkPrediction.addMLP('lp-pipeline',
  {hiddenLayerSizes: [4, 2], penalty: 1, patience: 2}
)


// Estimate memory for pipeline
CALL gds.beta.pipeline.linkPrediction.train.estimate('palmprintHost', {
  pipeline: 'lp-pipeline',
  modelName: 'lp-pipeline-model',
  targetRelationshipType: 'UNDIRECTED_HOST'
})


// Training
CALL gds.beta.pipeline.linkPrediction.train('palmprintHost', {
  pipeline: 'lp-pipeline',
  modelName: 'lp-pipeline-model',
  metrics: ['AUCPR'],
  sourceNodeLabel: 'Palmprint',
  targetNodeLabel: 'Taxon',
  targetRelationshipType: 'UNDIRECTED_HOST',
  randomSeed: 12
}) YIELD modelInfo, modelSelectionStats
RETURN
  modelInfo.bestParameters AS winningModel,
  modelInfo.metrics.AUCPR.train.avg AS avgTrainScore,
  modelInfo.metrics.AUCPR.outerTrain AS outerTrainScore,
  modelInfo.metrics.AUCPR.test AS testScore,
  [cand IN modelSelectionStats.modelCandidates | cand.metrics.AUCPR.validation.avg] AS validationScores


// Output top 5 approx predictions
CALL gds.beta.pipeline.linkPrediction.predict.stream('palmprintHost', {
  modelName: 'lp-pipeline-model',
  relationshipTypes: ['UNDIRECTED_HOST'],
  sampleRate: 0.5,
  topK: 1,
  randomJoins: 2,
  maxIterations: 3,
  // necessary for deterministic results
  concurrency: 1,
  randomSeed: 42
})
 YIELD node1, node2, probability
 RETURN gds.util.asNode(node1).palmId AS palmId, gds.util.asNode(node2).taxId AS taxId, probability
 ORDER BY probability DESC, palmId, taxId


// Output exhaustive top 5 predictions
CALL gds.beta.pipeline.linkPrediction.predict.stream('palmprintHost', {
  modelName: 'lp-pipeline-model',
  topN: 3,
  threshold: 0.5
})
 YIELD node1, node2, probability
 RETURN gds.util.asNode(node1).palmId AS palmId, gds.util.asNode(node2).taxId AS taxId, probability
 ORDER BY probability DESC, palmId, taxId


// Mutate exhaustive top 5 predictions
CALL gds.beta.pipeline.linkPrediction.predict.mutate('palmprintHost', {
  modelName: 'lp-pipeline-model',
  relationshipTypes: ['UNDIRECTED_HOST'],
  mutateRelationshipType: 'VIRUS_HOST_INTERACTION_PREDICTION',
  topN: 5,
  threshold: 0.9
}) YIELD relationshipsWritten, samplingStats

// Write approx predictions
CALL gds.beta.pipeline.linkPrediction.predict.mutate('palmprintHost', {
  modelName: 'lp-pipeline-model',
  relationshipTypes: ['UNDIRECTED_HOST'],
  mutateRelationshipType: 'VIRUS_HOST_INTERACTION_PREDICTION_APPROX',
  sampleRate: 0.5,
  topK: 1,
  randomJoins: 2,
  maxIterations: 3,
  // necessary for deterministic results
  concurrency: 1,
  randomSeed: 42
})
 YIELD relationshipsWritten, samplingStats


// Store model to disk (not be supported without gds license)
CALL gds.alpha.model.store(
    'lp-pipeline-model'
)

// Store graph projection to DB
CALL gds.graph.export('palmprintHost', { dbName: 'neo4j-catalog-palmprintHost' })

:use system CREATE DATABASE neo4j-catalog-palmprintHost;
:use neo4j-catalog-palmprintHost MATCH (n) RETURN n;


// Clean up graph, pipeline and model from catalog
CALL gds.graph.drop(
  'palmprintHost'
)
CALL gds.beta.pipeline.drop('lp-pipeline')
CALL gds.beta.model.drop('lp-pipeline-model')