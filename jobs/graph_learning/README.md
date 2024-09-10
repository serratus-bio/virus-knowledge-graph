# Graph learning

## Commands

### Setup

- `make etl-env`: Create template .env file. Used to provide ML image with Neo4j read creditials.

### ML workflows

- `make ml-dataset`: Create random-walk based dataset using configured projection schema and sampling ratio.
- `make lp-pyg`: Run Pytorch Geometric link-prediction task on dataset.
- `make lp-gds`: Run Neo4j GDS link-prediciton task on dataset.
- `make lp-nx`: Run networkx link-prediction task on dataset.

### Container management

- `make ml`: build docker image without running any commands.
- `make ml-connect`: connect to running docker image.

## Neo4j Graph Data Science (GDS)

### Overview

GDS offers a simple approach to training models and running other graph algorithms directly on the Neo4j DB server. This is the easiest approach for doing initial analysis and training, but requires the Neo4j DB server to share memory (JVM heap) and CPU for both storage and training.

The general process for using GDS:

1. Create a subgraph projection with the relevant nodes, edges, and properties needed for training then store in the Neo4j graph catalog. These graph projections may include virtual nodes or edges not in the original graph.
1. Run the graph algorithm or a graph ML job using a pipeline with train and evaluation steps.
1. Mutate original graph.
1. Store model weight checkpoint to disk.
1. Clean up graph projection, pipeline, and models from Neo4j catalog.

### Limitations
- Can not run cypher queries on projections
- Exported projections are in a format that is not easy to use with PyGeometric. It's easier to stream nodes and edges by property then manually reformat into more common csv structure
- Can not directly access train and test split in ML pipeline
- Can not use traditional link prediction algos on projections

### Useful References

- Main GDS docs: https://neo4j.com/docs/graph-data-science/current/
- Python Client: https://neo4j.com/docs/graph-data-science-client/current/

## PyTorch Geometric (PyG)

### Overview

- We may require more granular control over our graph learning pipeline and models. In that case, we can pull data from neo4j or psql and then use PyG for training graph models.

### Useful References

- PyG: https://pytorch-geometric.readthedocs.io/en/latest/
- Neo4j + PyG: https://neo4j.com/docs/graph-data-science-client/current/tutorials/import-sample-export-gnn/
- Neo4j + PyG: https://towardsdatascience.com/integrate-neo4j-with-pytorch-geometric-to-create-recommendations-21b0b7bc9aa
