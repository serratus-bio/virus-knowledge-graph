from queries import gds_queries, utils
from config.base import MODEL_CFG, DATASET_CFG


def run():
    run_uid = 'gds-lp'

    utils.store_run_artifact(
        run_uid, MODEL_CFG, 'model_cfg')
    utils.store_run_artifact(
        run_uid, DATASET_CFG, 'data_cfg')

    G_dataset = gds_queries.create_projection_from_dataset()
    utils.store_run_artifact(run_uid, G_dataset, 'dataset')

    print('Creating pipeline')
    pipeline = gds_queries.create_lp_pipeline()
    pipeline = gds_queries.add_training_method(pipeline)
    utils.store_run_artifact(run_uid, pipeline, 'pipeline')

    print('Training model')
    model, evals = gds_queries.train_model(G_dataset, pipeline)
    utils.store_run_artifact(run_uid, model, 'model')
    utils.store_run_artifact(run_uid, evals, 'eval')

    print('Streaming approx predictions')
    approx_predictions = gds_queries.stream_approx_predictions(
        G_dataset, model)
    utils.store_run_artifact(
        run_uid, approx_predictions, 'approx_predictions')

    # print('Streaming exhaustive predictions')
    # exhaustive_predictions = gds_queries.stream_exhaustive_predictions(
    #     G_dataset, model)
    # utils.store_run_artifact(
    #     run_uid, exhaustive_predictions, 'exhaustive_predictions')

    print('Cleaning up GDS catalog')
    for catalog_item in [G_dataset, pipeline, model]:
        if catalog_item:
            catalog_item.drop()
