from queries import graph_queries
from queries import feature_queries


def run(args):
    if args.task == 'all' or args.task == 'palmprint':
        print('Processing Palmprints')
        palmprint_nodes = graph_queries.get_palmprint_nodes()
        palmprint_fts = feature_queries.encode_palmprint_fts(palmprint_nodes)
        feature_queries.write_to_feature_store(
            palmprint_fts, 'palmprint_nodes.csv')

        has_sotu_edges = graph_queries.get_has_sotu_edges()
        has_sotu_edges_fts = feature_queries.encode_edges(has_sotu_edges)
        feature_queries.write_to_feature_store(
            has_sotu_edges_fts, 'has_sotu_edges.csv')

    if args.task == 'all' or args.task == 'taxon':
        print('Processing Taxons')
        taxon_nodes = graph_queries.get_taxon_nodes()
        taxon_fts = feature_queries.encode_taxon_fts(taxon_nodes)
        feature_queries.write_to_feature_store(
            taxon_fts, 'taxon_nodes.csv')

        has_parent_edges = graph_queries.get_has_parent_edges()
        has_parent_edges_fts = feature_queries.encode_edges(has_parent_edges)
        feature_queries.write_to_feature_store(
            has_parent_edges_fts, 'has_parent_edges.csv')

    if args.task == 'all' or args.task == 'edges':
        print('Processing heterogenous edges')
        has_host_edges = graph_queries.get_has_host_edges()
        has_host_edges_fts = feature_queries.encode_edges(has_host_edges)
        feature_queries.write_to_feature_store(
            has_host_edges_fts, 'has_host_edges.csv')
