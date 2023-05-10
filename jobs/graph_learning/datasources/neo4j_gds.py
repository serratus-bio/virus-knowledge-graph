from graphdatascience import GraphDataScience

NEO4J_URI = "bolt://35.174.107.132:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = ""

gds = GraphDataScience(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
