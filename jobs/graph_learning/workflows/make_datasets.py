from queries import gds_queries


def run(args):
    if args.task == 'all' or args.task == 'link_prediction':
        print('Creating full graph projection from feature store')
        G_full = gds_queries.create_projection_from_dataset(sampling_ratio=1)
        for sampling_ratio in [0.1, 0.25, 0.5, 0.75]:
            print('Creating dataset with sampling ratio:', sampling_ratio)
            G_dataset = gds_queries.create_subgraph_dataset(
                G_full,
                sampling_ratio=sampling_ratio,
            )
            print('Writing dataset with features')
            gds_queries.create_dataset_from_projection(G_dataset)
            G_dataset.drop()
        G_full.drop()
