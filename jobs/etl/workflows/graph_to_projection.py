from queries import projection_queries


# TODO: share data config from ml container
PROJECTION_VERSION = 5


def run():
    print(PROJECTION_VERSION)

    # All versions include taxons
    if PROJECTION_VERSION >= 1:
        print('Processing Taxon nodes')
        query_results = projection_queries.get_taxon_nodes()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='taxon_nodes.csv',
            projection_version=PROJECTION_VERSION,
        )

        print('Processing Taxon HAS_PARENT edges')
        query_results = projection_queries.get_has_parent_edges()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='has_parent_edges.csv',
            projection_version=PROJECTION_VERSION,
        )

    # v1 uses all palmprints
    if PROJECTION_VERSION == 1:
        print('Processing Palmprint nodes')
        query_results = projection_queries.get_palmprint_nodes()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='palmprint_nodes.csv',
            projection_version=PROJECTION_VERSION,
        )

        print('Processing Palmprint HAS_SOTU edges')
        query_results = projection_queries.get_has_sotu_edges()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='has_sotu_edges.csv',
            projection_version=PROJECTION_VERSION,
        )

        print('Processing Palmprint HAS_HOST_METADATA edges')
        query_results = projection_queries.get_palmprint_has_host_edges()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='palmprint_has_host_edges.csv',
            projection_version=PROJECTION_VERSION,
        )

    #  > v2 uses only SOTU palmprints
    if PROJECTION_VERSION > 2:
        print('Processing SOTU nodes')
        query_results = projection_queries.get_sotu_nodes()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='sotu_nodes.csv',
            projection_version=PROJECTION_VERSION,
        )

        print('Processing SOTU HAS_HOST_METADATA edges')
        query_results = projection_queries.get_sotu_has_host_metadata_edges()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='sotu_has_host_metadata_edges.csv',
            projection_version=PROJECTION_VERSION,
        )

    # v3 includes sequence alignment edges between SOTUs
    if PROJECTION_VERSION >= 3:
        print('Processing SOTU SEQUENCE_ALIGNMENT edges')
        query_results = []
        cursor = 0
        page_size = 100000
        while True:
            query_results = projection_queries.get_sotu_sequnce_aligment_edges(
                cursor=cursor,
                page_size=page_size,
            )
            projection_queries.write_to_disk(
                query_results=query_results,
                file_name='sotu_sequence_alignment_edges.csv',
                projection_version=PROJECTION_VERSION,
                mode='a' if cursor > 0 else 'w',
            )
            cursor += page_size
            if len(query_results) < page_size:
                break

    # v4 includes has_inferred_taxon edges between SOTU-Taxon
    if PROJECTION_VERSION >= 4:
        print('Processing SOTU HAS_INFERRED_TAXON edges')
        query_results = projection_queries.get_sotu_has_inferred_taxon()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='sotu_has_inferred_taxon_edges.csv',
            projection_version=PROJECTION_VERSION,
        )

    # v5 includes has_host_stat edges between SOTU-Taxon
    if PROJECTION_VERSION >= 5:
        print('Processing SOTU HAS_HOST_STAT edges')
        query_results = projection_queries.get_sotu_has_host_stat_edges()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='sotu_has_host_stat_edges.csv',
            projection_version=PROJECTION_VERSION,
        )
