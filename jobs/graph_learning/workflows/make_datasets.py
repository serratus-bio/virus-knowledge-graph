from queries import gds_queries, feature_queries

from config.base import DIR_CFG


def run():
    # print('Encoding base properties and storing in feature vector to support HGNNs in GDS')
    # feature_queries.encode_node_properties()
    # feature_queries.vectorize_node_properties()

    print('Creating full graph projection using base features')
    G_full = gds_queries.create_projection_from_dataset(sampling_ratio=1)

    print('Generate shallow feature embeddings and mutate projection')
    G_embeddings = gds_queries.generate_shallow_embeddings(G_full)

    print('Creating dataset with sampling ratio: 1.0')
    gds_queries.export_projection(
        G_dataset,
        export_prefix=sampling_ratio,
    )

    for sampling_ratio in [0.1]:  # [0.1, 0.25, 0.5, 0.75, 1]:
        print('Creating dataset with sampling ratio:', sampling_ratio)
        G_dataset = G_full
        G_dataset = gds_queries.create_random_walk_subgraph(
            G_full,
            sampling_ratio=sampling_ratio,
        )
    
        print('Generating and writing dataset with features')
        gds_queries.export_projection(
            G_dataset,
            export_prefix=sampling_ratio,
        )
        G_dataset.drop()
    # G_full.drop()

    print('Creating dataset with Apicomplexa-associated nodes')
    apicomplexa_start_nodes = feature_queries.get_features_from_file(
        file_name='sotu_apicomplexa_nodes.csv',
        dir_name=DIR_CFG['QUERY_CACHE'],
        select_columns=['nodeId'],
    )
    G_dataset = gds_queries.create_random_walk_subgraph(
        G_full,
        sampling_ratio=sampling_ratio,
        start_nodes=apicomplexa_start_nodes['nodeId'].tolist(),
    )
    gds_queries.export_projection(
        G_dataset,
        export_prefix='apicomplexa',
    )


    print('Creating dataset with Lenarviricota-associated nodes')
    lenaviricota_start_nodes = feature_queries.get_features_from_file(
        file_name='sotu_lenaviricota_nodes.csv',
        dir_name=DIR_CFG['QUERY_CACHE'],
        select_columns=['nodeId'],
    )
    G_dataset = gds_queries.create_random_walk_subgraph(
        G_full,
        export_prefix='lenaviricota',
        start_nodes=lenaviricota_start_nodes['nodeId'].tolist(),
    )

