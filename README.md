# Neo4j Virus-Host Graph Database

## Docs

See [Machines README](./machines/README) for machine setup and neo4j config managment.
See [ETL README](./jobs/etl/README) for ETL jobs.
See [ML README](./jobs/graphlearning/README) for ML jobs.
See [Makefile](./Makefile) for all available commands.

## Accessing Neo4j

### Credentials

Admin user credentials are stored in [AWS secrets](https://us-east-1.console.aws.amazon.com/secretsmanager/listsecrets?region=us-east-1). Read-only server is under `Neo4j-Graph-ReadOnly`, Read-Write is under `Neo4j-Graph`. Click "Retrieve secret value" in AWS Console.

### Web browser URL

Find URL in [Cloudformation stack "Outputs"](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/). Read-only CF stack is under `neo4j-graph-server`, Read-write CF stack is under `neo4j-graph-worker`.

### (Optional) Desktop app

- Download [https://neo4j.com/download/](https://neo4j.com/download/)
- Create new project with remote connection DBMS connection `neo4j@neo4j://{URL}:7687`

