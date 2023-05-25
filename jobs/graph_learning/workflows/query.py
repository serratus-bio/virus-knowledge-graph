from datasources.neo4j import gds


def run(args):
    r = gds.run_cypher(
        """
        MATCH (n:Palmprint) RETURN n LIMIT 10
        """
    )
    print(len(r))
    return r
