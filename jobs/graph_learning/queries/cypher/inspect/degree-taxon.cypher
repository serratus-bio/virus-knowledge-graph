// Create Palmprint with sequence alignment edges subgraph projection
// Ref: https://neo4j.com/docs/graph-data-science/current/management-ops/projections/graph-project/
CALL gds.graph.project(
    'SRATaxon',
    ['SRA', 'Taxon'],
    'HAS_HOST'
) YIELD
    graphName,
    nodeProjection,
    nodeCount,
    relationshipProjection,
    relationshipCount,
    projectMillis

// Automatic estimation and execution blocking.
CALL gds.degree.stream.estimate('SRATaxon')
YIELD nodeCount, relationshipCount, bytesMin, bytesMax, requiredMemory

// Find Taxon with most associated SRAs
// TODO: should only count unique experiments
CALL gds.degree.stream('SRATaxon', { relationshipTypes: ['HAS_HOST'], nodeLabels: ['Taxon'], orientation: 'UNDIRECTED' })
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).scientificName AS scientificName, score AS samples
ORDER BY samples DESC, scientificName DESC
LIMIT 10


CALL gds.degree.stats('SRATaxon', { relationshipTypes: ['HAS_HOST'], nodeLabels: ['Taxon'], orientation: 'UNDIRECTED' })
YIELD centralityDistribution
RETURN centralityDistribution.min AS minimumScore, centralityDistribution.mean AS meanScore

// Remove unused graph to free up memory
CALL gds.graph.drop(
  'SRATaxon'
)

CALL gds.degree.stream('palmprintHost', {
  nodeLabels: ['Host']
  relationshipTypes: ['UNDIRECTED_HOST'], 
  orientation: 'UNDIRECTED',
  relationshipWeightProperty: 'countOfReads'
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).taxId AS taxId, gds.util.asNode(nodeId).taxSpecies as taxSpecies,  score AS score
ORDER BY score DESC, taxId DESC
LIMIT 500

// Rank > superkingdom > phylum > class > order > family > genus

CALL gds.degree.stream('palmprintHost', {
  relationshipTypes: ['UNDIRECTED_HOST'], 
  orientation: 'UNDIRECTED',
  relationshipWeightProperty: 'countOfReads'
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) as node, score
WHERE node.taxId is not NULL
RETURN node.taxId, node.rank, node.taxSpecies, node.taxKingdom, node.taxPhylum, score
ORDER BY score DESC


https://stackoverflow.com/questions/57142419/degree-centrality-algorithm-returns-only-0-0-as-score
"Eukaryota"	18360
null	4628
"Bacteria"	2172
"Viruses"	542
"Archaea"	56

