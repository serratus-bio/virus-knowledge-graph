import time

from queries import gds_queries
from config import MODEL_CFGS, CUR_MODEL_VERSION


def run(args):
    pipeline = model = G_full = G_dataset = None
    custom_run_name = 'ft-eng-degree'
    run_uid = custom_run_name if custom_run_name else int(time.time())

    gds_queries.store_run_artifact(
        run_uid, MODEL_CFGS[CUR_MODEL_VERSION], 'config')

    G_dataset = gds_queries.create_projection_from_dataset(
        enriched_features=True)
    gds_queries.store_run_artifact(run_uid, G_dataset, 'dataset')

    if args.task == 'all' or args.task == 'pipeline':
        print('Creating pipeline')
        pipeline = gds_queries.create_lp_pipeline()
        pipeline = gds_queries.add_training_method(pipeline)
        gds_queries.store_run_artifact(run_uid, pipeline, 'pipeline')

    if args.task == 'all' or args.task == 'train':
        print('Training model')
        model, eval = gds_queries.train_model(G_dataset, pipeline)
        gds_queries.store_run_artifact(run_uid, model, 'model')
        gds_queries.store_run_artifact(run_uid, eval, 'eval')

    if args.task == 'all' or args.task == 'approx_predictions':
        print('Streaming approx predictions')
        approx_predictions = gds_queries.stream_approx_predictions(
            G_dataset, model)
        gds_queries.store_run_artifact(
            run_uid, approx_predictions, 'approx_predictions')

    # if args.task == 'all' or args.task == 'exhasutive_predictions':
    #     print('Streaming exhaustive predictions')
    #     exhaustive_predictions = gds_queries.stream_exhaustive_predictions(
    #         G_dataset, model)
    #     gds_queries.store_run_artifact(
    #         run_uid, exhaustive_predictions, 'exhaustive_predictions')

    print('Cleaning up GDS catalog')
    for catalog_item in [G_dataset, G_full, pipeline, model]:
        if catalog_item:
            catalog_item.drop()
