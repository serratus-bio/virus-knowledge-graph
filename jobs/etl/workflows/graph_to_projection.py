from queries import projection_queries


PROJECTION_VERSION = 4


# TODO: better handle versioning to avoid duplicate/shared values
def run(args):
    projection_version = args.task if type(
        args.task) == int else PROJECTION_VERSION

    # All versions include taxons
    if projection_version >= 1:
        print('Processing Taxon nodes')
        query_results = projection_queries.get_taxon_nodes()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='taxon_nodes.csv',
            projection_version=projection_version,
        )

        print('Processing Taxon HAS_PARENT edges')
        query_results = projection_queries.get_has_parent_edges()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='has_parent_edges.csv',
            projection_version=projection_version,
        )

    # v1 uses all palmprints
    if projection_version == 1:
        print('Processing Palmprint nodes')
        query_results = projection_queries.get_palmprint_nodes()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='palmprint_nodes.csv',
            projection_version=projection_version,
        )

        print('Processing Palmprint HAS_SOTU edges')
        query_results = projection_queries.get_has_sotu_edges()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='has_sotu_edges.csv',
            projection_version=projection_version,
        )

        print('Processing Palmprint HAS_HOST edges')
        query_results = projection_queries.get_palmprint_has_host_edges()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='palmprint_has_host_edges.csv',
            projection_version=projection_version,
        )

    #  > v2 uses only SOTU palmprints
    if projection_version > 2:
        print('Processing SOTU nodes')
        query_results = projection_queries.get_sotu_nodes()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='sotu_nodes.csv',
            projection_version=projection_version,
        )

        print('Processing SOTU HAS_HOST edges')
        query_results = projection_queries.get_sotu_has_host_edges()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='sotu_has_host_edges.csv',
            projection_version=projection_version,
        )

    # v3 includes sequence alignment edges between SOTUs
    if projection_version >= 3:
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
                projection_version=projection_version,
                mode='a' if cursor > 0 else 'w',
            )
            cursor += page_size
            if len(query_results) < page_size:
                break

    # v4 includes has_potential_taxon edges between SOTU-Taxon
    if projection_version >= 4:
        print('Processing SOTU HAS_POTENTIAL_TAXON edges')
        query_results = projection_queries.get_sotu_has_potential_taxon()
        projection_queries.write_to_disk(
            query_results=query_results,
            file_name='sotu_has_potential_taxon_edges.csv',
            projection_version=projection_version,
        )
