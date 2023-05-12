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



// Projection with Palmprint and Host nodes and UNDIRECTED_HOST edges
MATCH (source:Palmprint)
OPTIONAL MATCH (source:Palmprint)<-[:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(target:Taxon)
WHERE not (target)-[:HAS_PARENT*]->(:Taxon {taxId: '12908'})
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
