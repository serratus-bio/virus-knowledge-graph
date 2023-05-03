// Simple graph projection: https://neo4j.com/docs/graph-data-science/current/management-ops/projections/graph-project-cypher/
// Subgraph (filtered graph projection: https://neo4j.com/docs/graph-data-science/current/management-ops/projections/graph-project-subgraph/
// Virutal node projection: https://neo4j.com/labs/apoc/4.1/virtual/
// Pipeline: https://neo4j.com/docs/graph-data-science/current/machine-learning/linkprediction-pipelines/training/


// Training with additional context filters
// Taxon relationships: has parent
// Taxon properties: rank
// Palmprint properties: sotu, centroid
// Palmprint relationships: SEQUENCE_ALIGNMENT
// one hot encode node features that are strings

// Subgraph projection with Palmprint and Host nodes and HAS_HOST_VIRTUAL edges
MATCH (source:Palmprint)
OPTIONAL MATCH (source:Palmprint)<-[:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(target:Taxon)
OPTIONAL MATCH (target:Taxon)<-[:HAS_HOST]-(:SRA)-[:HAS_PALMPRINT]->(source:Palmprint)
WITH source, target, count(*) AS countOfReads
WITH gds.alpha.graph.project(
    'palmprintHost',
    source,
    target,
    {
      sourceNodeLabels: labels(source),
      sourceNodeProperties: source {
        palmId: coalesce(source.palmId, NULL),
        centroid: coalesce(source.centroid, NULL),
        sotu: coalesce(source.sotu, NULL)
      },
      targetNodeLabels: labels(target),
      targetNodeProperties: target {
        taxId: coalesce(target.taxId, NULL),
        rank: coalesce(target.rank, NULL),
        scientficName: coalesce(target.scientificName, NULL)
      },
    },
    {
      relationshipType: 'HOST_UNDIRECTED',
      properties: { countOfReads: countOfReads }
    },
    {
      undirectedRelationshipTypes: ['HOST_UNDIRECTED']
    }
) AS graph
RETURN graph.nodeCount AS nodeCount, graph.relationshipCount AS relationshipCount


// Inspect relationsip property
CALL gds.graph.relationshipProperty.stream('palmprintHost', 'countOfReads')
YIELD sourceNodeId, targetNodeId, propertyValue AS countOfReads
RETURN
  gds.util.asNode(sourceNodeId).name AS palmId,
  gds.util.asNode(targetNodeId).name AS taxId,
  countOfReads
ORDER BY countOfReads DESC
LIMIT 10


// Create pipeline
CALL gds.beta.pipeline.linkPrediction.create('pipe')

// Add node properties to pipeline
CALL gds.beta.pipeline.linkPrediction.addNodeProperty('pipe', 'fastRP', {
  mutateProperty: 'embedding',
  embeddingDimension: 256,
  randomSeed: 42,
  contextNodeLabels: ['City'],
  contextRelationshipTypes: ['LIVES', 'BORN']
})

// Add the link feature
CALL gds.beta.pipeline.linkPrediction.addFeature('pipe', 'hadamard', {
  nodeProperties: ['embedding', 'age']
})

// Configure the data splits
CALL gds.beta.pipeline.linkPrediction.configureSplit('pipe', {
  testFraction: 0.25,
  trainFraction: 0.6,
  validationFolds: 3
})

// Add an MLP model candidate
// https://neo4j.com/docs/graph-data-science/current/machine-learning/linkprediction-pipelines/config/#linkprediction-adding-model-candidates
// gds.beta.model.list()
// CALL gds.alpha.pipeline.linkPrediction.configureAutoTuning()
CALL gds.alpha.pipeline.linkPrediction.addMLP('pipe',
{hiddenLayerSizes: [4, 2], penalty: 1, patience: 2})


// Estimate memory for pipeline
CALL gds.beta.pipeline.linkPrediction.train.estimate('palmprintHost', {
  pipeline: 'pipe',
  modelName: 'lp-pipeline-model',
  targetRelationshipType: 'HOST_UNDIRECTED'
})
YIELD requiredMemory

// Training with context filters
CALL gds.beta.pipeline.linkPrediction.train('palmprintHost', {
  pipeline: 'pipe',
  modelName: 'lp-pipeline-model',
  metrics: ['AUCPR', 'OUT_OF_BAG_ERROR'],
  sourceNodeLabel: 'Palmprnt',
  targetNodeLabel: 'Taxon',
  targetRelationshipType: 'HOST_UNDIRECTED',
  randomSeed: 12
}) YIELD modelInfo, modelSelectionStats
RETURN
  modelInfo.bestParameters AS winningModel,
  modelInfo.metrics.AUCPR.train.avg AS avgTrainScore,
  modelInfo.metrics.AUCPR.outerTrain AS outerTrainScore,
  modelInfo.metrics.AUCPR.test AS testScore,
  [cand IN modelSelectionStats.modelCandidates | cand.metrics.AUCPR.validation.avg] AS validationScores

// Predict with context filtering
CALL gds.beta.pipeline.linkPrediction.predict.stream('palmprintHost', {
  modelName: 'lp-pipeline-model',
  topN: 5,
  threshold: 0.5
})
 YIELD node1, node2, probability
 RETURN gds.util.asNode(node1).name AS person1, gds.util.asNode(node2).name AS person2, probability
 ORDER BY probability DESC, person1



// Output exhaustive predictions
CALL gds.beta.pipeline.linkPrediction.predict.stream('palmprintHost', {
  modelName: 'lp-pipeline-model',
  topN: 5,
  threshold: 0.5
})
 YIELD node1, node2, probability
 RETURN gds.util.asNode(node1).name AS person1, gds.util.asNode(node2).name AS person2, probability
 ORDER BY probability DESC, person1


// Mutate
CALL gds.beta.pipeline.linkPrediction.predict.mutate('palmprintHost', {
  modelName: 'lp-pipeline-model',
  relationshipTypes: ['HOST_UNDIRECTED'],
  mutateRelationshipType: 'HOST_UNDIRECTED_EXHAUSTIVE_PREDICTED',
  topN: 5,
  threshold: 0.5
}) YIELD relationshipsWritten, samplingStats

// Mutate approx predictions
CALL gds.beta.pipeline.linkPrediction.predict.mutate('palmprintHost', {
  modelName: 'lp-pipeline-model',
  relationshipTypes: ['HOST_UNDIRECTED'],
  mutateRelationshipType: 'HOST_UNDIRECTED_APPROX_PREDICTED',
  sampleRate: 0.5,
  topK: 1,
  randomJoins: 2,
  maxIterations: 3,
  // necessary for deterministic results
  concurrency: 1,
  randomSeed: 42
})
 YIELD relationshipsWritten, samplingStats







// Misc


CALL gds.graph.drop(
  'palmprintHost'
)

CALL gds.beta.pipeline.drop('pipe')

CALL gds.beta.model.drop('my-model')

CALL gds.graph.list()

CALL gds.beta.model.list()

CALL gds.beta.pipeline.list()


CALL gds.graph.project.estimate('*', '*', {
    nodeCount: 310716,
    relationshipCount: 1498190
})


CALL gds.graph.relationshipProperties.stream(
  'palmprintHost',
  ['countOfReads'],
  ['HAS_HOST_VIRTUAL']
)

// Get degree centrality for Palmprint nodes
CALL gds.degree.stream('palmprintHost', {
    nodeLabels: ['Palmprint', 'Taxon'],
    relationshipTypes: ['HAS_HOST_VIRTUAL']
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).palmId AS palmId, score AS hostCount
ORDER BY hostCount DESC, palmId DESC


CALL gds.pageRank.stream('palmprintHost', {
    nodeLabels: ['Palmprint'],
    relationshipTypes: ['HAS_HOST_VIRTUAL'],
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId) AS name, score







// Virtual Edge aggregation projection
MATCH (sourceCity)<-[:IN_CITY]-(:Airport)-[:HAS_ROUTE]->(:Airport)-[:IN_CITY]->(targetCity)
WITH sourceCity, targetCity, count(*) AS countOfRoutes
WITH gds.alpha.graph.project('airports-virtual', sourceCity, targetCity,
  {},
  {relationshipType: 'VIRTUAL_ROUTE'},
  {}) AS graph
RETURN graph.nodeCount AS nodeCount, graph.relationshipCount AS relationshipCount

// Collapse SRA nodes into common palmprint node
MATCH (s:SRA)-[:HAS_PALMPRINT]->(p:Palmprint)
WITH p, collect(s) as subgraph
CALL apoc.nodes.collapse(subgraph, {properties: 'combine'}) yield from, rel, to
return from, rel, to

// Group SRA data by study
call apoc.nodes.group(['SRA'], ['sraStudy'])
yield node, relationship return *


