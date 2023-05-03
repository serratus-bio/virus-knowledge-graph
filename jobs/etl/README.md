## ETL

### Run with docker

Note, loading graph requires manually adding password to [neo4j database connection](queries/graph_queries.py).

```sh
# Build container and run
$ docker build -t etl . && docker run etl
```

### References:

- https://gist.github.com/nandosola/ebe2ced123e05a79e238edd6ec81fee5
