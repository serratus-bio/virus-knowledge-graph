// Create Palmprint with sequence alignment edges subgraph projection
// Ref: https://neo4j.com/docs/graph-data-science/current/management-ops/projections/graph-project/
CALL gds.graph.project(
  'palmprintAlignment',
  'Palmprint',
  'SEQUENCE_ALIGNMENT',
)

// Weakly cluster components using weighted edges with threshold
// Ref: https://neo4j.com/docs/graph-data-science/current/algorithms/wcc/?ref=pdf-gds-fraud-detection#algorithms-wcc-examples-weighted
CALL gds.wcc.stream('palmprintAlignment', {
  relationshipWeightProperty: 'distance',
  threshold: 0.8
}) YIELD nodeId, componentId
RETURN gds.util.asNode(nodeId).name AS Name, componentId AS ComponentId
ORDER BY ComponentId, Name


// Remove unused graph to free up memory
CALL gds.graph.drop(
  'palmprintAlignment'
)