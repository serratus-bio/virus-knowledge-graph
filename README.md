# Neo4j Virus-Host Graph Database

## Accessing Neo4j

### Credentials

Admin user credentials are stored in [AWS secrets - Neo4j-Graph](https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=Neo4j-Graph&region=us-east-1). Click "Retrieve secret value" in AWS Console.

### Web browser URL

Find URL under `Neo4j-Graph` [Cloudformation stack outputs](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/).

### (Optional) Desktop app

- Download [https://neo4j.com/download/](https://neo4j.com/download/)
- Create new project with remote connection DBMS connection `neo4j@neo4j://{URL}:7687`

## Data sources

### PalmDB

- Palmprints are subsequences within a Sequence Read Archive (SRA) run
- Each unique palmprint is assigned a unique identifier, i.e. its `palm_id`
- ([uclust](https://drive5.com/usearch/manual/uclust_algo.html)) identifies `palm_id` centroids as representatives of a species-like operational taxonomical unit (sOTU). The sOTU is described with its existing `palm_id`

### NCBI

- Taxonomy data reference [README](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/taxdump_readme.txt)

## Graph Schema

### Nodes

Labels:

| Labels                                | Properties                                                                                                                                                                                 |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SRA`                                 | `runId` <br /> `releaseDate` <br /> `avgLength` <br /> `experiment` <br /> `sraStudy` <br /> `projectId` <br /> etc                                                                        |
| `Palmprint` <br /> `SOTU` if centroid | `palmId`<br />`sotu`<br />`centroid`<br />`taxPhylum`<br />`taxPhylum`<br />`taxClass`<br />`taxOrder`<br />`taxFamily`<br />`taxGenus`<br />`taxSpecies`<br />`nickname`<br />`palmprint` |
| `Taxon` <br /> `Host` if host of SRA  | `scientificName` <br /> `taxId`                                                                                                                                                            |

### Relationships

| Types                 | Properties |
| --------------------- | ---------- |
| `SEQUENCE_ALIGNMENT`  | `distance` |
| `HAS_HOST`            |            |
| `HAS_PALMPRINT`       |            |
| `HAS_PARENT`          |            |
| `HAS_POTENTIAL_TAXON` |            |

## Infrastructure and system management

### Running jobs

See [Machines README](./machines/README) for machine setup and neo4j config managment.
See [Makefile](./Makefile) for available commands to run jobs.

### Cloudformation

- [Reference](https://github.com/neo4j-partners/amazon-cloud-formation-neo4j)

![architecture diagram](./machines/cloudformation/aws-community.png)

### Neo4j community edition

- Role-based security is an Enterprise Edition feature, high-availability clusters are also enterprise only
- In the future, we may want to upgrade to enterprise or rely on infrastructure as code (IaC) + GH actions (CI/CD) to write updates to the database while allowing users read-only access when writing is completed
