from queries import gds_queries, feature_queries


def run():
    print('Encoding existing base properties')
    feature_queries.encode_node_properties()
    print('Vectorize features to support heterogenous graphs in GDS')
    feature_queries.vectorize_node_properties()

    print('Creating full graph projection from feature store')
    G_full = gds_queries.create_projection_from_dataset(sampling_ratio=1)

    for sampling_ratio in [0.25]:  # [0.25, 0.5, 0.75, 1]:
        print('Creating dataset with sampling ratio:', sampling_ratio)
        G_dataset = gds_queries.create_random_walk_subgraph(
            G_full,
            sampling_ratio=sampling_ratio,
        )
        print('Generating and writing dataset with features')
        gds_queries.export_projection(
            G_dataset,
            sampling_ratio=sampling_ratio,
        )
        G_dataset.drop()
    G_full.drop()
