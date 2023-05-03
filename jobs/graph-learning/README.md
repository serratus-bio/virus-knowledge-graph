# Graph learning

## Neo4j Graph Data Science (GDS)

### Overview

GDS offers a simple approach to training models and running other graph algorithms directly on the Neo4j DB server. This is the easiest approach for doing initial analysis and training, but requires the Neo4j DB server to share memory (JVM heap) and CPU for both storage and training.

The general process for using GDS:

1. Create a subgraph projection with the relevant nodes, edges, and properties needed for training then store in the Neo4j graph catalog. These graph projections may include virtual nodes or edges not in the original graph.
1. Run the graph algorithm or a graph ML job using a pipeline with train and evaluation steps.
1. Mutate original graph.
1. Store model weight checkpoint to disk.
1. Clean up graph projection, pipeline, and models from Neo4j catalog.

### Useful References

- Main GDS docs: https://neo4j.com/docs/graph-data-science/current/
- Python Client: https://neo4j.com/docs/graph-data-science-client/current/

## PyTorch Geometric (PyG)

### Overview

- We may require more granular control over our graph learning pipeline and models. In that case, we can pull data from neo4j and psql and then use PyG for training graph models.

### Useful References

- PyG: https://pytorch-geometric.readthedocs.io/en/latest/
- Neo4j + PyG: https://neo4j.com/docs/graph-data-science-client/current/tutorials/import-sample-export-gnn/
- Neo4j + PyG: https://towardsdatascience.com/integrate-neo4j-with-pytorch-geometric-to-create-recommendations-21b0b7bc9aa
