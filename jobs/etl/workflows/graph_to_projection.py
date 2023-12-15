from queries import projection_queries


def run():
    print('Processing Taxon nodes')
    query_results = projection_queries.get_taxon_nodes()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_taxon_nodes.csv',
    )

    print('Processing Taxon HAS_PARENT edges')
    query_results = projection_queries.get_taxon_has_parent_edges()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_taxon_has_parent_edges.csv',
    )

    print('Processing Palmprint nodes')
    query_results = projection_queries.get_palmprint_nodes()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_palmprint_nodes.csv',
    )

    print('Processing Palmprint HAS_SOTU edges')
    query_results = projection_queries.get_has_sotu_edges()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_palmprint_has_sotu_edges.csv',
    )

    print('Processing Palmprint HAS_HOST_METADATA edges')
    query_results = projection_queries.get_palmprint_has_host_metadata_edges()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_palmprint_has_host_metadata_edges.csv',
    )

    print('Processing SOTU nodes')
    query_results = projection_queries.get_sotu_nodes()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_sotu_nodes.csv',
    )

    print('Processing SOTU HAS_HOST_METADATA edges')
    query_results = projection_queries.get_sotu_has_host_metadata_edges()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_sotu_has_host_metadata_edges.csv',
    )

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
            file_name='n4j_sotu_sequence_alignment_edges.csv',
            mode='a' if cursor > 0 else 'w',
        )
        cursor += page_size
        if len(query_results) < page_size:
            break

    print('Processing SOTU HAS_INFERRED_TAXON edges')
    query_results = projection_queries.get_sotu_has_inferred_taxon()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_sotu_has_inferred_taxon_edges.csv',
    )

    print('Processing SOTU HAS_HOST_STAT edges')
    query_results = projection_queries.get_sotu_has_host_stat_edges()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_sotu_has_host_stat_edges.csv',
    )

    print('Processing Tissue nodes')
    query_results = projection_queries.get_tissue_nodes()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_tissue_nodes.csv',
    )

    print('Processing Tissue HAS_PARENT edges')
    query_results = projection_queries.get_tissue_has_parent_edges()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_tissue_has_parent_edges.csv',
    )

    print('Processing SOTU HAS_TISSUE_METADATA edges')
    query_results = projection_queries.get_sotu_has_tissue_metadata_edges()
    projection_queries.write_to_disk(
        query_results=query_results,
        file_name='n4j_sotu_has_tissue_metadata_edges.csv',
    )
