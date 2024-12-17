# Neo4j Virus-Host Graph Database

## Docs

### READMEs
- [Machines README](./machines/README.md) for machine setup and neo4j config managment.
- [ETL README](./jobs/etl/README.md) for ETL jobs.
- [ML README](./jobs/graphlearning/README.md) for ML jobs.
- [Makefile](./Makefile) for all available commands.

### Important URLs

- AWS Cloudformation stacks for deployed resources: [neo4j-graph-server](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/resources?filteringText=&filteringStatus=active&viewNested=true&stackId=arn%3Aaws%3Acloudformation%3Aus-east-1%3A797308887321%3Astack%2Fneo4j-graph-server%2Fa813e6f0-75e2-11ef-a835-122c0cebc6e7), [neo4j-graph-worker](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/resources?filteringText=&filteringStatus=active&viewNested=true&stackId=arn%3Aaws%3Acloudformation%3Aus-east-1%3A797308887321%3Astack%2Fneo4j-graph-worker%2Fcb6d5730-944c-11ee-a270-0ebe8d2855a7)
- AWS secrets for DB user credentials: [neo4j-graph-server](https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=Neo4j-Graph-ReadOnly&region=us-east-1), [neo4j-graph-worker](https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=Neo4j-Graph&region=us-east-1) 
- AWS secrets for DB SSH key: [neo4j.pem](https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=neo4j.pem&region=us-east-1)
- S3 bucket for exported datasets and backups: [serratus-graph](https://us-east-1.console.aws.amazon.com/s3/buckets/serratus-graph?region=us-east-1&bucketType=general&tab=objects)
- Current web server URLS: [neo4j-graph-server](http://100.29.21.149:7474/), [neo4j-graph-worker](http://44.221.248.196:7474/)

## Accessing Neo4j

### Credentials

Admin user credentials are stored in [AWS secrets](https://us-east-1.console.aws.amazon.com/secretsmanager/listsecrets?region=us-east-1). Read-only server is under `Neo4j-Graph-ReadOnly`, Read-Write is under `Neo4j-Graph`. Click "Retrieve secret value" in AWS Console.

### Web browser URL

Find URL in [Cloudformation stack "Outputs"](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/). Read-only CF stack is under `neo4j-graph-server`, Read-write CF stack is under `neo4j-graph-worker`.

### (Optional) Desktop app

- Download [https://neo4j.com/download/](https://neo4j.com/download/)
- Create new project with remote connection DBMS connection `neo4j@neo4j://{URL}:7687`
