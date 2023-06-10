from queries import gds_queries, feature_queries


def run(args):
    if args.task == 'all' or args.task == 'base':
        print('Encoding existing base properties')
        feature_queries.encode_node_properties()
        feature_queries.encode_relationship_properties()

    if args.task == 'all' or args.task == 'vectorize':
        print('Vectorize features to support hetergenous graphs in GDS')
        feature_queries.vectorize_node_properties()

    if args.task == 'all' or args.task == 'enrich':
        print('Creating full projection')
        G_full = gds_queries.create_projection_from_dataset(
            sampling_ratio=1,
            enriched_features=False,
        )
        print('Mutating projection with topological features')
        gds_queries.mutate_degree_property(G_full)

        print('Writing generated features to feature store')
        gds_queries.export_projection(G_full, destination='features')
