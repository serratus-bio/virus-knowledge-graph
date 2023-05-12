CALL db.schema.visualization()


MATCH q1 = (t:Taxon)<-[:HAS_HOST]-(s:SRA)-[:HAS_PALMPRINT]->(p:Palmprint)-[:HAS_SOTU]->(:SOTU), 
  q2=(t:Taxon)-[:HAS_PARENT]->(t2)
RETURN q1, q2
LIMIT 25

MATCH q1 = (t:Taxon)<-[:HAS_HOST]-(s:SRA)-[:HAS_PALMPRINT]->(p:Palmprint)
WHERE p.palmId = 'u154368'
WITH q1, collect(s.runId) as sras
UNWIND sras as sra
WITH q1, collect(DISTINCT sras[0]) AS sras2
UNWIND sras2 as sra
OPTIONAL MATCH q2 = (r1:SRA)-->(r2:SRA)
WHERE r1.runId IN sras2 AND r2.runId IN sras2
RETURN q1



// Match Hosts (source organism of sample) that don't have top level rank of viruses
// Archaea:  {taxId: '2157'}
// Bacteria: {taxId: '2'}
// Eukaryota: {taxId: '2759'}
// Viruses: {taxId: '10239'}
// Other: {taxId: '28384'}
// Unclassified: {taxId: '12908'}
MATCH (s:Host)-[:HAS_PARENT*]->(t:Taxon {taxId: '10239'}) RETURN s, (n:Host)
WITH  collect (n) as all_hosts, collect(s) as virus_host
RETURN [x in all_hosts WHERE not(x in virus_host)] as delta,
       length(all_hosts), length(virus_host)

// Children derived from same parents
START c1=node(*), c2=node(*)
MATCH c1-[:ChildOf]->parent<-[:ChildOf]-c2
WITH c1, c2, count(parent) AS parentsFound
WHERE length(c1-[:ChildOf]->()) = parentsFound
  AND length(c2-[:ChildOf]->()) = parentsFound
  AND c1 <> c2
RETURN c1, c2