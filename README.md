# Neo4j Virus-Host Graph Database

## Accessing Neo4j

### URL

[http://44.201.81.84:7474](http://44.201.81.84:7474) (See [Cloudformation output](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/outputs?stackId=arn%3Aaws%3Acloudformation%3Aus-east-1%3A797308887321%3Astack%2FNeo4j-Graph%2Fac06ebb0-d94c-11ed-9d22-0e56430d81ed&filteringText=&filteringStatus=active&viewNested=true))

### Credentials

Admin user credentials are stored in [AWS secrets - Neo4j-Graph](https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=Neo4j-Graph&region=us-east-1). Click "Retrieve secret value" in AWS Console.

## PalmDB data source

- Palmprints are subsequences within an Sequence Read Archive (SRA) run
- Each unique palmprint is assigned a unique identifier, i.e. its `palm_id`
- A clustering algorithm identifies selected `palm_id` centroids to a species-like operational taxonomical unit (SOTU). The SOTU identifier is described with its given `palm_id`

## Graph Schema

### Nodes

| Label       | Attributes                                                                                                                                                                                 |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Palmprint` | `palmId`<br />`sotu`<br />`centroid`<br />`taxPhylum`<br />`taxPhylum`<br />`taxClass`<br />`taxOrder`<br />`taxFamily`<br />`taxGenus`<br />`taxSpecies`<br />`nickname`<br />`palmprint` |

### Edges

| Label              | Attributes |
| ------------------ | ---------- |
| `GLOBAL_ALIGNMENT` | `distance` |

## Cloudformation

- [Reference](https://github.com/neo4j-partners/amazon-cloud-formation-neo4j)

![architecture diagram](./aws-community.png)

## Future work

### Neo4j community edition

- Role-based security is an Enterprise Edition feature, high-availability clusters are also enterprise only
- In the future, we may want to upgrade to enterprise or rely on infrastructure as code (IaC) + GH actions (CI/CD) to write updates to the database while allowing users read-only access when writing is completed
- A possible workaround is described below:
  - To write to Neo4j, we rely on GH actions and `.cypher` script files
    - 1. Suspend `neo4j-public` user account from access
    - 2. Remove readonly constraint from config file
    - 3. Restart Neo4j instance
    - 4. Use `neo4j-private` to run write cypher queries contained in .cypher script files
  - To read from Neo4j, i.e. after write scripts are completed
    - 1. Add readonly constraint to config file
    - 2. Restart Neo4j instance
    - 2. Activate `neo4j-public` user account
