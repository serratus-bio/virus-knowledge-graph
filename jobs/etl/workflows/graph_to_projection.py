from queries import projection_queries


def run(args):
    if args.task == 'all' or args.task == 'palmprint-host':
        print('Processing Palmprints')
        query_results = projection_queries.get_palmprint_nodes()
        projection_queries.write_to_disk(
            query_results, 'palmprint_nodes.csv')
        query_results = projection_queries.get_has_sotu_edges()
        projection_queries.write_to_disk(
            query_results, 'has_sotu_edges.csv')

        print('Processing Taxons')
        query_results = projection_queries.get_taxon_nodes()
        projection_queries.write_to_disk(
            query_results, 'taxon_nodes.csv')
        query_results = projection_queries.get_has_parent_edges()
        projection_queries.write_to_disk(
            query_results, 'has_parent_edges.csv')

        print('Processing heterogenous edges')
        query_results = projection_queries.get_has_host_edges()
        projection_queries.write_to_disk(
            query_results, 'has_host_edges.csv')
