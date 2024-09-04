# ETL

## Commands

### Setup

- `make etl-env`: Create template .env file. Used to provide ETL image with Neo4j write creditials.

### ETL workflows

- `make etl-sql`: Run ETL pipeline to populate knoweledge graph from datasources listed below.
- `make etl-clear-cache`: Clear cached queries from above command.
- `make etl-projection`: Export full knowledge graph into pytorch-friendly dataset on disk.

### Container management

- `make etl`: build docker image without running any commands.
- `make etl-connect`: connect to running docker image

## Data sources

### PalmDB

- Palmprints are subsequences within a Sequence Read Archive (SRA) run
- Each unique palmprint is assigned a unique identifier, i.e. its `palm_id`
- ([uclust](https://drive5.com/usearch/manual/uclust_algo.html)) identifies `palm_id` centroids as representatives of a species-like operational taxonomical unit (sOTU). The sOTU is described with its existing `palm_id`

```
usearch -calc_distmx otu_centroids.fa -tabbedout palmdb.40id_edge.txt \
        -maxdist 0.6 -termdist 0.7
```

Input file is palmDB (https://github.com/rcedgar/palmdb)
OTU centroids from the 03-14-21 snapshot

### NCBI

- Taxonomy data reference [README](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/taxdump_readme.txt)

### NCBI STAT

- https://www.ncbi.nlm.nih.gov/sra/docs/sra-taxonomy-analysis-tool/

### Brenda Tissue Ontology (BTO)

- https://www.ebi.ac.uk/ols4/ontologies/bto

