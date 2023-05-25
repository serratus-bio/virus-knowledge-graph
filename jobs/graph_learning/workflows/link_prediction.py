from queries import gds_queries


def run(args):
    G = gds_queries.get_dataset_from_cache()

    if not G or args.task == 'dataset':
        print('Constructing graph projection from feature store')
        G_full = gds_queries.create_palmprint_host_projection()
        print('Constructing subgraph dataset and persisting')
        G = gds_queries.create_subgraph_dataset(G_full)
        gds_queries.store_subgraph_dataset(G)
        G_full.drop()
        gds_queries.log_graph(G)

    if args.task == 'all' or args.task == 'pipeline':
        print('Creating pipeline')
        pipeline = gds_queries.create_lp_pipeline()
        pipeline = gds_queries.add_training_method(pipeline)
        gds_queries.log_pipeline(pipeline)

    if args.task == 'all' or args.task == 'train':
        print('Training model')
        model, train_result = gds_queries.train_model(G, pipeline)
        gds_queries.store_model_results(model, train_result)

    if args.task == 'all' or args.task == 'predict_stream':
        print('Streaming predictions')
        pipeline = gds_queries.stream_predictions(G, model)

    if args.task == 'all' or args.task == 'predict_mutate':
        print('Writing predictions')
        pipeline = gds_queries.mutate_predictions(G, model)

    if args.task == 'all' or args.task == 'cleanup':
        print('Cleaning up GDS catalog')
        G.drop()
        pipeline.drop()
        model.drop()
