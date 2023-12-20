from queries import gds_queries, feature_queries

from config.base import DIR_CFG


def run():
    # print('Encoding base properties and storing in feature vector to support HGNNs in GDS')
    # feature_queries.encode_node_properties()
    # feature_queries.vectorize_node_properties()

    # print('Creating full graph projection using base features')
    # G_full = gds_queries.create_projection_from_dataset(sampling_ratio=1)

    # print('Generate shallow feature embeddings and mutate projection')
    # gds_queries.generate_shallow_embeddings(G_full)

    # print('Exporting dataset with sampling ratio: 1.0')
    # gds_queries.export_projection(
    #     G_full,
    #     export_prefix=1,
    # )

    # for sampling_ratio in [0.1]:  # [0.1, 0.25, 0.5, 0.75, 1]:
    #     print('Creating dataset with sampling ratio:', sampling_ratio)
    #     G_dataset = G_full
    #     G_dataset = gds_queries.create_random_walk_subgraph(
    #         G_full,
    #         sampling_ratio=sampling_ratio,
    #     )
    
    #     print('Exporting dataset with sampling ratio:', sampling_ratio)
    #     gds_queries.export_projection(
    #         G_dataset,
    #         export_prefix=sampling_ratio,
    #     )
    #     G_dataset.drop()
    # G_full.drop()

    print('Creating viral family and host specific datasets')
    for dataset_target in ['apicomplexa','lenarviricota']:
        print(f'Creating dataset with {dataset_target}-associated nodes')

        start_nodes_df = feature_queries.get_features_from_file(
            file_name=f'sotu_{dataset_target}_nodes.csv',
            dir_name=DIR_CFG['QUERY_CACHE_DIR'],
            select_columns=['nodeId'],
        )
        start_nodes = start_nodes_df.compute()['nodeId'].values.tolist()

        print('Creating filtered graph projection with start nodes')
        G_dataset = gds_queries.create_projection_from_dataset(
            sampling_ratio=1,
            start_nodes=start_nodes,
        )

        print('Generate shallow feature embeddings and mutate projection')
        gds_queries.generate_shallow_embeddings(G_dataset)

        print(f'Exporting dataset with {dataset_target}-associated nodes')
        gds_queries.export_projection(
            G_dataset,
            export_prefix=dataset_target,
        )
        G_dataset.drop()

    G_full.drop()
