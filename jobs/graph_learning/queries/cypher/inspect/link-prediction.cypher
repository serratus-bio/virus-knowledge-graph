MATCH q1 = (p1:Palmprint {palmId: 'u941800'})<-[:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(t:Taxon)
OPTIONAL MATCH q2 = (:Palmprint {palmId: 'u941800'})-[:HAS_SOTU]-(p2:Palmprint)<-[:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(t:Taxon)
WITH [x in collect(p1) + collect(p2)|id(x)] as matchedIds, q1, q2
MATCH (:Taxon {taxId: '315414'})-[:HAS_HOST]-(:SRA)-[:HAS_PALMPRINT]-(p3:Palmprint)
WITH [x in collect(p3) | id(x)] as predictedIds, q1, q2, matchedIds
UNWIND matchedIds as src
UNWIND predictedIds as tgt
OPTIONAL MATCH q3 = (:Palmprint {palmId: src })-[:SEQUENCE_ALIGNMENT]-(:Palmprint {palmId: tgt}) 
RETURN q1, q2, q3


MATCH q1 = (p1:Palmprint {palmId: 'u941800'})<-[:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(t:Taxon)
OPTIONAL MATCH q2 = (:Palmprint {palmId: 'u941800'})-[:HAS_SOTU]-(p2:Palmprint)<-[:HAS_PALMPRINT]-(:SRA)-[:HAS_HOST]->(t:Taxon)
WITH [x in collect(p1) + collect(p2)|id(x)] as matchedIds, q1, q2
OPTIONAL MATCH q3 = (:Taxon {taxId: '315414'})-[:HAS_HOST]-(:SRA)-[:HAS_PALMPRINT]-(p3:Palmprint)-[:HAS_SOTU]-(:Palmprint)
RETURN q1, q2, q3


WITH ['u467257', 'u167745', 'u941800', 'u637106'] AS pids
UNWIND pids as source
MATCH q = (:Palmprint {palmId: source})-[:SEQUENCE_ALIGNMENT]-(t:Palmprint)
WHERE t.palmId in pids
RETURN q